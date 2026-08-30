"""The CLI is the one seam: every package is reached through it."""

import subprocess
import sys

PLANNED_SUBCOMMANDS = ("extract", "progress", "runs", "watch")


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "brotato_coaching", *args],
        capture_output=True,
        text=True,
    )


def test_help_succeeds() -> None:
    result = run_cli("--help")
    assert result.returncode == 0, result.stderr


def test_help_lists_every_planned_subcommand() -> None:
    output = run_cli("--help").stdout
    for subcommand in PLANNED_SUBCOMMANDS:
        assert subcommand in output


def test_no_subcommand_is_an_error_that_names_the_choices() -> None:
    result = run_cli()
    assert result.returncode != 0
    for subcommand in PLANNED_SUBCOMMANDS:
        assert subcommand in result.stderr


def test_planned_subcommand_reports_that_it_is_not_built_yet() -> None:
    for subcommand in PLANNED_SUBCOMMANDS:
        result = run_cli(subcommand)
        assert result.returncode != 0
        assert "not implemented" in result.stderr.lower()
