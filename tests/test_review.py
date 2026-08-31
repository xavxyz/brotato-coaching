"""`review` reads a dead run back, and refuses to diagnose before the hypothesis.

Every test drives the CLI. The interesting behaviour is in three places: what a
briefing can say about a run without being told anything about it, the order the
hypothesis and the diagnosis have to be written in, and what falls out of the
records once several runs have been reviewed.
"""

import json
from pathlib import Path
from typing import Any

import pytest
from conftest import (
    COMMITTED_RUN,
    REPO_RUNS,
    CliRunner,
    Workspace,
    run_state,
    write_game_data,
)

from brotato_coaching.gamedata import godot_hash


def capture(workspace: Workspace, *states: dict[str, Any]) -> None:
    """Play a run past the watcher, one state at a time, then die."""
    for state in states:
        workspace.write_state(state)
        workspace.json_cli("watch", "--once")
    workspace.clear_state()
    workspace.json_cli("watch", "--once")


def a_run(workspace: Workspace, **overrides: Any) -> None:
    """One two-wave run, captured, ended, and ready to be reviewed."""
    capture(
        workspace,
        run_state(wave=1, **overrides),
        run_state(wave=2, gold=40, **overrides),
    )


def records_in(workspace: Workspace) -> list[Path]:
    return sorted(workspace.records_dir.glob("*.json"))


class TestBriefing:
    """What a review can say about a run before the player says anything."""

    def test_the_latest_run_is_read_without_being_named(
        self, workspace: Workspace
    ) -> None:
        a_run(workspace, character="character_mage")
        a_run(workspace, character="character_crazy")

        briefing = workspace.json_cli("review")

        assert briefing["character"] == "character_crazy"
        assert briefing["danger"] == 5
        assert briefing["waves"] == {"reached": 2, "of": 20}

    def test_the_build_comes_out_of_the_snapshots(self, workspace: Workspace) -> None:
        a_run(
            workspace,
            weapons=("weapon_shuriken_4", "weapon_shuriken_4", "weapon_pistol_1"),
            items=("item_hedgehog", "item_hedgehog", "item_scar"),
        )

        briefing = workspace.json_cli("review")

        assert briefing["weapons"] == [
            {"id": "weapon_shuriken_4", "tier": 4, "count": 2},
            {"id": "weapon_pistol_1", "tier": 1, "count": 1},
        ]
        assert {"id": "item_hedgehog", "count": 2} in briefing["key_items"]
        assert briefing["items_held"] == 3

    def test_key_items_are_the_ones_the_player_stacked(
        self, workspace: Workspace
    ) -> None:
        a_run(workspace, items=("item_hedgehog", "item_hedgehog", "item_scar"))

        briefing = workspace.json_cli("review")

        assert briefing["key_items"] == [{"id": "item_hedgehog", "count": 2}]

    def test_an_item_held_once_is_still_in_the_briefing(
        self, workspace: Workspace
    ) -> None:
        a_run(workspace, items=("item_hedgehog", "item_hedgehog", "item_scar"))

        briefing = workspace.json_cli("review")

        assert briefing["items"] == {"item_hedgehog": 2, "item_scar": 1}

    def test_final_stats_are_read_back_out_of_the_hashed_effects(
        self, workspace: Workspace
    ) -> None:
        a_run(workspace, stats={"stat_armor": 12, "stat_max_hp": 60})

        briefing = workspace.json_cli("review")

        assert briefing["final_stats"]["stat_armor"] == 12
        assert briefing["final_stats"]["stat_max_hp"] == 60

    def test_the_curve_holds_one_entry_per_wave(self, workspace: Workspace) -> None:
        capture(
            workspace,
            run_state(wave=1, gold=10, level=2),
            run_state(wave=1, gold=20, level=3),
            run_state(wave=2, gold=30, level=5),
        )

        curve = workspace.json_cli("review")["curve"]

        assert [entry["wave"] for entry in curve] == [1, 2]
        # The last reading of a wave is the one that describes it.
        assert curve[0]["gold"] == 20
        assert curve[0]["level"] == 3
        assert curve[1]["level"] == 5

    def test_a_briefing_carries_no_diagnosis(self, workspace: Workspace) -> None:
        a_run(workspace)

        briefing = workspace.json_cli("review")

        assert briefing["hypothesis"] is None
        assert briefing["diagnosis"] is None
        assert briefing["change"] is None

    def test_a_named_run_is_reviewed_instead_of_the_latest(
        self, workspace: Workspace
    ) -> None:
        a_run(workspace, character="character_mage")
        a_run(workspace, character="character_crazy")
        first = workspace.json_cli("runs")["runs"][0]["run_id"]

        briefing = workspace.json_cli("review", first)

        assert briefing["run_id"] == first
        assert briefing["character"] == "character_mage"

    def test_nothing_captured_is_reported_rather_than_failed(
        self, workspace: Workspace
    ) -> None:
        result = workspace.cli("review")

        assert result.returncode == 0, result.stderr
        assert json.loads(result.stdout) == {
            "reviewed": False,
            "reason": "no-runs-captured",
            "runs_dir": str(workspace.runs_dir),
        }

    def test_an_unknown_run_is_an_error_that_says_how_to_list_them(
        self, workspace: Workspace
    ) -> None:
        a_run(workspace)

        result = workspace.cli("review", "no-such-run")

        assert result.returncode != 0
        assert "runs" in result.stderr


