"""`runs` reads back what `watch` captured: the runs, and one run's snapshots."""

import json
from typing import Any

import pytest
from conftest import REPO_RUNS, CliRunner, Workspace, run_state

HIKER_RUN = "20260831T115414Z-character_hiker"


def play(workspace: Workspace, *waves: int, **fields: Any) -> str:
    """Capture a hand-written run, then end it the way the game does."""
    for wave in waves:
        workspace.write_state(run_state(wave=wave, **fields))
        result = workspace.json_cli("watch", "--once")
    workspace.clear_state()
    workspace.json_cli("watch", "--once")
    return str(result["run_id"])


def test_nothing_captured_yet_is_an_empty_list_not_a_failure(
    workspace: Workspace,
) -> None:
    assert workspace.json_cli("runs")["runs"] == []


def test_runs_lists_captured_runs_and_their_snapshot_counts(
    workspace: Workspace,
) -> None:
    first = play(workspace, 1, 2, 3, character="character_crazy")
    second = play(workspace, 1, 2, character="character_mage")

    listed = {run["run_id"]: run for run in workspace.json_cli("runs")["runs"]}

    assert listed[first]["snapshots"] == 3
    assert listed[first]["character"] == "character_crazy"
    assert listed[first]["waves"] == [1, 2, 3]
    assert listed[second]["snapshots"] == 2
    assert listed[second]["danger"] == 5


def test_a_run_in_progress_is_marked_as_such(workspace: Workspace) -> None:
    workspace.write_state(run_state(wave=1))
    workspace.json_cli("watch", "--once")

    (run,) = workspace.json_cli("runs")["runs"]
    assert run["in_progress"] is True


def test_runs_reads_back_one_run_s_snapshots_in_order(workspace: Workspace) -> None:
    run_id = play(workspace, 1, 2, 3)

    detail = workspace.json_cli("runs", run_id)

    assert detail["run_id"] == run_id
    assert [snapshot["wave"] for snapshot in detail["snapshots"]] == [1, 2, 3]
    # One number per snapshot, and it is the wave the player was in.
    assert "waves_cleared" not in detail["snapshots"][0]
    first = detail["snapshots"][0]["state"]["current_run_state"]
    # The game's own counter, copied whole: no waves cleared yet in wave 1.
    assert first["current_wave"] == 0
    assert first["players_data"][0]["current_character"] == "character_crazy"


def test_the_wave_reported_is_the_wave_being_played_not_the_count_cleared(
    workspace: Workspace,
) -> None:
    """The game's `current_wave` counts waves finished; a reader means the next.

    A reading taken in the shop after wave 7 is stored as `7` and describes the
    run standing at the start of wave 8.
    """
    workspace.write_state(run_state(wave=8))
    captured = workspace.json_cli("watch", "--once")

    assert captured["wave"] == 8
    (run,) = workspace.json_cli("runs")["runs"]
    assert run["waves"] == [8]
    stored = json.loads(
        (workspace.runs_dir / run["run_id"] / "run.json").read_text()
    )
    assert stored["snapshots"][0]["waves_cleared"] == 7
    assert "wave" not in stored["snapshots"][0]


def test_metadata_written_before_the_wave_fix_still_reads_back(
    workspace: Workspace,
) -> None:
    """`run.json` files captured then stored the cleared count under `wave`."""
    play(workspace, 5)
    (run,) = workspace.json_cli("runs")["runs"]
    metadata_path = workspace.runs_dir / run["run_id"] / "run.json"
    metadata = json.loads(metadata_path.read_text())
    for snapshot in metadata["snapshots"]:
        snapshot["wave"] = snapshot.pop("waves_cleared")
    metadata_path.write_text(json.dumps(metadata))

    (reread,) = workspace.json_cli("runs")["runs"]
    assert reread["waves"] == [5]


def test_a_real_captured_run_reports_the_waves_the_game_logged(
    cli: CliRunner,
) -> None:
    """The run issue #33 was diagnosed against, checked against the game's log.

    `log.txt` printed `Wave: 3  Gold: 13` beside the reading stored as
    `waves_cleared: 2`, and the run ended in wave 8. Wave 1 is absent because
    the earliest reading the game wrote already had a wave cleared.
    """
    if not (REPO_RUNS / HIKER_RUN).is_dir():
        pytest.skip("the committed hiker run is not in this checkout")

    runs = cli("runs", runs_dir=REPO_RUNS).json()["runs"]
    listed = {run["run_id"]: run for run in runs}

    assert listed[HIKER_RUN]["waves"] == [2, 3, 4, 5, 6, 7, 8]


def test_an_unknown_run_is_an_error_that_says_so(workspace: Workspace) -> None:
    play(workspace, 1)

    result = workspace.cli("runs", "no-such-run")

    assert result.returncode != 0
    assert "no-such-run" in result.stderr
