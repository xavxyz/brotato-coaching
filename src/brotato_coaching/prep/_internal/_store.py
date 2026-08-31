"""Where drills are kept, and the shape they are kept in.

One JSON file per drill, named by a sortable timestamp so the directory reads in
the order the drills were taken. The name deliberately does **not** carry the
character, the way a run directory does: a drill file sitting in a listing next
to the terminal the drill is being taken in would answer the question.

A drill file holds the truth as well as the card. It is written at the moment
the drill opens, so the answers cannot drift if the game is patched between
opening a drill and revealing it — and so a reveal needs no game data at all.
"""

from __future__ import annotations

import json
import uuid
from collections.abc import Iterator
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Sortable, second-precision, UTC. Two drills opened in the same second are told
# apart by the suffix, which is short because it is only ever typed by a person
# copying it off the line above.
_STAMP = "%Y%m%dT%H%M%SZ"
_SUFFIX_LENGTH = 4


def new_drill_id() -> str:
    return (
        f"{datetime.now(timezone.utc).strftime(_STAMP)}-"
        f"{uuid.uuid4().hex[:_SUFFIX_LENGTH]}"
    )


def now_stamp() -> str:
    return datetime.now(timezone.utc).strftime(_STAMP)


class DrillStore:
    """The drills directory, read and written one drill at a time."""

    def __init__(self, directory: Path) -> None:
        self._directory = directory

    def write(self, drill: dict[str, Any]) -> dict[str, Any]:
        self._directory.mkdir(parents=True, exist_ok=True)
        self._path(str(drill["drill_id"])).write_text(
            json.dumps(drill, indent=2) + "\n", encoding="utf-8"
        )
        return drill

    def read(self, drill_id: str) -> dict[str, Any] | None:
        try:
            drill = json.loads(self._path(drill_id).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
        return drill if isinstance(drill, dict) else None

    def all(self) -> Iterator[dict[str, Any]]:
        """Every readable drill, oldest first. A damaged file is skipped.

        History is a summary, and one unreadable file is not worth refusing the
        other thirty for.
        """
        if not self._directory.is_dir():
            return
        for path in sorted(self._directory.glob("*.json")):
            drill = self.read(path.stem)
            if drill is not None:
                yield drill

    def _path(self, drill_id: str) -> Path:
        # A drill id names a file, so it may not name a directory: a caller
        # passing a path where an id was asked for gets a refusal, not a write
        # somewhere else.
        return self._directory / f"{Path(drill_id).name}.json"
