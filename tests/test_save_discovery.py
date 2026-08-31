"""One question, one answer: where this player's Brotato directory is.

Parameterised over the *subcommands* that go looking, not over the function they
share. The defect this guards was a second consumer that never asked — a unit
test on discovery would have been green throughout.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from conftest import PLACEHOLDER_STEAM_ID, CliRunner, Workspace, run_state

# Every subcommand that touches the player's files, with the invocation that
# makes it touch them. A subcommand added later must be added here.
LOOKS_FOR_THE_PLAYERS_FILES = [
    pytest.param(("progress",), id="progress"),
    pytest.param(("watch", "--once"), id="watch"),
]


@pytest.mark.parametrize("arguments", LOOKS_FOR_THE_PLAYERS_FILES)
def test_every_subcommand_honours_the_application_support_setting(
    cli: CliRunner, tmp_path: Path, arguments: tuple[str, ...]
) -> None:
    """The setting is documented as the way to move the save root. It moves it.

    Asserted on the combined output because the two subcommands report a missing
    directory differently — `progress` cannot do its job without one and fails,
    `watch` reports it as a state — but neither may quietly read the real save.
    """
    elsewhere = tmp_path / "nowhere"

    result = cli(*arguments, application_support=elsewhere)

    assert "nowhere" in result.stdout + result.stderr
    assert "Traceback" not in result.stderr


@pytest.mark.parametrize("arguments", LOOKS_FOR_THE_PLAYERS_FILES)
def test_no_subcommand_falls_back_to_the_machine_it_runs_on(
    cli: CliRunner, tmp_path: Path, arguments: tuple[str, ...]
) -> None:
    """Pointed at an empty root, a subcommand refuses rather than guessing."""
    empty = tmp_path / "empty"
    empty.mkdir()

    output = cli(*arguments, application_support=empty)

    assert "Library/Application Support" not in output.stdout + output.stderr


def test_the_watcher_finds_the_live_run_state_through_discovery(
    workspace: Workspace,
) -> None:
    """No path is handed in: the save directory is discovered, the filename composed."""
    workspace.write_state(run_state(wave=1))

    result = workspace.json_cli("watch", "--once")

    assert result["captured"] is True
    assert str(workspace.state_path) in result["snapshot"] or result["run_id"]


def test_a_save_directory_with_a_run_but_no_save_is_watchable(
    cli: CliRunner, save_root: Path, tmp_path: Path
) -> None:
    """`watch` must not require a save file it never reads.

    A player whose run is in progress on a fresh install has a live run state and
    no save yet. The directory is discovered on its own evidence, so this works.
    """
    directory = save_root / PLACEHOLDER_STEAM_ID
    directory.mkdir()
    (directory / "run_v3_0.json").write_text(
        '{"current_run_state": {"has_run_state": false}}', encoding="utf-8"
    )

    result = cli("watch", "--once", application_support=save_root)

    assert result.exit_code == 0, result.stderr
    assert result.json()["reason"] == "no-run-in-progress"


# `--stop` and `--status` speak about a watcher and about `runs/`, and never
# about the game. Gating them on discovery — as building the `RunLog` up front
# once did — means a watcher detached before the save root moved or was unmounted
# can no longer be inspected *or* stopped, which is the worst moment to lose both.
INSPECTS_THE_WATCHER_ONLY = [
    pytest.param(("watch", "--status"), "running", id="status"),
    pytest.param(("watch", "--stop"), "stopped", id="stop"),
]


@pytest.mark.parametrize("arguments, answer", INSPECTS_THE_WATCHER_ONLY)
def test_the_watcher_can_be_inspected_and_stopped_with_no_save_directory(
    cli: CliRunner, tmp_path: Path, arguments: tuple[str, ...], answer: str
) -> None:
    """Both answer about the watcher, so neither may go looking for the game.

    No watcher is running here, which is the fast and non-flaky case: the point
    is that the answer is about a watcher at all, rather than the
    `no-save-directory` state that discovery would have produced first.
    """
    empty = tmp_path / "empty"
    empty.mkdir()

    result = cli(*arguments, application_support=empty)

    assert result.exit_code == 0, result.stderr
    payload = result.json()
    assert answer in payload
    assert payload.get("reason") != "no-save-directory"
