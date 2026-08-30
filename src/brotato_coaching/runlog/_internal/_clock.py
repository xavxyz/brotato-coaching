"""One timestamp format, shared by everything in this package that writes it.

UTC, millisecond precision, sortable as a string — which is what lets run
directories and snapshot metadata be ordered without parsing anything back.
"""

from datetime import datetime, timezone


def now() -> datetime:
    return datetime.now(timezone.utc)


def stamp(at: datetime) -> str:
    return at.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def now_stamp() -> str:
    return stamp(now())
