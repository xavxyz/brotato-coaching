# ADR-0002: Save ids are Godot string hashes of `my_id`

**Status:** accepted
**Date:** 2026-08-31
**Context:** `gamedata`, `savefile`, `progress`

## Context

The save writes entities as 32-bit integers. `killed_by_enemies` is
`{"1737060255": 5, ...}`, `items_bought` is keyed the same way, and
`characters_unlocked` is a bare list of them. ADR-0001 recorded the same
integers appearing throughout live run state. Ticket #8 listed the algorithm
behind them as unidentified, with brute-forcing a lookup table as the fallback.

No brute force was needed. Godot 3's `String.hash()` is a djb2 variant — seed
5381, `hash = hash * 33 + byte`, truncated to 32 bits — and applying it to a
character's `my_id` reproduces the save's integers on the first attempt:

| string             | hash        | in the save                    |
| ------------------ | ----------- | ------------------------------ |
| `character_mage`   | 904328779   | present in `characters_unlocked` |
| `character_crazy`  | 4061791930  | present in `characters_unlocked` |
| `lamprey`          | 1737060255  | `killed_by_enemies`, 5 deaths  |
| `character_glutton`| 134690238   | `items_bought`, 45 purchases   |

What is hashed is the `my_id` property of the resource, and nothing else. Both
alternatives were checked against the same save and neither matched: the
`res://` resource path (`res://items/characters/character_mage.tres` hashes to
3110696249, which appears nowhere) and the translation key (`CHARACTER_MAGE`,
2497878187, likewise absent).

Two properties of the id space, measured across both containers:

- **945 resources carry a `my_id`.** Ids are near enough unique: one is reused,
  `evil_mob`, which the DLC ships a second codex resource for. Two resources,
  one name — which is exactly what a name book wants.
- **No two different ids hash alike.** A hash therefore names exactly one
  entity, and a lookup table needs no tie-breaking by kind.

Resolving the committed real save against a full extraction of 1.1.12.0.beta-3
names **15 of 15** death causes and **260 of 260** purchases. Nothing is left
over, which is the evidence that this is the algorithm rather than one that
merely agrees often.

Two facts the join has to live with. First, `items_bought` is not only items:
`character_glutton` and `weapon_harpoon_gun_2` are both in it, because the shop
sells all three kinds. A name book that covered only `items.json` would resolve
most of the histogram and quietly miss the rest. Second, the enemies that kill
the player were not extracted at all before this ticket — they are described by
`ItemEnemy.gd` (83 codex entries) and `enemy_data.gd` (21 bosses and elites),
whose id sets are disjoint.

## Decision

1. **`gamedata` owns the hash.** `godot_hash` is the algorithm; `read_names`
   builds a `NameBook` from an extraction and `name_for` reads an integer back
   into an id. `savefile` gains no dependency on `gamedata` — it takes an
   optional function from id to name, and the CLI is what hands it one.

2. **No lookup table is committed.** The hash is a one-line function and the
   ids come from `data/`, which is gitignored publisher content. A table would
   be that content, copied, and stale after every patch.

3. **`extract` writes `enemies.json`.** Both scripts feed it, since a death
   histogram is unreadable without the bosses and elites.

4. **A name is an id, not English.** `lamprey`, not "Lamprey": the game keeps
   its display names in binary `.translation` resources, and the catalogues
   already record translation keys rather than decoding them. Resolving those
   is a separate concern, and the ids read perfectly well as names.

5. **Unresolved stays raw.** An id the extraction cannot name is reported as its
   digits. A player who has never run `extract` gets the same report they got
   before, plus a note on stderr saying why.

## Consequences

- `brotato progress` reads as a diagnosis: what kills the player is `lamprey`
  ×5, not `1737060255` ×5.
- The same book resolves live run state, whose `effects`, `active_sets` and
  `tracked_item_effects` are keyed identically (ADR-0001). Nothing here is
  specific to the save.
- A patch that renames an entity changes its hash. Old saves then hold ids
  nothing can name; they degrade to digits, which is loud enough to notice and
  cheap enough to ignore.
- The pinned values above are asserted in the test suite, and the full
  15-of-15 / 260-of-260 resolution is asserted against a live extraction — a
  test that is skipped where the game is not installed.
