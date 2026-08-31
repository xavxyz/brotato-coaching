"""Game data: what the game records about itself, read from the installed game.

The package hides two file formats — Godot's GDPC container and its text
resource format — behind a two-step interface: find the install, extract from
it. Callers never see a `.pck`, a `res://` path, or an `ExtResource` reference.

    install = find_install()
    extraction = extract(install, Path("data"))

`find_install` walks Steam's libraries, and `BROTATO_INSTALL_DIR` overrides it
for an install Steam does not list. `extract` writes `characters.json`,
`weapons.json`, `items.json` and `enemies.json`, each stamped with the game
version they came from — `UNKNOWN_VERSION` where the install would not say which
patch it is.

The package also owns the hash the game writes ids as. A save holds integers;
`read_names` turns an extraction into a `NameBook` that reads them back, and
`godot_hash` is the algorithm itself. A directory that was never extracted gives
an empty book rather than an error, so a caller can report raw ids and carry on.

`read_version` reads that stamp back off an extraction, so a report can say
which patch its numbers were true for.

A caller with containers of its own — a test, a second install — builds a
`GameInstall` directly and passes it in.

Output belongs in `data/`, which is gitignored: it is the publisher's content.
"""

from ._internal._extract import Extraction, extract, read_version
from ._internal._install import (
    INSTALL_DIR_VARIABLE,
    UNKNOWN_VERSION,
    GameInstall,
    InstallNotFound,
    find_install,
)
from ._internal._names import NameBook, godot_hash, read_names

__all__ = [
    "INSTALL_DIR_VARIABLE",
    "UNKNOWN_VERSION",
    "Extraction",
    "GameInstall",
    "InstallNotFound",
    "NameBook",
    "extract",
    "find_install",
    "godot_hash",
    "read_names",
    "read_version",
]
