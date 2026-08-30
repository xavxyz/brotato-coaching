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

from ._catalog import Catalog, build_catalog
from ._container import open_container
from ._install import GameInstall

_DLC_SOURCE = "abyssal_terrors"
_BASE_SOURCE = "base"


@dataclass(frozen=True)
class Extraction:
    """What an extraction produced: the files written, and what is in them."""

    version: str
    directory: Path
    files: tuple[Path, ...]
    counts: dict[str, int]


def extract(install: GameInstall, destination: Path) -> Extraction:
    """Read every container in `install` and write JSON into `destination`."""
    containers = {
        _source_name(path): open_container(path) for path in install.containers
    }
    catalog = build_catalog(containers)
    destination.mkdir(parents=True, exist_ok=True)

    files = tuple(
        _write(destination / f"{name}.json", install.version, name, entities)
        for name, entities in _catalogues(catalog)
    )
    return Extraction(
        version=install.version,
        directory=destination,
        files=files,
        counts={name: len(entities) for name, entities in _catalogues(catalog)},
    )


def _catalogues(catalog: Catalog) -> tuple[tuple[str, list], ...]:
    return (
        ("characters", catalog.characters),
        ("weapons", catalog.weapons),
        ("items", catalog.items),
    )


def _source_name(container: Path) -> str:
    return _DLC_SOURCE if "Abyssal" in container.name else _BASE_SOURCE


def _write(path: Path, version: str, name: str, entities: list) -> Path:
    document = {"game_version": version, name: entities}
    path.write_text(json.dumps(document, indent=2, sort_keys=False) + "\n")
    return path