class TestDeathCauses:
    """The save's death histogram, which is what the run itself cannot say."""

    def write_save(self, workspace: Workspace, **deaths: int) -> None:
        """A save whose only interesting field is what has killed the player."""
        document = {
            "version": 3,
            "data": {"run_started": 4, "run_won": 0},
            "difficulties_unlocked": [],
            "killed_by_enemies": {
                str(godot_hash(enemy)): count for enemy, count in deaths.items()
            },
            "items_bought": {},
        }
        (workspace.save_directory / "save_v3_0.json").write_text(json.dumps(document))

    def test_the_save_supplies_what_has_been_killing_the_player(
        self, workspace: Workspace
    ) -> None:
        self.write_save(workspace, lamprey=4, chaser=1)
        a_run(workspace)

        deaths = workspace.json_cli("review")["death_causes"]

        # Raw, because nothing has been extracted: still countable, still ordered.
        assert [cause["deaths"] for cause in deaths] == [4, 1]

    def test_death_causes_are_named_once_the_game_data_is_extracted(
        self, workspace: Workspace, tmp_path: Path
    ) -> None:
        self.write_save(workspace, lamprey=4, chaser=1)
        workspace.data_dir = write_game_data(
            tmp_path / "data", enemies=["lamprey", "chaser"]
        )
        a_run(workspace)

        deaths = workspace.json_cli("review")["death_causes"]

        assert deaths == [
            {"enemy": "lamprey", "deaths": 4},
            {"enemy": "chaser", "deaths": 1},
        ]

    def test_a_missing_save_leaves_the_review_readable(
        self, workspace: Workspace
    ) -> None:
        a_run(workspace)

        briefing = workspace.json_cli("review")

        assert briefing["death_causes"] == []
        assert briefing["death_causes_reason"] is not None


