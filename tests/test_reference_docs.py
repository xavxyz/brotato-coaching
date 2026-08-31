"""Reference docs, checked against the game they claim to describe.

A reference doc is printed and reread away from a screen, which is exactly the
condition under which a stale number does the most damage. So every numeric
claim in one carries a `data-claim` attribute naming where in the extracted game
data it came from, and this suite re-derives it.

The claim grammar, in full:

    game-version                     the extraction's version stamp
    count:<catalogue>                how many weapons / characters / items exist
    weapon:<id>:<field>              a field of one weapon's stats, or its tier or class
    weapon:<id>:scaling:<stat>       one weapon's scaling coefficient for a stat
    scaling-count:<stat>             how many weapon entries scale off a stat
    scaling-max:<stat>               the largest coefficient any weapon has for a stat

A `#pct` or `#seconds` suffix says the page displays the value transformed, so
that a crit chance stored as `0.5` may be printed as `50%` and a cooldown stored
in frames as seconds.

Values here are the game's, so a patch may move them. That is the point: when
this fails after an update, the failure is the reference doc going stale, and
the patch stamp on the page is the thing that has to change with it.
"""

from __future__ import annotations

import json
import re
from html.parser import HTMLParser
from pathlib import Path

import pytest

from conftest import INSTALL

from brotato_coaching.gamedata import extract

REFERENCE = Path(__file__).parent.parent / "reference"


def reference_docs() -> list[Path]:
    return sorted(REFERENCE.glob("*.html"))


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


@pytest.fixture(scope="module")
def extracted(tmp_path_factory: pytest.TempPathFactory) -> Path:
    assert INSTALL is not None
    return extract(INSTALL, tmp_path_factory.mktemp("data")).directory


@pytest.fixture(scope="module")
def game(extracted: Path) -> dict:
    return {
        name: json.loads((extracted / f"{name}.json").read_text())
        for name in ("characters", "weapons", "items")
    }


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


def test_there_is_a_reference_doc_on_stats_and_damage() -> None:
    assert REFERENCE.is_dir(), "reference docs live in reference/"
    assert any(
        "stats" in page.name and "damage" in page.name for page in reference_docs()
    )


@pytest.mark.parametrize("page", reference_docs(), ids=lambda page: page.name)
def test_a_reference_doc_makes_checkable_claims(page: Path) -> None:
    assert claims_in(page), f"{page.name} states no numbers the suite can check"


@pytest.mark.parametrize("page", reference_docs(), ids=lambda page: page.name)
def test_a_reference_doc_cites_the_sources_it_interprets(page: Path) -> None:
    text = page.read_text()

    assert "RESOURCES.md" in text, "interpretive claims are cited to RESOURCES.md"
    assert re.search(r"STAT-S\d+", text), "no source id appears on the page"


@pytest.mark.skipif(
    INSTALL is None, reason="Brotato is not installed on this machine"
)
@pytest.mark.parametrize("page", reference_docs(), ids=lambda page: page.name)
def test_every_number_on_the_page_is_still_the_games(page: Path, game: dict) -> None:
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

    assert not wrong, "\n".join(wrong)


@pytest.mark.skipif(
    INSTALL is None, reason="Brotato is not installed on this machine"
)
@pytest.mark.parametrize("page", reference_docs(), ids=lambda page: page.name)
def test_the_patch_stamp_is_the_installed_patch(page: Path, game: dict) -> None:
    assert INSTALL is not None
    stamps = [text for claim, text in claims_in(page) if claim == "game-version"]

    assert stamps, f"{page.name} is not patch-stamped"
    assert all(stamp == INSTALL.version for stamp in stamps)
