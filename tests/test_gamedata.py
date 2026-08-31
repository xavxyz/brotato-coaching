"""The extractor, tested against a container this file builds byte by byte.

Nothing here reads the installed game: a synthetic GDPC holding a handful of
hand-written resources exercises the container reader, the `.tres` reader and
the catalogue in one pass, and it is checked into the repo in the only form the
publisher's content may take — a fake.
"""

import json
import struct
from pathlib import Path

import pytest

from brotato_coaching.gamedata import (
    INSTALL_DIR_VARIABLE,
    UNKNOWN_VERSION,
    GameInstall,
    InstallNotFound,
    extract,
    find_install,
    godot_hash,
    read_names,
)

CHARACTER_TRES = """[gd_resource type="Resource" load_steps=4 format=2]

[ext_resource path="res://items/characters/spud/spud_icon.png" type="Texture" id=1]
[ext_resource path="res://items/global/character_data.gd" type="Script" id=2]
[ext_resource path="res://items/characters/spud/spud_effect_1.tres" type="Resource" id=3]
[ext_resource path="res://weapons/melee/spoon/1/spoon_data.tres" type="Resource" id=4]

[resource]
script = ExtResource( 2 )
my_id = "character_spud"
unlocked_by_default = true
icon = ExtResource( 1 )
name = "CHARACTER_SPUD"
effects = [ ExtResource( 3 ) ]
tags = [  ]
wanted_tags = [ "melee_damage" ]
starting_weapons = [ ExtResource( 4 ) ]
starting_items = [  ]
"""

EFFECT_TRES = """[gd_resource type="Resource" load_steps=2 format=2]

[ext_resource path="res://items/global/effect.gd" type="Script" id=1]

[resource]
script = ExtResource( 1 )
key = "stat_max_hp"
text_key = "EFFECT_STAT"
value = -5
storage_method = 0
custom_args = [  ]
"""

WEAPON_TRES = """[gd_resource type="Resource" load_steps=3 format=2]

[ext_resource path="res://items/global/weapon_data.gd" type="Script" id=1]
[ext_resource path="res://weapons/melee/spoon/1/spoon_stats.tres" type="Resource" id=2]
[ext_resource path="res://weapons/melee/spoon/spoon.tscn" type="PackedScene" id=3]

[resource]
script = ExtResource( 1 )
my_id = "weapon_spoon_1"
weapon_id = "weapon_spoon"
name = "WEAPON_SPOON"
tier = 0
value = 20
scene = ExtResource( 3 )
stats = ExtResource( 2 )
effects = [  ]
sets = [  ]
"""

WEAPON_STATS_TRES = """[gd_resource type="Resource" load_steps=2 format=2]

[ext_resource path="res://weapons/weapon_stats/melee_weapon_stats.gd" type="Script" id=1]

[resource]
script = ExtResource( 1 )
cooldown = 67
damage = 12
crit_chance = 0.03
scaling_stats = [ [ "stat_melee_damage", 1.0 ] ]
is_healing = false
"""

ITEM_TRES = """[gd_resource type="Resource" load_steps=3 format=2]

[ext_resource path="res://items/global/item_data.gd" type="Script" id=1]
[ext_resource path="res://items/all/gravy/gravy_effect_1.tres" type="Resource" id=2]

[resource]
script = ExtResource( 1 )
my_id = "item_gravy"
name = "ITEM_GRAVY"
tier = 1
value = 15
effects = [ ExtResource( 2 ) ]
tags = [ "food" ]
"""

ITEM_EFFECT_TRES = """[gd_resource type="Resource" load_steps=2 format=2]

[ext_resource path="res://items/global/effect.gd" type="Script" id=1]

[resource]
script = ExtResource( 1 )
key = "stat_hp_regeneration"
value = 3
"""

ENEMY_TRES = """[gd_resource type="Resource" load_steps=2 format=2]

[ext_resource path="res://entities/units/enemies/ItemEnemy.gd" type="Script" id=1]

[resource]
script = ExtResource( 1 )
my_id = "mantis"
name = "MANTIS_NAME"
is_boss = false
is_elite = true
"""

