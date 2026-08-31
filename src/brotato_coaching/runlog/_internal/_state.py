"""Reading `run_v3_0.json`: the game's live run state, as it sits on disk.

The file is written by the game while a run is in progress and reduced to
`{"current_run_state": {"has_run_state": false}}` when the run ends. Everything
this module knows about its shape is here, so the rest of the package can reason
about runs without ever indexing into the game's JSON.
"""

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


LIVE_RUN_STATE_FILENAME = "run_v3_0.json"


class UnreadableState(Exception):
    """The file exists but is not JSON — usually the game mid-write."""


@dataclass(frozen=True)
class LiveState:
    """One reading of the live run state file."""

    raw: dict[str, Any]
    digest: str

    @property
    def _run(self) -> dict[str, Any]:
        run = self.raw.get("current_run_state")
        return run if isinstance(run, dict) else {}

    @property
    def _player(self) -> dict[str, Any]:
        players = self._run.get("players_data")
        if isinstance(players, list) and players and isinstance(players[0], dict):
            return players[0]
        return {}

    @property
    def has_run(self) -> bool:
        """Whether a run is in progress at all."""
        return bool(self._run.get("has_run_state", False))

    @property
    def character(self) -> str | None:
        return _as_str(self._player.get("current_character"))

    @property
    def waves_cleared(self) -> int | None:
        """The game's `current_wave`: how many waves this run has finished.

        The storage form, not the name — the counter ticks over during the
        wave-cleared animation, so it is one behind the wave a player would say
        they are on. `wave_in_progress` is the number a reader means.
        """
        return _as_int(self._run.get("current_wave"))

    @property
    def wave_in_progress(self) -> int | None:
        """The wave being played: one past the count cleared.

        A reading stamped N is either the shop after wave N was cleared or wave
        N+1 already in progress; both describe wave N+1, so one number answers
        for both without a reader having to know which it was.
        """
        cleared = self.waves_cleared
        return None if cleared is None else cleared + 1

    @property
    def danger(self) -> int | None:
        return _as_int(self._run.get("current_difficulty"))

    @property
    def zone(self) -> int | None:
        return _as_int(self._run.get("current_zone"))

    @property
    def identity(self) -> tuple[str | None, int | None, int | None]:
        """What must hold steady for two readings to belong to the same run."""
        return (self.character, self.danger, self.zone)


def read_live_state(path: Path) -> LiveState:
    """Read the live run state.

    Raises `FileNotFoundError` if the game has never written it, and
    `UnreadableState` if it is not valid JSON — which a poll will hit whenever it
    lands mid-write, and which is not an error worth stopping for.
    """
    payload = path.read_bytes()
    try:
        raw = json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise UnreadableState(str(error)) from error
    if not isinstance(raw, dict):
        raise UnreadableState("live run state is not a JSON object")
    return LiveState(raw=raw, digest=hashlib.sha256(payload).hexdigest())


def _as_int(value: object) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _as_str(value: object) -> str | None:
    return value if isinstance(value, str) and value else None
