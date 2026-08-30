"""Reading one value out of a `.env`, without a dependency to do it.

`.env` holds the player's Steam ID and is gitignored. It is looked for from the
working directory upwards, so the tool works from anywhere inside the repo.
"""

from __future__ import annotations

from pathlib import Path

FILENAME = ".env"


def find_dotenv(start: Path) -> Path | None:
    """The nearest `.env` at or above ``start``, if there is one."""
    for directory in (start, *start.parents):
        candidate = directory / FILENAME
        if candidate.is_file():
            return candidate
    return None


def read_value(key: str, start: Path) -> str | None:
    """The value ``key`` is given in the nearest `.env`, or None.

    Deliberately small: ``KEY=value``, ``#`` comments, blank lines, and quotes
    stripped. A `.env` that needs more than that is doing too much.
    """
    path = find_dotenv(start)
    if path is None:
        return None
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        name, _, value = stripped.partition("=")
        if name.strip() != key:
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        return value or None
    return None
