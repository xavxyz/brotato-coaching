"""Finding the installed game, and naming which patch it is.

Discovery walks Steam's own bookkeeping rather than guessing: `libraryfolders.vdf`
lists every library on the machine, and Brotato lives at
`<library>/steamapps/common/Brotato` in whichever one holds it. A machine with a
library Steam does not list — an external drive, a copy pulled from elsewhere —
sets `BROTATO_INSTALL_DIR` and skips the search entirely.

The version is the game's, not the engine's: the patch the extracted numbers are
true for. macOS keeps it in the app bundle's `Info.plist`; where there is no
bundle, Steam's build id names the patch just as unambiguously, if less legibly.
"""

import os
import plistlib
import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

INSTALL_DIR_VARIABLE = "BROTATO_INSTALL_DIR"

_STEAM_APP_ID = "1942280"
_BASE_CONTAINER = "Brotato.app/Contents/Resources/Brotato.pck"
_LINUX_BASE_CONTAINER = "Brotato.pck"
_DLC_CONTAINER = "BrotatoAbyssalTerrors.pck"
_BUILD_ID = re.compile(r'"buildid"\s*"(\d+)"')
_LIBRARY_PATH = re.compile(r'"path"\s*"([^"]+)"')

_STEAM_ROOTS = (
    "~/Library/Application Support/Steam",
    "~/.local/share/Steam",
    "~/.steam/steam",
    "C:/Program Files (x86)/Steam",
)


class InstallNotFound(Exception):
    """The game could not be located, and no override said where it is."""


@dataclass(frozen=True)
class GameInstall:
    """Where the game is, and which patch it is.

    `containers` are the `.pck` files to read, base game first. Constructing one
    directly is how a caller points the extractor at containers of its own.
    """

    directory: Path
    containers: tuple[Path, ...]
    version: str


def find_install(environment: Mapping[str, str] | None = None) -> GameInstall:
    """Locate the installed game. Raises `InstallNotFound`."""
    environment = os.environ if environment is None else environment
    override = environment.get(INSTALL_DIR_VARIABLE)
    if override:
        directory = Path(override).expanduser()
        if not directory.is_dir():
            raise InstallNotFound(
                f"{INSTALL_DIR_VARIABLE} is set to {directory}, which is not a directory"
            )
        return _install_at(directory)

    for directory in _candidate_directories():
        if directory.is_dir():
            return _install_at(directory)
    raise InstallNotFound(
        "no Brotato install found in any Steam library; set "
        f"{INSTALL_DIR_VARIABLE} to the directory holding {_DLC_CONTAINER}"
    )


def _candidate_directories() -> list[Path]:
    directories: list[Path] = []
    for root in _STEAM_ROOTS:
        steam = Path(root).expanduser()
        for library in _libraries(steam):
            directories.append(library / "steamapps" / "common" / "Brotato")
    return directories


def _libraries(steam_root: Path) -> list[Path]:
    """Every library Steam knows about, the root itself included."""
    libraries = [steam_root]
    manifest = steam_root / "steamapps" / "libraryfolders.vdf"
    if manifest.is_file():
        for path in _LIBRARY_PATH.findall(manifest.read_text(errors="replace")):
            library = Path(path)
            if library not in libraries:
                libraries.append(library)
    return libraries


def _install_at(directory: Path) -> GameInstall:
    containers = [
        candidate
        for candidate in (
            directory / _BASE_CONTAINER,
            directory / _LINUX_BASE_CONTAINER,
            directory / _DLC_CONTAINER,
        )
        if candidate.is_file()
    ]
    if not containers:
        raise InstallNotFound(f"{directory} holds no .pck container")
    return GameInstall(
        directory=directory,
        containers=tuple(containers),
        version=_version_at(directory),
    )


def _version_at(directory: Path) -> str:
    bundle = directory / "Brotato.app" / "Contents" / "Info.plist"
    if bundle.is_file():
        with bundle.open("rb") as handle:
            plist = plistlib.load(handle)
        version = plist.get("CFBundleShortVersionString")
        if version:
            return str(version)

    # steamapps/common/Brotato -> steamapps/appmanifest_<app id>.acf
    manifest = directory.parent.parent / f"appmanifest_{_STEAM_APP_ID}.acf"
    if manifest.is_file():
        found = _BUILD_ID.search(manifest.read_text(errors="replace"))
        if found:
            return f"steam-build-{found.group(1)}"
    return "unknown"
