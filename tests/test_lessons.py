"""Lessons, checked against the promises a lesson makes.

A lesson is the one artefact in this workspace that is *worked through* rather
than reread, so the things that can quietly break it are different from a
reference doc's. Three of them are checked here.

**The quiz must not leak its answer through formatting.** Once options are on
screen, the longest and most qualified one is the correct one often enough that
a reader learns to pick it without learning anything else. So every option of a
question is written to the same word count and within a few characters of the
same length, and that is arithmetic the suite can do.

**The lesson must stay short.** "Completable in a few minutes" is the property
that gets it read at all, and prose grows by a paragraph at a time.

**Its numbers must still be the game's**, on the same terms as a reference doc —
see `pages.py`.

The markup contract a lesson is written to, which the parser below reads:

    <li class="quiz__question">
      <p class="quiz__prompt">…</p>
      <ul class="quiz__options">
        <li class="quiz__option" data-correct>
          <button class="quiz__choice">the answer</button>
          <p class="quiz__note">why it is the answer</p>
"""

from __future__ import annotations

import re
from html.parser import HTMLParser
from pathlib import Path

import pytest

from conftest import INSTALL
from pages import derived_claims_in, wrong_claims

REPO_ROOT = Path(__file__).resolve().parent.parent
LESSONS = REPO_ROOT / "lessons"
RESOURCES = REPO_ROOT / "RESOURCES.md"

# A lesson is read in one sitting, before or after a session and never during
# one. This is the budget that keeps it that way, in words of body text.
LONGEST_LESSON = 1200

# How far apart two options of the same question may be in characters. Equal
# word counts are required outright; characters cannot always be made equal
# without writing something false, so they are made close.
WIDEST_SPREAD = 4

VOID_TAGS = {"br", "col", "embed", "hr", "img", "input", "link", "meta", "source"}


class Quiz(HTMLParser):
    """Every quiz question on a page, with its options and their answer text."""

    def __init__(self) -> None:
        super().__init__()
        self.questions: list[dict] = []
        self._stack: list[tuple[str, str | None]] = []
        self._question: dict | None = None
        self._option: dict | None = None
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        classes = (attributes.get("class") or "").split()
        marker = None
        if "quiz__question" in classes:
            marker = "question"
            self._question = {"prompt": "", "options": []}
        elif "quiz__option" in classes:
            marker = "option"
            self._option = {"correct": "data-correct" in attributes, "note": False}
        elif "quiz__choice" in classes:
            marker, self._text = "choice", []
        elif "quiz__prompt" in classes:
            marker, self._text = "prompt", []
        elif "quiz__note" in classes:
            marker = "note"
        if tag not in VOID_TAGS:
            self._stack.append((tag, marker))

    def handle_data(self, data: str) -> None:
        if any(marker in ("choice", "prompt") for _, marker in self._stack):
            self._text.append(data)

    def handle_endtag(self, tag: str) -> None:
        while self._stack:
            name, marker = self._stack.pop()
            self._close(marker)
            if name == tag:
                return

    def _close(self, marker: str | None) -> None:
        text = " ".join("".join(self._text).split())
        match marker:
            case "prompt" if self._question is not None:
                self._question["prompt"] = text
            case "choice" if self._option is not None:
                self._option["answer"] = text
            case "note" if self._option is not None:
                self._option["note"] = True
            case "option" if self._question is not None and self._option is not None:
                self._question["options"].append(self._option)
                self._option = None
            case "question" if self._question is not None:
                self.questions.append(self._question)
                self._question = None


class Text(HTMLParser):
    """A page's body text, with markup, scripts and styles taken out."""

    def __init__(self) -> None:
        super().__init__()
        self._skipping = 0
        self.words: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in ("script", "style", "head"):
            self._skipping += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in ("script", "style", "head"):
            self._skipping = max(0, self._skipping - 1)

    def handle_data(self, data: str) -> None:
        if not self._skipping:
            self.words.extend(data.split())


def lessons() -> list[Path]:
    return sorted(LESSONS.glob("*.html"))


def questions_in(page: Path) -> list[dict]:
    parser = Quiz()
    parser.feed(page.read_text())
    return parser.questions


def words_in(page: Path) -> list[str]:
    parser = Text()
    parser.feed(page.read_text())
    return parser.words


def trust_of(source_id: str) -> str | None:
    """The trust tier `RESOURCES.md` records for a source, or None if unlisted."""
    for line in RESOURCES.read_text().splitlines():
        columns = [cell.strip() for cell in line.split("|")]
        if len(columns) > 4 and columns[1] == source_id:
            return columns[4]
    return None


def test_the_spine_has_a_lesson_in_it() -> None:
    assert LESSONS.is_dir(), "lessons live in lessons/"
    assert lessons(), "the lesson spine is empty"


