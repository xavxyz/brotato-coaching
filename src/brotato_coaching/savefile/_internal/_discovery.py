"""Finding the player's Brotato directory, so that no caller spells out a path.

Two things are hidden here. One is the Steam ID: it names the save directory, it
is the player's, and it never appears in this repo — it is read from the
environment or from `.env`, and the tool works without it by globbing instead.
The other is `save_v3_0.json`: the `_v3_0` is a schema version, and the day it
becomes `_v4_0` this is the only file that should know.

The *directory* is what is discovered; the save file is derived from it. The
other way round — the directory as "the parent of the save we found" — would
make a save file the price of admission for anyone who wants the directory, and
`runlog` wants exactly that and never reads a save. A player mid-run on a fresh
install has a live run state and no save yet, and that has to work.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

from . import _dotenv
from ._errors import SaveDirectoryUnavailable, SaveUnavailable

SAVE_FILENAME = "save_v3_0.json"
STEAM_ID_VARIABLE = "STEAM_ID"
APPLICATION_SUPPORT_VARIABLE = "BROTATO_APPLICATION_SUPPORT"
DEFAULT_APPLICATION_SUPPORT = "~/Library/Application Support/Brotato"

# A Steam account id is exactly 17 digits, and naming the directory is the whole
# of its job here. `str.isdigit` was the old test, and it was only ever safe
# because holding a save was the real evidence; now that the name *is* the
# evidence, it would admit `007`. `[0-9]` rather than `\d`, because `\d` matches
# every Unicode digit and a directory name is not free text.
#
# The test suite spells this shape too, and deliberately: that one is a privacy
# scrubber hunting a 17-digit run anywhere inside a file, this one asks whether
# one directory name is a Steam ID. Same shape, different questions, so neither
# is the other's duplicate and unifying them would break one of them.
_STEAM_ID_SHAPED = re.compile(r"[0-9]{17}")


def _setting(name: str) -> str | None:
    """A configured value: the environment first, then the nearest `.env`.

    The environment wins so that a one-off run can override the file without
    editing it.
    """
    from_environment = os.environ.get(name)
    if from_environment:
        return from_environment.strip()
    return _dotenv.read_value(name, Path.cwd())


def _application_support() -> Path:
    """Where Brotato keeps its per-player directories.

    Overridable so that the suite can point discovery at a fixture and still
    exercise it for real, rather than testing a path it was handed.
    """
    override = _setting(APPLICATION_SUPPORT_VARIABLE)
    root = Path(override) if override else Path(DEFAULT_APPLICATION_SUPPORT)
    return root.expanduser()


def _steam_directories(root: Path) -> list[Path]:
    """The Steam-ID-named directories under `root`, in name order.

    Brotato writes an empty `user/` save beside the Steam one, so every real
    install has at least two directories and "which of these did you mean?"
    would otherwise be the answer every single time. `user` is not 17 digits, so
    it is simply not a candidate — this tool reads Steam saves and nothing else.
    """
    return sorted(
        child
        for child in root.iterdir()
        if child.is_dir() and _STEAM_ID_SHAPED.fullmatch(child.name)
    )


def save_directory() -> Path:
    """This player's Brotato directory, or `SaveDirectoryUnavailable` saying why not."""
    root = _application_support()
    if not root.is_dir():
        raise SaveDirectoryUnavailable(
            f"No Brotato directory at {root}. "
            f"Set {APPLICATION_SUPPORT_VARIABLE} if the game keeps its saves elsewhere."
        )

    steam_id = _setting(STEAM_ID_VARIABLE)
    if steam_id is not None:
        # Taken as given rather than shape-checked: a set value is the player
        # naming their own directory, and "it is not there" is already the
        # useful error. A shape check would add a second way to fail and no
        # information. The id itself is not echoed back.
        directory = root / steam_id
        if not directory.is_dir():
            raise SaveDirectoryUnavailable(
                f"{STEAM_ID_VARIABLE} is set, but there is no directory of that "
                f"name under {root}. Check it against the directories there, or "
                "unset it to have the save directory found for you."
            )
        return directory

    found = _steam_directories(root)
    if not found:
        raise SaveDirectoryUnavailable(
            f"No Brotato save directory under {root}. "
            "Play a run, or point the tool at the right place with "
            f"{APPLICATION_SUPPORT_VARIABLE}."
        )
    if len(found) > 1:
        raise SaveDirectoryUnavailable(
            f"{len(found)} Steam save directories under {root}, and nothing says "
            f"which is yours. Set {STEAM_ID_VARIABLE} in .env to the one that is."
        )
    return found[0]


def save_file() -> Path:
    """The save to read, or a `SaveUnavailable` saying why there isn't one."""
    directory = save_directory()
    candidate = directory / SAVE_FILENAME
    if not candidate.is_file():
        raise SaveUnavailable(
            f"The Brotato save directory holds no {SAVE_FILENAME}. "
            "Play a run, or check that the directory named by "
            f"{STEAM_ID_VARIABLE} is the right one."
        )
    return candidate
