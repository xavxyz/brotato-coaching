# ADR-0001: Snapshot live run state whole, at every change

**Status:** accepted
**Date:** 2026-08-30
**Context:** `runlog`, `watch`, `runs`

## Context

The spec listed live run state as its first known unknown: `run_v3_0.json` had
only ever been observed as `{"current_run_state":{"has_run_state":false}}`, so
nobody knew whether a snapshot was worth taking at all.

It was observed populated on 2026-08-30, mid-run: **26,796 bytes**, danger 5,
`character_crazy`, wave 2 of 20, Abyssal Terrors enabled. Minutes later, before
the watcher existed to catch it, the same file was back to **45 bytes** and
`has_run_state: false`. The premise of this work is confirmed twice over: the
state is rich, and the game erases it.

### What one reading contains

`current_run_state` carries the run's framing — `current_wave`, `nb_of_waves`,
`current_difficulty`, `current_zone`, `current_background`, `enabled_dlcs`,
`is_coop_run`, `is_endless_run`, `retries`, `enemy_scaling`, `bosses_spawn`,
`elites_spawn`, the per-wave event lists, `bonus_gold` / `total_bonus_gold`, the
reroll counters, and both `shop_items` and `locked_shop_items` as complete item
and weapon objects with their prices.

`players_data[0]` carries the **build**: `current_character`, `current_health`,
`current_level`, `current_xp`, `gold`, `selected_weapon`, `active_sets`, and full
objects for every `items` entry and every `weapons` entry — a weapon's `stats`
block (damage, cooldown, crit chance and damage, range, `scaling_stats`, type),
its set bonuses, and `dmg_dealt_last_wave` per weapon instance.

Two things it does **not** contain: any timestamp or run identifier, and any
history. It is a point-in-time state, nothing more.

It is also, on the reading observed, free of the player's Steam ID — that appears
only in the containing directory name — so snapshots are safe to commit.

`players_data[0].effects` (~230 entries), `active_sets`, `elites_spawn` and
`tracked_item_effects` are keyed by the same **integer hashes** as the save file.
Resolving them is `gamedata`'s job (spec unknown #2), not `runlog`'s.

## Decision

1. **A snapshot is the file, copied whole.** No projection, no schema of our own.
   The state is dense, undocumented, and patch-dependent; anything we choose to
   keep now is something a future review cannot ask for. `runlog` reads exactly
   five fields — `has_run_state`, `current_wave`, `current_difficulty`,
   `current_zone`, `current_character` — and only to decide which run a reading
   belongs to.

2. **Capture on every change, not once per wave.** There is no history in the
   file, so the only way to get the per-wave build curve a review needs is to
   snapshot each time the bytes change. Dedup is by SHA-256 of the file, so a
   quiet minute costs nothing on disk.

3. **A run ends when `has_run_state` goes false.** The clear is the death (or the
   win). The watcher closes the run and keeps its snapshots; the next populated
   reading opens a new run. Because a poll can miss the clear entirely, a change
   of character, danger or zone — or a wave earlier than one already captured —
   also starts a new run.

   Those three hold steady within a run by definition, not by observation:
   CONTEXT.md has Danger as "the difficulty tier a run is played at" and Zone as
   "selected before a run". If a future patch makes either change mid-run, this
   rule splits one run across several directories, which is loud in `runs` rather
   than silent — the counts will not add up.

4. **Polling, at 2 seconds.** `fswatch` is not installed on this machine and the
   spec forbids runtime dependencies. Two seconds is far below the length of a
   wave, and a poll that lands mid-write reads invalid JSON, which is reported
   and retried rather than treated as an error.

## Consequences

- `runs/` grows by ~120 KB per captured change — the first real run measured 6.6
  MB across 56 snapshots, six times the megabyte estimated here before one had
  been taken. The file grows as the build does: 48 KB at wave 1, 130 KB by wave
  19. Still acceptable, and still the price of not having to guess now what a
  review will want later, but a run is a megabyte only in its opening waves.
- Snapshots are only as readable as the hashes in them. Until `gamedata` lands,
  `runs <run-id>` returns states whose stat keys are integers.
- Settled on 2026-08-30 by `20260830T193810Z-character_crazy`, committed here: a
  full run captured start to finish by the watcher, waves 1 through 19 at ~3
  snapshots each, closed by the watcher itself when the game cleared the file.
  The five field names `_state.py` reads are confirmed against real data, and
  the field inventory above no longer rests on a single wave-2 reading.
- That run is the fixture the tests never had. They remain hand-written, which
  keeps them legible; the committed run is what a change to `_state.py` should
  now be checked against.
- Across all 56 snapshots the only file containing the player's Steam ID is
  `runs/.watcher/last_session.json`, which records the live-state path and is
  gitignored. Snapshots are safe to commit, as this ADR assumed from one reading.
