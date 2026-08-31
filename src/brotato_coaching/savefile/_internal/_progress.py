"""What the save says, said in the workspace's own words.

The save's storage forms do not survive this file. `difficulty_value` becomes
**danger**, and its ``-1`` for "never" becomes ``None``, because -1 is a thing
the file format does and not a thing that happened in a game.

What does survive is the ids. `killed_by_enemies` and `items_bought` are keyed
by integer hashes, and turning those into names needs the installed game — a
different package, and a join that happens above both. What this file will take
is a function from id to name, lent by whoever is doing that joining.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
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

    ``unlocked_characters`` is the same kind of id, as a plain list: the save
    records which characters the player has access to, and it is the only place
    that says so.
    """

    characters: tuple[CharacterProgress, ...]
    unlocked_characters: tuple[int, ...]
    runs_started: int
    runs_won: int
    deaths: Mapping[int, int]
    purchases: Mapping[int, int]

    def as_json_object(
        self, name_for: Callable[[int], str | None] | None = None
    ) -> dict[str, Any]:
        """The report, ready for `json.dumps`.

        The shape of the output lives here rather than in the CLI: it is what
        this package has to say, and a caller that reformats it is one that has
        started to know too much.

        `name_for` is how a caller lends this package names it has no way to
        know: hand it a function from id to name and the histogram keys come out
        named, keep it and they come out as digits. Either way the answer is the
        same shape, so a reader that cannot resolve one id is not a reader that
        gets nothing.
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
            "unlocked_characters": sorted(
                _name(identifier, name_for) for identifier in self.unlocked_characters
            ),
            "deaths": _named(self.deaths, name_for),
            "purchases": _named(self.purchases, name_for),
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
        unlocked_characters=tuple(
            int(identifier) for identifier in document.get("characters_unlocked") or []
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


def _unnamed(_identifier: int) -> None:
    """What a caller with no names to lend supplies: no name, for anything."""
    return None


def _name(identifier: int, name_for: Callable[[int], str | None] | None) -> str:
    """One id, as its name if that is knowable and as its digits if it is not."""
    return (name_for or _unnamed)(identifier) or str(identifier)


def _named(
    histogram: Mapping[int, int], name_for: Callable[[int], str | None] | None
) -> dict[str, int]:
    """A histogram keyed by name where one is known, and by digits where it is not.

    Order is preserved, so the commonest cause stays first whether or not it
    could be named.
    """
    return {
        _name(identifier, name_for): count for identifier, count in histogram.items()
    }


def _histogram(counts: Mapping[str, int] | None) -> Mapping[int, int]:
    """Raw ids to counts, commonest first, ties broken by id so it is stable."""
    if not counts:
        return {}
    ordered = sorted(counts.items(), key=lambda item: (-item[1], int(item[0])))
    return {int(key): count for key, count in ordered}
