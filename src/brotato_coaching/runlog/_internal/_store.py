"""The on-disk layout of `runs/`, and the only code that knows it.

    runs/
      20260830T200512Z-character_crazy/
        run.json                 what the run is, and what was captured when
        snapshots/0001.json      the live state, copied whole
        snapshots/0002.json
      .watcher/                  the watcher's own runtime state, not a run

Snapshots are written under the run they belong to and never rewritten, so the
game clearing `run_v3_0.json` at the end of a run cannot reach them.
"""

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from ._clock import stamp
from ._state import LiveState

WATCHER_DIRECTORY = ".watcher"

_METADATA = "run.json"
_SNAPSHOTS = "snapshots"
_WAVES_CLEARED = "waves_cleared"
# What metadata written before wave numbers were fixed called the same count.
_LEGACY_WAVE = "wave"


class UnknownRun(Exception):
    """No run by that id has been captured."""


@dataclass
class RunRecord:
    """One captured run: its identity, and the snapshots taken of it."""

    directory: Path
    metadata: dict[str, Any]

    @property
    def run_id(self) -> str:
        return str(self.metadata["run_id"])

    @property
    def digests(self) -> set[str]:
        return {snapshot["digest"] for snapshot in self.metadata["snapshots"]}

    @property
    def in_progress(self) -> bool:
        return self.metadata["ended_at"] is None

    @property
    def waves(self) -> list[int]:
        """Every wave this run was seen in, numbered as the player numbers them.

        Seen, not played: the lowest number here is where capture began, not
        where the run did. Every run captured so far has its first reading in
        the shop after wave 1, so wave 1 goes unrecorded even when the watcher
        was running before the run started.
        """
        seen = [
            wave
            for snapshot in self.metadata["snapshots"]
            if (wave := _wave_in_progress(snapshot)) is not None
        ]
        return sorted(set(seen))

    def continues(self, state: LiveState) -> bool:
        """Whether this reading belongs to this run rather than a new one.

        A different character, danger or zone is plainly a different run. So is a
        wave earlier than one already captured: the player restarted, and the
        watcher never saw the file cleared in between.
        """
        identity = (
            self.metadata["character"],
            self.metadata["danger"],
            self.metadata["zone"],
        )
        if identity != state.identity:
            return False
        waves = self.waves
        wave = state.wave_in_progress
        return not (waves and wave is not None and wave < waves[-1])

    def summary(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "character": self.metadata["character"],
            "danger": self.metadata["danger"],
            "zone": self.metadata["zone"],
            "started_at": self.metadata["started_at"],
            "last_captured_at": self.metadata["last_captured_at"],
            "ended_at": self.metadata["ended_at"],
            "in_progress": self.in_progress,
            "waves": self.waves,
            "snapshots": len(self.metadata["snapshots"]),
        }


def _waves_cleared(snapshot: dict[str, Any]) -> int | None:
    """How many waves a snapshot entry records as cleared.

    Metadata written before wave numbers were fixed stored the same count under
    `wave`, so runs captured then read back as the runs they were.
    """
    value = snapshot.get(_WAVES_CLEARED, snapshot.get(_LEGACY_WAVE))
    # `True` is an `int` here; metadata is a file on disk, not a promise.
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _wave_in_progress(snapshot: dict[str, Any]) -> int | None:
    """The wave a snapshot entry was taken in: one past the count it cleared."""
    cleared = _waves_cleared(snapshot)
    return None if cleared is None else cleared + 1


def _reported(snapshot: dict[str, Any]) -> dict[str, Any]:
    """One snapshot entry as a reader gets it, with the stored count dropped.

    A document carrying both `waves_cleared: 7` and `wave: 8` invites exactly
    the confusion the count was renamed to end, so only the wave goes out.
    """
    return {
        **{
            key: value
            for key, value in snapshot.items()
            if key not in (_WAVES_CLEARED, _LEGACY_WAVE)
        },
        "wave": _wave_in_progress(snapshot),
    }


class RunStore:
    """Every read and write under `runs/` goes through here."""

    def __init__(self, runs_directory: Path) -> None:
        self._root = runs_directory

    def open_run(self, state: LiveState, at: datetime) -> RunRecord:
        directory = self._root / self._unused_id(state, at)
        (directory / _SNAPSHOTS).mkdir(parents=True)
        run = RunRecord(
            directory=directory,
            metadata={
                "run_id": directory.name,
                "started_at": stamp(at),
                "last_captured_at": None,
                "ended_at": None,
                "character": state.character,
                "danger": state.danger,
                "zone": state.zone,
                "snapshots": [],
            },
        )
        self._write_metadata(run)
        return run

    def append(self, run: RunRecord, state: LiveState, at: datetime) -> Path:
        name = f"{len(run.metadata['snapshots']) + 1:04d}.json"
        path = run.directory / _SNAPSHOTS / name
        path.write_text(json.dumps(state.raw, indent=2, sort_keys=True))
        run.metadata["snapshots"].append(
            {
                "file": name,
                "captured_at": stamp(at),
                _WAVES_CLEARED: state.waves_cleared,
                "digest": state.digest,
            }
        )
        run.metadata["last_captured_at"] = stamp(at)
        self._write_metadata(run)
        return path

    def close(self, run: RunRecord, at: datetime) -> None:
        run.metadata["ended_at"] = stamp(at)
        self._write_metadata(run)

    def current_run(self) -> RunRecord | None:
        """The most recently started run the game has not been seen to end."""
        open_runs = [run for run in self._all() if run.in_progress]
        return open_runs[-1] if open_runs else None

    def summaries(self) -> list[dict[str, Any]]:
        return [run.summary() for run in self._all()]

    def snapshots(self, run_id: str) -> dict[str, Any]:
        """One run's captured states, oldest first, read back whole."""
        for run in self._all():
            if run.run_id == run_id:
                return {
                    **run.summary(),
                    "snapshots": [
                        {
                            **_reported(snapshot),
                            "state": json.loads(
                                (run.directory / _SNAPSHOTS / snapshot["file"])
                                .read_text()
                            ),
                        }
                        for snapshot in run.metadata["snapshots"]
                    ],
                }
        raise UnknownRun(run_id)

    def _all(self) -> list[RunRecord]:
        if not self._root.is_dir():
            return []
        runs = []
        for directory in sorted(self._root.iterdir()):
            metadata = directory / _METADATA
            if directory.name == WATCHER_DIRECTORY or not metadata.is_file():
                continue
            runs.append(
                RunRecord(directory=directory, metadata=json.loads(metadata.read_text()))
            )
        return sorted(runs, key=lambda run: (run.metadata["started_at"], run.run_id))

    def _unused_id(self, state: LiveState, at: datetime) -> str:
        stem = at.strftime("%Y%m%dT%H%M%SZ")
        if state.character:
            stem = f"{stem}-{state.character}"
        candidate, attempt = stem, 1
        while (self._root / candidate).exists():
            attempt += 1
            candidate = f"{stem}-{attempt}"
        return candidate

    def _write_metadata(self, run: RunRecord) -> None:
        (run.directory / _METADATA).write_text(
            json.dumps(run.metadata, indent=2, sort_keys=True)
        )
