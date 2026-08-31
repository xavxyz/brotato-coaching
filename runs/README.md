# Captured runs

One directory per run, written by `brotato-coaching watch` and read back by
`brotato-coaching runs`. Nothing in here is edited by hand.

```
20260830T200512Z-character_crazy/
  run.json                 what the run was, and what was captured when
  snapshots/0001.json      the live run state, copied whole
  snapshots/0002.json
```

A snapshot is a byte-for-byte copy of `run_v3_0.json` at the moment it changed,
so a run survives the game erasing that file on death. See
`docs/adr/0001-snapshot-live-run-state-whole.md` for what is in one and why it is
kept whole.

These are the player's own data and are committed. `.watcher/`, which holds the
watcher's pid and session counters, is not.

What a review *concludes* about a run is not kept here: it goes to `records/`,
one file per reviewed run, so that nothing outside `runlog` writes under `runs/`.
