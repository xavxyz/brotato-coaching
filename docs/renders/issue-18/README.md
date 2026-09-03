# Renders: restyling the lesson stylesheet (#18)

Before and after `assets/lesson.css` was restyled from the installed game
(ADR-0006). A restyle's diff is a column of hex values, which nobody can review;
these are what actually changed.

Both sides render the same page, `lessons/001-what-a-point-of-a-stat-is-worth.html`,
whose markup was not touched — that is the point of the pairing. Before is the
stylesheet at `master`; after is this branch.

| | Before | After |
| --- | --- | --- |
| Light | `before-light.png` | `after-light.png` |
| Dark | `before-dark.png` | `after-dark.png` |
| Print, page 1 | `before-print.png` | `after-print.png` |
| Print, the quiz | `before-print-quiz.png` | `after-print-quiz.png` |

The second print page is here rather than page 1 alone because it is the only one
that shows the guarantee worth checking by eye: on paper every option and every
note is revealed, and the control that hid them is gone.

## How they were made

Chrome headless against the `file://` URL, at a 900px viewport, with `data-theme`
pinned on `<html>` for the two screen renders; `--print-to-pdf` for the print
pair, rasterised at 1.6× and downscaled to 620px wide.

They are evidence, not an input: nothing reads them, and no test regenerates
them. A later restyle adds its own directory rather than editing this one, so
this pair keeps meaning what it meant.
