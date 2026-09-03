# ADR-0006: The workspace look is derived from the installed game, never copied from it

**Status:** accepted
**Date:** 2026-09-03
**Context:** `assets/lesson.css`, `assets/fonts/`, `gamedata`

## Context

A lesson is read either side of a session, about the game, in the same half hour
as the game. Set as a well-mannered document it reads as homework *about*
playing; set as the game it reads as part of playing. That is the whole argument
for restyling `assets/lesson.css`, and it only pays off if the resemblance is
real. A palette recalled from memory or picked off a wiki screenshot is the same
mistake as writing a lesson from a stale tier list: it is confidently wrong, and
it goes wrong again silently at the next patch.

The exact values are available locally. `gamedata` already opens the `.pck` to
read characters and weapons, and the same container holds
`res://resources/themes/` and `res://resources/fonts/` — the theme resources that
define every colour, corner radius and border weight the game's UI draws with.

That access is also the trap. This repository is public, and the game's content
is Blackpowder Games'. `data/` is gitignored for exactly this reason, and a
stylesheet that reached for a sprite or a texture would put back what that
gitignore keeps out.

## Decision

1. **Values are read off the installed game, and each one says where from.**
   Every token in `assets/lesson.css` carries the `res://` path it was read from
   — the page background is `LineEdit/styles/normal` in `base_theme.tres`, the
   panel is `panel/panel_style.tres`, the gold is the border
   `special_button_theme.tres` puts on the button that matters. A later patch is
   checked against the same resource, not against a memory of this restyle.

2. **The derived look may be committed; the game's files may not.** Hex values,
   corner radii, border weights and spacing ratios are facts about how the game
   looks, and they are ours to record. Fonts, sprites and textures out of the
   `.pck` are not, at any size, for any reason. Where a rule could only be
   satisfied by shipping a game file, the rule loses and the comment says so.

3. **The one shipped font is licensed independently of the game.** The game's UI
   font is Anybody — every `font_*.tres` names `Anybody-Medium.ttf` — which is
   published under the SIL Open Font License 1.1. It ships here as the Google
   Fonts subsets, fetched from Google Fonts rather than lifted from the `.pck`,
   with `assets/fonts/OFL.txt` committed beside it. Self-hosted, so a lesson
   opened from a `file://` URL with no network still looks like the game.

4. **Readability outranks resemblance, and the suite decides.** The game can
   afford a low-contrast panel for the two seconds a tooltip is up; a page read
   for ten minutes cannot. `tests/test_lesson_style.py` reads both palettes off
   the `light-dark()` pairs and scores every ink-on-surface pairing against WCAG
   AA, checks that printing is still black on white with the toggle dropped, and
   refuses any game-owned file extension under `assets/`. Where the game's own
   value fails — its gold on a light surface — the hue is kept and the value
   moved until it passes, and the token says that is what happened.

5. **Running prose keeps a reading face.** The game's font does the headings, the
   chrome, the numbers and the controls, which is where its character lives.
   Three paragraphs of a squarish display grotesque is not a lesson anybody
   finishes, so body text stays in a plain sans.

## Consequences

- The dark theme is the game's, read off its resources. The light theme is not:
  Brotato has no light mode, so light is the same palette turned over — the cream
  the codex prints its text in becomes the paper. That asymmetry is permanent and
  is stated in the stylesheet rather than hidden.
- A patch that restyles the game does not break the workspace; it makes it stale,
  and staleness here is invisible in a way a wrong weapon coefficient is not.
  There is no `data-claim` grammar for a colour, and inventing one would mean
  extracting the theme into `data/` for a payoff of "the page is still the right
  shade of black". The re-read is manual, and cheap.
- Panels are darker than the page in dark mode, because that is what the game
  does — `panel_style.tres` is black over a lighter surface. It looks wrong for
  about five seconds if you are expecting a document, and right immediately if
  you are expecting Brotato.
- `assets/` now holds binary. It is 46 KB of woff2 with its licence beside it,
  and the suite refuses anything else.
