"""The drill, from opening it to the hit rate it eventually contributes to.

The refusals in here are the feature. A reveal before the predictions are in, or
a second commit over the top of the first, are the two ways a derivation drill
quietly turns into a lookup: both are refused, at the one place that can see the
whole drill, rather than being left to whoever is driving the CLI to remember.
"""

from __future__ import annotations

from collections.abc import Collection, Mapping, Sequence
from pathlib import Path
from typing import Any

from brotato_coaching.gamedata import Catalog

from ._card import build
from ._propose import propose
from ._scoring import DIMENSIONS, PENDING, score, tally
from ._store import DrillStore, new_drill_id, now_stamp


class PrepRefused(Exception):
    """A drill could not do what it was asked, said in words for the player.

    One exception for every refusal, because every refusal has the same
    consequence — the command exits non-zero and prints this sentence — and a
    caller that told them apart would only be re-deciding what to print.
    """


class PrepDrills:
    """Every drill the player has taken, and the one they are taking now.

    Handed the directory to keep them in, and handed the extracted game data
    when a drill is opened. It never goes looking for either: what the game
    says lives in `gamedata`, where the player's Brotato is lives in
    `savefile`, and joining those to a save is the job of the tier above.
    """

    def __init__(self, drills_directory: Path) -> None:
        self._store = DrillStore(drills_directory)

    def open_drill(
        self,
        catalog: Catalog,
        *,
        character_id: str | None = None,
        unlocked: Collection[str] = (),
        cleared: Collection[str] = (),
    ) -> dict[str, Any]:
        """Start a drill, and print everything about it except who it is.

        With no `character_id` the choice is made from `cleared` — the
        characters the player has already had to reason about all the way to a
        win — so that the drill lands somewhere they have not been.
        """
        if not catalog.characters:
            raise PrepRefused(
                "no extracted game data, and a drill is nothing without the "
                "character's modifiers; `brotato-coaching extract` writes them"
            )
        if character_id is None:
            proposed = propose(
                catalog.characters, unlocked=unlocked, cleared=cleared
            )
            if proposed is None:
                raise PrepRefused(
                    "every character the save knows about has been cleared; "
                    "name one explicitly to drill it again"
                )
            character, proposal = proposed
        else:
            found = _character(catalog.characters, character_id)
            if found is None:
                raise PrepRefused(
                    f"no character with id {character_id!r} in the extracted data; "
                    "ids look like `character_mage`"
                )
            character, proposal = found, None

        card, truth = build(
            character, _weapons(catalog), game_version=catalog.game_version
        )
        drill = self._store.write(
            {
                "drill_id": new_drill_id(),
                "opened_at": now_stamp(),
                "game_version": catalog.game_version,
                "proposal": proposal,
                "card": card,
                "truth": truth,
                "predictions": None,
                "committed_at": None,
                "verdicts": None,
                "revealed_at": None,
                "actual_wave": None,
                "settled_at": None,
            }
        )
        return {
            "drill_id": drill["drill_id"],
            "state": "open",
            "proposal": proposal,
            "card": card,
            "predictions_wanted": list(DIMENSIONS),
            "next": (
                "commit all four predictions with "
                "`prep --commit <drill-id> --primary-stat ... --secondary-stat ... "
                "--weapon-class ... --weakest-wave ...`; nothing is revealed before then"
            ),
        }

    def commit(
        self,
        drill_id: str,
        *,
        primary_stat: str,
        secondary_stat: str,
        weapon_class: str,
        weakest_wave: int,
    ) -> dict[str, Any]:
        """Record the four answers. Refused if this drill already has some."""
        drill = self._load(drill_id)
        if drill["predictions"] is not None:
            raise PrepRefused(
                f"{drill_id} was committed at {drill['committed_at']}; a committed "
                "prediction is not revisable, which is the only thing that makes it "
                "a prediction. Open a new drill to answer again"
            )
        drill["predictions"] = {
            "primary_stat": primary_stat,
            "secondary_stat": secondary_stat,
            "weapon_class": weapon_class,
            "weakest_wave": weakest_wave,
        }
        drill["committed_at"] = now_stamp()
        self._store.write(drill)
        return {
            "drill_id": drill_id,
            "state": "committed",
            "predictions": drill["predictions"],
            "next": f"`prep --reveal {drill_id}`",
        }

    def reveal(self, drill_id: str) -> dict[str, Any]:
        """Name the character, and score each prediction against the game data."""
        drill = self._load(drill_id)
        if drill["predictions"] is None:
            raise PrepRefused(
                f"{drill_id} has no committed predictions, and the reveal is what "
                "they are for; commit four answers first"
            )
        drill["verdicts"] = score(
            drill["truth"], drill["predictions"], drill.get("actual_wave")
        )
        drill["revealed_at"] = drill.get("revealed_at") or now_stamp()
        self._store.write(drill)
        return {
            "drill_id": drill_id,
            "state": "revealed",
            "character": drill["truth"],
            "predictions": drill["predictions"],
            "verdicts": drill["verdicts"],
            "next": (
                f"after playing it, `prep --settle {drill_id} --actual-wave <wave>` "
                "scores the wave prediction"
            )
            if drill["verdicts"]["weakest_wave"]["verdict"] == PENDING
            else None,
        }

    def settle(self, drill_id: str, *, actual_wave: int) -> dict[str, Any]:
        """Score the wave prediction against the wave the run actually broke at."""
        drill = self._load(drill_id)
        if drill["predictions"] is None:
            raise PrepRefused(
                f"{drill_id} has no committed predictions to settle; commit four "
                "answers first"
            )
        drill["actual_wave"] = actual_wave
        drill["settled_at"] = now_stamp()
        drill["verdicts"] = score(drill["truth"], drill["predictions"], actual_wave)
        self._store.write(drill)
        return {
            "drill_id": drill_id,
            "state": "settled",
            "actual_wave": actual_wave,
            "verdicts": drill["verdicts"],
        }

    def history(self) -> dict[str, Any]:
        """The hit rate per dimension, and the drills it is made of.

        This is the number `MISSION.md` says the workspace is judged on, so it
        is a command rather than something to be counted up by hand. Only
        revealed drills are listed: an open one still has a name to withhold.
        """
        drills = list(self._store.all())
        scored = [drill["verdicts"] for drill in drills if drill.get("verdicts")]
        return {
            "drills": len(drills),
            "committed": sum(1 for drill in drills if drill.get("predictions")),
            "revealed": len(scored),
            "settled": sum(1 for drill in drills if drill.get("actual_wave") is not None),
            "hit_rate": tally(scored),
            "taken": [_summary(drill) for drill in drills if drill.get("verdicts")],
        }

    def _load(self, drill_id: str) -> dict[str, Any]:
        drill = self._store.read(drill_id)
        if drill is None:
            raise PrepRefused(
                f"no drill with id {drill_id!r}; `prep --history` lists the ones "
                "there are"
            )
        return drill


def _summary(drill: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "drill_id": drill.get("drill_id"),
        "opened_at": drill.get("opened_at"),
        "character_id": (drill.get("truth") or {}).get("character_id"),
        "game_version": drill.get("game_version"),
        "verdicts": {
            dimension: (drill["verdicts"].get(dimension) or {}).get("verdict")
            for dimension in DIMENSIONS
        },
    }


def _character(
    characters: Sequence[Mapping[str, Any]], character_id: str
) -> Mapping[str, Any] | None:
    return next(
        (
            character
            for character in characters
            if str(character.get("id")) == character_id
        ),
        None,
    )


def _weapons(catalog: Catalog) -> dict[str, Mapping[str, Any]]:
    return {
        str(weapon["id"]): weapon
        for weapon in catalog.weapons
        if isinstance(weapon.get("id"), str)
    }
