"""Writing the catalogues to disk as patch-stamped JSON.

Every file carries the game version it was read from, because a number without a
patch behind it is a number you cannot trust later. The output is deterministic —
sorted, no timestamps — so a re-extraction after a patch shows exactly what the
patch changed.

The destination is `data/`, which is gitignored: this is the publisher's content,
and it regenerates in seconds from files the player already owns.
"""

import json
from dataclasses import dataclass
from pathlib import Path

from ._catalog import build_catalog
from ._container import open_container
from ._install import GameInstall

ABYSSAL_TERRORS_SOURCE = "abyssal_terrors"
BASE_SOURCE = "base"

_CONTAINER_SOURCES = {
    "BrotatoAbyssalTerrors.pck": ABYSSAL_TERRORS_SOURCE,
    "Brotato.pck": BASE_SOURCE,
}


@dataclass(frozen=True)
class Extraction:
    """What an extraction produced: the files written, and what is in them.

    `sources` names the zones the catalogues were read from, so a caller can see
    that an install was missing a container rather than inferring it from a
    surprisingly small count.
    """

    version: str
    directory: Path
    files: tuple[Path, ...]
    counts: dict[str, int]
    sources: tuple[str, ...]


def extract(install: GameInstall, destination: Path) -> Extraction:
    """Read every container in `install` and write JSON into `destination`."""
    containers = {
        _source_name(path): open_container(path) for path in install.containers
    }
    catalog = build_catalog(containers)
    destination.mkdir(parents=True, exist_ok=True)

    files: list[Path] = []
    counts: dict[str, int] = {}
    for name, entities in catalog.by_name():
        files.append(_write(destination / f"{name}.json", install.version, name, entities))
        counts[name] = len(entities)

    return Extraction(
        version=install.version,
        directory=destination,
        files=tuple(files),
        counts=counts,
        sources=tuple(containers),
    )


def _source_name(container: Path) -> str:
    """Which zone a container holds, by the name the game ships it under."""
    return _CONTAINER_SOURCES.get(container.name, container.stem)


def _write(path: Path, version: str, name: str, entities: list) -> Path:
    document = {"game_version": version, name: entities}
    path.write_text(json.dumps(document, indent=2) + "\n")
    return path
