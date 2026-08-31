"""`brotato progress`: what the player's own save says, as raw ids.

Every assertion here is on JSON a user could see. Nothing reaches into
`_internal/` — `tach` would reject it, and the point of the seam is that the
save parser stays free to change without touching a test.
"""

from __future__ import annotations

import json
from pathlib import Path

from conftest import (
    PLACEHOLDER_STEAM_ID,
    CliRunner,
    steam_ids_in,
    write_game_data,
)

# Values read off the committed real save. They are assertions about the
# fixture, so they are allowed to be exact.
CHARACTER_COUNT = 64
RUNS_STARTED = 58
RUNS_WON = 5
CLEARED_CHARACTERS = {
    "character_mage",
    "character_explorer",
    "character_one_arm",
    "character_diver",
}
DEATH_CAUSE_COUNT = 15
DEATH_TOTAL = 24
PURCHASED_ITEM_COUNT = 260

# A second save directory, for the tests about choosing between saves. Built
# rather than written out, because a 17-digit literal in a tracked file is the
# exact thing `test_no_steam_id.py` exists to reject — including when it is
# obviously fake.
ANOTHER_STEAM_ID = "1" * 17


def _character(report: dict, character_id: str) -> dict:
    for character in report["characters"]:
        if character["character_id"] == character_id:
            return character
    raise AssertionError(f"{character_id} is missing from the report")


def _zone(character: dict, zone_id: int) -> dict:
    for zone in character["zones"]:
        if zone["zone_id"] == zone_id:
            return zone
    raise AssertionError(f"zone {zone_id} is missing from {character['character_id']}")


def _write_save(directory: Path, document: object) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "save_v3_0.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    return path


def _empty_save_document() -> dict:
    """A save the game has written but the player has not yet played against."""
    return {
        "version": 3,
        "data": {"run_started": 0, "run_won": 0},
        "difficulties_unlocked": [],
        "killed_by_enemies": {},
        "items_bought": {},
    }


# --- the report ------------------------------------------------------------


def test_progress_writes_json_to_stdout(cli: CliRunner, real_save_root: Path) -> None:
    result = cli("progress", application_support=real_save_root)
    assert result.exit_code == 0, result.stderr
    assert isinstance(result.json(), dict)


def test_lifetime_totals_come_from_the_save(
    cli: CliRunner, real_save_root: Path
) -> None:
    lifetime = cli("progress", application_support=real_save_root).json()["lifetime"]
    assert lifetime == {"runs_started": RUNS_STARTED, "runs_won": RUNS_WON}


def test_every_character_is_reported_not_only_the_played_ones(
    cli: CliRunner, real_save_root: Path
) -> None:
    report = cli("progress", application_support=real_save_root).json()
    assert len(report["characters"]) == CHARACTER_COUNT


def test_max_danger_beaten_is_reported_per_zone(
    cli: CliRunner, real_save_root: Path
) -> None:
    report = cli("progress", application_support=real_save_root).json()
    mage = _character(report, "character_mage")
    assert _zone(mage, 0)["max_danger_beaten"] == 0
    assert _zone(mage, 1)["max_danger_beaten"] == 4


def test_a_zone_never_beaten_reads_as_null_not_as_minus_one(
    cli: CliRunner, real_save_root: Path
) -> None:
    """The save stores "never" as -1. That is storage, and it stays hidden."""
    report = cli("progress", application_support=real_save_root).json()
    explorer = _character(report, "character_explorer")
    assert _zone(explorer, 1)["max_danger_beaten"] is None
    assert _zone(explorer, 1)["max_wave_reached"] is None


def test_the_wave_reached_is_reported_alongside_the_danger(
    cli: CliRunner, real_save_root: Path
) -> None:
    report = cli("progress", application_support=real_save_root).json()
    assert _zone(_character(report, "character_mage"), 1)["max_wave_reached"] == 20


def test_uncleared_characters_are_the_ones_that_are_not_cleared(
    cli: CliRunner, real_save_root: Path
) -> None:
    report = cli("progress", application_support=real_save_root).json()
    cleared = {c["character_id"] for c in report["characters"] if c["cleared"]}
    assert cleared == CLEARED_CHARACTERS


