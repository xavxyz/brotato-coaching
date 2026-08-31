"""What the save says, said in the workspace's own words.

The save's storage forms do not survive this file. `difficulty_value` becomes
**danger**, and its ``-1`` for "never" becomes ``None``, because -1 is a thing
the file format does and not a thing that happened in a game.

What does survive is the ids. `killed_by_enemies` and `items_bought` are keyed
by integer hashes, and turning those into names needs the installed game — a
different package, and a join that happens above both.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ._document import read_document

# The save writes "never beaten" as -1 rather than omitting the record.
_NEVER = -1


@dataclass(frozen=True)
class ZoneProgress:
    """How far one character has got in one zone."""

    zone_id: int
    max_danger_beaten: int | None
    max_wave_reached: int | None

    @property
    def cleared(self) -> bool:
        return self.max_danger_beaten is not None

    def as_json_object(self) -> dict[str, Any]:
        return {
            "zone_id": self.zone_id,
            "max_danger_beaten": self.max_danger_beaten,
            "max_wave_reached": self.max_wave_reached,
        }


@dataclass(frozen=True)
class CharacterProgress:
    """How far one character has got, zone by zone."""

    character_id: str
    zones: tuple[ZoneProgress, ...]

    @property
    def cleared(self) -> bool:
        """Whether this character has ever been cleared, in any zone."""
        return any(zone.cleared for zone in self.zones)

    def as_json_object(self) -> dict[str, Any]:
        return {
            "character_id": self.character_id,
            "cleared": self.cleared,
            "zones": [zone.as_json_object() for zone in self.zones],
        }


@dataclass(frozen=True)
class Progress:
    """Everything the save knows about the player, in one value.

    ``deaths`` and ``purchases`` are keyed by the game's integer ids. Both are
    ordered by count, commonest first, because "what kills me most" is the only
    question either is ever asked.
    """

    characters: tuple[CharacterProgress, ...]
    runs_started: int
    runs_won: int
    deaths: Mapping[int, int]
    purchases: Mapping[int, int]

    def as_json_object(self) -> dict[str, Any]:
        """The report, ready for `json.dumps`.

        The shape of the output lives here rather than in the CLI: it is what
        this package has to say, and a caller that reformats it is one that has
        started to know too much.
        """
        return {
            "lifetime": {
                "runs_started": self.runs_started,
                "runs_won": self.runs_won,
            },
            "characters": [
                {
                    "character_id": character.character_id,
                    "cleared": character.cleared,
                    "zones": [
                        {
                            "zone_id": zone.zone_id,
                            "max_danger_beaten": zone.max_danger_beaten,
                            "max_wave_reached": zone.max_wave_reached,
                        }
                        for zone in character.zones
                    ],
                }
                for character in self.characters
            ],
            "deaths": {str(key): count for key, count in self.deaths.items()},
            "purchases": {str(key): count for key, count in self.purchases.items()},
        }


def read_progress(path: Path) -> Progress:
    """Roll up the save at `path`.

    Handed the file rather than going to find it: `save_file()` answers where,
    this answers what, and the two compose at the seam above.

    Raises `SaveUnavailable` when the file is not a readable save, with a
    message written for the player.
    """
    document = read_document(path)
    totals = document.get("data") or {}
    return Progress(
        characters=tuple(
            _character(entry) for entry in document.get("difficulties_unlocked") or []
        ),
        runs_started=int(totals.get("run_started", 0)),
        runs_won=int(totals.get("run_won", 0)),
        deaths=_histogram(document.get("killed_by_enemies")),
        purchases=_histogram(document.get("items_bought")),
    )


def _character(entry: Mapping[str, Any]) -> CharacterProgress:
    return CharacterProgress(
        character_id=entry["character_id"],
        zones=tuple(
            _zone(zone) for zone in entry.get("zones_difficulty_info") or []
        ),
    )


def _zone(entry: Mapping[str, Any]) -> ZoneProgress:
    beaten = entry.get("max_difficulty_beaten") or {}
    danger = beaten.get("difficulty_value", _NEVER)
    wave = beaten.get("wave_number", _NEVER)
    return ZoneProgress(
        zone_id=entry["zone_id"],
        max_danger_beaten=None if danger == _NEVER else danger,
        max_wave_reached=None if danger == _NEVER or wave == _NEVER else wave,
    )


def _histogram(counts: Mapping[str, int] | None) -> Mapping[int, int]:
    """Raw ids to counts, commonest first, ties broken by id so it is stable."""
    if not counts:
        return {}
    ordered = sorted(counts.items(), key=lambda item: (-item[1], int(item[0])))
    return {int(key): count for key, count in ordered}
