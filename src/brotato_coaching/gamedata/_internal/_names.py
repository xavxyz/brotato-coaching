"""The hash the game writes ids as, and the book that reads them back.

Brotato stores an entity in a save as a 32-bit integer rather than as its id:
`killed_by_enemies` is keyed by `1737060255`, not by `lamprey`. The integer is
Godot 3's `String.hash()` — the djb2 variant below — applied to the entity's
`my_id`, and nothing else: not the resource path, not the translation key. See
`docs/adr/0002-save-ids-are-godot-string-hashes.md` for how that was pinned down
and what was ruled out.

Nothing here reaches for the game. A `NameBook` is built from what `extract`
already wrote, so resolution works from a directory of JSON and degrades to an
empty book — never an error — when the player has not extracted yet.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

# Every catalogue `extract` writes. A hash may name any of them: the shop sells
# items, weapons and characters alike, so a purchase can be any of the three.
CATALOGUES = ("characters", "enemies", "items", "weapons")

_HASH_SEED = 5381
_32_BITS = 0xFFFFFFFF


def godot_hash(text: str) -> int:
    """Godot 3's `String.hash()`: djb2 over the utf-8 bytes, wrapped to 32 bits."""
    value = _HASH_SEED
    for byte in text.encode("utf-8"):
        value = ((value << 5) + value + byte) & _32_BITS
    return value


@dataclass(frozen=True)
class NameBook:
    """Every id the extracted data knows, findable by the hash the save holds.

    A book that knows nothing is falsy, so a caller can tell "not extracted
    yet" from "extracted, but this id is not in it" without catching anything.
    """

    names: Mapping[int, str]

    def name_for(self, identifier: int) -> str | None:
        """The id behind one of the save's integers, or `None` if unknown."""
        return self.names.get(identifier)

    def __bool__(self) -> bool:
        return bool(self.names)

    def __len__(self) -> int:
        return len(self.names)


def read_names(directory: Path) -> NameBook:
    """Build a book from the catalogues in `directory`.

    A missing directory, a missing catalogue, or a file the player has damaged
    contributes nothing rather than raising: a name is a convenience, and no
    report is worth failing for the want of one.
    """
    names: dict[int, str] = {}
    for catalogue in CATALOGUES:
        for identifier in _identifiers(directory / f"{catalogue}.json", catalogue):
            names[godot_hash(identifier)] = identifier
    return NameBook(names=names)


def _identifiers(path: Path, catalogue: str) -> list[str]:
    try:
        document = json.loads(path.read_text())
    except (OSError, ValueError):
        return []
    entities = document.get(catalogue) if isinstance(document, dict) else None
    if not isinstance(entities, list):
        return []
    return [
        entity["id"]
        for entity in entities
        if isinstance(entity, dict) and isinstance(entity.get("id"), str)
    ]
