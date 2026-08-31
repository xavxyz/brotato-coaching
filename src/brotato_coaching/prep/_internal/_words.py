"""Reading a game id as words, which is what makes both halves of a drill work.

Two jobs need the same trick. Withholding a character's identity means finding
`mage` inside `res://items/characters/mage/mage_data.tres` while *not* finding
it inside `stat_melee_damage` — a substring search fails that on the first try,
and fails it silently. Scoring a prediction means reading "Elemental Damage" and
`stat_elemental_damage` as the same name.

Both fall out of the same reading: an id is a sequence of words, and everything
between them is punctuation.
"""

from __future__ import annotations

import re
from collections.abc import Callable

_SEPARATORS = re.compile(r"[^a-z0-9]+")
_BETWEEN_WORDS = r"[^a-zA-Z0-9]+"
_NOT_A_WORD_CHARACTER = r"[a-zA-Z0-9]"

# What a redacted name is replaced by. One ellipsis for the whole run, so
# `mage_data.tres` reads as `….tres` rather than as a shape to count letters in.
ELLIPSIS = "…"

# Prefixes the game puts on its own vocabulary. A player writing a prediction down
# will not type them, and should not have to.
_PREFIXES = frozenset({"stat", "set", "character", "weapon", "item"})


def words(text: str) -> tuple[str, ...]:
    """`"res://weapons/wand_1"` -> `("res", "weapons", "wand", "1")`."""
    return tuple(word for word in _SEPARATORS.split(text.lower()) if word)


def key(text: str) -> str:
    """One name reduced to what it says, so two spellings of it compare equal.

    Applied to both sides of a comparison — what the player predicted and what
    the game declares. The game's own prefix is dropped, because `stat_armor`,
    `Armor` and `armor` are one name and only one of them is a thing a player
    types.
    """
    said = words(text)
    if said and said[0] in _PREFIXES:
        said = said[1:]
    return "_".join(said)


def redactor(name: str) -> Callable[[str], str]:
    """A function that strikes `name` out of any string, word for word.

    Word for word, never letter for letter. `mage` is struck out of
    `mage_data.tres` and is left alone in `stat_melee_damage`, because the match
    is anchored to word boundaries on both sides — and a name of several words,
    like `one_arm`, matches across whatever punctuation separates them.

    A name that reduces to no words at all redacts nothing, rather than
    redacting everything.
    """
    said = words(name)
    if not said:
        return lambda text: text
    pattern = re.compile(
        f"(?<!{_NOT_A_WORD_CHARACTER})"
        + _BETWEEN_WORDS.join(re.escape(word) for word in said)
        + f"(?!{_NOT_A_WORD_CHARACTER})",
        re.IGNORECASE,
    )
    return lambda text: pattern.sub(ELLIPSIS, text)
