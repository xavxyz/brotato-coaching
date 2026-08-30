"""Driving the CLI, which is the only seam the tests are allowed to use.

Every fixture here hands a test a throwaway workspace: a live run state file the
test writes by hand, and an empty `runs/` directory for the watcher to fill.
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

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
            **os.environ,
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
