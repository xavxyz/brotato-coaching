"""`watch` decides, one file change at a time, whether to keep a snapshot.

Every test here drives that decision synchronously through `watch --once`
against a hand-written sequence of live run states, except the last group, which
drives the long-running watcher through its start/stop/status commands.
"""

import json
import time
from typing import Any, Callable

from conftest import Workspace, run_state


def capture(workspace: Workspace, state: dict[str, Any]) -> Any:
    """Write one live state, then make one capture decision about it."""
    workspace.write_state(state)
    return workspace.json_cli("watch", "--once")


def wait_until(predicate: Callable[[], bool], timeout: float = 10.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.05)
    return predicate()


class TestCaptureDecision:
    def test_a_run_in_progress_is_captured(self, workspace: Workspace) -> None:
        result = capture(workspace, run_state(wave=1))

        assert result["captured"] is True
        assert result["wave"] == 1
        assert result["character"] == "character_crazy"
        assert len(workspace.snapshot_files()) == 1

    def test_the_snapshot_holds_the_whole_live_state(
        self, workspace: Workspace
    ) -> None:
        state = run_state(wave=1, gold=40)
        capture(workspace, state)

        (snapshot,) = workspace.snapshot_files()
        assert json.loads(snapshot.read_text()) == state

    def test_an_unchanged_file_is_not_captured_again(
        self, workspace: Workspace
    ) -> None:
        state = run_state(wave=1)
        first = capture(workspace, state)
        second = capture(workspace, state)

        assert second["captured"] is False
        assert second["reason"] == "unchanged"
        assert second["run_id"] == first["run_id"]
        assert len(workspace.snapshot_files()) == 1

    def test_every_change_adds_a_snapshot_to_the_same_run(
        self, workspace: Workspace
    ) -> None:
        results = [capture(workspace, run_state(wave=wave)) for wave in (1, 2, 3)]

        assert all(result["captured"] for result in results)
        assert len({result["run_id"] for result in results}) == 1
        assert len(workspace.snapshot_files()) == 3

    def test_a_change_within_one_wave_is_captured_too(
        self, workspace: Workspace
    ) -> None:
        capture(workspace, run_state(wave=3, gold=10))
        result = capture(workspace, run_state(wave=3, gold=55))

        assert result["captured"] is True
        assert len(workspace.snapshot_files()) == 2

    def test_no_run_in_progress_is_reported_rather_than_captured(
        self, workspace: Workspace
    ) -> None:
        workspace.clear_state()
        result = workspace.json_cli("watch", "--once")

        assert result["captured"] is False
        assert result["reason"] == "no-run-in-progress"
        assert workspace.snapshot_files() == []

    def test_a_missing_live_state_file_is_reported_rather_than_failing(
        self, workspace: Workspace
    ) -> None:
        result = workspace.cli("watch", "--once")

        assert result.returncode == 0, result.stderr
        assert json.loads(result.stdout)["reason"] == "no-live-state-file"

    def test_a_half_written_live_state_file_is_reported_rather_than_failing(
        self, workspace: Workspace
    ) -> None:
        workspace.state_path.write_text('{"current_run_state": {"has_run')
        result = workspace.cli("watch", "--once")

        assert result.returncode == 0, result.stderr
        assert json.loads(result.stdout)["reason"] == "unreadable-live-state"


class TestRunBoundaries:
    def test_snapshots_survive_the_game_clearing_the_file(
        self, workspace: Workspace
    ) -> None:
        for wave in (1, 2, 3):
            capture(workspace, run_state(wave=wave))

        workspace.clear_state()
        ended = workspace.json_cli("watch", "--once")

        assert len(workspace.snapshot_files()) == 3
        (run,) = workspace.json_cli("runs")["runs"]
        assert run["run_id"] == ended["ended_run"]
        assert run["snapshots"] == 3
        assert run["in_progress"] is False

    def test_a_run_played_after_a_clear_is_a_separate_run(
        self, workspace: Workspace
    ) -> None:
        first = capture(workspace, run_state(wave=1))
        capture(workspace, run_state(wave=2))
        workspace.clear_state()
        workspace.json_cli("watch", "--once")
        second = capture(workspace, run_state(wave=1))

        assert second["run_id"] != first["run_id"]
        assert len(workspace.json_cli("runs")["runs"]) == 2

    def test_a_new_character_starts_a_new_run_even_without_a_clear(
        self, workspace: Workspace
    ) -> None:
        first = capture(workspace, run_state(wave=4, character="character_crazy"))
        second = capture(workspace, run_state(wave=1, character="character_mage"))

        assert second["run_id"] != first["run_id"]

    def test_a_wave_going_backwards_starts_a_new_run(
        self, workspace: Workspace
    ) -> None:
        first = capture(workspace, run_state(wave=6))
        second = capture(workspace, run_state(wave=1))

        assert second["run_id"] != first["run_id"]


class TestWatcherLifecycle:
    def test_the_watcher_is_not_running_before_it_is_started(
        self, workspace: Workspace
    ) -> None:
        status = workspace.json_cli("watch", "--status")

        assert status["running"] is False
        assert status["pid"] is None

    def test_one_command_starts_it_and_one_command_stops_it(
        self, workspace: Workspace
    ) -> None:
        workspace.write_state(run_state(wave=1))
        started = workspace.json_cli("watch", "--start")
        assert started["started"] is True

        assert wait_until(lambda: len(workspace.snapshot_files()) == 1)
        assert workspace.json_cli("watch", "--status")["running"] is True

        workspace.write_state(run_state(wave=2))
        assert wait_until(lambda: len(workspace.snapshot_files()) == 2)

        stopped = workspace.json_cli("watch", "--stop")
        assert stopped["stopped"] is True
        assert stopped["captured"] == 2
        assert workspace.json_cli("watch", "--status")["running"] is False

    def test_starting_a_watcher_that_is_already_running_is_refused(
        self, workspace: Workspace
    ) -> None:
        workspace.clear_state()
        workspace.json_cli("watch", "--start")
        try:
            again = workspace.json_cli("watch", "--start")
            assert again["started"] is False
            assert again["reason"] == "already-running"
        finally:
            workspace.json_cli("watch", "--stop")

    def test_a_session_that_captured_nothing_is_reported(
        self, workspace: Workspace
    ) -> None:
        workspace.clear_state()
        workspace.json_cli("watch", "--start")
        stopped = workspace.json_cli("watch", "--stop")

        assert stopped["captured"] == 0
        assert "captured nothing" in stopped["note"]
        assert workspace.json_cli("watch", "--status")["last_session"]["captured"] == 0

    def test_stopping_a_watcher_that_is_not_running_is_reported(
        self, workspace: Workspace
    ) -> None:
        result = workspace.cli("watch", "--stop")

        assert result.returncode == 0, result.stderr
        assert json.loads(result.stdout)["reason"] == "not-running"
