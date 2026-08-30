"""The CLI is the one seam: every package is reached through it."""

from conftest import CliRunner

PLANNED_SUBCOMMANDS = ("extract", "progress", "runs", "watch")
NOT_BUILT_YET = ("extract", "runs", "watch")


def test_help_succeeds(cli: CliRunner) -> None:
    result = cli("--help")
    assert result.exit_code == 0, result.stderr


def test_help_lists_every_planned_subcommand(cli: CliRunner) -> None:
    output = cli("--help").stdout
    for subcommand in PLANNED_SUBCOMMANDS:
        assert subcommand in output


def test_no_subcommand_is_an_error_that_names_the_choices(cli: CliRunner) -> None:
    result = cli()
    assert result.exit_code != 0
    for subcommand in PLANNED_SUBCOMMANDS:
        assert subcommand in result.stderr


def test_planned_subcommand_reports_that_it_is_not_built_yet(cli: CliRunner) -> None:
    for subcommand in NOT_BUILT_YET:
        result = cli(subcommand)
        assert result.exit_code != 0
        assert "not implemented" in result.stderr.lower()
