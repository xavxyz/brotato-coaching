"""The settings that are about this workspace, not about the player's files.

App-tier code: the packages are handed what they need, they never go looking.
Where the player's Brotato directory is, is `savefile`'s question — it used to be
answered a second time here, which is how `BROTATO_APPLICATION_SUPPORT` came to
work for `progress` and not for `watch`.
"""

import os
from pathlib import Path

_DEFAULT_POLL_INTERVAL = 2.0
# Where `extract` writes and `progress` reads: relative to the working
# directory, because the extraction belongs to whatever workspace is in use.
DEFAULT_DATA_DIRECTORY = Path("data")

# The repo root: src/brotato_coaching/_settings.py -> brotato_coaching -> src -> here.
_REPO_ROOT = Path(__file__).resolve().parents[2]


def runs_directory() -> Path:
    """Where snapshots are kept. Committed, so it lives in the repo."""
    if override := os.environ.get("BROTATO_RUNS_DIR"):
        return Path(override).expanduser()
    return _REPO_ROOT / "runs"


def records_directory() -> Path:
    """Where run records are kept. Committed, so it lives in the repo too.

    A sibling of `runs/`, not a child of it: `runlog` owns everything under
    `runs/` and rewrites a run's metadata as it captures, and a record written
    by a review is the player's writing, not the watcher's output.
    """
    if override := os.environ.get("BROTATO_RECORDS_DIR"):
        return Path(override).expanduser()
    return _REPO_ROOT / "records"


def poll_interval() -> float:
    """How often the watcher re-reads the live run state, in seconds."""
    try:
        return float(os.environ["BROTATO_POLL_INTERVAL"])
    except (KeyError, ValueError):
        return _DEFAULT_POLL_INTERVAL


def data_directory() -> Path:
    """Where `extract` left the game data, if the player has run it.

    `BROTATO_DATA_DIR` wins; otherwise `data/` relative to where the command was
    run, which is what `extract` writes to by default. Nothing here checks that
    it exists: an absent directory is the ordinary case before a first extract,
    and reading it is what discovers that.
    """
    if override := os.environ.get("BROTATO_DATA_DIR"):
        return Path(override).expanduser()
    return DEFAULT_DATA_DIRECTORY
