"""Finding the save file, so that no caller ever spells out a path.

Two things are hidden here. One is the Steam ID: it names the save directory,
it is the player's, and it never appears in this repo — it is read from the
environment or from `.env`, and the tool works without it by globbing instead.
The other is `save_v3_0.json`: the `_v3_0` is a schema version, and the day it
becomes `_v4_0` this is the only file that should know.
"""

from __future__ import annotations

import os
from pathlib import Path

from . import _dotenv
from ._errors import SaveUnavailable

SAVE_FILENAME = "save_v3_0.json"
STEAM_ID_VARIABLE = "STEAM_ID"
APPLICATION_SUPPORT_VARIABLE = "BROTATO_APPLICATION_SUPPORT"
DEFAULT_APPLICATION_SUPPORT = "~/Library/Application Support/Brotato"


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


def _steam_saves_first(found: list[Path]) -> list[Path]:
    """The Steam saves, if there are any, else whatever was found.

    Brotato writes an empty `user/` profile beside the Steam one, so every real
    install has at least two saves and "which of these did you mean?" would be
    the answer every single time. A Steam save sits in a directory named after
    a Steam ID, which is all digits; `user` is not, and loses to it.
    """
    steam = [path for path in found if path.parent.name.isdigit()]
    return steam or found


def find_save_file() -> Path:
    """The save to read, or a `SaveUnavailable` saying why there isn't one."""
    root = _application_support()
    if not root.is_dir():
        raise SaveUnavailable(
            f"No Brotato directory at {root}. "
            f"Set {APPLICATION_SUPPORT_VARIABLE} if the game keeps its saves elsewhere."
        )

    steam_id = _setting(STEAM_ID_VARIABLE)
    if steam_id is not None:
        candidate = root / steam_id / SAVE_FILENAME
        if not candidate.is_file():
            # The Steam ID itself is not echoed back: it is the one value in
            # this whole system that should not travel, and an error message is
            # the most-pasted text there is.
            raise SaveUnavailable(
                f"{STEAM_ID_VARIABLE} is set, but the directory it names under "
                f"{root} holds no {SAVE_FILENAME}. Check it against the "
                "directories there, or unset it to have the save found for you."
            )
        return candidate

    found = _steam_saves_first(sorted(root.glob(f"*/{SAVE_FILENAME}")))
    if not found:
        raise SaveUnavailable(
            f"No Brotato save under {root}. "
            "Play a run, or point the tool at the right place with "
            f"{APPLICATION_SUPPORT_VARIABLE}."
        )
    if len(found) > 1:
        raise SaveUnavailable(
            f"{len(found)} saves under {root}, and nothing says which is yours. "
            f"Set {STEAM_ID_VARIABLE} in .env to the directory name that is."
        )
    return found[0]
