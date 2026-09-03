<h1 align="center">
  <img src="https://static.wikia.nocookie.net/brotato/images/8/8a/Wisdom.png/revision/latest?cb=20220622224054" alt="Wisdom" width="56" valign="middle" />
  &nbsp;Get JPot to coach your Brotato run
</h1>

A teaching workspace for learning [Brotato](https://store.steampowered.com/app/1942280/Brotato/)
deeply enough to reach Danger 5 solo on every archetype — backed by tooling that reads what
the game already writes to disk.

<p align="center">
  <img src="https://www.goclecd.fr/wp-content/uploads/Pixel-Sundays-Brotato-Feature.webp" alt="Brotato" width="100%" />
</p>

The tooling reads three things and invents none of them:

- **Save data** — what the player has cleared, what has killed them, what they buy.
- **Game data** — character modifiers, weapon stats and item effects, extracted from the
  installed game.
- **Snapshots** — the live state of a run in progress, copied every time it changes, so a run
  outlives the game erasing it on death.

Everything it prints is JSON on stdout. Nothing asks for attention while a run is in
progress: playing is hacking time.

## Requirements

- macOS, with Brotato installed via Steam. The save and install paths are macOS-only, per
  `MISSION.md`.
- Python 3.14+ and [uv](https://docs.astral.sh/uv/).

## Getting started

```sh
uv sync
cp .env.example .env       # optional; a normal install needs nothing set
uv run brotato --help
```

`brotato` and `brotato-coaching` are the same command.

## The subcommands

```sh
uv run brotato progress                 # your save: progress per character, deaths, purchases, totals
uv run brotato extract                  # game data -> data/ (gitignored: it is the publisher's content)
uv run brotato watch                    # capture snapshots until you stop it (Ctrl-C)
uv run brotato runs                     # list every captured run
uv run brotato runs <run-id>            # one run's snapshots, read back whole
uv run brotato review                   # the latest dead run, read back: build, curve, death causes
uv run brotato records                  # every reviewed run, and the patterns that recur
uv run brotato prep                     # the derivation drill, on a character chosen from your save
```

`watch` also runs detached, which is how you use it around an actual session:

```sh
uv run brotato watch --start            # start the watcher in the background and return
uv run brotato watch --status           # is it running, and what has it caught?
uv run brotato watch --stop             # stop it, and report the session it just finished
uv run brotato watch --once             # make a single capture decision and exit
```

`review` reads a dead run back, and it has an order it will not let you break:

```sh
uv run brotato review                                        # the briefing: what happened, nothing concluded
uv run brotato review --hypothesis "I never scaled damage"   # your read, on record first
uv run brotato review --diagnosis "..." --change "..."       # refused until a hypothesis is recorded
```

The refusal is the feature: seeing a diagnosis first would let you quietly revise your read,
and the gap between the two is where the learning is. `/brotato-review` drives this loop.

`prep` is the drill `/brotato-prep` runs. It shows a character's modifiers and starting
weapon with every trace of its name removed, takes four committed predictions, and only
then names it and scores each one:

```sh
uv run brotato prep character_mage      # or drill a character you name
uv run brotato prep --commit <drill-id> --primary-stat ... --secondary-stat ... \
                    --weapon-class ... --weakest-wave ...
uv run brotato prep --reveal <drill-id> # refused until all four are committed
uv run brotato prep --settle <drill-id> --actual-wave 13
uv run brotato prep --history           # prediction hit rate, per dimension, over time
```

A subcommand exits non-zero only when it could not do what it was asked. "No run in
progress", "nothing captured", "no watcher running" are JSON on stdout and an exit code of
zero — reporting them *is* the job.

**Ids read as names once you have extracted.** `deaths` and `items_bought` are keyed in the
save by the integer hashes the game uses internally; resolving them is the join between the
save and `data/`. Before a first `extract` they come out as digits, which is a report worth
having rather than an error.

## Configuration

Everything is discovered by default. `.env` (gitignored) exists for the cases where discovery
needs help; see `.env.example` for the full list. The one worth knowing:

| Variable | What it is for |
| --- | --- |
| `STEAM_ID` | Names your save directory. Only needed if globbing finds more than one save. |
| `BROTATO_INSTALL_DIR` | Only if Steam does not list the library holding the game. |

**Your Steam ID never enters this repo.** It names a directory, `.env` is gitignored, and the
error messages deliberately do not echo it back.

## What lives where

| Path | What it holds |
| --- | --- |
| `MISSION.md` | The reason for learning, and the honest baseline it is measured against. |
| `CONTEXT.md` | The domain glossary — the game's vocabulary and the workspace's, one meaning each. |
| `NOTES.md` | Standing preferences, and JPot's recorded heuristics. |
| `RESOURCES.md` | The sources every cited claim names, and the workspace's patch stamp. |
| `docs/adr/` | Decisions, with the context that produced them. |
| `docs/research/` | Research passes: stat mechanics, shop economy, wave scaling, weapon classes. |
| `runs/` | Captured runs. Committed — they are the player's own data. |
| `records/` | Run records: one per reviewed run, in a fixed schema. Committed. |
| `drills/` | Prep drills and their verdicts. Committed, for the same reason. |
| `learning-records/` | Written only when the player's model of the game actually changed. |
| `lessons/`, `assets/` | Teaching artefacts and their styling. |
| `reference/` | Reference docs: one printable page per concept. Every number in one is re-derived from the installed game by the test suite. |
| `src/brotato_coaching/` | The tooling. Its README documents the package rules. |
| `data/` | Extracted game data. Gitignored, regenerated by `extract`. |

## Development

```sh
uv run pytest                              # the suite
uv run tach check                          # every import goes through a public surface
uv run python scripts/check_cycles.py      # no cycles in the real import graph
```

Package boundaries are machine-checked: a name is importable from outside its package only if
every segment of its path starts with something other than `_`. Read
`src/brotato_coaching/README.md` before adding a package or importing across one.

Agents working in this repo start from `CLAUDE.md`.
