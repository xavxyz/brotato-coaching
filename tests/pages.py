"""The claim grammar every published page is checked against.

A lesson and a reference doc are both HTML pages that state the game's numbers,
and both go stale the same way: a patch moves a coefficient and the page keeps
asserting the old one. So a number a page prints carries a `data-claim`
attribute naming where in the extracted game data it came from, and the suite
re-derives it.

The grammar, in full:

    game-version                     the extraction's version stamp
    count:<catalogue>                how many weapons / characters / items exist
    weapon:<id>:<field>              a field of one weapon's stats, or its tier or class
    weapon:<id>:scaling:<stat>       one weapon's scaling coefficient for a stat
    scaling-count:<stat>             how many weapon entries scale off a stat
    scaling-max:<stat>               the largest coefficient any weapon has for a stat

A `#pct` or `#seconds` suffix says the page displays the value transformed, so
that a crit chance stored as `0.5` may be printed as `50%` and a cooldown stored
in frames as seconds.

Values here are the game's, so a patch may move them. That is the point: when a
check fails after an update, the failure is the page going stale, and the patch
stamp on it is the thing that has to change with it.
"""

from __future__ import annotations

import re
from html.parser import HTMLParser
from pathlib import Path


class Claims(HTMLParser):
    """Every `data-claim` on a page, paired with the text that renders it.

    A claim element holds text and nothing else. Markup inside one is rejected
    rather than parsed around: the whole point is that the number the suite
    checks is the number on the paper, and nesting is how those two drift apart.
    """

    def __init__(self) -> None:
        super().__init__()
        self._claim: str | None = None
        self._text: list[str] = []
        self.found: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if self._claim is not None:
            raise AssertionError(
                f"<{tag}> inside claim {self._claim!r}: a claim holds text only"
            )
        claim = dict(attrs).get("data-claim")
        if claim is not None:
            self._claim, self._text = claim, []

    def handle_data(self, data: str) -> None:
        if self._claim is not None:
            self._text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if self._claim is not None:
            self.found.append((self._claim, "".join(self._text).strip()))
            self._claim = None


def claims_in(page: Path) -> list[tuple[str, str]]:
    parser = Claims()
    parser.feed(page.read_text())
    return parser.found


def number_in(text: str) -> tuple[float, int]:
    """The first number in `text`, and how many decimals it is shown to.

    A page is allowed to round — `0.03` for a cooldown of two frames is the
    honest thing to print — but not to misstate, so the comparison is made at
    the precision the page itself chose to display.
    """
    match = re.search(r"-?\d+(?:\.(\d+))?", text)
    if match is None:
        raise AssertionError(f"no number in {text!r}")
    return float(match.group()), len(match.group(1) or "")


def expected(claim: str, game: dict) -> float | str:
    """Re-derive one claim from the extracted data."""
    body, _, transform = claim.partition("#")
    parts = body.split(":")
    value = _resolve(parts, game)
    if isinstance(value, str):
        assert not transform, f"{claim}: a transform makes no sense on a string"
        return value
    match transform:
        case "":
            return value
        case "pct":
            return value * 100
        case "seconds":
            return value / 60
        case _:
            raise AssertionError(f"unknown transform in {claim}: {transform!r}")


def wrong_claims(page: Path, game: dict) -> list[str]:
    """Every claim on `page` the extracted data no longer agrees with."""
    wrong = []
    for claim, text in claims_in(page):
        want = expected(claim, game)
        if isinstance(want, str):
            if text != want:
                wrong.append(f"{claim}: page says {text!r}, game says {want!r}")
            continue
        shown, decimals = number_in(text)
        if shown != round(want, decimals):
            wrong.append(f"{claim}: page says {text!r}, game says {want}")
    return wrong


def _resolve(parts: list[str], game: dict) -> float | str:
    match parts:
        case ["game-version"]:
            return game["weapons"]["game_version"]
        case ["count", "weapon-families"]:
            return len({weapon["weapon_id"] for weapon in game["weapons"]["weapons"]})
        case ["count", catalogue]:
            return len(game[catalogue][catalogue])
        case ["weapon", identifier, "scaling", stat]:
            return dict(_weapon(identifier, game)["stats"]["scaling_stats"])[stat]
        case ["weapon", identifier, field]:
            weapon = _weapon(identifier, game)
            return weapon["stats"][field] if field in weapon["stats"] else weapon[field]
        case ["scaling-count", stat]:
            return len(_coefficients(stat, game))
        case ["scaling-max", stat]:
            return max(_coefficients(stat, game))
        case _:
            raise AssertionError(f"unknown claim: {':'.join(parts)}")


def _weapon(identifier: str, game: dict) -> dict:
    for weapon in game["weapons"]["weapons"]:
        if weapon["id"] == identifier:
            return weapon
    raise AssertionError(f"no such weapon: {identifier}")


def _coefficients(stat: str, game: dict) -> list[float]:
    return [
        coefficient
        for weapon in game["weapons"]["weapons"]
        for key, coefficient in weapon["stats"]["scaling_stats"]
        if key == stat
    ]
