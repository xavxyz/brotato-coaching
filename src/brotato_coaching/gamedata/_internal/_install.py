"""Finding the installed game, and naming which patch it is.

Discovery walks Steam's own bookkeeping rather than guessing: `libraryfolders.vdf`
lists every library on the machine, and Brotato lives at
`<library>/steamapps/common/Brotato` in whichever one holds it. A machine with a
library Steam does not list — an external drive, a copy pulled from elsewhere —
sets `BROTATO_INSTALL_DIR` and skips the search entirely.

Two containers make up the game: the base game's, and the Abyssal Terrors zone's.
An install is whichever of them are on disk.

The version is the game's, not the engine's: the patch the extracted numbers are
true for. macOS keeps it in the app bundle's `Info.plist`; where there is no
bundle, Steam's build id names the patch just as unambiguously, if less legibly.
Where neither is readable the version is `UNKNOWN_VERSION`, and the caller is
expected to say so rather than pass an unstamped extraction off as a stamped one.
"""

import os
import plistlib
import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

INSTALL_DIR_VARIABLE = "BROTATO_INSTALL_DIR"
UNKNOWN_VERSION = "unknown"

_STEAM_APP_ID = "1942280"
_BASE_CONTAINERS = (
    Path("Brotato.app/Contents/Resources/Brotato.pck"),  # macOS
    Path("Brotato.pck"),  # everywhere else
)
_ABYSSAL_TERRORS_CONTAINER = Path("BrotatoAbyssalTerrors.pck")
_BUILD_ID = re.compile(r'"buildid"\s*"(\d+)"')
_LIBRARY_PATH = re.compile(r'"path"\s*"([^"]+)"')

_STEAM_ROOTS = (
    "Library/Application Support/Steam",
    ".local/share/Steam",
    ".steam/steam",
)
_WINDOWS_STEAM_ROOTS = ("C:/Program Files (x86)/Steam",)


class InstallNotFound(Exception):
    """The game could not be located, and no override said where it is."""


@dataclass(frozen=True)
class GameInstall:
    """Where the game is, and which patch it is.

    `containers` are the `.pck` files to read, the base game's first.
    Constructing one directly is how a caller points the extractor at containers
    of its own.
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

    searched: list[Path] = []
    for directory in _candidate_directories(environment):
        searched.append(directory)
        if not directory.is_dir():
            continue
        try:
            return _install_at(directory)
        except InstallNotFound:
            # A directory Steam still lists but no longer fills — a partial
            # uninstall — must not end the search for a library that has it.
            continue
    raise InstallNotFound(
        f"no Brotato install found in {len(searched)} Steam location(s); set "
        f"{INSTALL_DIR_VARIABLE} to the directory holding "
        f"{_ABYSSAL_TERRORS_CONTAINER}"
    )


def _candidate_directories(environment: Mapping[str, str]) -> list[Path]:
    home = Path(environment.get("HOME") or Path.home())
    roots = [home / root for root in _STEAM_ROOTS]
    roots += [Path(root) for root in _WINDOWS_STEAM_ROOTS]
    return [
        library / "steamapps" / "common" / "Brotato"
        for root in roots
        for library in _libraries(root)
    ]


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
    """Read the containers in `directory`. Raises `InstallNotFound` if none."""
    containers = [
        base
        for base in (directory / name for name in _BASE_CONTAINERS)
        if base.is_file()
    ][:1]
    abyssal_terrors = directory / _ABYSSAL_TERRORS_CONTAINER
    if abyssal_terrors.is_file():
        containers.append(abyssal_terrors)
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
    return UNKNOWN_VERSION