BOSS_TRES = """[gd_resource type="Resource" load_steps=2 format=2]

[ext_resource path="res://entities/units/enemies/enemy_data.gd" type="Script" id=1]

[resource]
script = ExtResource( 1 )
my_id = "boss_crab"
zone_id = 0
"""

ABYSSAL_TERRORS_CHARACTER_TRES = """[gd_resource type="Resource" load_steps=2 format=2]

[ext_resource path="res://items/global/character_data.gd" type="Script" id=1]

[resource]
script = ExtResource( 1 )
my_id = "character_diver"
name = "CHARACTER_DIVER"
effects = [  ]
"""

BASE_RESOURCES = {
    "res://items/characters/spud/spud_data.tres": CHARACTER_TRES,
    "res://items/characters/spud/spud_effect_1.tres": EFFECT_TRES,
    "res://weapons/melee/spoon/1/spoon_data.tres": WEAPON_TRES,
    "res://weapons/melee/spoon/1/spoon_stats.tres": WEAPON_STATS_TRES,
    "res://items/all/gravy/gravy_data.tres": ITEM_TRES,
    "res://items/all/gravy/gravy_effect_1.tres": ITEM_EFFECT_TRES,
    "res://items/global/effect.gd": "# script bytes, never parsed\n",
    "res://entities/units/enemies/mantis/mantis_item.tres": ENEMY_TRES,
    "res://entities/units/enemies/boss/all/predator_data.tres": BOSS_TRES,
}

ABYSSAL_TERRORS_RESOURCES = {
    "res://dlcs/dlc_1/characters/diver/diver_data.tres": ABYSSAL_TERRORS_CHARACTER_TRES,
}


def write_container(path: Path, resources: dict[str, str]) -> Path:
    """Build a GDPC format 1 container: header, index, then the bytes."""
    header = bytearray()
    header += b"GDPC"
    header += struct.pack("<4I", 1, 3, 7, 0)
    header += b"\0" * (16 * 4)
    header += struct.pack("<I", len(resources))

    encoded = {name.encode("utf-8"): text.encode("utf-8") for name, text in resources.items()}
    # An entry is 4 bytes of length, the path, two 64-bit numbers and an md5,
    # so the index's size — and with it the first body's offset — is known up
    # front without a placeholder pass.
    index_size = sum(4 + len(name) + 8 + 8 + 16 for name in encoded)

    index = bytearray()
    offset = len(header) + index_size
    for name, body in encoded.items():
        index += struct.pack("<I", len(name)) + name
        index += struct.pack("<QQ", offset, len(body))
        index += b"\0" * 16
        offset += len(body)

    path.write_bytes(bytes(header + index) + b"".join(encoded.values()))
    return path


@pytest.fixture
def synthetic_install(tmp_path: Path) -> GameInstall:
    directory = tmp_path / "Brotato"
    directory.mkdir()
    return GameInstall(
        directory=directory,
        containers=(
            write_container(directory / "Brotato.pck", BASE_RESOURCES),
            write_container(
                directory / "BrotatoAbyssalTerrors.pck", ABYSSAL_TERRORS_RESOURCES
            ),
        ),
        version="1.2.3-test",
    )


def read_json(path: Path) -> dict:
    return json.loads(path.read_text())


def test_extract_writes_every_catalogue(
    synthetic_install: GameInstall, tmp_path: Path
) -> None:
    extraction = extract(synthetic_install, tmp_path / "data")

    assert sorted(file.name for file in extraction.files) == [
        "characters.json",
        "enemies.json",
        "items.json",
        "weapons.json",
    ]
    assert all(file.is_file() for file in extraction.files)


def test_enemies_are_extracted_from_both_of_the_scripts_that_describe_them(
    synthetic_install: GameInstall, tmp_path: Path
) -> None:
    """A codex entry names an enemy; an `enemy_data` resource names a boss."""
    extraction = extract(synthetic_install, tmp_path / "data")

    enemies = read_json(extraction.directory / "enemies.json")["enemies"]
    by_id = {enemy["id"]: enemy for enemy in enemies}
    assert set(by_id) == {"mantis", "boss_crab"}
    assert by_id["mantis"]["name_key"] == "MANTIS_NAME"
    assert by_id["mantis"]["is_elite"] is True
    assert by_id["boss_crab"]["zone_id"] == 0


