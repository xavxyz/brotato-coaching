# ADR-0005: A quiz asks for the answer before it shows the options

**Status:** accepted
**Date:** 2026-09-03
**Context:** `lessons/`, `assets/quiz.js`, `assets/lesson.css`

## Context

The mission measures derivation, not results, and a lesson is only worth writing
if what it teaches survives to the moment it is needed — a shop screen, twenty
seconds, wave 9. Retrieval practice is the mechanism that gets it there:
producing an answer from memory strengthens recall, recognising one in a list
does not.

A multiple-choice quiz is the natural component to reach for, and it is also the
natural way to destroy the property. Once four options are on screen, the reader
is doing recognition, and recognition feels like knowing. Two smaller versions of
the same leak sit inside it: an answer can be picked from its *shape* rather than
its content — the longest option, the most qualified one, the only one with a
number in it — and feedback deferred to a marking step at the bottom of the page
arrives after the reader has stopped caring.

This is the same failure the review workflow has, in a different costume:
ADR-0004 exists because a diagnosis read first silently rewrites the hypothesis.
A list of options read first silently rewrites what you knew.

## Decision

1. **The options are hidden until the reader asks for them.** Each question shows
   its prompt and a button; the answer is produced from memory first, and the
   button is the reader's own statement that they have one. The commitment is not
   enforceable the way `review --diagnosis` is — nothing can tell whether an
   answer was really formed — so this is a gate on the honest reader, not a lock.

2. **Every option of a question is the same length in words, and within four
   characters.** `tests/test_lessons.py` computes this rather than trusting the
   author, because it is exactly the kind of constraint a writer breaks while
   improving a sentence. Where characters cannot be equalised without writing
   something false, the words win and the spread stays inside the tolerance.

3. **Feedback is immediate and per option, never a marking step.** Every option
   carries a note saying why it is right or wrong, revealed the moment one is
   chosen. A wrong choice is answered with a reason, which is the only part of
   being wrong that teaches anything.

4. **The first answer is the only one.** A question locks once answered. It is
   not scored, and no tally is kept anywhere: the number this workspace tracks is
   the drill's prediction hit rate (`CONTEXT.md`), and a second measurement of the
   same thing, taken less rigorously, would only dilute it.

5. **The component lives in `assets/`, and a lesson inlines nothing.** `quiz.js`
   holds the behaviour and `lesson.css` the styling, on the same terms as the
   shared stylesheet: a page that needs a style adds it there so the next page
   inherits it. The suite checks that a lesson carries no inline script.

6. **Nothing is hidden in the markup — the script hides what it can re-show.**
   With JavaScript off, a lesson is a complete quiz with its options and notes
   visible; before printing, the script drops every question's state so paper
   gets the same. A reader who cannot run the interaction still gets the lesson.

## Consequences

- Writing a question is harder than writing prose: four options, one correct,
  four notes, all to the same word count. That cost is deliberate and it is where
  the leak-proofing lives.
- The equal-length rule bounds how much nuance an option can carry, so nuance
  goes in the note instead, where it is read at the moment it lands.
- A lesson has a word budget (`LONGEST_LESSON`), and questions spend from the
  same budget as the prose. A fifth question costs a paragraph.
- The state machine is one attribute, `data-state` on a question, shared between
  `quiz.js` and `lesson.css`. Anything that wants to reveal a quiz — a print
  stylesheet, a future "show me everything" control — sets or drops it.
