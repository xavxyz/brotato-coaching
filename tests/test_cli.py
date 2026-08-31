"""The CLI is the one seam: every package is reached through it."""

from pathlib import Path

from conftest import CliRunner
from test_gamedata import ABYSSAL_TERRORS_RESOURCES, BASE_RESOURCES, write_container

PLANNED_SUBCOMMANDS = (
    "extract",
    "prep",
    "progress",
    "records",
    "review",
    "runs",
    "watch",
)


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


def synthetic_install(directory: Path) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    write_container(directory / "Brotato.pck", BASE_RESOURCES)
    write_container(directory / "BrotatoAbyssalTerrors.pck", ABYSSAL_TERRORS_RESOURCES)
    return directory


def test_extract_writes_json_into_the_destination(
    cli: CliRunner, tmp_path: Path
) -> None:
    install = synthetic_install(tmp_path / "Brotato")
    destination = tmp_path / "data"

    result = cli("extract", "--destination", str(destination), install_dir=install)

    assert result.exit_code == 0, result.stderr
    summary = result.json()
    assert summary["counts"]["characters"] == 2
    assert sorted(path.name for path in destination.iterdir()) == [
        "characters.json",
        "enemies.json",
        "items.json",
        "weapons.json",
    ]


def test_extract_reports_an_install_it_cannot_find(
    cli: CliRunner, tmp_path: Path
) -> None:
    result = cli(
        "extract",
        "--destination",
        str(tmp_path / "data"),
        install_dir=tmp_path / "nowhere",
    )

    assert result.exit_code != 0
    assert "BROTATO_INSTALL_DIR" in result.stderr
