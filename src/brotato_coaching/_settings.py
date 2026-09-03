"""The settings that are about this workspace, not about the player's files.

App-tier code: the packages are handed what they need, they never go looking.
Where the player's Brotato directory is, is `savefile`'s question — it used to be
answered a second time here, which is how `BROTATO_APPLICATION_SUPPORT` came to
work for `progress` and not for `watch`.
"""

import os
from pathlib import Path

# The two names a detached watcher is relaunched with, and so the only two that
# are read in one place and written in another. Named because that gap is where
# a rename goes wrong silently: the child would fall back to the default and
# write its snapshots somewhere else, with nothing pointing at the cause. The
# rest are read here and nowhere else, so their literal is their definition.
RUNS_DIRECTORY_VARIABLE = "BROTATO_RUNS_DIR"
POLL_INTERVAL_VARIABLE = "BROTATO_POLL_INTERVAL"

_DEFAULT_POLL_INTERVAL = 2.0
# Where `extract` writes and `progress` reads: relative to the working
# directory, because the extraction belongs to whatever workspace is in use.
DEFAULT_DATA_DIRECTORY = Path("data")

# The repo root: src/brotato_coaching/_settings.py -> brotato_coaching -> src -> here.
_REPO_ROOT = Path(__file__).resolve().parents[2]


def runs_directory() -> Path:
    """Where snapshots are kept. Committed, so it lives in the repo."""
    if override := os.environ.get(RUNS_DIRECTORY_VARIABLE):
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


def drills_directory() -> Path:
    """Where prep drills are kept. Committed, like `runs/`: the player's own data."""
    if override := os.environ.get("BROTATO_DRILLS_DIR"):
        return Path(override).expanduser()
    return _REPO_ROOT / "drills"


def poll_interval() -> float:
    """How often the watcher re-reads the live run state, in seconds."""
    try:
        return float(os.environ[POLL_INTERVAL_VARIABLE])
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


def watcher_environment(runs_directory: Path, poll_interval: float) -> dict[str, str]:
    """Name the settings a detached watcher must be relaunched with.

    The child is a fresh CLI process: it re-reads its configuration from this
    module, and would otherwise take the defaults. Naming that configuration is
    this module's job and not `runlog`'s — that package is handed the values,
    and has no business knowing what they are called.

    The values are arguments rather than another call to `runs_directory()` and
    `poll_interval()`, so that the child is pinned to what the caller is
    *actually* using. Resolving a second time would let a `RunLog` built from
    anything else spawn a watcher filling a different directory, silently —
    which is the failure this whole change is about.

    Only these two: the save directory is not passed, because the child inherits
    the environment and working directory and reaches it by running the same
    discovery.
    """
    return {
        RUNS_DIRECTORY_VARIABLE: str(runs_directory),
        POLL_INTERVAL_VARIABLE: str(poll_interval),
    }