def test_extract_creates_a_destination_that_does_not_exist(
    synthetic_install: GameInstall, tmp_path: Path
) -> None:
    extraction = extract(synthetic_install, tmp_path / "nested" / "data")

    assert extraction.directory.is_dir()


def test_every_catalogue_records_the_game_version(
    synthetic_install: GameInstall, tmp_path: Path
) -> None:
    extraction = extract(synthetic_install, tmp_path / "data")

    for file in extraction.files:
        assert read_json(file)["game_version"] == "1.2.3-test"


def test_character_modifiers_are_expanded_from_their_effect_resources(
    synthetic_install: GameInstall, tmp_path: Path
) -> None:
    extraction = extract(synthetic_install, tmp_path / "data")

    characters = read_json(extraction.directory / "characters.json")["characters"]
    spud = next(character for character in characters if character["id"] == "character_spud")
    assert spud["name_key"] == "CHARACTER_SPUD"
    assert spud["modifiers"] == [
        {
            "kind": "effect",
            "key": "stat_max_hp",
            "text_key": "EFFECT_STAT",
            "value": -5,
            "storage_method": 0,
            "custom_args": [],
        }
    ]


def test_character_starting_weapons_are_resolved_to_weapon_ids(
    synthetic_install: GameInstall, tmp_path: Path
) -> None:
    extraction = extract(synthetic_install, tmp_path / "data")

    characters = read_json(extraction.directory / "characters.json")["characters"]
    spud = next(character for character in characters if character["id"] == "character_spud")
    assert spud["starting_weapons"] == ["weapon_spoon_1"]


def test_weapon_stats_are_pulled_in_from_the_stats_resource(
    synthetic_install: GameInstall, tmp_path: Path
) -> None:
    extraction = extract(synthetic_install, tmp_path / "data")

    weapons = read_json(extraction.directory / "weapons.json")["weapons"]
    assert len(weapons) == 1
    spoon = weapons[0]
    assert spoon["id"] == "weapon_spoon_1"
    assert spoon["class"] == "melee"
    assert spoon["stats"]["damage"] == 12
    assert spoon["stats"]["cooldown"] == 67
    assert spoon["stats"]["crit_chance"] == pytest.approx(0.03)
    assert spoon["stats"]["is_healing"] is False


def test_item_effects_are_expanded(
    synthetic_install: GameInstall, tmp_path: Path
) -> None:
    extraction = extract(synthetic_install, tmp_path / "data")

    items = read_json(extraction.directory / "items.json")["items"]
    assert [item["id"] for item in items] == ["item_gravy"]
    assert items[0]["tags"] == ["food"]
    assert items[0]["effects"] == [
        {"kind": "effect", "key": "stat_hp_regeneration", "value": 3}
    ]


def test_both_containers_are_read_and_each_entity_names_its_source(
    synthetic_install: GameInstall, tmp_path: Path
) -> None:
    extraction = extract(synthetic_install, tmp_path / "data")

    characters = read_json(extraction.directory / "characters.json")["characters"]
    sources = {character["id"]: character["source"] for character in characters}
    assert sources == {"character_spud": "base", "character_diver": "abyssal_terrors"}


def test_presentation_properties_are_left_out(
    synthetic_install: GameInstall, tmp_path: Path
) -> None:
    characters = read_json(
        extract(synthetic_install, tmp_path / "data").directory / "characters.json"
    )["characters"]

    assert "icon" not in characters[0]


def test_output_is_stable_across_extractions(
    synthetic_install: GameInstall, tmp_path: Path
) -> None:
    first = extract(synthetic_install, tmp_path / "one").directory / "characters.json"
    second = extract(synthetic_install, tmp_path / "two").directory / "characters.json"

    assert first.read_text() == second.read_text()