def test_the_death_histogram_is_reported_as_raw_enemy_ids(
    cli: CliRunner, real_save_root: Path
) -> None:
    deaths = cli("progress", application_support=real_save_root).json()["deaths"]
    assert len(deaths) == DEATH_CAUSE_COUNT
    assert sum(deaths.values()) == DEATH_TOTAL
    assert all(
        key.isdigit() for key in deaths
    ), "with no extracted data, ids stay raw rather than failing"


def test_the_death_histogram_leads_with_what_kills_most(
    cli: CliRunner, real_save_root: Path
) -> None:
    counts = list(cli("progress", application_support=real_save_root).json()["deaths"].values())
    assert counts == sorted(counts, reverse=True)


def test_purchase_counts_are_reported_as_raw_item_ids(
    cli: CliRunner, real_save_root: Path
) -> None:
    purchases = cli("progress", application_support=real_save_root).json()["purchases"]
    assert len(purchases) == PURCHASED_ITEM_COUNT
    assert all(key.isdigit() for key in purchases)


# --- resolving ids to names ------------------------------------------------
#
# The ids below are the real save's, and the names are what the game's hash
# says they are. They are the end-to-end assertion that the algorithm in
# `gamedata` is the one the game used when it wrote this file.


def test_deaths_are_named_once_the_game_data_has_been_extracted(
    cli: CliRunner, real_save_root: Path, tmp_path: Path
) -> None:
    data = write_game_data(tmp_path / "data", enemies=["lamprey", "giant", "crab"])

    deaths = cli(
        "progress", application_support=real_save_root, data_directory=data
    ).json()["deaths"]

    assert deaths["lamprey"] == 5
    assert deaths["giant"] == 2
    assert deaths["crab"] == 2
    assert sum(deaths.values()) == DEATH_TOTAL


def test_the_death_histogram_still_leads_with_what_kills_most_when_named(
    cli: CliRunner, real_save_root: Path, tmp_path: Path
) -> None:
    data = write_game_data(tmp_path / "data", enemies=["lamprey"])

    deaths = cli(
        "progress", application_support=real_save_root, data_directory=data
    ).json()["deaths"]

    assert next(iter(deaths)) == "lamprey"


def test_an_id_the_extracted_data_does_not_know_stays_raw(
    cli: CliRunner, real_save_root: Path, tmp_path: Path
) -> None:
    data = write_game_data(tmp_path / "data", enemies=["lamprey"])

    deaths = cli(
        "progress", application_support=real_save_root, data_directory=data
    ).json()["deaths"]

    assert "lamprey" in deaths
    assert len(deaths) == DEATH_CAUSE_COUNT
    assert sum(key.isdigit() for key in deaths) == DEATH_CAUSE_COUNT - 1


def test_purchases_are_named_across_every_catalogue(
    cli: CliRunner, real_save_root: Path, tmp_path: Path
) -> None:
    """The shop sells items, weapons and characters, so a name may be any of them."""
    data = write_game_data(
        tmp_path / "data",
        characters=["character_glutton"],
        items=["item_alien_baby"],
        weapons=["weapon_harpoon_gun_2"],
    )

    purchases = cli(
        "progress", application_support=real_save_root, data_directory=data
    ).json()["purchases"]

    assert purchases["character_glutton"] == 45
    assert purchases["item_alien_baby"] == 1
    assert "weapon_harpoon_gun_2" in purchases
    assert len(purchases) == PURCHASED_ITEM_COUNT


def test_a_data_directory_that_was_never_extracted_is_not_an_error(
    cli: CliRunner, real_save_root: Path, tmp_path: Path
) -> None:
    result = cli(
        "progress",
        application_support=real_save_root,
        data_directory=tmp_path / "never-extracted",
    )

    assert result.exit_code == 0
    assert all(key.isdigit() for key in result.json()["deaths"])


def test_no_steam_id_reaches_the_output(cli: CliRunner, real_save_root: Path) -> None:
    stdout = cli("progress", application_support=real_save_root).stdout
    assert steam_ids_in(stdout) == set()


# --- finding the save ------------------------------------------------------


def test_the_steam_id_in_the_environment_picks_the_save_directory(
    cli: CliRunner, real_save_root: Path
) -> None:
    _write_save(real_save_root / ANOTHER_STEAM_ID, _empty_save_document())
    report = cli(
        "progress", application_support=real_save_root, steam_id=PLACEHOLDER_STEAM_ID
    ).json()
    assert report["lifetime"]["runs_started"] == RUNS_STARTED


