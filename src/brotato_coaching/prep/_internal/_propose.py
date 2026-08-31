"""Choosing the character, when the player does not.

Left to preference a player returns to the characters they have already cleared,
which is the one place there is nothing left to derive. So the proposal picks
the character that introduces the most reasoning the player has never had to do,
and it picks it deterministically: the same save proposes the same character
until that character has been played, rather than shuffling until something
comfortable comes up.

"Reasoning the player has never had to do" is read off the stats the game says a
character wants. Those stats are an **archetype** seen from the data's side —
`CONTEXT.md` defines one as the characters that reward the same reasoning, and
the characters that want Elemental Damage do, whatever else differs between them.

The reasoning this module hands back is **counts only, never stat names**. It is
printed beside the card, before any prediction is committed, and a sentence
naming the archetype would answer two of the four questions outright.
"""

from __future__ import annotations

from collections.abc import Collection, Mapping, Sequence
from typing import Any

from ._words import key


def propose(
    characters: Sequence[Mapping[str, Any]],
    *,
    unlocked: Collection[str],
    cleared: Collection[str],
) -> tuple[Mapping[str, Any], dict[str, Any]] | None:
    """The character to drill next, and why — or `None` when there is none left.

    `cleared` is what the save can actually say: `difficulties_unlocked` records
    the best danger *beaten* per character and nothing about attempts that went
    nowhere, so a character cleared is the only evidence in the file that its
    reasoning has been done.

    `unlocked` empty means "no save to read", not "nothing unlocked": every
    character is a candidate, because refusing to propose would be worse than
    proposing one the player has yet to earn.
    """
    by_id = {str(character.get("id")): character for character in characters}
    reasoned = {
        stat
        for identifier in cleared
        for stat in _stats(by_id.get(identifier, {}))
    }
    candidates = [
        character
        for identifier, character in by_id.items()
        if _stats(character)
        and identifier not in cleared
        and (not unlocked or identifier in unlocked)
    ]
    if not candidates:
        return None
    chosen = min(
        candidates,
        key=lambda character: (
            -_novelty(character, reasoned),
            str(character.get("id")),
        ),
    )
    return chosen, {
        "reason": (
            "never cleared, and it rewards reasoning you have not had to do"
            if _novelty(chosen, reasoned) and reasoned
            else "never cleared"
        ),
        "candidates": len(candidates),
        "unlocked_known": len(unlocked),
        "archetypes_reasoned_about": len(reasoned),
        "archetypes_new_here": _novelty(chosen, reasoned),
    }


def _stats(character: Mapping[str, Any]) -> frozenset[str]:
    """The stats the game says this character wants — its archetype, in data.

    Empty means the game names none, and a character the game names none for
    would score `unscorable` on two of the four dimensions. Such a character is
    never *proposed*; naming one explicitly still works, because the player may
    want to reason about it anyway.
    """
    wanted = character.get("wanted_tags")
    if not isinstance(wanted, list):
        return frozenset()
    return frozenset(key(str(stat)) for stat in wanted if str(stat))


def _novelty(character: Mapping[str, Any], reasoned: Collection[str]) -> int:
    """How much of this character's archetype the player has never met."""
    return len(_stats(character) - frozenset(reasoned))
