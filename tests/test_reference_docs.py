"""Reference docs, checked against the game they claim to describe.

A reference doc is printed and reread away from a screen, which is exactly the
condition under which a stale number does the most damage. So every number in one
is a derived claim, carrying a claim path this suite re-derives, and every page
carries the patch stamp saying which build those claims were checked against. The
claim path grammar and the re-derivation live in `pages.py`, shared with lessons;
`CONTEXT.md` defines the terms.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from conftest import INSTALL
from pages import derived_claims_in, wrong_claims

REFERENCE = Path(__file__).parent.parent / "reference"


def reference_docs() -> list[Path]:
    return sorted(REFERENCE.glob("*.html"))


def test_there_is_a_reference_doc_on_stats_and_damage() -> None:
    assert REFERENCE.is_dir(), "reference docs live in reference/"
    assert any(
        "stats" in page.name and "damage" in page.name for page in reference_docs()
    )


@pytest.mark.parametrize("page", reference_docs(), ids=lambda page: page.name)
def test_a_reference_doc_makes_derived_claims(page: Path) -> None:
    assert derived_claims_in(page), f"{page.name} states no numbers the suite can check"


@pytest.mark.parametrize("page", reference_docs(), ids=lambda page: page.name)
def test_a_reference_doc_cites_the_sources_it_interprets(page: Path) -> None:
    text = page.read_text()

    assert "RESOURCES.md" in text, "cited claims name a source id from RESOURCES.md"
    assert re.search(r"STAT-S\d+", text), "no source id appears on the page"


@pytest.mark.skipif(
    INSTALL is None, reason="Brotato is not installed on this machine"
)
@pytest.mark.parametrize("page", reference_docs(), ids=lambda page: page.name)
def test_every_number_on_the_page_is_still_the_games(page: Path, game: dict) -> None:
    assert not (wrong := wrong_claims(page, game)), "\n".join(wrong)


@pytest.mark.skipif(
    INSTALL is None, reason="Brotato is not installed on this machine"
)
@pytest.mark.parametrize("page", reference_docs(), ids=lambda page: page.name)
def test_the_patch_stamp_is_the_installed_patch(page: Path, game: dict) -> None:
    assert INSTALL is not None
    stamps = [
        text for path, text in derived_claims_in(page) if path == "game-version"
    ]

    assert stamps, f"{page.name} is not patch-stamped"
    assert all(stamp == INSTALL.version for stamp in stamps)
