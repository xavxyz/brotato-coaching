"""Turning a file on disk into a save document, or into a clear refusal.

Brotato writes plain JSON, so there is no parsing to speak of. What there is,
is every way the file can disappoint: absent, empty, half-written, or simply
some other JSON file that happens to sit at that path. Each of those is a
sentence for the player rather than a traceback, and that is this file's job.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ._errors import SaveUnavailable

# The keys a Brotato save always has, whether or not a single run has been
# played. Their absence means the file is not a save.
_REQUIRED_KEYS = ("data", "difficulties_unlocked")


def read_document(path: Path) -> dict[str, Any]:
    """The save at ``path`` as a dict, or `SaveUnavailable` saying why not."""
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as error:
        raise SaveUnavailable(f"Could not read the save at {path}: {error}") from error

    if not raw.strip():
        raise SaveUnavailable(
            f"The save at {path} is empty. The game may have been interrupted "
            "mid-write; launching it again usually rewrites the file."
        )

    try:
        document = json.loads(raw)
    except json.JSONDecodeError as error:
        raise SaveUnavailable(
            f"The save at {path} is not valid JSON ({error}). "
            "It may have been written to while being read; try again."
        ) from error

    if not isinstance(document, dict) or not all(
        key in document for key in _REQUIRED_KEYS
    ):
        raise SaveUnavailable(
            f"The file at {path} is JSON, but not a Brotato save: it is "
            f"missing {' and '.join(_REQUIRED_KEYS)}."
        )
    return document
