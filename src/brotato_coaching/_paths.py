"""Where the game's files and this workspace's files are, on this machine.

App-tier code: the packages are handed paths, they never go looking. macOS only,
per the spec.

Save-directory discovery belongs to `savefile` once that package exists; until
then it lives here, where it is composed rather than depended on.
"""

import os
from pathlib import Path

_SAVE_ROOT = Path.home() / "Library" / "Application Support" / "Brotato"
_LIVE_RUN_STATE = "run_v3_0.json"
# Where `extract` writes and `progress` reads: relative to the working
# directory, because the extraction belongs to whatever workspace is in use.
DEFAULT_DATA_DIRECTORY = Path("data")
_DEFAULT_POLL_INTERVAL = 2.0

# The repo root: src/brotato_coaching/_paths.py -> brotato_coaching -> src -> here.
_REPO_ROOT = Path(__file__).resolve().parents[2]


def live_run_state_path() -> Path:
    """The file the game keeps the current run in, wherever this player's is.

    `BROTATO_RUN_STATE_PATH` wins; then `STEAM_ID` from the environment or
    `.env`; then the save directory holding the most recently written run state.
    """
    if (override := os.environ.get("BROTATO_RUN_STATE_PATH")):
        return Path(override).expanduser()
    if (steam_id := _steam_id()):
        return _SAVE_ROOT / steam_id / _LIVE_RUN_STATE
    # The game rewrites these files under us, so a candidate can vanish between
    # the glob and the stat. Skip it rather than fail discovery.
    candidates = []
    for candidate in _SAVE_ROOT.glob(f"*/{_LIVE_RUN_STATE}"):
        try:
            candidates.append((candidate.stat().st_mtime, candidate))
        except OSError:
            continue
    return max(candidates)[1] if candidates else _SAVE_ROOT / _LIVE_RUN_STATE


def runs_directory() -> Path:
    """Where snapshots are kept. Committed, so it lives in the repo."""
    if (override := os.environ.get("BROTATO_RUNS_DIR")):
        return Path(override).expanduser()
    return _REPO_ROOT / "runs"


def data_directory() -> Path:
    """Where `extract` left the game data, if the player has run it.

    `BROTATO_DATA_DIR` wins; otherwise `data/` relative to where the command was
    run, which is what `extract` writes to by default. Nothing here checks that
    it exists: an absent directory is the ordinary case before a first extract,
    and reading it is what discovers that.
    """
    if (override := os.environ.get("BROTATO_DATA_DIR")):
        return Path(override).expanduser()
    return DEFAULT_DATA_DIRECTORY


def poll_interval() -> float:
    """How often the watcher re-reads the live run state, in seconds."""
    try:
        return float(os.environ["BROTATO_POLL_INTERVAL"])
    except (KeyError, ValueError):
        return _DEFAULT_POLL_INTERVAL


def _steam_id() -> str | None:
    if (from_environment := os.environ.get("STEAM_ID")):
        return from_environment
    return _dotenv().get("STEAM_ID")


def _dotenv() -> dict[str, str]:
    """`.env` is gitignored and holds the Steam ID; absent is the normal case."""
    try:
        lines = (_REPO_ROOT / ".env").read_text().splitlines()
    except OSError:
        return {}
    values = {}
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        values[key.strip()] = value.strip().strip("'\"")
    return values
