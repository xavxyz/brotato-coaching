# Run records

One file per reviewed run, written by `brotato review` and read back by
`brotato records`. Nothing in here is edited by hand.

```
20260830T193810Z-character_crazy.json
```

The name is the run id, so a record sits next to the run it is about in
`runs/`, and records sort by when the run started.

## The schema

Fixed, so that "you have died this way four times" is a query rather than a
memory, and so that a run reviewed today is still readable once the player's
model has improved.

| Field | What it holds |
| --- | --- |
| `schema_version` | The shape of this file. Bumped when a field changes meaning. |
| `run_id`, `character`, `danger`, `zone` | Which run this was. |
| `patch` | The game version `data/` was extracted from, or `null` if it was never extracted. |
| `waves` | `reached` and `of` — where the run stopped, out of how many. |
| `weapons`, `key_items` | The build as it ended: weapons by id and tier, items the player stacked. |
| `final_stats` | The reported stats, read back out of the game's hashed `effects` map. |
| `death_causes` | The save's lifetime death histogram at the time of the review. |
| `hypothesis` | The player's one-line read, and when it was written. |
| `diagnosis` | What the data said, written only after the hypothesis. |
| `change` | The one change to try next time. |
| `revisions` | Previous reviews of this run, kept when it is re-diagnosed. |

`hypothesis`, `diagnosis` and `change` each carry a `recorded_at`, which is what
makes the ordering checkable after the fact rather than merely claimed.

These are the player's own writing about the player's own data, and they commit.
See `docs/adr/0004-the-hypothesis-is-recorded-before-the-diagnosis.md`.
