"""Reading a snapshot for what it says about the build.

`runlog` reads five fields out of the live run state, and only to decide which
run a reading belongs to — ADR-0001 keeps the snapshot whole precisely so that
nobody has to guess, at capture time, what a review will later want. This module
is that later want: it is the only code that interprets the rest of the file.

Nothing here fails on a field that is missing or shaped unexpectedly. A snapshot
is the game's output for a patch nobody controls, and a review that refuses to
open a run because one key moved is worth less than one that reports what it
could read.
"""

from collections.abc import Iterable, Mapping
from typing import Any

from brotato_coaching.gamedata import godot_hash

# The stats a review reports, in the order the game's own character sheet lists
# them. `effects` carries ~230 entries, most of them internal bookkeeping; these
# are the ones a build is argued about in. A stat the game stops writing simply
# stops appearing, which is why the map is built from what is present.
REPORTED_STATS = (
    "stat_max_hp",
    "stat_hp_regeneration",
    "stat_lifesteal",
    "stat_percent_damage",
    "stat_melee_damage",
    "stat_ranged_damage",
    "stat_elemental_damage",
    "stat_attack_speed",
    "stat_crit_chance",
    "stat_engineering",
    "stat_range",
    "stat_armor",
    "stat_dodge",
    "stat_speed",
    "stat_luck",
    "stat_harvesting",
)

# The game writes an effect's key as the Godot hash of the stat name, as a
# string. Same hash as the save file's ids: see ADR-0003.
_STAT_BY_HASH = {str(godot_hash(stat)): stat for stat in REPORTED_STATS}

# An `items` entry whose id is the character itself: the game keeps the
# character's own effects in the same list as the shop's, and it is not an item
# the player bought.
_CHARACTER_PREFIX = "character_"


def weapons(state: Mapping[str, Any]) -> list[dict[str, Any]]:
    """The weapons held, grouped by id, commonest first.

    Six shuriken instances are one decision made six times, not six decisions,
    so they are reported as a count rather than as a list to be eyeballed.
    """
    counted: dict[str, dict[str, Any]] = {}
    for weapon in _list(_player(state).get("weapons")):
        identifier = _text(weapon.get("my_id"))
        if identifier is None:
            continue
        entry = counted.setdefault(
            identifier, {"id": identifier, "tier": _tier(weapon), "count": 0}
        )
        entry["count"] += 1
    return sorted(counted.values(), key=lambda entry: -entry["count"])


def items(state: Mapping[str, Any]) -> dict[str, int]:
    """How many of each item is held, the character's own entry left out."""
    counted: dict[str, int] = {}
    for item in _list(_player(state).get("items")):
        identifier = _text(item.get("my_id"))
        if identifier is None or identifier.startswith(_CHARACTER_PREFIX):
            continue
        counted[identifier] = counted.get(identifier, 0) + 1
    return counted


def key_items(state: Mapping[str, Any]) -> list[dict[str, Any]]:
    """The items held more than once: the ones the player deliberately stacked.

    A single copy of an item is often what the shop happened to offer. A second
    copy is a decision, and repeated stacking across runs is the habit a review
    is looking for.
    """
    return [
        {"id": identifier, "count": count}
        for identifier, count in sorted(
            items(state).items(), key=lambda pair: (-pair[1], pair[0])
        )
        if count > 1
    ]


def final_stats(state: Mapping[str, Any]) -> dict[str, int]:
    """The reported stats, read back out of the hashed `effects` map."""
    effects = _player(state).get("effects")
    if not isinstance(effects, Mapping):
        return {}
    resolved = {}
    for key, stat in _STAT_BY_HASH.items():
        value = effects.get(key)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            resolved[stat] = int(value)
    return resolved


def wave_count(state: Mapping[str, Any]) -> int | None:
    """How many waves this run was going to be, if the state says."""
    return _number(_run(state).get("nb_of_waves"))


def wave(state: Mapping[str, Any]) -> int | None:
    return _number(_run(state).get("current_wave"))


def curve_entry(state: Mapping[str, Any]) -> dict[str, Any]:
    """One wave of the build curve: where the build had got to by then.

    There is no history in the live run state, so this — one entry per wave,
    read off the last snapshot taken in it — is the only way to see a build fall
    behind rather than only see where it ended.
    """
    player = _player(state)
    return {
        "wave": wave(state),
        "level": _number(player.get("current_level")),
        "health": _number(player.get("current_health")),
        "gold": _number(player.get("gold")),
        "weapons": len(_list(player.get("weapons"))),
        "items": sum(items(state).values()),
        "damage_last_wave": _damage_last_wave(player),
    }


def _damage_last_wave(player: Mapping[str, Any]) -> int:
    """What the whole arsenal did last wave. Written as a string by the game."""
    return sum(
        _number(weapon.get("dmg_dealt_last_wave")) or 0
        for weapon in _list(player.get("weapons"))
    )


def _tier(weapon: Mapping[str, Any]) -> int | None:
    """The tier the player sees: I to IV, from the zero-based index stored.

    The game writes `"tier": "3"` for `weapon_shuriken_4`. Reporting the storage
    form would put a 3 next to an id ending in 4 in every review — the same trap
    `difficulty_value` sets, and CONTEXT.md's rule is to report the name rather
    than the storage.
    """
    stored = _number(weapon.get("tier"))
    return None if stored is None else stored + 1


def _run(state: Mapping[str, Any]) -> Mapping[str, Any]:
    run = state.get("current_run_state") if isinstance(state, Mapping) else None
    return run if isinstance(run, Mapping) else {}


def _player(state: Mapping[str, Any]) -> Mapping[str, Any]:
    players = _run(state).get("players_data")
    if isinstance(players, list) and players and isinstance(players[0], Mapping):
        return players[0]
    return {}


def _list(value: object) -> Iterable[Mapping[str, Any]]:
    if not isinstance(value, list):
        return ()
    return [entry for entry in value if isinstance(entry, Mapping)]


def _number(value: object) -> int | None:
    """An int, whether the game wrote it as one, as a float, or as a string."""
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, str):
        try:
            return int(float(value))
        except ValueError:
            return None
    return None


def _text(value: object) -> str | None:
    return value if isinstance(value, str) and value else None
