"""The watcher's lifecycle: one command to start it, one to stop it, one to ask.

`fswatch` is not available, so the mechanism is a poll loop in a detached child
process. What makes it inspectable is a single file, `runs/.watcher/watcher.json`,
which the running watcher owns and updates as it takes snapshots. When the
watcher stops it moves that file to `last_session.json`, so the session it just
finished — and in particular one that took no snapshots — is still there to be
reported.

"Session" here is the glossary's session: one sitting at the game, in which one
or more runs are played. Starting the watcher is how a sitting begins.
"""

import json
import os
import signal
import subprocess
import sys
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from ._clock import now_stamp
from ._store import WATCHER_DIRECTORY

_CURRENT = "watcher.json"
_LAST = "last_session.json"
_LOG = "watch.log"

_NOTHING_CAPTURED = (
    "This session captured nothing: no change to the live run state was seen "
    "while the watcher was running."
)

# How long `--start` waits for the child to claim the watcher file, and `--stop`
# waits for it to let go. Both are process handshakes, not game-speed waits.
_HANDSHAKE_TIMEOUT = 10.0

# What a session is worth reporting. `live_state_path` is among them because the
# watcher recorded the file it actually opened: status reporting the claim, rather
# than re-deriving a path, stays truthful if the save root moves under a live watcher.
_REPORTED = (
    "pid",
    "live_state_path",
    "started_at",
    "stopped_at",
    "snapshots",
    "last_snapshot_at",
    "runs",
    "note",
    "ended_unexpectedly",
)


class AlreadyWatching(Exception):
    """A watcher is already running against this `runs/` directory."""

    def __init__(self, session: dict[str, Any]) -> None:
        super().__init__(f"watcher already running as pid {session['pid']}")
        self.pid = int(session["pid"])


class WatcherState:
    """The watcher's runtime state on disk, and the questions asked of it."""

    def __init__(self, runs_directory: Path) -> None:
        self._directory = runs_directory / WATCHER_DIRECTORY

    @property
    def log_path(self) -> Path:
        return self._directory / _LOG

    def running(self) -> dict[str, Any] | None:
        """The live session, or None — retiring a claim left by a dead process."""
        session = _read(self._directory / _CURRENT)
        if session is None:
            return None
        if _alive(int(session["pid"])):
            return session
        self._retire(session, reason="watcher exited without stopping")
        return None

    def last_session(self) -> dict[str, Any] | None:
        return _read(self._directory / _LAST)

    def claim(self, **details: Any) -> dict[str, Any]:
        """Register this process as the watcher. Raises if one is already live."""
        if (live := self.running()) is not None:
            raise AlreadyWatching(live)
        session = {
            "pid": os.getpid(),
            "started_at": now_stamp(),
            "stopped_at": None,
            "snapshots": 0,
            "last_snapshot_at": None,
            "runs": [],
            **details,
        }
        _write(self._directory / _CURRENT, session)
        return session

    def record_snapshot(self, run_id: str) -> None:
        session = _read(self._directory / _CURRENT)
        if session is None:
            return
        session["snapshots"] += 1
        session["last_snapshot_at"] = now_stamp()
        if run_id not in session["runs"]:
            session["runs"].append(run_id)
        _write(self._directory / _CURRENT, session)

    def release(self) -> dict[str, Any] | None:
        session = _read(self._directory / _CURRENT)
        return None if session is None else self._retire(session)

    def _retire(
        self, session: dict[str, Any], reason: str | None = None
    ) -> dict[str, Any]:
        session["stopped_at"] = now_stamp()
        if reason is not None:
            session["ended_unexpectedly"] = reason
        session["note"] = _note(session)
        _write(self._directory / _LAST, session)
        (self._directory / _CURRENT).unlink(missing_ok=True)
        return session


def start(state: WatcherState, environment: dict[str, str]) -> dict[str, Any]:
    """Spawn a detached watcher and wait until it has claimed the session."""
    if (live := state.running()) is not None:
        return {"started": False, "reason": "already-running", "pid": live["pid"]}

    state.log_path.parent.mkdir(parents=True, exist_ok=True)
    with state.log_path.open("a") as log:
        child = subprocess.Popen(
            [sys.executable, "-m", "brotato_coaching", "watch"],
            stdout=log,
            stderr=log,
            stdin=subprocess.DEVNULL,
            start_new_session=True,
            env={**os.environ, **environment},
        )

    session = _wait_for(state.running, _HANDSHAKE_TIMEOUT)
    if session is None:
        child.terminate()
        return {
            "started": False,
            "reason": "watcher-did-not-start",
            "log": str(state.log_path),
        }
    return {
        "started": True,
        "pid": session["pid"],
        "started_at": session["started_at"],
        "log": str(state.log_path),
    }


def stop(state: WatcherState) -> dict[str, Any]:
    """Signal the watcher to stop, then report the session it just finished."""
    session = state.running()
    if session is None:
        return {
            "stopped": False,
            "reason": "not-running",
            "last_session": _report(state.last_session()),
        }

    pid = int(session["pid"])
    _signal(pid, signal.SIGTERM)
    finished = _wait_for(
        lambda: None if _alive(pid) else state.last_session(), _HANDSHAKE_TIMEOUT
    )
    if finished is None:
        # The watcher would not go, or went without tidying up after itself.
        _signal(pid, signal.SIGKILL)
        finished = state.release() or session
    return {"stopped": True, **(_report(finished) or {})}


def status(state: WatcherState) -> dict[str, Any]:
    session = state.running()
    if session is None:
        return {
            "running": False,
            "pid": None,
            "last_session": _report(state.last_session()),
        }
    return {"running": True, **(_report(session) or {}), "note": _note(session)}


def _note(session: dict[str, Any]) -> str | None:
    """The one thing a session is asked to volunteer: that it caught nothing."""
    return _NOTHING_CAPTURED if session["snapshots"] == 0 else None


def _report(session: dict[str, Any] | None) -> dict[str, Any] | None:
    if session is None:
        return None
    return {key: session[key] for key in _REPORTED if key in session}


def _wait_for(read: Callable[[], Any], timeout: float) -> Any:
    """Poll `read` until it returns something, or the timeout runs out."""
    deadline = time.monotonic() + timeout
    while True:
        value = read()
        if value is not None or time.monotonic() >= deadline:
            return value
        time.sleep(0.02)


def _signal(pid: int, number: int) -> None:
    try:
        os.kill(pid, number)
    except ProcessLookupError:
        pass


def _alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _read(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def _write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True))
