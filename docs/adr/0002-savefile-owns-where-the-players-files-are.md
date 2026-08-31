# ADR-0002: `savefile` owns where the player's files are

**Status:** accepted
**Date:** 2026-08-31
**Context:** `savefile`, `runlog`, `watch`, `progress`

## Context

Two modules answered "where is this player's Brotato directory". `savefile`'s
`_discovery` read `BROTATO_APPLICATION_SUPPORT`, searched for the nearest `.env`
upwards from the working directory, preferred a digit-named directory and raised
when nothing was found. The app tier's `_paths.live_run_state_path` hardcoded the
save root, read only the repo-root `.env`, broke ties by modification time, and
returned a path whether or not anything was there.

They disagreed on every one of those points, and the disagreement was a live
defect: `.env.example` documented `BROTATO_APPLICATION_SUPPORT` as the way to
move the save root, `progress` honoured it, and `watch` silently read the real
save instead. `_paths.py` had conceded the point in its own docstring from the
start — "belongs to `savefile` once that package exists" — and that package
existed.

Making the two agree would have been the smaller change and the worse one. Two
implementations that agree are a silent duplicate; the next setting added to one
diverges again, and nothing fails until a user notices.

## Decision

1. **`savefile` owns discovery, and exposes it.** `save_directory()` is public
   because the question is not only this package's: the live run state sits in
   the same directory. `save_file()` derives the save from it, and
   `read_progress(path)` is handed the file rather than going to find it.

2. **The directory is discovered; the file is derived.** Not the other way
   round. "The parent of the save we found" would make a save file the price of
   admission for anyone who wants the directory, and `runlog` wants exactly that
   and never reads a save — a player mid-run on a fresh install has a live run
   state and no save yet.

3. **`runlog` composes its own filename.** It is handed the save directory and
   puts `run_v3_0.json` on the end itself, the same rule that keeps
   `save_v3_0.json` inside `savefile`: a schema version belongs to whoever's
   file it is. The directory is a *parameter of the two methods that read the
   game* — `capture_once` and `watch` — and not of `RunLog` itself, so there is
   no optional field and no unreachable "no save directory" branch. Reviewing a
   captured run must not need a Brotato install, and neither must inspecting or
   stopping a watcher: `runs`, `snapshots`, `start_watcher`, `stop_watcher` and
   `watcher_status` answer from `runs/` alone, so `watch --status` and
   `watch --stop` keep working when the save root moves or is unmounted under a
   running watcher. `__main__` resolves the directory lazily, for `--once`,
   `--start` and the bare watch loop only, and "no-save-directory" is therefore
   spelled exactly once, where it is reported.

4. **A Steam save directory is one named by exactly 17 digits.** `str.isdigit`
   was a cheap proxy that was only ever safe because holding a save was the real
   evidence; once the name *is* the evidence it would admit `007`. The pattern
   is `[0-9]{17}` rather than `\d{17}`, because `\d` matches every Unicode digit
   and a directory name is not free text.

5. **Two failures, not one.** `SaveDirectoryUnavailable` for "no Brotato
   directory for this player", `SaveUnavailable` for "that directory holds no
   save". The second subclasses the first's parent so `progress` keeps one
   catch; the split exists for `watch`, which needs the directory and has no
   business caring about a save. `__main__` reports a missing directory as a
   zero-exit JSON state, per the rule it already states about itself: a state
   worth reporting is not a crash.

6. **`BROTATO_RUN_STATE_PATH` is retired.** Once
   `BROTATO_APPLICATION_SUPPORT` works for every subcommand it covers the real
   use case. Its only remaining user was the test suite pointing at a single
   file — testing a path it was handed rather than exercising discovery, which
   is the thing `_discovery` exists to avoid.

## Consequences

- **The tool is Steam-only, by decision.** `_prefer_steam_saves` is gone rather
  than restated: the empty `user/` directory Brotato writes beside the Steam one
  is excluded because it is not 17 digits, not because it loses a tie-break. A
  save that exists *only* in `user/` used to be readable and now is not. This is
  deliberate — the whole workspace is built on Steam saves — and it is the one
  behaviour this ADR removes rather than moves.
- **"Two saves, which is yours?" now means two Steam accounts.** It stopped
  being the answer on every normal install, so the error can be believed.
- **Two spellings of "Steam-ID-shaped" are correct.** `_discovery`'s asks whether
  one directory name is a Steam ID; `tests/conftest.py`'s `STEAM_ID_SHAPED` is a
  privacy scrubber hunting a 17-digit run anywhere inside a file, and needs the
  digit-boundary anchors that #22 gave it. Same shape, different questions, so
  the "one definition" rule from #22 does not reach across this boundary.
- **The regression test is over consumers, not over the function.** The defect
  was a second consumer that never asked; a unit test on discovery would have
  been green throughout. `tests/test_save_discovery.py` parameterises over every
  subcommand that touches the player's files, so a third one must opt in.
- **`runlog` still knows two app-tier variable names.** `_environment()` sets
  `BROTATO_RUNS_DIR` and `BROTATO_POLL_INTERVAL` so a detached watcher can be
  relaunched. It no longer passes the live state path — the child inherits the
  environment and working directory and reaches the same directory by running
  the same discovery — but the remaining two travel as string literals through a
  subprocess, where `tach` cannot see them. Eliminating that means moving process
  launch to the app tier, which is left for its own change.