def test_the_steam_id_in_dot_env_picks_the_save_directory(
    cli: CliRunner, real_save_root: Path, tmp_path: Path
) -> None:
    _write_save(real_save_root / ANOTHER_STEAM_ID, _empty_save_document())
    working_directory = tmp_path / "work"
    working_directory.mkdir()
    (working_directory / ".env").write_text(
        f"# a comment\n\nSTEAM_ID={PLACEHOLDER_STEAM_ID}\n", encoding="utf-8"
    )
    report = cli(
        "progress", application_support=real_save_root, cwd=working_directory
    ).json()
    assert report["lifetime"]["runs_started"] == RUNS_STARTED


def test_without_a_steam_id_the_save_directory_is_found_by_globbing(
    cli: CliRunner, real_save_root: Path
) -> None:
    report = cli("progress", application_support=real_save_root).json()
    assert report["lifetime"]["runs_started"] == RUNS_STARTED


def test_the_offline_save_does_not_shadow_the_steam_save(
    cli: CliRunner, real_save_root: Path
) -> None:
    """Brotato writes an empty `user/` save beside the Steam one.

    Every real install has both, so globbing that stopped at "two saves, which
    one?" would never once find the save it was written to find.
    """
    _write_save(real_save_root / "user", _empty_save_document())
    report = cli("progress", application_support=real_save_root).json()
    assert report["lifetime"]["runs_started"] == RUNS_STARTED


def test_several_steam_saves_and_no_steam_id_asks_for_one(
    cli: CliRunner, real_save_root: Path
) -> None:
    _write_save(real_save_root / ANOTHER_STEAM_ID, _empty_save_document())
    result = cli("progress", application_support=real_save_root)
    assert result.exit_code != 0
    assert "STEAM_ID" in result.stderr
    assert "Traceback" not in result.stderr


def test_only_an_offline_save_is_still_worth_reading(
    cli: CliRunner, save_root: Path
) -> None:
    _write_save(save_root / "user", _empty_save_document())
    report = cli("progress", application_support=save_root).json()
    assert report["lifetime"] == {"runs_started": 0, "runs_won": 0}


# --- when there is nothing to read -----------------------------------------


def test_a_missing_application_support_directory_is_explained(
    cli: CliRunner, tmp_path: Path
) -> None:
    result = cli("progress", application_support=tmp_path / "nowhere")
    assert result.exit_code != 0
    assert "Traceback" not in result.stderr
    assert "nowhere" in result.stderr


def test_no_save_at_all_is_explained(cli: CliRunner, save_root: Path) -> None:
    result = cli("progress", application_support=save_root)
    assert result.exit_code != 0
    assert "Traceback" not in result.stderr
    assert "save" in result.stderr.lower()


def test_a_steam_id_naming_a_directory_without_a_save_is_explained(
    cli: CliRunner, real_save_root: Path
) -> None:
    result = cli(
        "progress", application_support=real_save_root, steam_id=ANOTHER_STEAM_ID
    )
    assert result.exit_code != 0
    assert "Traceback" not in result.stderr
    assert "STEAM_ID" in result.stderr


def test_an_empty_save_file_is_explained(cli: CliRunner, real_save_root: Path) -> None:
    (real_save_root / PLACEHOLDER_STEAM_ID / "save_v3_0.json").write_text(
        "", encoding="utf-8"
    )
    result = cli("progress", application_support=real_save_root)
    assert result.exit_code != 0
    assert "Traceback" not in result.stderr
    assert "empty" in result.stderr.lower()


def test_a_save_that_is_not_a_save_is_explained(
    cli: CliRunner, save_root: Path
) -> None:
    _write_save(save_root / PLACEHOLDER_STEAM_ID, {"something": "else"})
    result = cli("progress", application_support=save_root)
    assert result.exit_code != 0
    assert "Traceback" not in result.stderr
    assert "save" in result.stderr.lower()


def test_a_save_with_nothing_played_yet_reports_zeroes_rather_than_failing(
    cli: CliRunner, save_root: Path
) -> None:
    _write_save(save_root / PLACEHOLDER_STEAM_ID, _empty_save_document())
    report = cli("progress", application_support=save_root).json()
    assert report == {
        "lifetime": {"runs_started": 0, "runs_won": 0},
        "characters": [],
        "deaths": {},
        "purchases": {},
    }
