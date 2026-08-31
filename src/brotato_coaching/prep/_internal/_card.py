"""The two halves of a drill: what the player is shown, and what is held back.

A card and a truth are built together, from the same character record, and they
are built *once* — at the moment the drill opens. Everything the player is
allowed to see goes into the card; everything that would answer a prediction
goes into the truth, which is written to the drill file and not printed until
the four answers are in.

The withholding is mechanical rather than careful. The card is assembled from an
allowed list of fields and then swept for the character's own name, so a field
nobody thought about cannot leak by being forgotten — and `wanted_tags`, which
is literally the answer to two of the four predictions, is never on the allowed
list in the first place.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ._words import redactor

WITHHELD = "withheld"

# A card is assembled field by field, and what is not assembled in is not shown.
# `id`, `name_key` and `resource` name the character; `wanted_tags` *is* the
# answer to both stat predictions; `tags` and `banned_items` describe the
# character in the same vocabulary those answers are written in. None of them
# appear below, and the sweep at the end is the second line of defence.

# Fields of an effect that carry mechanics rather than presentation or
# bookkeeping. `text_key` and `storage_method` say how the game renders and
# stores an effect, which teaches nothing about what it does.
_MECHANICAL = ("kind", "key", "value", "stat_displayed", "stats_modified")

# A weapon, as much of it as helps derive a plan. Its own id is shown: the drill
# withholds the *character*, and the starting weapon is the evidence.
_WEAPON_SHOWN = ("id", "name_key", "weapon_id", "class", "sets", "tier", "stats")


def character_name(character_id: str) -> str:
    """`character_mage` -> `mage`: the word a card must not contain."""
    return character_id.removeprefix("character_")


def build(
    character: Mapping[str, Any],
    weapons: Mapping[str, Mapping[str, Any]],
    *,
    game_version: str | None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """One character record, split into the card shown and the truth kept.

    `weapons` is every extracted weapon by id, because a character record names
    its weapons and does not describe them, and the description is the evidence.
    """
    starting = _starting_weapons(character, weapons)
    starting_weapon = starting[0] if starting else None
    card = _redacted(
        {
            "identity": WITHHELD,
            "game_version": game_version,
            "zone": character.get("source"),
            "modifiers": [_effect(effect) for effect in _list(character, "modifiers")],
            "starting_items": _list(character, "starting_items"),
            "starting_weapon": _weapon(starting_weapon),
            "starting_pool": _pool(starting),
        },
        character_name(str(character.get("id", ""))),
    )
    truth = {
        "character_id": character.get("id"),
        "name_key": character.get("name_key"),
        "zone": character.get("source"),
        "wanted_stats": _list(character, "wanted_tags"),
        "starting_weapon": (starting_weapon or {}).get("id"),
        "weapon_classes": _list(starting_weapon or {}, "sets"),
        "weapon_delivery": (starting_weapon or {}).get("class"),
    }
    return card, truth


def _starting_weapons(
    character: Mapping[str, Any], weapons: Mapping[str, Mapping[str, Any]]
) -> list[Mapping[str, Any]]:
    """The character's weapons, described, in the order the game lists them.

    **The first is the starting weapon and the rest are the pool it is drawn
    from.** That is an inference from the resources — the game does not label
    one of them — but it holds everywhere it has been checked: the Mage's list
    opens with the Wand, the Ranger's with the Pistol. A character whose list is
    empty starts with nothing, which is a fact about the character.
    """
    described = (weapons.get(str(weapon)) for weapon in _list(character, "starting_weapons"))
    return [weapon for weapon in described if weapon is not None]


def _weapon(weapon: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if weapon is None:
        return None
    return {field: weapon.get(field) for field in _WEAPON_SHOWN if field in weapon}


def _pool(starting: list[Mapping[str, Any]]) -> dict[str, Any]:
    """The weapons the character may be offered, and how they break down.

    The tally is the part worth reading: a pool that is eighteen weapons and
    fifteen of them melee has said something about the character that no single
    weapon in it says.
    """
    pool = starting[1:]
    tally: dict[str, int] = {}
    for weapon in pool:
        delivery = weapon.get("class")
        if isinstance(delivery, str):
            tally[delivery] = tally.get(delivery, 0) + 1
    return {
        "weapons": [weapon.get("id") for weapon in pool],
        "by_delivery": dict(sorted(tally.items())),
    }


def _effect(effect: Mapping[str, Any]) -> dict[str, Any]:
    """One modifier, with the game's rendering and storage details dropped."""
    described = {
        field: effect[field]
        for field in _MECHANICAL
        if field in effect and effect[field] not in (None, "", [])
    }
    nested = [
        [_effect(item) for item in value]
        for name, value in effect.items()
        if name not in _MECHANICAL
        and isinstance(value, list)
        and all(isinstance(item, dict) for item in value)
        and value
    ]
    if nested:
        described["effects"] = [item for group in nested for item in group]
    return described


def _list(record: Mapping[str, Any], name: str) -> list[Any]:
    value = record.get(name)
    return list(value) if isinstance(value, list) else []


def _redacted(card: dict[str, Any], name: str) -> dict[str, Any]:
    """The card with the character's own name struck out of every string in it.

    The sweep is over the finished card rather than over each field as it is
    built, so it covers fields added later by someone who has forgotten this
    file exists — which is the only kind of leak worth defending against.
    """
    strike = redactor(name)

    def swept(value: Any) -> Any:
        if isinstance(value, str):
            return strike(value)
        if isinstance(value, list):
            return [swept(item) for item in value]
        if isinstance(value, dict):
            return {key: swept(item) for key, item in value.items()}
        return value

    return swept(card)
