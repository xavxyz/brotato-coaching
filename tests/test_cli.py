"""The CLI is the one seam: every package is reached through it."""

import json
import os
import subprocess
import sys
from pathlib import Path

from test_gamedata import BASE_RESOURCES, ABYSSAL_TERRORS_RESOURCES, write_container

PLANNED_SUBCOMMANDS = ("extract", "progress", "runs", "watch")
UNBUILT_SUBCOMMANDS = ("progress", "runs", "watch")


def run_cli(
    *args: str, environment: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "brotato_coaching", *args],
        capture_output=True,
        text=True,
        env={**os.environ, **(environment or {})},
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


def test_a_subcommand_that_is_not_built_yet_says_so() -> None:
    for subcommand in UNBUILT_SUBCOMMANDS:
        result = run_cli(subcommand)
        assert result.returncode != 0
        assert "not implemented" in result.stderr.lower()


def synthetic_install(directory: Path) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    write_container(directory / "Brotato.pck", BASE_RESOURCES)
    write_container(directory / "BrotatoAbyssalTerrors.pck", ABYSSAL_TERRORS_RESOURCES)
    return directory


def test_extract_writes_json_into_the_destination(tmp_path: Path) -> None:
    install = synthetic_install(tmp_path / "Brotato")
    destination = tmp_path / "data"

    result = run_cli(
        "extract",
        "--destination",
        str(destination),
        environment={"BROTATO_INSTALL_DIR": str(install)},
    )

    assert result.returncode == 0, result.stderr
    summary = json.loads(result.stdout)
    assert summary["counts"]["characters"] == 2
    assert sorted(path.name for path in destination.iterdir()) == [
        "characters.json",
        "items.json",
        "weapons.json",
    ]


def test_extract_reports_an_install_it_cannot_find(tmp_path: Path) -> None:
    result = run_cli(
        "extract",
        "--destination",
        str(tmp_path / "data"),
        environment={"BROTATO_INSTALL_DIR": str(tmp_path / "nowhere")},
    )

    assert result.returncode != 0
    assert "BROTATO_INSTALL_DIR" in result.stderr
