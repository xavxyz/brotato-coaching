"""The derivation drill, driven through the one seam.

Everything a drill promises is a thing an outside observer can check on the JSON
the CLI prints: that the card does not name the character, that a reveal before
the four predictions is refused, that each is scored on its own, and that the
hit rate adds up across drills. None of these tests know how any of it is done.

The catalogue below is hand-written but its **ids are the game's**, because the
committed save is the game's too: `character_mage` is cleared in it and
`character_ghost` is locked, and a proposal that ignored either would pass
against invented ids and fail against a real save.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pytest

from conftest import CliRunner, CliResult

MAGE = "character_mage"
RANGER = "character_ranger"
GHOST = "character_ghost"


def _character(
    identifier: str, *, wanted: list[str], weapons: list[str], modifiers: list[dict]
) -> dict[str, Any]:
    return {
        "id": identifier,
        "name_key": identifier.replace("character_", "CHARACTER_").upper(),
        "source": "base",
        "resource": f"res://items/characters/{identifier.removeprefix('character_')}/data.tres",
        "modifiers": modifiers,
        "starting_weapons": weapons,
        "starting_items": [],
        "tags": [],
        "wanted_tags": wanted,
        "banned_items": [],
    }


def _weapon(identifier: str, *, delivery: str, sets: list[str]) -> dict[str, Any]:
    return {
        "id": identifier,
        "name_key": identifier.replace("weapon_", "WEAPON_").upper(),
        "weapon_id": identifier.removesuffix("_1"),
        "source": "base",
        "class": delivery,
        "sets": sets,
        "tier": 0,
        "stats": {"damage": 10, "cooldown": 40},
    }


CHARACTERS = [
    _character(
        MAGE,
        wanted=["stat_elemental_damage"],
        weapons=["weapon_wand_1", "weapon_torch_1"],
        modifiers=[
            {
                "kind": "stat_gains_modification_effect",
                "key": "effect_increase_stat_gains",
                "text_key": "",
                "value": 25,
                "storage_method": 0,
                "stat_displayed": "stat_elemental_damage",
                "stats_modified": ["stat_elemental_damage"],
            },
            {
                "kind": "stat_gains_modification_effect",
                "key": "effect_reduce_stat_gains",
                "value": -100,
                "stat_displayed": "stat_melee_damage",
                "stats_modified": ["stat_melee_damage"],
            },
        ],
    ),
    _character(
        RANGER,
        wanted=["stat_ranged_damage", "stat_range"],
        weapons=["weapon_pistol_1"],
        modifiers=[{"kind": "effect", "key": "stat_range", "value": 20}],
    ),
    # Locked in the committed save, and the most novel character in the
    # catalogue: a proposal that ignored the save would pick it every time.
    _character(
        GHOST,
        wanted=["stat_dodge", "stat_speed", "stat_luck"],
        weapons=["weapon_ghost_flint_1"],
        modifiers=[{"kind": "effect", "key": "ghost_effect", "value": 1}],
    ),
]

WEAPONS = [
    _weapon("weapon_wand_1", delivery="ranged", sets=["set_elemental"]),
    _weapon("weapon_torch_1", delivery="melee", sets=["set_elemental"]),
    _weapon("weapon_pistol_1", delivery="ranged", sets=["set_gun", "set_precise"]),
    _weapon("weapon_ghost_flint_1", delivery="ranged", sets=["set_ethereal"]),
]


@pytest.fixture
def game_data(tmp_path: Path) -> Path:
    """An extracted `data/`, shaped exactly as `extract` writes one."""
    directory = tmp_path / "data"
    directory.mkdir()
    for name, entities in (("characters", CHARACTERS), ("weapons", WEAPONS)):
        (directory / f"{name}.json").write_text(
            json.dumps({"game_version": "1.1.12.0.beta-3", name: entities})
        )
    return directory


def words(document: Any) -> set[str]:
    """Every word in a JSON document, read the way a name is read.

    Deliberately not a substring search: `stat_melee_damage` contains the
    letters of `mage` and does not name the Mage, and a test that could not tell
    those apart would pass on a card that gave the answer away.
    """
    return {
        word
        for word in re.split(r"[^a-z0-9]+", json.dumps(document).lower())
        if word
    }


def open_drill(cli: CliRunner, game_data: Path, *arguments: str, **options) -> Any:
    return cli("prep", *arguments, data_directory=game_data, **options).json()


def committed(cli: CliRunner, drill_id: str, **answers: Any) -> CliResult:
    answered = {
        "primary_stat": "elemental damage",
        "secondary_stat": "attack speed",
        "weapon_class": "elemental",
        "weakest_wave": 12,
        **answers,
    }
    return cli(
        "prep",
        "--commit",
        drill_id,
        *(
            argument
            for name, value in answered.items()
            for argument in (f"--{name.replace('_', '-')}", str(value))
        ),
    )


def test_a_named_character_opens_a_drill(cli: CliRunner, game_data: Path) -> None:
    opened = open_drill(cli, game_data, MAGE)

    assert opened["state"] == "open"
    assert opened["drill_id"]
    assert opened["predictions_wanted"] == [
        "primary_stat",
        "secondary_stat",
        "weapon_class",
        "weakest_wave",
    ]


def test_the_card_never_names_the_character(cli: CliRunner, game_data: Path) -> None:
    card = open_drill(cli, game_data, MAGE)["card"]

    assert card["identity"] == "withheld"
    assert "mage" not in words(card)
    assert "character_mage" not in json.dumps(card)


def test_the_card_never_names_the_character_through_its_own_weapon(
    cli: CliRunner, game_data: Path
) -> None:
    """The Ghost starts with the Ghost Flint, which is the whole difficulty."""
    card = open_drill(cli, game_data, GHOST)["card"]

    assert "ghost" not in words(card)
    assert card["starting_weapon"]["id"] != "weapon_ghost_flint_1"


def test_the_card_never_says_which_stats_the_character_wants(
    cli: CliRunner, game_data: Path
) -> None:
    """`wanted_tags` is the answer to two of the four predictions."""
    card = open_drill(cli, game_data, RANGER)["card"]

    assert "wanted_tags" not in json.dumps(card)
    assert "stat_ranged_damage" not in json.dumps(card)


def test_the_card_shows_the_modifiers_and_the_starting_weapon(
    cli: CliRunner, game_data: Path
) -> None:
    card = open_drill(cli, game_data, MAGE)["card"]

    assert card["starting_weapon"]["id"] == "weapon_wand_1"
    assert card["starting_weapon"]["sets"] == ["set_elemental"]
    assert card["starting_weapon"]["stats"]["damage"] == 10
    modified = [
        stat for modifier in card["modifiers"] for stat in modifier["stats_modified"]
    ]
    assert modified == ["stat_elemental_damage", "stat_melee_damage"]
    assert card["game_version"] == "1.1.12.0.beta-3"


def test_a_character_with_no_starting_weapon_still_opens_a_drill(
    cli: CliRunner, tmp_path: Path, game_data: Path
) -> None:
    (game_data / "characters.json").write_text(
        json.dumps(
            {
                "game_version": "1.1.12.0.beta-3",
                "characters": [
                    _character(
                        "character_bull",
                        wanted=["stat_armor"],
                        weapons=[],
                        modifiers=[],
                    )
                ],
            }
        )
    )

    card = open_drill(cli, game_data, "character_bull")["card"]

    assert card["starting_weapon"] is None


def test_the_reveal_is_refused_until_the_predictions_are_committed(
    cli: CliRunner, game_data: Path
) -> None:
    drill_id = open_drill(cli, game_data, MAGE)["drill_id"]

    result = cli("prep", "--reveal", drill_id)

    assert result.exit_code != 0
    assert "committed" in result.stderr
    assert "mage" not in words(result.stderr + result.stdout)


def test_three_predictions_are_not_enough(cli: CliRunner, game_data: Path) -> None:
    drill_id = open_drill(cli, game_data, MAGE)["drill_id"]

    result = cli(
        "prep",
        "--commit",
        drill_id,
        "--primary-stat",
        "elemental damage",
        "--secondary-stat",
        "attack speed",
        "--weapon-class",
        "elemental",
    )

    assert result.exit_code != 0
    assert "--weakest-wave" in result.stderr


def test_a_committed_prediction_cannot_be_revised(
    cli: CliRunner, game_data: Path
) -> None:
    drill_id = open_drill(cli, game_data, MAGE)["drill_id"]
    assert committed(cli, drill_id).exit_code == 0

    again = committed(cli, drill_id, primary_stat="armor")

    assert again.exit_code != 0
    assert "not revisable" in again.stderr


def test_committing_reveals_nothing(cli: CliRunner, game_data: Path) -> None:
    drill_id = open_drill(cli, game_data, MAGE)["drill_id"]

    result = committed(cli, drill_id)

    assert result.exit_code == 0, result.stderr
    assert "mage" not in words(result.stdout)


def test_the_reveal_names_the_character(cli: CliRunner, game_data: Path) -> None:
    drill_id = open_drill(cli, game_data, MAGE)["drill_id"]
    committed(cli, drill_id)

    revealed = cli("prep", "--reveal", drill_id).json()

    assert revealed["character"]["character_id"] == MAGE
    assert revealed["character"]["wanted_stats"] == ["stat_elemental_damage"]
    assert revealed["character"]["starting_weapon"] == "weapon_wand_1"


def test_each_prediction_is_scored_separately(
    cli: CliRunner, game_data: Path
) -> None:
    drill_id = open_drill(cli, game_data, RANGER)["drill_id"]
    committed(
        cli,
        drill_id,
        primary_stat="ranged damage",
        secondary_stat="engineering",
        weapon_class="gun",
        weakest_wave=12,
    )

    verdicts = cli("prep", "--reveal", drill_id).json()["verdicts"]

    assert verdicts["primary_stat"]["verdict"] == "hit"
    assert verdicts["secondary_stat"]["verdict"] == "miss"
    assert verdicts["weapon_class"]["verdict"] == "hit"
    assert verdicts["weakest_wave"]["verdict"] == "pending"


def test_an_answer_scores_however_it_is_spelled(
    cli: CliRunner, game_data: Path
) -> None:
    drill_id = open_drill(cli, game_data, MAGE)["drill_id"]
    committed(cli, drill_id, primary_stat="Elemental Damage")

    verdicts = cli("prep", "--reveal", drill_id).json()["verdicts"]

    assert verdicts["primary_stat"]["verdict"] == "hit"


def test_either_of_the_two_classes_a_weapon_carries_scores(
    cli: CliRunner, game_data: Path
) -> None:
    drill_id = open_drill(cli, game_data, RANGER)["drill_id"]
    committed(cli, drill_id, weapon_class="precise")

    verdicts = cli("prep", "--reveal", drill_id).json()["verdicts"]

    assert verdicts["weapon_class"]["verdict"] == "hit"


def test_a_stat_the_game_never_names_is_unscorable_rather_than_a_miss(
    cli: CliRunner, game_data: Path
) -> None:
    """The Mage wants one stat, so there is no second one to have been wrong about."""
    drill_id = open_drill(cli, game_data, MAGE)["drill_id"]
    committed(cli, drill_id)

    verdicts = cli("prep", "--reveal", drill_id).json()["verdicts"]

    assert verdicts["secondary_stat"]["verdict"] == "unscorable"


def test_naming_the_same_stat_twice_is_one_prediction(
    cli: CliRunner, game_data: Path
) -> None:
    drill_id = open_drill(cli, game_data, RANGER)["drill_id"]
    committed(cli, drill_id, primary_stat="range", secondary_stat="range")

    verdicts = cli("prep", "--reveal", drill_id).json()["verdicts"]

    assert verdicts["primary_stat"]["verdict"] == "hit"
    assert verdicts["secondary_stat"]["verdict"] == "miss"


def test_the_wave_prediction_is_settled_against_a_run(
    cli: CliRunner, game_data: Path
) -> None:
    drill_id = open_drill(cli, game_data, MAGE)["drill_id"]
    committed(cli, drill_id, weakest_wave=12)

    settled = cli("prep", "--settle", drill_id, "--actual-wave", "13").json()

    assert settled["verdicts"]["weakest_wave"]["verdict"] == "hit"
    assert settled["verdicts"]["weakest_wave"]["actual"] == 13


def test_a_wave_prediction_well_wide_of_the_run_is_a_miss(
    cli: CliRunner, game_data: Path
) -> None:
    drill_id = open_drill(cli, game_data, MAGE)["drill_id"]
    committed(cli, drill_id, weakest_wave=4)

    settled = cli("prep", "--settle", drill_id, "--actual-wave", "17").json()

    assert settled["verdicts"]["weakest_wave"]["verdict"] == "miss"


def test_settling_needs_the_wave_the_run_broke_at(
    cli: CliRunner, game_data: Path
) -> None:
    drill_id = open_drill(cli, game_data, MAGE)["drill_id"]
    committed(cli, drill_id)

    result = cli("prep", "--settle", drill_id)

    assert result.exit_code != 0
    assert "--actual-wave" in result.stderr


def test_history_reports_the_hit_rate_per_dimension(
    cli: CliRunner, game_data: Path
) -> None:
    for primary in ("ranged damage", "engineering"):
        drill_id = open_drill(cli, game_data, RANGER)["drill_id"]
        committed(cli, drill_id, primary_stat=primary)
        cli("prep", "--reveal", drill_id)

    rate = cli("prep", "--history").json()["hit_rate"]

    assert rate["primary_stat"] == {
        "hits": 1,
        "scored": 2,
        "rate": 0.5,
        "pending": 0,
        "unscorable": 0,
    }
    assert rate["weakest_wave"]["pending"] == 2


def test_an_unscorable_dimension_stays_out_of_the_hit_rate(
    cli: CliRunner, game_data: Path
) -> None:
    drill_id = open_drill(cli, game_data, MAGE)["drill_id"]
    committed(cli, drill_id)
    cli("prep", "--reveal", drill_id)

    rate = cli("prep", "--history").json()["hit_rate"]["secondary_stat"]

    assert rate == {
        "hits": 0,
        "scored": 0,
        "rate": None,
        "pending": 0,
        "unscorable": 1,
    }


def test_history_counts_a_drill_that_is_still_open_without_naming_it(
    cli: CliRunner, game_data: Path
) -> None:
    open_drill(cli, game_data, MAGE)

    history = cli("prep", "--history").json()

    assert history == {
        "drills": 1,
        "committed": 0,
        "revealed": 0,
        "settled": 0,
        "hit_rate": history["hit_rate"],
        "taken": [],
    }
    assert "mage" not in words(history)


def test_a_drill_settled_but_never_revealed_is_not_counted_as_revealed(
    cli: CliRunner, game_data: Path
) -> None:
    drill_id = open_drill(cli, game_data, MAGE)["drill_id"]
    committed(cli, drill_id)
    cli("prep", "--settle", drill_id, "--actual-wave", "13")

    history = cli("prep", "--history").json()

    assert history["settled"] == 1
    assert history["revealed"] == 0


@pytest.mark.parametrize(
    ("arguments", "ignored"),
    [
        (("--history",), "a character"),
        (("--reveal", "any-drill", "--primary-stat", "armor"), "--primary-stat"),
        (("--settle", "any-drill", "--actual-wave", "9", "--weapon-class", "gun"),
         "--weapon-class"),
    ],
)
def test_an_argument_a_mode_does_not_read_is_refused_not_dropped(
    cli: CliRunner, game_data: Path, arguments: tuple[str, ...], ignored: str
) -> None:
    """Silently discarding the character would be a confidently wrong answer."""
    result = cli("prep", MAGE, *arguments, data_directory=game_data)

    assert result.exit_code != 0
    assert ignored in result.stderr


def test_history_is_empty_before_the_first_drill(cli: CliRunner) -> None:
    history = cli("prep", "--history").json()

    assert history["drills"] == 0
    assert history["hit_rate"]["primary_stat"]["rate"] is None


def test_an_unknown_character_is_refused_by_name(
    cli: CliRunner, game_data: Path
) -> None:
    result = cli("prep", "character_nobody", data_directory=game_data)

    assert result.exit_code != 0
    assert "character_nobody" in result.stderr


def test_a_drill_needs_extracted_game_data(cli: CliRunner, tmp_path: Path) -> None:
    result = cli("prep", MAGE, data_directory=tmp_path / "nothing-extracted")

    assert result.exit_code != 0
    assert "extract" in result.stderr


def test_naming_a_character_works_without_a_save(
    cli: CliRunner, game_data: Path, save_root: Path
) -> None:
    """The save decides nothing when the player has already decided."""
    result = cli(
        "prep", MAGE, data_directory=game_data, application_support=save_root
    )

    assert result.exit_code == 0, result.stderr


def proposed(cli: CliRunner, game_data: Path, save: Path) -> Any:
    return cli(
        "prep",
        data_directory=game_data,
        application_support=save,
        steam_id="00000000000000000",
    ).json()


def test_with_no_argument_a_character_is_proposed_from_the_save(
    cli: CliRunner, game_data: Path, real_save_root: Path
) -> None:
    opened = proposed(cli, game_data, real_save_root)
    drill_id = opened["drill_id"]
    committed(cli, drill_id)

    revealed = cli("prep", "--reveal", drill_id).json()

    # The Mage is cleared in the committed save and the Ghost is locked in it,
    # which leaves exactly one character worth proposing.
    assert revealed["character"]["character_id"] == RANGER


def test_a_proposal_says_why_without_saying_what(
    cli: CliRunner, game_data: Path, real_save_root: Path
) -> None:
    """The reasoning is printed beside the card, so it may not answer it."""
    opened = proposed(cli, game_data, real_save_root)

    assert opened["proposal"]["reason"]
    assert opened["proposal"]["candidates"] == 1
    assert opened["proposal"]["archetypes_reasoned_about"] == 1
    assert not words(opened["proposal"]) & {"ranged", "range", "elemental", "dodge"}


def test_a_proposal_falls_back_to_every_character_without_a_save(
    cli: CliRunner, game_data: Path, save_root: Path
) -> None:
    opened = cli(
        "prep", data_directory=game_data, application_support=save_root
    ).json()

    assert opened["proposal"]["candidates"] == len(CHARACTERS)
    assert opened["proposal"]["unlocked_known"] == 0
