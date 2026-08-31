"""Everything the suite shares: one way to drive the CLI.

The CLI is the only seam. Tests reach the packages through it and assert on the
JSON that comes out, never on how it was produced.

Every fixture here hands a test a throwaway workspace — an empty stand-in for
the save directory, or a live run state file the test writes by hand next to an
empty `runs/` for the watcher to fill.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from brotato_coaching.gamedata import (
    GameInstall,
    InstallNotFound,
    find_install,
    godot_hash,
)

FIXTURES = Path(__file__).parent / "fixtures"
REAL_SAVE_ROOT = FIXTURES / "save"
PLACEHOLDER_STEAM_ID = "00000000000000000"

# A Steam account id is exactly 17 digits. The digit-boundary anchors are
# load-bearing: the repo cites Steam forum and news URLs, whose thread ids are
# longer than an account id, and an unanchored 17-digit window would match
# inside every one of them.
STEAM_ID_SHAPED = re.compile(r"(?<!\d)\d{17}(?!\d)")


def steam_ids_in(text: str) -> set[str]:
    """Steam-ID-shaped digit runs in `text`, minus the documented placeholder."""
    return {
        match
        for match in STEAM_ID_SHAPED.findall(text)
        if match != PLACEHOLDER_STEAM_ID
    }

# Discovery reads these. Tests always set them explicitly, and always start from
# an environment with them cleared, so the machine running the suite cannot leak
# a real save — or a real Steam ID, or a real game install — into a result.
_DISCOVERY_VARIABLES = (
    "STEAM_ID",
    "BROTATO_APPLICATION_SUPPORT",
    "BROTATO_INSTALL_DIR",
    "BROTATO_RUNS_DIR",
    "BROTATO_RECORDS_DIR",
    "BROTATO_DRILLS_DIR",
    "BROTATO_POLL_INTERVAL",
    "BROTATO_DATA_DIR",
)


def _isolated_environment() -> dict[str, str]:
    return {
        key: value
        for key, value in os.environ.items()
        if key not in _DISCOVERY_VARIABLES
    }


class CliResult:
    """A finished CLI invocation, with its stdout parsed on demand."""

    def __init__(self, completed: subprocess.CompletedProcess[str]) -> None:
        self._completed = completed

    @property
    def exit_code(self) -> int:
        return self._completed.returncode

    @property
    def stdout(self) -> str:
        return self._completed.stdout

    @property
    def stderr(self) -> str:
        return self._completed.stderr

    def json(self) -> Any:
        assert self.exit_code == 0, f"CLI failed: {self.stderr}"
        return json.loads(self.stdout)


CliRunner = Callable[..., CliResult]


@pytest.fixture
def cli(tmp_path: Path) -> CliRunner:
    """Run the CLI in a directory of its own, with discovery under test control.

    ``cwd`` defaults to a temporary directory rather than the repo, so a real
    ``.env`` sitting at the repo root can never reach a test.
    """

    def run(
        *arguments: str,
        application_support: Path | str | None = None,
        steam_id: str | None = None,
        install_dir: Path | str | None = None,
        data_directory: Path | str | None = None,
        cwd: Path | None = None,
        runs_dir: Path | None = None,
        records_dir: Path | None = None,
        drills_dir: Path | None = None,
    ) -> CliResult:
        environment = _isolated_environment()
        # Always set, never defaulted: a subcommand that writes must not be able
        # to reach the repo's committed `runs/` or `drills/` from a test.
        environment["BROTATO_RUNS_DIR"] = str(runs_dir or tmp_path / "runs")
        # The same reasoning for run records and prep drills: a test that
        # reviews or drills must not be able to write into the repo's own.
        environment["BROTATO_RECORDS_DIR"] = str(records_dir or tmp_path / "records")
        environment["BROTATO_DRILLS_DIR"] = str(drills_dir or tmp_path / "drills")
        if data_directory is not None:
            environment["BROTATO_DATA_DIR"] = str(data_directory)
        if application_support is not None:
            environment["BROTATO_APPLICATION_SUPPORT"] = str(application_support)
        if steam_id is not None:
            environment["STEAM_ID"] = steam_id
        if install_dir is not None:
            environment["BROTATO_INSTALL_DIR"] = str(install_dir)
        completed = subprocess.run(
            [sys.executable, "-m", "brotato_coaching", *arguments],
            capture_output=True,
            text=True,
            env=environment,
            cwd=cwd or tmp_path,
        )
        return CliResult(completed)

    return run


@pytest.fixture
def save_root(tmp_path: Path) -> Path:
    """An empty stand-in for the Brotato application-support directory."""
    root = tmp_path / "application-support" / "Brotato"
    root.mkdir(parents=True)
    return root


@pytest.fixture
def real_save_root(save_root: Path) -> Path:
    """The committed real save, in a directory the test may then damage."""
    destination = save_root / PLACEHOLDER_STEAM_ID
    shutil.copytree(REAL_SAVE_ROOT / PLACEHOLDER_STEAM_ID, destination)
    return save_root


def write_game_data(directory: Path, **catalogues: list[str]) -> Path:
    """An extracted `data/` directory holding only the ids a test cares about.

    Shaped exactly like what `extract` writes — a catalogue name, a version
    stamp, a list of entities — so a test that fakes it is still asserting
    against the real contract.
    """
    directory.mkdir(parents=True, exist_ok=True)
    for name, identifiers in catalogues.items():
        document = {
            "game_version": "1.2.3-test",
            name: [{"id": identifier} for identifier in identifiers],
        }
        (directory / f"{name}.json").write_text(json.dumps(document), encoding="utf-8")
    return directory


NO_RUN_IN_PROGRESS: dict[str, Any] = {"current_run_state": {"has_run_state": False}}


def run_state(
    *,
    wave: int,
    character: str = "character_crazy",
    danger: int = 5,
    zone: int = 0,
    gold: int = 0,
    weapons: tuple[str, ...] = ("weapon_shuriken_1",),
    items: tuple[str, ...] = (),
    stats: dict[str, int] | None = None,
    level: int = 1,
    health: int = 10,
) -> dict[str, Any]:
    """One hand-written live run state, shaped like the real file's fields.

    Only the fields the watcher and a review reason about are spelled out; the
    real file carries far more, and the watcher copies it whole either way.

    `stats` is written the way the game writes it — an `effects` map keyed by
    the Godot hash of the stat name — so a test that hands over `stat_armor` is
    asserting against the real encoding rather than a convenient one.
    """
    return {
        "current_run_state": {
            "has_run_state": True,
            "current_wave": wave,
            "current_difficulty": danger,
            "current_zone": zone,
            "nb_of_waves": 20,
            "is_coop_run": False,
            "players_data": [
                {
                    "current_character": character,
                    "gold": gold,
                    "current_level": level,
                    "current_health": health,
                    "weapons": [_weapon(weapon) for weapon in weapons],
                    "items": [{"my_id": item} for item in items],
                    "effects": {
                        str(godot_hash(stat)): value
                        for stat, value in (stats or {}).items()
                    },
                }
            ],
        }
    }


def _weapon(identifier: str) -> dict[str, Any]:
    """One weapon entry, tiered the way the game tiers it.

    The game stores the tier zero-based and as a string: `weapon_shuriken_4` is
    a tier-4 weapon written `"tier": "3"`. A fixture that tidied that up would
    hide exactly the conversion worth testing.
    """
    suffix = identifier.rsplit("_", 1)[-1]
    stored = int(suffix) - 1 if suffix.isdigit() else 0
    return {
        "my_id": identifier,
        "name": identifier.rsplit("_", 1)[0].upper(),
        "tier": str(max(stored, 0)),
        "dmg_dealt_last_wave": "0",
    }


# The one real run captured start to finish, committed with ADR-0001. A test
# that reviews it is checking the reader against the game's own output rather
# than against a fixture written to suit it.
REPO_RUNS = Path(__file__).parent.parent / "runs"
COMMITTED_RUN = "20260830T193810Z-character_crazy"


class Workspace:
    """A tmp application-support tree, plus the `runs/` the watcher fills.

    Shaped like the real thing — a Steam-ID-named directory under an
    application-support root — because the watcher now finds the live run state
    by discovering that directory, rather than by being handed a path. A fixture
    that was handed a path would exercise nothing.
    """

    def __init__(self, root: Path) -> None:
        self.root = root
        self.application_support = root / "application-support" / "Brotato"
        self.save_directory = self.application_support / PLACEHOLDER_STEAM_ID
        self.save_directory.mkdir(parents=True)
        self.state_path = self.save_directory / "run_v3_0.json"
        self.runs_dir = root / "runs"
        self.records_dir = root / "records"
        # Set by a test that wants ids resolved to names; left unset, the
        # workspace behaves like a machine that has never run `extract`.
        self.data_dir: Path | None = None

    def write_state(self, payload: dict[str, Any]) -> None:
        self.state_path.write_text(json.dumps(payload))

    def clear_state(self) -> None:
        """What the game does at the end of a run."""
        self.write_state(NO_RUN_IN_PROGRESS)

    def delete_state(self) -> None:
        self.state_path.unlink(missing_ok=True)

    def environment(self) -> dict[str, str]:
        data = {"BROTATO_DATA_DIR": str(self.data_dir)} if self.data_dir else {}
        return {
            **_isolated_environment(),
            **data,
            "BROTATO_APPLICATION_SUPPORT": str(self.application_support),
            "BROTATO_RUNS_DIR": str(self.runs_dir),
            "BROTATO_RECORDS_DIR": str(self.records_dir),
            "BROTATO_POLL_INTERVAL": "0.05",
        }

    def cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-m", "brotato_coaching", *args],
            capture_output=True,
            text=True,
            env=self.environment(),
            cwd=self.root,
        )

    def json_cli(self, *args: str) -> Any:
        result = self.cli(*args)
        assert result.returncode == 0, result.stderr
        return json.loads(result.stdout)

    def snapshot_files(self) -> list[Path]:
        return sorted(self.runs_dir.glob("*/snapshots/*.json"))


@pytest.fixture
def workspace(tmp_path: Path) -> Workspace:
    return Workspace(tmp_path)


# Two suites assert against the game as installed on this machine: the extractor
# itself, and the reference docs whose numbers come out of it. Both need the
# install at import time, to decide whether to skip, so it is discovered once
# here rather than in each of them.
def installed_game() -> GameInstall | None:
    try:
        return find_install()
    except InstallNotFound:
        return None


INSTALL = installed_game()
