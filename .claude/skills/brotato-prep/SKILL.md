---
name: brotato-prep
description: The derivation drill, run before playing an unfamiliar Brotato character. Shows the character's extracted modifiers and starting weapon with its name withheld, takes four committed predictions, then reveals and scores each. Use when the player says "/brotato-prep", asks to prep or drill a character, or asks which character to play next.
---

# `/brotato-prep`: the derivation drill

The player is learning to derive a plan for a character they have never played, instead
of recalling one. **Everything in this skill exists to stop them recalling.** A drill they
hedged their way through has taught them nothing, and a hint from you before they commit
has taught them less than nothing.

You are running a drill, not coaching a run. Coaching starts at step 5, and not before.

## The tool does the withholding, not you

`brotato prep` strips the character's name out of the card before you ever see it — the
id, the translation key, the resource path, and the character's own name struck out of
any weapon or effect that carries it. The stats the game says the character wants are
never on the card either, because they are the answer to two of the four questions.

So you cannot leak the identity by accident. You **can** leak it in three ways, and all
three are on you:

1. **Reading the drill file.** `drills/<drill-id>.json` holds the truth as well as the
   card, because a reveal has to work after a patch. **Never open it.** `--reveal` is the
   only way to see what is in it, and it is refused until the four predictions are in.
   The same goes for `data/characters.json`, which would let you look the character up.
2. **Deducing it and saying so.** If you recognise the character from its modifiers, say
   nothing about it until step 5.
3. **Hinting.** See step 3.

## Before you start

Every step shells out to the CLI. Never read `data/`, `drills/`, `runs/` or the save file
yourself, and never compute a stat or a set bonus by hand — the numbers come from the
installed game or they are not used.

```sh
uv run brotato prep --history      # is there anything set up at all?
```

If any command reports that there is no extracted game data, run `uv run brotato extract`
and carry on. It takes seconds.

## Step 1 — open the drill

```sh
uv run brotato prep                        # let it propose a character
uv run brotato prep character_mage         # or drill a named one
```

With no argument it reads the save and proposes a character the player has never cleared,
from an archetype whose reasoning they have never had to do. The `proposal`
block gives counts and no stat names, on purpose; you may repeat it verbatim.

Note the `drill_id`. Every later step needs it.

## Step 2 — present the card

Show the player, in your own words and in a readable table rather than as JSON:

- every **modifier**, with its sign and value
- the **starting weapon**: its class or classes, its scaling stats, damage and cooldown
- the **starting pool** and how it breaks down between melee and ranged
- the **zone** and the **patch stamp**

Then ask for the four predictions, in one message, and stop.

## Step 3 — take four committed predictions

Ask all four at once. Do not accept the drill moving on until you have all four.

1. **Primary stat** — the stat that matters most for this character.
2. **Secondary stat** — the stat that matters next. It must be a different stat.
3. **Weapon class** — one of the game's 17 classes (Blade, Blunt, Elemental, Ethereal,
   Explosive, Gun, Heavy, Legendary, Medical, Medieval, Musical, Naval, Precise,
   Primitive, Support, Tool, Unarmed). Not "melee" or "ranged" — those are how a weapon
   is delivered, not what class it is. See `docs/research/weapon-classes.md`.
4. **Weakest wave** — the wave number they expect this build to be at its weakest.

**A hedge is not a prediction.** "Elemental damage, or maybe attack speed" is two
predictions and
teaches nothing about either. If they hedge, say so plainly and ask for the one they would
put money on. Same for "I don't know": ask for the one they would commit to anyway,
because a wrong committed prediction is scored and a refusal is not.

**Do not help.** No hints, no narrowing, no "well, look at the cooldown". If they ask what
you would predict, tell them that predicting for them is the one thing this drill cannot
survive, and ask again.

When you have all four:

```sh
uv run brotato prep --commit <drill-id> \
  --primary-stat "elemental damage" \
  --secondary-stat "attack speed" \
  --weapon-class "elemental" \
  --weakest-wave 12
```

Spelling and capitalisation do not matter; `stat_elemental_damage`, `Elemental Damage` and
`elemental damage` all score the same. The commit is final — the CLI refuses a second one,
and that refusal is the point.

## Step 4 — reveal

```sh
uv run brotato prep --reveal <drill-id>
```

Now name the character and report each verdict on its own:

- `hit` / `miss` — scored against what the game itself declares.
- `unscorable` — the game declares nothing for this dimension, so the player was not wrong.
  Say so; do not let it read as a miss.
- `pending` — the wave prediction, which no game file can settle. It waits for a run.

## Step 5 — teach, once, and only now

This is the part that transfers. For each dimension, walk the derivation the player could
have made from the card alone: which modifier pointed at the stat, why the starting
weapon's scaling stat and class point where they do, what the shape of the starting pool
said. Lean on `docs/research/` — stat mechanics, shop economy, wave scaling, weapon
classes — and cite what you use. Where `NOTES.md` records a JPot heuristic that bears on
it, quote it and name the disagreement if the data disagrees; never average the two.

**Spend the most words on the misses.** A hit needs a sentence confirming the reasoning
was the right reasoning and not a lucky recall. A miss is the whole reason the drill ran.

Then finish with:

```sh
uv run brotato prep --history
```

Report the hit rate per dimension. This is the number `MISSION.md` says the workspace is
judged on — say plainly whether it is moving.

## After the run

The wave prediction is settled once, against a run that actually happened:

```sh
uv run brotato prep --settle <drill-id> --actual-wave 13
```

`uv run brotato runs` lists captured runs if the wave needs looking up. Within one wave
counts as a hit — the prediction is about where a build gives out, not which wave.
