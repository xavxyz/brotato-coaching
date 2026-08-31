"""Choosing the character, when the player does not.

Left to preference a player returns to the characters they have already cleared,
which is the one place there is nothing left to derive. So the proposal picks
the character that introduces the most reasoning the player has never had to do,
and it picks it deterministically: the same save proposes the same character
until that character has been played, rather than shuffling until something
comfortable comes up.

"Reasoning the player has never had to do" is read off the stats the game says a
character wants. Those stats are what `CONTEXT.md` calls an archetype seen from
the data's side — the characters that want Elemental Damage reward the same
reading, whatever else differs between them.

The reasoning this module hands back is **counts only, never stat names**. It is
printed beside the card, before any prediction is committed, and a sentence
naming the family would answer two of the four questions outright.
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
    reasoned = {stat for identifier in cleared for stat in _wants(characters, identifier)}
    candidates = [
        character
        for character in characters
        if _wants_anything(character)
        and str(character.get("id")) not in cleared
        and (not unlocked or str(character.get("id")) in unlocked)
    ]
    if not candidates:
        return None
    chosen = min(candidates, key=lambda character: (-_novelty(character, reasoned), str(character.get("id"))))
    return chosen, {
        "reason": (
            "never cleared, and it rewards reasoning you have not had to do"
            if _novelty(chosen, reasoned) and reasoned
            else "never cleared"
        ),
        "candidates": len(candidates),
        "unlocked_known": len(unlocked),
        "families_reasoned_about": len(reasoned),
        "families_new_here": _novelty(chosen, reasoned),
    }


def _wants(
    characters: Sequence[Mapping[str, Any]], identifier: str
) -> frozenset[str]:
    for character in characters:
        if str(character.get("id")) == identifier:
            return _stats(character)
    return frozenset()


def _stats(character: Mapping[str, Any]) -> frozenset[str]:
    wanted = character.get("wanted_tags")
    if not isinstance(wanted, list):
        return frozenset()
    return frozenset(key(str(stat)) for stat in wanted if str(stat))


def _wants_anything(character: Mapping[str, Any]) -> bool:
    """Whether a drill on this character could be scored at all.

    A character the game names no wanted stat for would score `unscorable` on
    two of the four dimensions. Naming one explicitly still works — the player
    may want to reason about it anyway — but it is never *proposed*.
    """
    return bool(_stats(character))


def _novelty(character: Mapping[str, Any], reasoned: Collection[str]) -> int:
    """How many of this character's wanted stats the player has never met."""
    return len(_stats(character) - frozenset(reasoned))
