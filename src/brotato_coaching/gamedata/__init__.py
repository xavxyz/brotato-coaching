"""Game data: what the game records about itself, read from the installed game.

The package hides two file formats — Godot's GDPC container and its text
resource format — behind a two-step interface: find the install, extract from
it. Callers never see a `.pck`, a `res://` path, or an `ExtResource` reference.

    install = find_install()
    extraction = extract(install, Path("data"))

`find_install` walks Steam's libraries, and `BROTATO_INSTALL_DIR` overrides it
for an install Steam does not list. `extract` writes `characters.json`,
`weapons.json` and `items.json`, each stamped with the game version they came
from. A caller with containers of its own — a test, a second install — builds a
`GameInstall` directly and passes it in.

Output belongs in `data/`, which is gitignored: it is the publisher's content.
"""

from ._internal._extract import Extraction, extract
from ._internal._install import (
    INSTALL_DIR_VARIABLE,
    GameInstall,
    InstallNotFound,
    find_install,
)

__all__ = [
    "INSTALL_DIR_VARIABLE",
    "Extraction",
    "GameInstall",
    "InstallNotFound",
    "extract",
    "find_install",
]
