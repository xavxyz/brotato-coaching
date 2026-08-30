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
    "BROTATO_RUN_STATE_PATH",
    "BROTATO_RUNS_DIR",
    "BROTATO_POLL_INTERVAL",
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
        cwd: Path | None = None,
    ) -> CliResult:
        environment = _isolated_environment()
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


NO_RUN_IN_PROGRESS: dict[str, Any] = {"current_run_state": {"has_run_state": False}}


def run_state(
    *,
    wave: int,
    character: str = "character_crazy",
    danger: int = 5,
    zone: int = 0,
    gold: int = 0,
    weapons: tuple[str, ...] = ("weapon_shuriken_1",),
) -> dict[str, Any]:
    """One hand-written live run state, shaped like the real file's fields.

    Only the fields the watcher reasons about are spelled out; the real file
    carries far more, and the watcher copies it whole either way.
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
                    "weapons": [{"my_id": weapon} for weapon in weapons],
                }
            ],
        }
    }


class Workspace:
    """A tmp directory standing in for the game's save directory and `runs/`."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.state_path = root / "run_v3_0.json"
        self.runs_dir = root / "runs"

    def write_state(self, payload: dict[str, Any]) -> None:
        self.state_path.write_text(json.dumps(payload))

    def clear_state(self) -> None:
        """What the game does at the end of a run."""
        self.write_state(NO_RUN_IN_PROGRESS)

    def delete_state(self) -> None:
        self.state_path.unlink(missing_ok=True)

    def environment(self) -> dict[str, str]:
        return {
            **_isolated_environment(),
            "BROTATO_RUN_STATE_PATH": str(self.state_path),
            "BROTATO_RUNS_DIR": str(self.runs_dir),
            "BROTATO_POLL_INTERVAL": "0.05",
        }

    def cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-m", "brotato_coaching", *args],
            capture_output=True,
            text=True,
            env=self.environment(),
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
