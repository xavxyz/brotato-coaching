"""Everything the suite shares: one way to drive the CLI.

The CLI is the only seam. Tests reach the packages through it and assert on the
JSON that comes out, never on how it was produced.
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
)


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
        environment = {
            key: value
            for key, value in os.environ.items()
            if key not in _DISCOVERY_VARIABLES
        }
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
