# 001 — On a character with a free guaranteed item, that item is the engine; the shop stats I buy are only the multiplier

**Date:** 2026-09-02
**From:** run `20260902T160446Z-character_fisherman` (danger 3, zone 1, wave 20 of 20)

## What I believed

Asked what carried the run, I said: "it was impressive to have no speed and high
regeneration; melee damage first half, attack speed second half; a bit of
armor/dodge." I read the run as a story about the stats I chose in the shop —
the two-phase damage build, the regeneration, the speed I gave up for it.

## What the data said

The two-phase damage build was real. Melee damage climbed 2 → 45 by wave 12 with
attack speed still at 0; from wave 10 attack speed took over, 4 → 24 → 49 → 99,
while melee flattened at 45–51 for eight waves. Armor stayed at 6–9 and dodge at
1–16 all run, so "a bit of armor/dodge" was accurate too.

The rest did not hold. Speed was 0 through wave 10 — neutral, not sacrificed —
and only fell to −22 at wave 13. Regeneration was **0 until wave 14**, first
appeared at +2 on wave 15, and reached 11 only on wave 20. It was absent for the
two waves that actually hurt: I entered wave 10 on 11 health and wave 13 on 17.

What carried the run was Bait. I finished holding 49 of them. Bait gives +8%
damage each (`data/items.json`), so 49 × 8 = **392 of my 408 percent damage**.
Fisherman buys Bait at −100% price and is guaranteed one in every shop
(`data/characters.json`), so every one of those was free. Fisherman also grants
+2 harvesting per Bait, which is 98 of my 132 harvesting — the economy came from
the same item.

Bait's cost lands on the same stack: each one adds an enemy to the next wave.
That is what the mid-game health dips were. With attack speed still at 4 on wave
10 and 24 on wave 12, the enemy count the Bait stack was adding outran what I
could clear. From wave 14, at 49 attack speed, damage per wave went vertical:
30k → 46k → 57k → 84k → 93k → 172k.

## What I now believe

When a character is handed one item for free and guaranteed, I should read that
item's numbers **first** and treat everything I buy afterwards as a multiplier on
it, not as the reason the run worked. % Damage is multiplicative on base damage
(`docs/research/stat-mechanics.md`), so a free +392% is a base I cannot match by
shopping — and the stat that converts it into cleared waves is the one the free
item does not supply.

The corollary, which the next Fisherman run should test: with percent damage
already free, the wave 8–10 shops should buy attack speed ahead of damage, and
reaching 50 attack speed by wave 10 should remove the mid-game health dips. If
those dips happen anyway at 50 attack speed, this record is wrong about the
cause and should be revised.
