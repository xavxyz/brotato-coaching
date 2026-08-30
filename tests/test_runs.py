"""`runs` reads back what `watch` captured: the runs, and one run's snapshots."""

from typing import Any

from conftest import Workspace, run_state


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
    first = detail["snapshots"][0]["state"]["current_run_state"]
    assert first["current_wave"] == 1
    assert first["players_data"][0]["current_character"] == "character_crazy"


def test_an_unknown_run_is_an_error_that_says_so(workspace: Workspace) -> None:
    play(workspace, 1)

    result = workspace.cli("runs", "no-such-run")

    assert result.returncode != 0
    assert "no-such-run" in result.stderr
