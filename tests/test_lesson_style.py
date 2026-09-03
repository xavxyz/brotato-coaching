"""The shared stylesheet, checked against the promises a styled page makes.

`assets/lesson.css` is allowed to look like anything. What it is not allowed to
do is stop being readable, stop printing, or start shipping somebody else's
content — and all three are things a restyle breaks quietly, because the page
still renders.

**Contrast.** The palette lives in one place, as `--token: light-dark(a, b)`
pairs, so both themes can be read off the file and every text-on-surface pairing
scored against WCAG. A game can afford a low-contrast panel for the two seconds
a tooltip is up; a lesson read for ten minutes cannot.

**Print.** Paper is white and ink is black however the screen was themed, the
toggle is not printed, and no recall answer stays hidden behind a control paper
does not have.

**Licences.** The look is derived from the installed game; the game's own files
are not. Anything committed under `assets/fonts/` is a font this repo has the
right to redistribute, and its licence is committed beside it.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
STYLESHEET = REPO_ROOT / "assets" / "lesson.css"
FONTS = REPO_ROOT / "assets" / "fonts"

# WCAG 2.1 AA: 4.5:1 for body text, 3:1 for a border or other non-text signal.
TEXT_CONTRAST = 4.5
NON_TEXT_CONTRAST = 3.0

# Which ink is allowed to land on which surface. A pairing absent here is one no
# page makes; a pairing here is one the stylesheet has to keep legible.
TEXT_ON_SURFACE = [
    (ink, surface)
    for ink in ("--ink", "--ink-muted", "--ink-faint", "--accent")
    for surface in ("--bg", "--bg-raised", "--bg-sunken", "--accent-wash")
]

# Right and wrong in a quiz are drawn as borders, never as the only signal, so
# they are held to the non-text threshold on the surfaces a question uses.
# `--rule` is not here: a divider is decoration, and WCAG asks nothing of it.
SIGNAL_ON_SURFACE = [
    (signal, surface)
    for signal in ("--good", "--bad")
    for surface in ("--bg-raised", "--accent-wash")
]

_PAIR = re.compile(
    r"^\s*(--[a-z-]+):\s*light-dark\(\s*(#[0-9a-fA-F]{6})\s*,\s*(#[0-9a-fA-F]{6})\s*\)",
    re.MULTILINE,
)
_PRINT_VALUE = re.compile(r"^\s*(--[a-z-]+):\s*(#[0-9a-fA-F]{6})\s*;", re.MULTILINE)


def stylesheet() -> str:
    return STYLESHEET.read_text()


def print_block() -> str:
    """Everything inside the stylesheet's `@media print` rule."""
    start = stylesheet().index("@media print")
    depth, index = 0, start
    text = stylesheet()
    while index < len(text):
        if text[index] == "{":
            depth += 1
        elif text[index] == "}":
            depth -= 1
            if depth == 0:
                return text[start : index + 1]
        index += 1
    raise AssertionError("@media print is never closed")


def palettes() -> tuple[dict[str, str], dict[str, str]]:
    """The light and dark palettes, read off the `light-dark()` pairs."""
    light, dark = {}, {}
    for token, on_light, on_dark in _PAIR.findall(stylesheet()):
        light[token] = on_light
        dark[token] = on_dark
    assert light, "no light-dark() palette found in lesson.css"
    return light, dark


def relative_luminance(colour: str) -> float:
    channels = []
    for offset in (1, 3, 5):
        value = int(colour[offset : offset + 2], 16) / 255
        channels.append(
            value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4
        )
    red, green, blue = channels
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def contrast(foreground: str, background: str) -> float:
    lighter, darker = sorted(
        (relative_luminance(foreground), relative_luminance(background)), reverse=True
    )
    return (lighter + 0.05) / (darker + 0.05)


THEMES = dict(zip(("light", "dark"), palettes()))


@pytest.mark.parametrize("theme", sorted(THEMES))
@pytest.mark.parametrize("ink,surface", TEXT_ON_SURFACE, ids=lambda pair: str(pair))
def test_body_text_passes_wcag_aa(theme: str, ink: str, surface: str) -> None:
    palette = THEMES[theme]
    assert ink in palette, f"{ink} is not a light-dark() token"
    assert surface in palette, f"{surface} is not a light-dark() token"

    ratio = contrast(palette[ink], palette[surface])

    assert ratio >= TEXT_CONTRAST, (
        f"{theme}: {ink} {palette[ink]} on {surface} {palette[surface]} "
        f"is {ratio:.2f}:1, below {TEXT_CONTRAST}:1"
    )


@pytest.mark.parametrize("theme", sorted(THEMES))
@pytest.mark.parametrize("signal,surface", SIGNAL_ON_SURFACE, ids=lambda pair: str(pair))
def test_a_border_that_carries_meaning_is_visible(
    theme: str, signal: str, surface: str
) -> None:
    palette = THEMES[theme]
    ratio = contrast(palette[signal], palette[surface])

    assert ratio >= NON_TEXT_CONTRAST, (
        f"{theme}: {signal} {palette[signal]} on {surface} {palette[surface]} "
        f"is {ratio:.2f}:1, below {NON_TEXT_CONTRAST}:1"
    )


def test_printing_is_black_ink_on_white_paper() -> None:
    printed = dict(_PRINT_VALUE.findall(print_block()))

    assert printed.get("--bg") == "#ffffff", "paper is white"
    assert printed.get("--ink") == "#000000", "ink is black"
    for token in ("--bg-raised", "--bg-sunken", "--accent-wash"):
        assert printed.get(token) == "#ffffff", f"{token} is paper too"
    for token in ("--ink-muted", "--ink-faint", "--accent"):
        assert contrast(printed[token], "#ffffff") >= TEXT_CONTRAST, (
            f"printed {token} is too pale for paper"
        )


def test_the_theme_toggle_is_not_printed() -> None:
    assert re.search(r"\.theme-toggle\s*\{\s*display:\s*none", print_block()), (
        "the toggle is a screen control; paper has nothing to toggle"
    )


def test_a_printed_recall_answer_is_revealed() -> None:
    printed = print_block()

    assert "details[open] > summary" in printed, (
        "lesson.js opens every answer for printing; the control that hid it goes"
    )
    assert "::details-content" in printed, (
        "Safari fires no beforeprint, so the answer is forced open in CSS too"
    )


def test_only_freely_licensed_fonts_are_committed() -> None:
    if not FONTS.is_dir():
        pytest.skip("no fonts are shipped")
    shipped = sorted(path.name for path in FONTS.iterdir() if path.is_file())

    assert "OFL.txt" in shipped, "a shipped font ships its licence beside it"
    for name in shipped:
        assert name == "OFL.txt" or name.endswith(".woff2"), (
            f"{name}: fonts ship as woff2, and nothing else ships here"
        )


def test_no_game_owned_asset_is_committed() -> None:
    """Sprites and textures belong to the publisher; the look derived from them
    does not. A restyle that needed a game file would be a restyle that ships
    one, so the extensions it would arrive under are refused outright."""
    strays = [
        path.relative_to(REPO_ROOT)
        for path in (REPO_ROOT / "assets").rglob("*")
        if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".ttf", ".otf"}
    ]

    assert not strays, f"game assets are never committed: {strays}"
