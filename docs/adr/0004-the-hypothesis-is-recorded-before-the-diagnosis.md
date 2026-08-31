# ADR-0004: The hypothesis is recorded before the diagnosis, and the tool enforces it

**Status:** accepted
**Date:** 2026-08-31
**Context:** `review`, `records`, `/brotato-review`

## Context

The point of reviewing a dead run is not the diagnosis. It is the **gap** between
what the player thought went wrong and what the data says went wrong — that gap
is the measurement of their model, and it is the only thing in this workspace
that says whether the coaching is working.

That measurement is destroyed by ordering. A player who reads a diagnosis first
will unconsciously revise their read to agree with it, and will report a
hypothesis they did not hold. Nobody does this deliberately; it is why the rule
cannot be left to good intentions.

The obvious place to put the rule is the skill's prompt: "ask for the hypothesis
first". Prompts are advice. An agent that has already computed a diagnosis, or a
player who asks "so what went wrong?", is one sentence away from breaking the
only property the workflow has.

## Decision

1. **The CLI refuses a diagnosis until a hypothesis is on record.** `review
   --diagnosis` exits non-zero, naming the missing hypothesis, when the run has
   no `hypothesis` written. The ordering is a property of the tool, not of
   whoever is driving it, and it holds for a human at a terminal exactly as it
   holds for an agent.

2. **The briefing states nothing.** `review` with no flags reports what is in the
   snapshots — build, per-wave curve, final stats — plus the patch and the save's
   death histogram, and concludes nothing from any of it. There is no code path
   that produces a diagnosis, so there is nothing for the CLI to leak early.

3. **Re-diagnosing needs a fresh hypothesis.** A run already diagnosed accepts a
   new diagnosis only after a new hypothesis, and the previous review moves into
   `revisions` rather than being overwritten. Re-reading an old run once the
   model has improved is the point of keeping records; doing it without
   re-committing to a read would be reading the answer.

4. **Records live in `records/`, one JSON file per run, in a fixed schema.** A
   sibling of `runs/`, not a child: `runlog` owns everything under `runs/` and
   rewrites a run's metadata as it captures, while a record is the player's
   writing. Both commit — they are the player's own data.

5. **`review` interprets the snapshot; `runlog` does not.** ADR-0001 keeps
   snapshots whole and has `runlog` read exactly five fields, only to decide
   which run a reading belongs to. Reading the rest — weapons, items, the stats
   behind the hashed `effects` map — is what a review *is*, so it lives in
   `review` and the two packages know the game's file for different reasons.

6. **Exactly one change per review, recorded with the diagnosis.** `--change` is
   required with `--diagnosis`, and it is a single string, so "one change" is
   arithmetic rather than discipline.

## Consequences

- The hypothesis and the diagnosis each carry a `recorded_at`, so the ordering
  is checkable in the file long after the review, not merely asserted by it.
- A review is two or three CLI calls rather than one. That is the cost of the
  ordering being real, and it is small.
- The stat names `review` reports are a fixed list hashed with `godot_hash`
  (ADR-0003). A patch that renames a stat drops it from `final_stats` rather
  than breaking a review, and the list is the one place to update.
- `review` depends on `gamedata` for that hash, which is a new edge in the
  import graph: app-tier-ward, acyclic, and checked by `scripts/check_cycles.py`.
  The spec's warning was against `savefile` depending on `gamedata`, which would
  couple the player's data to having the game installed; a review already needs
  both, and degrades to raw ids and a null patch when the game data is absent.
- Nothing here reads the player's *intent* — a review can still be shallow. What
  it cannot be is retroactively confident.