class TestOrdering:
    """The hypothesis is written first. That is the point of the whole loop."""

    def test_a_diagnosis_before_a_hypothesis_is_refused(
        self, workspace: Workspace
    ) -> None:
        a_run(workspace)

        result = workspace.cli(
            "review", "--diagnosis", "too few weapons", "--change", "buy earlier"
        )

        assert result.returncode != 0
        assert "hypothesis" in result.stderr
        assert records_in(workspace) == []

    def test_a_diagnosis_needs_the_one_change_with_it(
        self, workspace: Workspace
    ) -> None:
        a_run(workspace)

        result = workspace.cli("review", "--diagnosis", "too few weapons")

        assert result.returncode != 0
        assert "--change" in result.stderr

    def test_the_hypothesis_is_recorded_with_the_run_it_is_about(
        self, workspace: Workspace
    ) -> None:
        a_run(workspace, items=("item_scar", "item_scar"), stats={"stat_armor": 12})

        recorded = workspace.json_cli(
            "review", "--hypothesis", "I over-bought armour and never scaled damage"
        )

        assert recorded["hypothesis"]["text"] == (
            "I over-bought armour and never scaled damage"
        )
        assert recorded["diagnosis"] is None
        assert [path.name for path in records_in(workspace)] == [
            f"{recorded['run_id']}.json"
        ]

    def test_the_record_follows_the_fixed_schema(self, workspace: Workspace) -> None:
        a_run(workspace)
        workspace.json_cli("review", "--hypothesis", "ran out of damage")
        workspace.json_cli(
            "review", "--diagnosis", "damage flat from wave 9", "--change", "buy a tier-2 weapon by wave 6"
        )

        (record,) = records_in(workspace)
        written = json.loads(record.read_text())

        assert set(written) == {
            "schema_version",
            "run_id",
            "character",
            "danger",
            "zone",
            "patch",
            "waves",
            "weapons",
            "items",
            "key_items",
            "final_stats",
            "death_causes",
            "hypothesis",
            "diagnosis",
            "change",
            "revisions",
        }
        assert written["diagnosis"]["text"] == "damage flat from wave 9"
        assert written["change"]["text"] == "buy a tier-2 weapon by wave 6"

    def test_the_diagnosis_is_recorded_after_the_hypothesis(
        self, workspace: Workspace
    ) -> None:
        a_run(workspace)
        workspace.json_cli("review", "--hypothesis", "ran out of damage")

        diagnosed = workspace.json_cli(
            "review", "--diagnosis", "damage flat from wave 9", "--change", "buy earlier"
        )

        assert diagnosed["hypothesis"]["text"] == "ran out of damage"
        assert diagnosed["hypothesis"]["recorded_at"] <= (
            diagnosed["diagnosis"]["recorded_at"]
        )
        assert diagnosed["change"]["text"] == "buy earlier"

    def test_a_briefing_shows_what_has_already_been_recorded(
        self, workspace: Workspace
    ) -> None:
        a_run(workspace)
        workspace.json_cli("review", "--hypothesis", "ran out of damage")

        briefing = workspace.json_cli("review")

        assert briefing["hypothesis"]["text"] == "ran out of damage"
        assert briefing["diagnosis"] is None

    def test_rediagnosing_needs_a_fresh_hypothesis_first(
        self, workspace: Workspace
    ) -> None:
        a_run(workspace)
        workspace.json_cli("review", "--hypothesis", "ran out of damage")
        workspace.json_cli(
            "review", "--diagnosis", "damage flat from wave 9", "--change", "buy earlier"
        )

        result = workspace.cli(
            "review", "--diagnosis", "armour was the real gap", "--change", "buy armour"
        )

        assert result.returncode != 0
        assert "hypothesis" in result.stderr

    def test_a_fresh_hypothesis_keeps_the_old_review_as_a_revision(
        self, workspace: Workspace
    ) -> None:
        a_run(workspace)
        workspace.json_cli("review", "--hypothesis", "ran out of damage")
        workspace.json_cli(
            "review", "--diagnosis", "damage flat from wave 9", "--change", "buy earlier"
        )

        again = workspace.json_cli("review", "--hypothesis", "armour was the gap")

        assert again["hypothesis"]["text"] == "armour was the gap"
        assert again["diagnosis"] is None
        assert again["change"] is None
        assert [revision["diagnosis"]["text"] for revision in again["revisions"]] == [
            "damage flat from wave 9"
        ]

    def test_a_damaged_record_is_reported_rather_than_overwritten(
        self, workspace: Workspace
    ) -> None:
        a_run(workspace)
        workspace.json_cli("review", "--hypothesis", "ran out of damage")
        (record,) = records_in(workspace)
        record.write_text("{ this is not json")

        result = workspace.cli("review", "--hypothesis", "second thoughts")

        assert result.returncode != 0
        assert record.read_text() == "{ this is not json"

    def test_a_hypothesis_can_be_corrected_before_the_diagnosis_lands(
        self, workspace: Workspace
    ) -> None:
        a_run(workspace)
        workspace.json_cli("review", "--hypothesis", "ran out of damage")

        second = workspace.json_cli("review", "--hypothesis", "ran out of armour")

        assert second["hypothesis"]["text"] == "ran out of armour"
        assert second["revisions"] == []