def test_a_file_that_is_not_a_container_is_reported_as_such(
    tmp_path: Path,
) -> None:
    not_a_container = tmp_path / "Brotato.pck"
    not_a_container.write_bytes(b"not a godot container at all")
    install = GameInstall(
        directory=tmp_path, containers=(not_a_container,), version="0"
    )

    with pytest.raises(Exception, match="GDPC"):
        extract(install, tmp_path / "data")


class TestFindInstall:
    def test_the_environment_override_wins(self, tmp_path: Path) -> None:
        directory = tmp_path / "elsewhere"
        directory.mkdir()
        write_container(directory / "BrotatoAbyssalTerrors.pck", ABYSSAL_TERRORS_RESOURCES)

        install = find_install({INSTALL_DIR_VARIABLE: str(directory)})

        assert install.directory == directory
        assert [container.name for container in install.containers] == [
            "BrotatoAbyssalTerrors.pck"
        ]

    def test_an_override_pointing_nowhere_is_an_error_naming_the_variable(
        self, tmp_path: Path
    ) -> None:
        with pytest.raises(InstallNotFound, match=INSTALL_DIR_VARIABLE):
            find_install({INSTALL_DIR_VARIABLE: str(tmp_path / "missing")})

    def test_a_directory_without_containers_is_an_error(self, tmp_path: Path) -> None:
        with pytest.raises(InstallNotFound, match="no .pck"):
            find_install({INSTALL_DIR_VARIABLE: str(tmp_path)})

    def test_the_version_comes_from_the_app_bundle_when_there_is_one(
        self, tmp_path: Path
    ) -> None:
        import plistlib

        contents = tmp_path / "Brotato.app" / "Contents"
        (contents / "Resources").mkdir(parents=True)
        write_container(contents / "Resources" / "Brotato.pck", BASE_RESOURCES)
        (contents / "Info.plist").write_bytes(
            plistlib.dumps({"CFBundleShortVersionString": "1.1.12.0.beta-3"})
        )

        install = find_install({INSTALL_DIR_VARIABLE: str(tmp_path)})

        assert install.version == "1.1.12.0.beta-3"

    def test_the_steam_build_id_names_the_patch_without_a_bundle(
        self, tmp_path: Path
    ) -> None:
        directory = tmp_path / "steamapps" / "common" / "Brotato"
        directory.mkdir(parents=True)
        write_container(directory / "Brotato.pck", BASE_RESOURCES)
        (tmp_path / "steamapps" / "appmanifest_1942280.acf").write_text(
            '"AppState"\n{\n\t"appid"\t\t"1942280"\n\t"buildid"\t\t"23429717"\n}\n'
        )

        install = find_install({INSTALL_DIR_VARIABLE: str(directory)})

        assert install.version == "steam-build-23429717"


def install_directory(
    directory: Path, *, base: bool = True, abyssal_terrors: bool = True
) -> Path:
    """A directory shaped like a Steam install of the game."""
    directory.mkdir(parents=True, exist_ok=True)
    if base:
        write_container(directory / "Brotato.pck", BASE_RESOURCES)
    if abyssal_terrors:
        write_container(
            directory / "BrotatoAbyssalTerrors.pck", ABYSSAL_TERRORS_RESOURCES
        )
    return directory


def steam_library(root: Path, *, with_game: bool) -> Path:
    """A Steam library, holding the game or merely claiming to."""
    common = root / "steamapps" / "common"
    common.mkdir(parents=True, exist_ok=True)
    if with_game:
        install_directory(common / "Brotato")
    else:
        (common / "Brotato").mkdir(exist_ok=True)  # a partial uninstall
    return root


def library_manifest(steam_root: Path, library: Path) -> None:
    manifest = steam_root / "steamapps" / "libraryfolders.vdf"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(
        '"libraryfolders"\n{\n\t"0"\n\t{\n\t\t"path"\t\t"%s"\n\t}\n}\n' % library
    )


