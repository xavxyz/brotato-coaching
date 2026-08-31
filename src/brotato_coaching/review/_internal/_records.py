"""Run records on disk: one file per reviewed run, and the questions they answer.

    records/
      20260830T193810Z-character_crazy.json

A record is written in one fixed schema, because "you have died this way four
times" has to be a query rather than a vibe, and because a run reviewed a year
ago has to still be readable when the player's model has improved enough to
re-diagnose it.

The ordering rule lives here rather than in the CLI: a diagnosis without a
hypothesis already recorded is refused, so the seam that enforces it is the same
one that writes the file.
"""

import json
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1

# The fixed schema, in the order a record reads on the page: what the run was,
# what was read off it, then what the player and the review said about it.
_FACTS = (
    "run_id",
    "character",
    "danger",
    "zone",
    "patch",
    "waves",
    "weapons",
    "key_items",
    "final_stats",
    "death_causes",
)


class HypothesisMissing(Exception):
    """A diagnosis was offered for a run whose hypothesis is not yet written."""


@dataclass(frozen=True)
class Records:
    """Every read and write under `records/` goes through here."""

    directory: Path

    def read(self, run_id: str) -> dict[str, Any] | None:
        path = self._path(run_id)
        if not path.is_file():
            return None
        try:
            record = json.loads(path.read_text())
        except ValueError:
            return None
        return record if isinstance(record, dict) else None

    def write_hypothesis(self, facts: dict[str, Any], text: str) -> dict[str, Any]:
        """Record the player's read of the run, and only then open it to diagnosis.

        Recording a hypothesis against a run that already has a diagnosis is a
        re-diagnosis: the previous review moves into `revisions` rather than
        being overwritten, so improving a model never costs the evidence that it
        has improved. Recording one against a run not yet diagnosed is a
        correction, and simply replaces it.
        """
        existing = self.read(facts["run_id"]) or _blank()
        revisions = list(existing.get("revisions") or [])
        if existing.get("diagnosis") is not None:
            revisions.append(
                {
                    key: existing.get(key)
                    for key in ("hypothesis", "diagnosis", "change")
                }
            )
        record = {
            "schema_version": SCHEMA_VERSION,
            # The facts are refreshed from the run every time, so a re-diagnosis
            # reads a record stamped with what is known now, not in the past.
            **{key: facts.get(key) for key in _FACTS},
            "hypothesis": _said(text),
            "diagnosis": None,
            "change": None,
            "revisions": revisions,
        }
        return self._write(record)

    def diagnose(self, run_id: str, *, diagnosis: str, change: str) -> dict[str, Any]:
        """Write the diagnosis and the one change. Raises `HypothesisMissing`."""
        record = self.read(run_id)
        if record is None or record.get("hypothesis") is None:
            raise HypothesisMissing(run_id)
        if record.get("diagnosis") is not None:
            # Already diagnosed: a second diagnosis would be one written after
            # this one had been read, which is the ordering this refuses.
            raise HypothesisMissing(run_id)
        record["diagnosis"] = _said(diagnosis)
        record["change"] = _said(change)
        return self._write(record)

    def all(self) -> list[dict[str, Any]]:
        """Every record, oldest run first — run ids sort by when they started."""
        if not self.directory.is_dir():
            return []
        records = []
        for path in sorted(self.directory.glob("*.json")):
            record = self.read(path.stem)
            if record is not None:
                records.append({**record, "complete": _complete(record)})
        return records

    def patterns(self, records: list[dict[str, Any]]) -> dict[str, Any]:
        """What only several records can say: what keeps happening.

        Death causes are the player's *lifetime* histogram out of the save, so
        they are reported from the most recent record rather than summed across
        records, which would count the same deaths once per review.
        """
        latest = records[-1] if records else None
        return {
            "runs_reviewed": len(records),
            "by_character": _counts(record.get("character") for record in records),
            "by_danger": _counts(record.get("danger") for record in records),
            "by_final_wave": _counts(
                (record.get("waves") or {}).get("reached") for record in records
            ),
            "changes": [
                {"text": text, "count": count}
                for text, count in Counter(
                    record["change"]["text"]
                    for record in records
                    if record.get("change")
                ).most_common()
            ],
            "latest_death_causes": (latest or {}).get("death_causes") or [],
        }

    def _write(self, record: dict[str, Any]) -> dict[str, Any]:
        self.directory.mkdir(parents=True, exist_ok=True)
        self._path(record["run_id"]).write_text(
            json.dumps(record, indent=2) + "\n", encoding="utf-8"
        )
        return {**record, "complete": _complete(record)}

    def _path(self, run_id: str) -> Path:
        return self.directory / f"{run_id}.json"


def _blank() -> dict[str, Any]:
    return {"revisions": [], "diagnosis": None, "hypothesis": None, "change": None}


def _complete(record: dict[str, Any]) -> bool:
    """A review is finished when it has cost the player one change to try."""
    return record.get("change") is not None


def _said(text: str) -> dict[str, str]:
    """One line, and when it was written. The order is the whole point."""
    return {"text": text.strip(), "recorded_at": _stamp()}


def _stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def _counts(values: Any) -> dict[str, int]:
    """A histogram with JSON-safe keys, commonest first."""
    counter = Counter(str(value) for value in values if value is not None)
    return dict(counter.most_common())
