"""The extractor against the real thing, skipped where the game is not installed.

The synthetic tests prove the readers; these prove the readers are pointed at
the right numbers. They assert a known character's modifiers, because a parser
can be perfectly correct about a file and still be reading the wrong field.

Values here are the game's, so a patch may move them. That is the point of the
version stamp: when one of these fails after an update, the failure is the news.
"""

import json
from pathlib import Path

import pytest
from conftest import INSTALL, PLACEHOLDER_STEAM_ID, REAL_SAVE_ROOT

from brotato_coaching.gamedata import extract, read_names

pytestmark = pytest.mark.skipif(
    INSTALL is None, reason="Brotato is not installed on this machine"
)


@pytest.fixture(scope="module")
def extracted(tmp_path_factory: pytest.TempPathFactory) -> Path:
    assert INSTALL is not None
    return extract(INSTALL, tmp_path_factory.mktemp("data")).directory


def catalogue(directory: Path, name: str) -> list[dict]:
    return json.loads((directory / f"{name}.json").read_text())[name]


def test_the_extraction_is_stamped_with_the_installed_version(extracted: Path) -> None:
    assert INSTALL is not None
    stamped = json.loads((extracted / "characters.json").read_text())["game_version"]

    assert stamped == INSTALL.version
    assert stamped != "unknown"


def test_both_zones_contribute_characters(extracted: Path) -> None:
    sources = {character["source"] for character in catalogue(extracted, "characters")}

    assert sources == {"base", "abyssal_terrors"}


def test_a_dlc_character_is_extracted(extracted: Path) -> None:
    identifiers = {character["id"] for character in catalogue(extracted, "characters")}

    assert "character_buccaneer" in identifiers


def test_the_wildlings_modifiers_are_the_ones_the_game_ships(extracted: Path) -> None:
    wildling = next(
        character
        for character in catalogue(extracted, "characters")
        if character["id"] == "character_wildling"
    )

    assert wildling["name_key"] == "CHARACTER_WILDLING"
    assert [
        (modifier["kind"], modifier["key"], modifier["value"])
        for modifier in wildling["modifiers"]
    ] == [
        ("class_bonus_effect", "EFFECT_WEAPON_CLASS_BONUS", 30),
        ("effect", "weapon_stick_1", 1),
        ("effect", "max_weapon_tier", 1),
    ]
    lifesteal_on_primitives = wildling["modifiers"][0]
    assert lifesteal_on_primitives["set_id"] == "set_primitive"
    assert lifesteal_on_primitives["stat_name"] == "lifesteal"
    assert wildling["starting_weapons"][0] == "weapon_stick_1"


def test_a_known_weapons_stats_are_the_ones_the_game_ships(extracted: Path) -> None:
    pistol = next(
        weapon
        for weapon in catalogue(extracted, "weapons")
        if weapon["id"] == "weapon_pistol_1"
    )

    assert pistol["class"] == "ranged"
    assert pistol["stats"]["damage"] == 12
    assert pistol["stats"]["cooldown"] == 60
    assert pistol["upgrades_into"] == "weapon_pistol_2"
    assert pistol["sets"] == ["set_gun"]


def test_a_known_items_effects_are_extracted(extracted: Path) -> None:
    turret = next(
        item for item in catalogue(extracted, "items") if item["id"] == "item_turret"
    )

    assert turret["name_key"] == "ITEM_TURRET"
    assert turret["effects"], "an item with an effect should carry it"


def test_every_catalogue_is_populated(extracted: Path) -> None:
    for name in ("characters", "weapons", "items", "enemies"):
        assert len(catalogue(extracted, name)) > 30, name


def test_every_id_in_the_real_save_resolves_to_a_name(extracted: Path) -> None:
    """The hash, against the only data that can falsify it: a real save.

    The committed save was written by the game, not by this repo. Every id in
    it hashing back to an extracted entity is what identifies the algorithm.
    """
    save = json.loads(
        (REAL_SAVE_ROOT / PLACEHOLDER_STEAM_ID / "save_v3_0.json").read_text()
    )
    names = read_names(extracted)

    unresolved = [
        identifier
        for field in ("killed_by_enemies", "items_bought")
        for identifier in save[field]
        if names.name_for(int(identifier)) is None
    ]
    deaths = save["killed_by_enemies"]
    commonest = max(deaths, key=lambda identifier: deaths[identifier])

    assert unresolved == []
    assert names.name_for(int(commonest)) == "lamprey"


def test_no_two_extracted_ids_hash_to_the_same_integer(extracted: Path) -> None:
    """What lets a hash name exactly one thing — asserted, not assumed.

    A collision between two different ids would be silent: the book keeps one
    and the other becomes unnameable. ADR-0003 rests on there being none.

    Two *resources* sharing one id is a different matter and does happen — the
    DLC ships a second `evil_mob` — but they hash alike because they are named
    alike, so the name that comes back is right either way.
    """
    identifiers = {
        entity["id"]
        for name in ("characters", "weapons", "items", "enemies")
        for entity in catalogue(extracted, name)
    }

    assert len(read_names(extracted)) == len(identifiers)
