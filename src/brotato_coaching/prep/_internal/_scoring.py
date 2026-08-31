"""Scoring four committed predictions, one at a time.

Each dimension is scored on its own and reported on its own, because the point
of the drill is to find out *which* part of the reasoning is weak. A player who
reads the stats right and the weapon wrong learns nothing from a single mark out
of four.

Three of the four are answered by the game's own data and are scored at the
reveal. The fourth — the wave the build is expected to break at — is not
something the game declares anywhere, so it is left `pending` and settled later
against a run that actually happened. Guessing at ground truth for it would make
the hit rate a number about nothing.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from ._words import key

# Every dimension, in the order they are asked and reported.
DIMENSIONS = ("primary_stat", "secondary_stat", "weapon_class", "weakest_wave")

HIT = "hit"
MISS = "miss"
# The game declares nothing here, so neither a hit nor a miss would mean anything.
# An unscorable dimension stays out of the hit rate rather than counting as a
# miss, which would quietly punish the player for the data being thin.
UNSCORABLE = "unscorable"
# Committed, and waiting on a run to compare against.
PENDING = "pending"

# A wave prediction is about where a build gives out, not about which wave.
# Naming wave 11 when it broke on 12 is a read that was right.
WAVE_TOLERANCE = 1

# The game declares which stats a character wants as a set, not as a ranking, so
# a player who names the two in the other order has not been wrong about
# anything the data can see. Both predictions score against the whole set; only
# naming the *same* stat twice fails to be a second prediction.
_ORDER_NOTE = (
    "the game declares wanted stats as a set, not a ranking, so either order scores"
)


def score(
    truth: Mapping[str, Any],
    predictions: Mapping[str, Any],
    actual_wave: int | None = None,
) -> dict[str, dict[str, Any]]:
    """Each prediction against what the game says, as its own verdict."""
    wanted = [key(str(stat)) for stat in truth.get("wanted_stats") or []]
    classes = [key(str(name)) for name in truth.get("weapon_classes") or []]
    primary = key(str(predictions.get("primary_stat", "")))
    secondary = key(str(predictions.get("secondary_stat", "")))
    return {
        "primary_stat": _against(
            predictions.get("primary_stat"),
            primary,
            wanted,
            missing="this character wants no stat the game names",
            note=_ORDER_NOTE,
        ),
        "secondary_stat": _against(
            predictions.get("secondary_stat"),
            secondary if secondary != primary else None,
            wanted if len(wanted) > 1 else [],
            missing="the game names only one stat this character wants",
            note=(
                "naming the same stat twice is one prediction, not two"
                if secondary == primary
                else _ORDER_NOTE
            ),
        ),
        "weapon_class": _against(
            predictions.get("weapon_class"),
            key(str(predictions.get("weapon_class", ""))),
            classes,
            missing="the starting weapon belongs to no class",
            note="the starting weapon may carry several classes; any of them scores",
        ),
        "weakest_wave": _wave(predictions.get("weakest_wave"), actual_wave),
    }


def _against(
    predicted: Any,
    said: str | None,
    accepted: Sequence[str],
    *,
    missing: str,
    note: str,
) -> dict[str, Any]:
    if not accepted:
        return {"predicted": predicted, "verdict": UNSCORABLE, "why": missing}
    return {
        "predicted": predicted,
        "verdict": HIT if said in accepted else MISS,
        "accepted": list(accepted),
        "why": note,
    }


def _wave(predicted: Any, actual: int | None) -> dict[str, Any]:
    if actual is None:
        return {
            "predicted": predicted,
            "verdict": PENDING,
            "why": "no run to compare against yet; settle the drill after playing it",
        }
    within = isinstance(predicted, int) and abs(predicted - actual) <= WAVE_TOLERANCE
    return {
        "predicted": predicted,
        "verdict": HIT if within else MISS,
        "actual": actual,
        "why": f"scored within {WAVE_TOLERANCE} wave of where the run actually broke",
    }


def tally(scored: Sequence[Mapping[str, Mapping[str, Any]]]) -> dict[str, Any]:
    """Hit rate per dimension across every drill that has been scored.

    Unscorable dimensions leave the denominator alone and pending ones are
    counted separately, so the rate is only ever over predictions that could
    have been wrong.
    """
    return {
        dimension: _rate([verdicts.get(dimension, {}) for verdicts in scored])
        for dimension in DIMENSIONS
    }


def _rate(verdicts: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    counted = [verdict.get("verdict") for verdict in verdicts]
    hits = counted.count(HIT)
    scored = hits + counted.count(MISS)
    return {
        "hits": hits,
        "scored": scored,
        "rate": round(hits / scored, 2) if scored else None,
        "pending": counted.count(PENDING),
        "unscorable": counted.count(UNSCORABLE),
    }
