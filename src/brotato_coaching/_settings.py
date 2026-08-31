"""The two settings that are about this workspace, not about the player's files.

App-tier code: the packages are handed what they need, they never go looking.
Where the player's Brotato directory is, is `savefile`'s question — it used to be
answered a second time here, which is how `BROTATO_APPLICATION_SUPPORT` came to
work for `progress` and not for `watch`.
"""

import os
from pathlib import Path

_DEFAULT_POLL_INTERVAL = 2.0

# The repo root: src/brotato_coaching/_settings.py -> brotato_coaching -> src -> here.
_REPO_ROOT = Path(__file__).resolve().parents[2]


def runs_directory() -> Path:
    """Where snapshots are kept. Committed, so it lives in the repo."""
    if override := os.environ.get("BROTATO_RUNS_DIR"):
        return Path(override).expanduser()
    return _REPO_ROOT / "runs"


def poll_interval() -> float:
    """How often the watcher re-reads the live run state, in seconds."""
    try:
        return float(os.environ["BROTATO_POLL_INTERVAL"])
    except (KeyError, ValueError):
        return _DEFAULT_POLL_INTERVAL