class TestRecords:
    """Several reviewed runs, asked the question one run cannot answer."""

    def review(self, workspace: Workspace, hypothesis: str, change: str) -> None:
        workspace.json_cli("review", "--hypothesis", hypothesis)
        workspace.json_cli(
            "review", "--diagnosis", f"diagnosed: {hypothesis}", "--change", change
        )

    def test_nothing_reviewed_is_an_empty_answer_not_an_error(
        self, workspace: Workspace
    ) -> None:
        result = workspace.cli("records")

        assert result.returncode == 0, result.stderr
        assert json.loads(result.stdout)["records"] == []

    def test_every_reviewed_run_is_listed(self, workspace: Workspace) -> None:
        a_run(workspace, character="character_mage")
        self.review(workspace, "no damage", "buy damage")
        a_run(workspace, character="character_crazy")
        self.review(workspace, "no armour", "buy armour")

        records = workspace.json_cli("records")["records"]

        assert [record["character"] for record in records] == [
            "character_mage",
            "character_crazy",
        ]
        assert [record["change"]["text"] for record in records] == [
            "buy damage",
            "buy armour",
        ]

    def test_a_repeated_change_surfaces_with_its_count(
        self, workspace: Workspace
    ) -> None:
        for _ in range(3):
            a_run(workspace)
            self.review(workspace, "no damage", "buy a tier-2 weapon by wave 6")

        patterns = workspace.json_cli("records")["patterns"]

        assert patterns["changes"][0] == {
            "text": "buy a tier-2 weapon by wave 6",
            "count": 3,
        }

    def test_dying_the_same_way_repeatedly_is_countable(
        self, workspace: Workspace
    ) -> None:
        for character in ("character_crazy", "character_crazy", "character_mage"):
            a_run(workspace, character=character)
            self.review(workspace, "no damage", "buy damage")

        patterns = workspace.json_cli("records")["patterns"]

        assert patterns["runs_reviewed"] == 3
        assert patterns["by_character"]["character_crazy"] == 2
        assert patterns["by_final_wave"]["2"] == 3
        # The joint count, which is what "you have died this way twice" means.
        assert patterns["repeated_deaths"] == [
            {"character": "character_crazy", "wave": 2, "count": 2}
        ]

    def test_a_run_reviewed_only_as_far_as_the_hypothesis_is_marked_incomplete(
        self, workspace: Workspace
    ) -> None:
        a_run(workspace)
        workspace.json_cli("review", "--hypothesis", "no damage")

        (record,) = workspace.json_cli("records")["records"]

        assert record["complete"] is False


class TestTheCommittedRun:
    """The one real run, read by the same code paths as a hand-written one."""

    @pytest.fixture(autouse=True)
    def committed_run_exists(self) -> None:
        if not (REPO_RUNS / COMMITTED_RUN).is_dir():
            pytest.skip("the committed run is not in this checkout")

    def test_the_real_run_reads_back_as_the_build_that_was_played(
        self, cli: CliRunner
    ) -> None:
        briefing = cli("review", COMMITTED_RUN, runs_dir=REPO_RUNS).json()

        assert briefing["character"] == "character_crazy"
        assert briefing["danger"] == 5
        # The last snapshot is the shop after wave 19 — the start of wave 20,
        # which the save confirms this run went on to win.
        assert briefing["waves"] == {"reached": 20, "of": 20}
        # The game stores that weapon's tier as "3"; a review reports the tier
        # the player was looking at.
        assert briefing["weapons"][0] == {
            "id": "weapon_shuriken_4",
            "tier": 4,
            "count": 4,
        }
        assert briefing["final_stats"]["stat_max_hp"] == 60
        assert briefing["curve"][-1]["wave"] == 20
