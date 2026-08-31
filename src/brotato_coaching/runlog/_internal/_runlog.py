"""The capture decision, and the loop that keeps making it.

One method here is the whole of the interesting behaviour: `capture_once` looks
at the live run state and decides whether it is a snapshot worth keeping, which
run it belongs to, and whether the run it was watching has ended. `watch` is that
method in a loop; everything else reads back what it wrote.
"""

import os
import signal
import time
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from . import _watcher
from ._clock import now
from ._state import (
    LIVE_RUN_STATE_FILENAME,
    LiveState,
    UnreadableState,
    read_live_state,
)
from ._store import RunRecord, RunStore, UnknownRun


class RunLog:
    """Captured runs: `runs/` on disk, and the watcher that fills it.

    Every method returns the JSON document the corresponding CLI subcommand
    prints — that document, not any object here, is the contract.
    """

    def __init__(self, *, runs_directory: Path, poll_interval: float = 2.0) -> None:
        """`runs_directory` is where snapshots go, and is all this needs to exist.

        Where the game keeps this player's files is *not* held here: only
        `capture_once` and `watch` read them, and they are handed the save
        directory when they are called. Everything else — starting, stopping and
        inspecting the watcher, listing runs, reading snapshots — answers from
        `runs/` alone, so none of it can be gated on finding a Brotato install.
        """
        self._runs_directory = runs_directory
        self._poll_interval = poll_interval
        self._store = RunStore(runs_directory)
        self._watcher_state = _watcher.WatcherState(runs_directory)

    def capture_once(self, save_directory: Path) -> dict[str, Any]:
        """Decide, once and synchronously, whether to snapshot the live state.

        Handed the directory, not the file: where the player's files are is
        `savefile`'s answer, and `run_v3_0.json` is this package's filename to
        know — the same rule that keeps `save_v3_0.json` over there.
        """
        live_state_path = save_directory / LIVE_RUN_STATE_FILENAME
        if (owner := self._other_watcher()) is not None:
            # Two processes writing one run's metadata would corrupt it, and the
            # watcher is already doing this work anyway.
            return self._nothing("watcher-already-running", pid=owner)
        try:
            state = read_live_state(live_state_path)
        except FileNotFoundError:
            return self._nothing("no-live-state-file", path=str(live_state_path))
        except UnreadableState:
            # The game writes the file in place; a poll can land mid-write.
            return self._nothing("unreadable-live-state")

        if not state.has_run:
            return self._nothing("no-run-in-progress", ended_run=self._end_current())

        run = self._run_for(state)
        if state.digest in run.digests:
            return self._nothing("unchanged", run_id=run.run_id)

        snapshot = self._store.append(run, state, now())
        self._watcher_state.record_snapshot(run.run_id)
        return {
            "captured": True,
            "reason": None,
            "run_id": run.run_id,
            "character": state.character,
            "wave": state.wave,
            "snapshot": str(snapshot),
        }

    def watch(self, save_directory: Path) -> Iterator[dict[str, Any]]:
        """Capture on every change until stopped, yielding each decision.

        Claims the watcher session for this process, recording the file it is
        actually watching, so that `--status` can report it and `--stop` can end
        it, whether it was started in the foreground or detached by `--start`.
        """
        live_state_path = save_directory / LIVE_RUN_STATE_FILENAME
        signal.signal(signal.SIGTERM, _stop_watching)
        session = self._watcher_state.claim(
            live_state_path=str(live_state_path),
            runs_directory=str(self._runs_directory),
            poll_interval=self._poll_interval,
        )
        yield {"watching": str(live_state_path), "pid": session["pid"]}
        try:
            while True:
                decision = self.capture_once(save_directory)
                if decision["captured"] or decision["reason"] == "no-run-in-progress":
                    yield decision
                time.sleep(self._poll_interval)
        except (KeyboardInterrupt, _Stopped):
            pass
        finally:
            self._watcher_state.release()

    def runs(self) -> dict[str, Any]:
        return {
            "runs_dir": str(self._runs_directory),
            "runs": self._store.summaries(),
        }

    def snapshots(self, run_id: str) -> dict[str, Any]:
        """One run's snapshots, read back whole. Raises `UnknownRun`."""
        return self._store.snapshots(run_id)

    def start_watcher(self) -> dict[str, Any]:
        return _watcher.start(self._watcher_state, self._environment())

    def stop_watcher(self) -> dict[str, Any]:
        return _watcher.stop(self._watcher_state)

    def watcher_status(self) -> dict[str, Any]:
        """What the watcher is doing, answered from `runs/` and nothing else.

        The watched file comes back out of the session the running watcher
        claimed, not from recomputing discovery here: status then reports what is
        *actually* being watched, which stays true even if the save root has
        since moved. With no session running there is no such file, and no key.
        """
        return {
            **_watcher.status(self._watcher_state),
            "runs_dir": str(self._runs_directory),
        }

    def _run_for(self, state: LiveState) -> RunRecord:
        """The run this reading belongs to, opening a new one when it doesn't."""
        current = self._store.current_run()
        if current is not None:
            if current.continues(state):
                return current
            self._store.close(current, now())
        return self._store.open_run(state, now())

    def _end_current(self) -> str | None:
        """Close the run the game has just cleared, keeping its snapshots."""
        current = self._store.current_run()
        if current is None:
            return None
        self._store.close(current, now())
        return current.run_id

    def _other_watcher(self) -> int | None:
        """The pid of a watcher that is not this process, if one holds `runs/`."""
        session = self._watcher_state.running()
        if session is None or int(session["pid"]) == os.getpid():
            return None
        return int(session["pid"])

    def _nothing(self, reason: str, **details: Any) -> dict[str, Any]:
        return {"captured": False, "reason": reason, "run_id": None, **details}

    def _environment(self) -> dict[str, str]:
        """What a relaunched watcher needs that it cannot work out for itself.

        Not the live state path: the child inherits this process's environment
        and working directory, so it reaches the same directory by running the
        same discovery rather than by being told the answer. These two are
        app-tier settings with no other channel, and knowing their names here is
        the one place this package reaches upwards.
        """
        return {
            "BROTATO_RUNS_DIR": str(self._runs_directory),
            "BROTATO_POLL_INTERVAL": str(self._poll_interval),
        }


class _Stopped(Exception):
    """Raised in the watch loop when the process is asked to stop."""


def _stop_watching(*_signal_arguments: Any) -> None:
    """Signal handler: turn the stop command's SIGTERM into an ordinary exit."""
    raise _Stopped

