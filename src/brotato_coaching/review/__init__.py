"""Reviewed runs: reading a dead run back, and writing down what it taught.

A review has an order, and the order is the point. The player's one-line
hypothesis is written first, against a **briefing** — everything the snapshots
say about the run, and nothing concluded from it — and only then is a diagnosis
accepted. Seeing the diagnosis first would let the read be unconsciously
revised, and the gap between the two is where the learning is. `diagnose`
refuses a run whose hypothesis is not yet recorded, so that ordering is a
property of the tool rather than of whoever is driving it.

This package hides how a snapshot is interpreted — the weapons and items held,
the stats behind the game's hashed `effects` map, the per-wave build curve — and
the fixed schema every run record is written in, so that repeated failures are a
query across `records/` rather than a memory.

    reviews = Reviews(records_directory=Path("records"))
    briefing = reviews.briefing(run, patch="1.1.10.0", death_causes=deaths)
    reviews.record_hypothesis(briefing, "I never scaled damage")
    reviews.diagnose(briefing["run_id"], diagnosis="...", change="...")

A run is handed in, already read from `runs/`, together with the patch it was
played on and what the save says has been killing the player. Composing those is
the app tier's job: this package knows how to read a run, not where runs, saves
and game data live.

Records are the player's own writing about their own data, and commit.
"""

from ._internal._records import HypothesisMissing
from ._internal._reviews import Reviews

__all__ = ["HypothesisMissing", "Reviews"]
