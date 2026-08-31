---
name: brotato-review
description: Review a dead Brotato run. Use when the player has just died, says a run ended, or asks for a post-mortem, review or run record. Reads the captured snapshots, takes the player's hypothesis first, then diagnoses and ends with one change to try.
---

# `/brotato-review`

A review has an order, and the order is the whole value: the player commits to
their read of the run **before** seeing a diagnosis. The CLI enforces this — a
diagnosis is refused until a hypothesis is on record. Do not try to work around
that refusal; it is the feature.

Run every command from the repo root.

## 1. Read the run

```sh
uv run brotato review           # the latest run; add a run id to review an older one
```

If the answer is `{"reviewed": false, "reason": "no-runs-captured"}`, say so —
the watcher captured nothing — and stop.

Otherwise you have the **briefing**: character, danger, zone, patch, waves
reached, weapons and key items held, final stats, the per-wave build curve, and
what the save says has been killing this player. Never ask the player to
describe their build. You have it.

## 2. Show the briefing, conclude nothing

Summarise it in a few lines: the run's framing, the build as it ended, and the
curve. State only what is in the data — wave numbers, counts, stat values.

**Do not** name a cause, hint at one, or ask a leading question ("did the damage
stall?"). If the player asks what you think, tell them it comes after their
hypothesis.

## 3. Take the hypothesis

Ask for **one line**: what they think went wrong. Wait for it. Then record it
verbatim:

```sh
uv run brotato review --hypothesis "<their line, their words>"
```

Their words, not a tidied version of them. The record is evidence about their
model, and paraphrase destroys it.

## 4. Only now, diagnose

With the hypothesis on record, work out what the data says. Pull on:

- **the curve** — the wave where level, health, gold or `damage_last_wave`
  flattened or fell relative to earlier waves;
- **the build** — weapons stuck at low tiers, a stacked item that did nothing
  for this character, a `final_stats` line that is far ahead of or behind the
  rest;
- **the death causes** — the save's lifetime histogram, which says whether this
  death is the one that keeps happening;
- **`docs/research/`** and the reference docs, for what the numbers should have
  been by that wave.

Say plainly where the hypothesis was right and where it was wrong. That gap is
what the player came for. One cause, the most likely one — not a list.

## 5. End with exactly one change

One concrete, testable change for the next run ("buy a tier-2 weapon by wave 6",
not "manage the economy better"). Record it with the diagnosis:

```sh
uv run brotato review --diagnosis "<one or two sentences>" --change "<the one change>"
```

Then check whether this is a repeat:

```sh
uv run brotato records
```

Mention a pattern only when it actually recurs — the same change proposed twice,
the same character dying at the same wave three times. `patterns` counts it for
you; do not editorialise a single data point into a trend.

## 6. Propose a learning record — only if the model changed

A learning record is written when the player's **model of the game** changed: a
heuristic disproved, the friend's advice contradicted by the data, a stat they
had been over-buying revealed as a trap. Not for an ordinary mistake, not for a
missed execution, not once per review — one per review would bury the signal.

If nothing changed, say so in a sentence and stop. That is the common case.

If something did change, say what it was and offer to write it. The player can
decline; take the decline and stop. On a yes, write
`learning-records/<NNN>-<slug>.md` (next free number), following
`learning-records/README.md`.

## Re-diagnosing an old run

A run already diagnosed needs a **fresh hypothesis** before a new diagnosis:

```sh
uv run brotato review <run-id> --hypothesis "<their new read>"
uv run brotato review <run-id> --diagnosis "..." --change "..."
```

The previous review moves into the record's `revisions`, so a model improving is
itself on record.

## Vocabulary

Use `CONTEXT.md`'s words: run, wave, danger, zone, character, build, run record,
learning record. Not "game", "round", "difficulty", "loadout", "post-mortem".
