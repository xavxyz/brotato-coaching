# Prep drills

One JSON file per drill, written by `brotato-coaching prep` and read back by
`brotato-coaching prep --history`. Nothing in here is edited by hand.

```
20260831T115503Z-a5f8.json
```

The name is a timestamp and a short suffix, and deliberately **not** the
character — unlike a run directory, which is named after the character it
captured. A drill withholds the character's name until four predictions are
committed, and a filename sitting in a listing next to the terminal the drill is
being taken in would answer the question.

Each file holds both halves of the drill: the card the player was shown, and the
truth they were scored against. The truth is written at the moment the drill
opens, so the answers cannot move if the game is patched between opening a drill
and revealing it, and so a reveal needs no game data at all.

These are the player's own data and are committed. The hit rate they add up to
is the number `MISSION.md` says this workspace is judged on.