class TestDiscovery:
    """Finding the install by walking Steam's own bookkeeping."""

    def home_with_steam(self, tmp_path: Path) -> tuple[Path, Path]:
        home = tmp_path / "home"
        steam = home / "Library" / "Application Support" / "Steam"
        steam.mkdir(parents=True)
        return home, steam

    def test_the_game_is_found_in_the_default_library(self, tmp_path: Path) -> None:
        home, steam = self.home_with_steam(tmp_path)
        steam_library(steam, with_game=True)

        install = find_install({"HOME": str(home)})

        assert install.directory.name == "Brotato"
        assert [container.name for container in install.containers] == [
            "Brotato.pck",
            "BrotatoAbyssalTerrors.pck",
        ]

    def test_a_library_steam_lists_elsewhere_is_searched(self, tmp_path: Path) -> None:
        home, steam = self.home_with_steam(tmp_path)
        elsewhere = steam_library(tmp_path / "external-drive", with_game=True)
        library_manifest(steam, elsewhere)

        install = find_install({"HOME": str(home)})

        assert install.directory == elsewhere / "steamapps" / "common" / "Brotato"

    def test_a_library_that_no_longer_holds_the_game_does_not_end_the_search(
        self, tmp_path: Path
    ) -> None:
        home, steam = self.home_with_steam(tmp_path)
        steam_library(steam, with_game=False)
        elsewhere = steam_library(tmp_path / "second-library", with_game=True)
        library_manifest(steam, elsewhere)

        install = find_install({"HOME": str(home)})

        assert install.directory == elsewhere / "steamapps" / "common" / "Brotato"

    def test_no_install_anywhere_is_an_error_naming_the_override(
        self, tmp_path: Path
    ) -> None:
        home, _ = self.home_with_steam(tmp_path)

        with pytest.raises(InstallNotFound, match=INSTALL_DIR_VARIABLE):
            find_install({"HOME": str(home)})


class TestVersion:
    def test_an_install_that_names_no_patch_is_stamped_unknown(
        self, tmp_path: Path
    ) -> None:
        directory = install_directory(tmp_path / "Brotato")

        install = find_install({INSTALL_DIR_VARIABLE: str(directory)})

        assert install.version == UNKNOWN_VERSION

    def test_an_unstamped_extraction_says_so_in_the_json(self, tmp_path: Path) -> None:
        directory = install_directory(tmp_path / "Brotato")
        install = find_install({INSTALL_DIR_VARIABLE: str(directory)})

        extraction = extract(install, tmp_path / "data")

        version = read_json(extraction.directory / "characters.json")["game_version"]
        assert version == UNKNOWN_VERSION


def test_an_extraction_names_the_zones_it_read(
    synthetic_install: GameInstall, tmp_path: Path
) -> None:
    extraction = extract(synthetic_install, tmp_path / "data")

    assert extraction.sources == ("base", "abyssal_terrors")


def test_an_install_missing_a_container_names_only_the_zone_it_has(
    tmp_path: Path,
) -> None:
    directory = install_directory(tmp_path / "Brotato", abyssal_terrors=False)
    install = find_install({INSTALL_DIR_VARIABLE: str(directory)})

    extraction = extract(install, tmp_path / "data")

    assert extraction.sources == ("base",)


# --- names -----------------------------------------------------------------


def test_the_hash_is_the_one_the_game_wrote_into_the_save() -> None:
    """Fixed values, read off the committed real save. See ADR 0003."""
    assert godot_hash("character_mage") == 904328779
    assert godot_hash("lamprey") == 1737060255
    assert godot_hash("") == 5381


def test_a_name_book_resolves_ids_from_every_catalogue(
    synthetic_install: GameInstall, tmp_path: Path
) -> None:
    extraction = extract(synthetic_install, tmp_path / "data")

    names = read_names(extraction.directory)

    for identifier in ("character_spud", "weapon_spoon_1", "item_gravy", "mantis"):
        assert names.name_for(godot_hash(identifier)) == identifier


def test_a_name_book_does_not_invent_a_name_for_an_id_it_has_never_seen(
    synthetic_install: GameInstall, tmp_path: Path
) -> None:
    extraction = extract(synthetic_install, tmp_path / "data")

    assert read_names(extraction.directory).name_for(1) is None


def test_a_name_book_from_a_directory_that_was_never_extracted_is_empty(
    tmp_path: Path,
) -> None:
    names = read_names(tmp_path / "never-extracted")

    assert not names
    assert names.name_for(godot_hash("character_spud")) is None
