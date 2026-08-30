"""The capture decision, and the loop that keeps making it.

One method here is the whole of the interesting behaviour: `capture_once` looks
at the live run state and decides whether it is a snapshot worth keeping, which
run it belongs to, and whether the run it was watching has ended. `watch` is that
method in a loop; everything else reads back what it wrote.
"""

import signal
import time
from collections.abc import Iterator
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import _watcher
from ._state import LiveState, UnreadableState, read_live_state
from ._store import RunRecord, RunStore, UnknownRun


class RunLog:
    """Captured runs: `runs/` on disk, and the watcher that fills it.

    Every method returns the JSON document the corresponding CLI subcommand
    prints — that document, not any object here, is the contract.
    """

    def __init__(
        self,
        *,
        live_state_path: Path,
        runs_directory: Path,
        poll_interval: float = 2.0,
    ) -> None:
        self._live_state_path = live_state_path
        self._runs_directory = runs_directory
        self._poll_interval = poll_interval
        self._store = RunStore(runs_directory)
        self._watcher_state = _watcher.WatcherState(runs_directory)

    def capture_once(self) -> dict[str, Any]:
        """Decide, once and synchronously, whether to snapshot the live state."""
        try:
            state = read_live_state(self._live_state_path)
        except FileNotFoundError:
            return self._nothing(
                "no-live-state-file", path=str(self._live_state_path)
            )
        except UnreadableState:
            # The game writes the file in place; a poll can land mid-write.
            return self._nothing("unreadable-live-state")

        if not state.has_run:
            return self._nothing("no-run-in-progress", ended_run=self._end_current())

        run = self._run_for(state)
        if state.digest in run.digests:
            return self._nothing("unchanged", run_id=run.run_id)

        snapshot = self._store.append(run, state, _now())
        self._watcher_state.record_capture(run.run_id)
        return {
            "captured": True,
            "reason": None,
            "run_id": run.run_id,
            "character": state.character,
            "wave": state.wave,
            "snapshot": str(snapshot),
        }

    def watch(self) -> Iterator[dict[str, Any]]:
        """Capture on every change until stopped, yielding each decision.

        Claims the watcher session for this process, so that `--status` can see
        it and `--stop` can end it, whether it was started in the foreground or
        detached by `--start`.
        """
        signal.signal(signal.SIGTERM, _stop_watching)
        session = self._watcher_state.claim(
            live_state_path=str(self._live_state_path),
            runs_directory=str(self._runs_directory),
            poll_interval=self._poll_interval,
        )
        yield {"watching": str(self._live_state_path), "pid": session["pid"]}
        try:
            while True:
                decision = self.capture_once()
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
        return {
            **_watcher.status(self._watcher_state),
            "live_state_path": str(self._live_state_path),
            "runs_dir": str(self._runs_directory),
        }

    def _run_for(self, state: LiveState) -> RunRecord:
        """The run this reading belongs to, opening a new one when it doesn't."""
        current = self._store.current_run()
        if current is not None:
            if current.continues(state):
                return current
            self._store.close(current, _now())
        return self._store.open_run(state, _now())

    def _end_current(self) -> str | None:
        """Close the run the game has just cleared, keeping its snapshots."""
        current = self._store.current_run()
        if current is None:
            return None
        self._store.close(current, _now())
        return current.run_id

    def _nothing(self, reason: str, **details: Any) -> dict[str, Any]:
        return {"captured": False, "reason": reason, "run_id": None, **details}

    def _environment(self) -> dict[str, str]:
        return {
            "BROTATO_RUN_STATE_PATH": str(self._live_state_path),
            "BROTATO_RUNS_DIR": str(self._runs_directory),
            "BROTATO_POLL_INTERVAL": str(self._poll_interval),
        }


class _Stopped(Exception):
    """Raised in the watch loop when the process is asked to stop."""


def _stop_watching(*_signal_arguments: Any) -> None:
    """Signal handler: turn the stop command's SIGTERM into an ordinary exit."""
    raise _Stopped


def _now() -> datetime:
    return datetime.now(timezone.utc)


__all__ = ["RunLog", "UnknownRun"]
