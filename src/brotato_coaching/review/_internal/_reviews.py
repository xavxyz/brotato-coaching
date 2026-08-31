"""The post-mortem loop: brief, then hypothesise, then diagnose.

One class holds the three, because they are one workflow and the order they
happen in is the behaviour worth protecting.
"""

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from . import _build
from ._records import HypothesisMissing, Records


class Reviews:
    """Reviewed runs: `records/` on disk, and how a run is read into one.

    Every method returns the JSON document the matching CLI subcommand prints —
    that document, not any object here, is the contract.

    A run is handed in, already read: this package never goes looking for
    `runs/`, because the run it is reviewing might have come from anywhere, and
    because the joins a briefing needs — the patch, the player's death causes —
    are the app tier's to make.
    """

    def __init__(self, *, records_directory: Path) -> None:
        self._records = Records(records_directory)

    def briefing(
        self,
        run: Mapping[str, Any],
        *,
        patch: str | None = None,
        death_causes: Sequence[Mapping[str, Any]] = (),
        death_causes_reason: str | None = None,
    ) -> dict[str, Any]:
        """Everything read off the run, and nothing concluded from it.

        A briefing states no diagnosis, by construction rather than by
        instruction: the player's hypothesis has to be written against evidence,
        not against an opinion they can revise their read to agree with.
        """
        facts = self._facts(
            run,
            patch=patch,
            death_causes=death_causes,
        )
        recorded = self._records.read(str(run["run_id"])) or {}
        states = _states(run)
        return {
            **facts,
            "started_at": run.get("started_at"),
            "ended_at": run.get("ended_at"),
            "in_progress": run.get("in_progress"),
            "snapshots": len(states),
            "items_held": sum(_build.items(states[-1]).values()) if states else 0,
            "curve": _curve(run),
            "death_causes_reason": death_causes_reason,
            "hypothesis": recorded.get("hypothesis"),
            "diagnosis": recorded.get("diagnosis"),
            "change": recorded.get("change"),
            "revisions": recorded.get("revisions") or [],
        }

    def record_hypothesis(
        self, briefing: Mapping[str, Any], text: str
    ) -> dict[str, Any]:
        """Write the player's read of the run, before any diagnosis exists."""
        return self._records.write_hypothesis(dict(briefing), text)

    def diagnose(self, run_id: str, *, diagnosis: str, change: str) -> dict[str, Any]:
        """Write the diagnosis and the one change. Raises `HypothesisMissing`."""
        return self._records.diagnose(run_id, diagnosis=diagnosis, change=change)

    def records(self) -> dict[str, Any]:
        """Every reviewed run, and what keeps recurring across them."""
        records = self._records.all()
        return {
            "records_dir": str(self._records.directory),
            "records": records,
            "patterns": self._records.patterns(records),
        }

    def _facts(
        self,
        run: Mapping[str, Any],
        *,
        patch: str | None,
        death_causes: Sequence[Mapping[str, Any]],
    ) -> dict[str, Any]:
        """What the run was, and what the last snapshot says the build became."""
        states = _states(run)
        final = states[-1] if states else {}
        return {
            "run_id": run.get("run_id"),
            "character": run.get("character"),
            "danger": run.get("danger"),
            "zone": run.get("zone"),
            "patch": patch,
            "waves": {
                "reached": max(_waves(run), default=None),
                "of": _build.wave_count(final),
            },
            "weapons": _build.weapons(final),
            "key_items": _build.key_items(final),
            "final_stats": _build.final_stats(final),
            "death_causes": [dict(cause) for cause in death_causes],
        }


def _states(run: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    return [
        snapshot["state"]
        for snapshot in run.get("snapshots") or []
        if isinstance(snapshot, Mapping) and isinstance(snapshot.get("state"), Mapping)
    ]


def _waves(run: Mapping[str, Any]) -> list[int]:
    return [
        snapshot["wave"]
        for snapshot in run.get("snapshots") or []
        if isinstance(snapshot, Mapping) and isinstance(snapshot.get("wave"), int)
    ]


def _curve(run: Mapping[str, Any]) -> list[dict[str, Any]]:
    """One entry per wave, taken from the last snapshot captured in that wave."""
    by_wave: dict[int, dict[str, Any]] = {}
    for snapshot in run.get("snapshots") or []:
        if not isinstance(snapshot, Mapping) or not isinstance(snapshot.get("state"), Mapping):
            continue
        entry = _build.curve_entry(snapshot["state"])
        if entry["wave"] is not None:
            by_wave[entry["wave"]] = entry
    return [by_wave[wave] for wave in sorted(by_wave)]


__all__ = ["HypothesisMissing", "Reviews"]