@pytest.mark.parametrize("page", lessons(), ids=lambda page: page.name)
def test_a_lesson_uses_the_shared_stylesheet_and_theme_toggle(page: Path) -> None:
    text = page.read_text()

    assert "assets/lesson.css" in text, "a lesson links the shared stylesheet"
    assert "assets/lesson.js" in text, "a lesson links the shared behaviour"
    assert 'class="theme-toggle"' in text, "a lesson carries the light/dark toggle"


@pytest.mark.parametrize("page", lessons(), ids=lambda page: page.name)
def test_a_lesson_uses_the_shared_quiz_rather_than_its_own(page: Path) -> None:
    text = page.read_text()
    inline = re.findall(r"<script\b[^>]*>(.*?)</script>", text, re.DOTALL)

    assert "assets/quiz.js" in text, "the quiz component lives in assets/"
    assert not any(body.strip() for body in inline), (
        "a lesson inlines no behaviour: reuse is the default, not the exception"
    )


@pytest.mark.parametrize("page", lessons(), ids=lambda page: page.name)
def test_a_lesson_practises_retrieval(page: Path) -> None:
    questions = questions_in(page)

    assert len(questions) >= 3, f"{page.name} asks {len(questions)} questions"
    for question in questions:
        assert question["prompt"], "a question with no prompt"
        options = question["options"]
        assert len(options) >= 3, f"{question['prompt']}: {len(options)} options"
        correct = [option for option in options if option["correct"]]
        assert len(correct) == 1, f"{question['prompt']}: {len(correct)} correct"
        assert all(option["note"] for option in options), (
            f"{question['prompt']}: an option gives no feedback when chosen"
        )


@pytest.mark.parametrize("page", lessons(), ids=lambda page: page.name)
def test_the_shape_of_an_answer_gives_nothing_away(page: Path) -> None:
    leaks = []
    for question in questions_in(page):
        answers = [option["answer"] for option in question["options"]]
        counts = {len(answer.split()) for answer in answers}
        lengths = [len(answer) for answer in answers]
        if len(counts) > 1:
            leaks.append(f"{question['prompt']}: word counts {sorted(counts)}")
        if max(lengths) - min(lengths) > WIDEST_SPREAD:
            leaks.append(f"{question['prompt']}: character spread {lengths}")
    assert not leaks, "\n".join(leaks)


@pytest.mark.parametrize("page", lessons(), ids=lambda page: page.name)
def test_a_lesson_is_completable_in_a_few_minutes(page: Path) -> None:
    length = len(words_in(page))

    assert length <= LONGEST_LESSON, f"{page.name} is {length} words"


@pytest.mark.parametrize("page", lessons(), ids=lambda page: page.name)
def test_a_lesson_links_a_reference_doc_by_anchor(page: Path) -> None:
    links = re.findall(r'href="\.\./reference/([^"#]+)#([^"]+)"', page.read_text())

    assert links, "a lesson sends the reader to the reference doc it builds on"
    for name, anchor in links:
        target = REPO_ROOT / "reference" / name
        assert target.exists(), f"no such reference doc: {name}"
        assert f'id="{anchor}"' in target.read_text(), f"{name} has no #{anchor}"


@pytest.mark.parametrize("page", lessons(), ids=lambda page: page.name)
def test_a_lesson_recommends_one_high_trust_source(page: Path) -> None:
    text = page.read_text()
    recommended = re.findall(r'data-read-next="([^"]+)"', text)

    assert "RESOURCES.md" in text, "cited claims name a source id from RESOURCES.md"
    assert len(recommended) == 1, f"{len(recommended)} sources recommended, want 1"
    trust = trust_of(recommended[0])
    assert trust is not None, f"{recommended[0]} is not in RESOURCES.md"
    assert trust.startswith(("A", "B")), f"{recommended[0]} is trust tier {trust}"


@pytest.mark.parametrize("page", lessons(), ids=lambda page: page.name)
def test_a_lesson_says_the_agent_can_be_asked(page: Path) -> None:
    assert "follow-up question" in page.read_text().lower()


@pytest.mark.skipif(
    INSTALL is None, reason="Brotato is not installed on this machine"
)
@pytest.mark.parametrize("page", lessons(), ids=lambda page: page.name)
def test_every_number_in_a_lesson_is_still_the_games(page: Path, game: dict) -> None:
    assert not (wrong := wrong_claims(page, game)), "\n".join(wrong)


@pytest.mark.skipif(
    INSTALL is None, reason="Brotato is not installed on this machine"
)
@pytest.mark.parametrize("page", lessons(), ids=lambda page: page.name)
def test_the_patch_stamp_is_the_installed_patch(page: Path, game: dict) -> None:
    assert INSTALL is not None
    stamps = [
        text for path, text in derived_claims_in(page) if path == "game-version"
    ]

    assert stamps, f"{page.name} is not patch-stamped"
    assert all(stamp == INSTALL.version for stamp in stamps)
