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

4. **Polling, at 2 seconds.** `fswatch` is not installed on this machine and the
   spec forbids runtime dependencies. Two seconds is far below the length of a
   wave, and a poll that lands mid-write reads invalid JSON, which is reported
   and retried rather than treated as an error.

## Consequences

- `runs/` grows by ~25 KB per captured change. A 20-wave run is on the order of a
  megabyte. Acceptable, and the price of not having to guess now what a review
  will want later.
- Snapshots are only as readable as the hashes in them. Until `gamedata` lands,
  `runs <run-id>` returns states whose stat keys are integers.
- Still unproven: a full run captured start to finish by the watcher. That needs
  one play session with `watch --start` running, which no tooling can do for us.
