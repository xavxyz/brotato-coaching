# Research: stat mechanics and damage math

Researched 2026-08-30. Install is **Brotato 1.1.12.0.beta-3** (see `RESOURCES.md`);
sources name their own patches, some newer. Source ids `STAT-S1`–`STAT-S20` and
open questions `STAT-Q1`–`STAT-Q8` are defined in `RESOURCES.md`; read the access notes there
before trusting a constant.

These are *interpretive* findings — how the numbers combine. Exact values belong in extracted game
data (ticket #6), not here.

## Damage types and how they combine

- **Flat damage stats (Melee / Ranged / Elemental Damage) are additive into the weapon's base
  damage, gated by a per-weapon scaling coefficient.** Tooltip: "Modifies the base attack damage of
  weapons, **if their damage scales with** Melee/Ranged/Elemental Damage." [STAT-S1]
- **The scaling coefficient is a literal multiplier on the stat.** "If a weapon has 80% [Melee],
  every Melee Damage stat gives extra 0.8 more damage to that weapon." Worked example, Tier 4 Knife
  `20(80% Melee)` at 30 Melee Damage → `20 + (30 × 0.8) = 44`. [STAT-S2]
- **A weapon only scales with the stats printed on it — the melee/ranged classification is cosmetic
  for scaling purposes.** The scaling legend lists Melee, Ranged, Elemental, Armor, Engineering,
  Range, Attack Speed and Level as possible scaling stats. [STAT-S2, STAT-S19]
- **% Damage is a separate multiplicative layer on top of the flat-scaled total.** "Increases all
  damage dealt by 1% per point in Damage." [STAT-S1] STAT-S2's worked example ends "(assuming Damage stat is
  +0%)", implying % Damage applies after the base + flat-scaling sum. [STAT-S1, STAT-S2]
- **% Damage and % Explosion Damage stack additively with each other** — Dynamite plus +30% Damage
  gives explosive weapons +45% total. [STAT-S3]
- **% Damage does not apply to Engineering structures.** [STAT-S1, STAT-S3, STAT-S8, STAT-S9, STAT-S10]
- **% Damage does apply to item-sourced damage** such as Baby Elephant and Cyberball. [STAT-S3]
- **Damage floors:** negative % Damage reduces output (−60% → 40% damage) but minimum damage from
  any weapon or effect is always 1. [STAT-S1, STAT-S3, STAT-S13]
- **Elemental Damage drives burn.** `5x8 +(100% Elemental)` = 8 damage/second for 5 seconds, scaling
  with Elemental Damage **and** % Damage. [STAT-S13, STAT-S14]
- **Patch 1.1.0.0 changed rounding:** bonus % damage from items and effects is now rounded rather
  than rounded down. [STAT-S16]

## Attack Speed

- **Stated behaviour: +100% Attack Speed halves the weapon cooldown.** [STAT-S1, STAT-S4]
- **Attack Speed does not apply to structures**, nor to Cyberball, Baby with a Beard, Rip and Tear.
  [STAT-S1, STAT-S4]
- **Displayed ("cooldown text") formulas**, datamined and consistent across two independent
  sources [STAT-S5, STAT-S6] — note these describe *animation and recoil overhead*, which is where the
  diminishing returns and the Range penalty live:
  - Ranged: `(cooldown / 60) + (recoil_duration * 2)`
  - Melee: `(cooldown / 60) + recoil_duration + (atk_duration / 2) + back_duration`, where
    - `back_duration = 0.2 / (1 + stat_attack_speed * 3)`
    - `atk_duration  = max(0.01, 0.2 - stat_attack_speed / 10.0) + range_factor * 0.15`
    - `range_factor  = max(0.0, (max_range + stat_range / 2) / clamp(70.0 * (1 + stat_attack_speed / 3), 70.0, 120.0))`
    - `stat_attack_speed` is a fraction (1.0 = +100%). `recoil_duration` is 0.1 for nearly
      everything; exceptions include Crossbow 0.15, Flamethrower 0.02, Laser Gun 0.2, Minigun 0.02,
      Nuclear Launcher 0.142, Obliterator 0.2, Rocket Launcher 0.142, Shredder 0.15, Slingshot 0.15,
      SMG 0.05, Sniper Gun 0.2. [STAT-S5]
  - **Caveat:** none of these show Attack Speed applied to the `cooldown / 60` term itself. The
    multiplier on the underlying cooldown timer lives in `weapon_service.gd` and is unpublished —
    see open question STAT-Q2 in `RESOURCES.md`.
- **Diminishing returns are real and weapon-dependent, not one global curve.** Fast melee (Fist T4,
  Circular Saw T4) and fast ranged (SMG T4, Flamethrower T4, Minigun T3/T4) have diminishing returns
  from 0% Attack Speed onward; fast ranged is affected more. "The diminishing returns start out slow
  and become more prominent the more attack speed you have." [STAT-S4] This matches the melee formula:
  `atk_duration` floors at 0.01 and `back_duration` is asymptotic to 0.
- **Negative Attack Speed uses a different, much gentler formula.** At −100% AS a Tier 4 Fist
  attacks only 14% less often; a Tier 4 Nuclear Launcher 46% less often. [STAT-S4]
- **Range slows melee attacks:** +100 Range costs roughly 3–10% attack speed depending on weapon.
  [STAT-S4, STAT-S12] The `clamp(70 * (1 + AS/3), 70, 120)` denominator means Attack Speed partially offsets
  the Range penalty, saturating at +200% AS. [STAT-S5, STAT-S6]
- **Ball and Chain imposes a hard 0.75s minimum cooldown**, excluding melee animation time. [STAT-S4]
- Tooltips round displayed cooldown down to 0.01s; the game does not round internally. [STAT-S4]

## Crit Chance

- **Cap 100%**; floor 0% total — negative Crit Chance subtracts from the weapon's base. [STAT-S1, STAT-S11]
- **There is no global crit-damage stat.** The multiplier is a per-weapon property. Most weapons:
  3% base chance, ×2 damage. Knife reaches ×4 at max tier; Fist is ×1.5. The weapons table's crit
  column reads "Multiplier (Chance)", e.g. `x2.5 (20%)`. [STAT-S2, STAT-S11, STAT-S16]
- **Multipliers vary by tier** on some weapons — 1.1.0.0 changed one from `x2` to
  `x2/x2.15/x2.3/x2.5`. [STAT-S16]
- **Can crit:** all weapon hits and spawned projectiles; each pierce and each bounce independently;
  all explosions; item projectiles like Alien Eyes and Baby with a Beard. [STAT-S11]
- **Cannot crit:** structures (unless you have Pile of Books); burn; the Lucky and Lich abilities;
  randomly-targeted item damage (Baby Elephant, Cyberball, Riposte). [STAT-S11, STAT-S14]
- Precise class gives +3% crit per weapon up to +15% at six. Hunter and Diver amplify crit
  modifications by 25%. [STAT-S11]

## Engineering

- **Engineering is the only primary stat that affects structures.** "Turrets and Landmines do not
  scale with Primary Stats except Engineering, but do scale with Secondary Stats and other effects
  provided by Items." [STAT-S1, STAT-S8, STAT-S9, STAT-S10]
- **Same additive base + coefficient pattern as weapons.** The Turret item page reads
  **`10 + (80% Engineering)`** damage every 0.73s. [STAT-S10]
- Reported coefficients [STAT-S8] — only the Turret was confirmed against raw page source [STAT-S10]:
  Turret `10 (+80%)`, Landmines `10 (+100%)`, Laser Turret `20 (+125%)`, Explosive Turret
  `25 (+150%)`, Incendiary Turret `8×5 (+33%)`, Medical Turret `3 healing (+5%)`.
- **Weapons that scale with Engineering:** Brick, Chain Gun, Chainsaw, DEX-troyer, Drill, Particle
  Accelerator, Plank, Pruner, Screwdriver, War Hammer, Wrench. [STAT-S8]
- **Structures:** Garden, Landmines, Turret, Incendiary Turret, Medical Turret, Laser Turret, Tyler,
  Explosive Turret, Wandering Bot. Max 100 on the map at once. [STAT-S9]
- **Secondary stats do apply to structures:** piercing, bouncing, knockback, slow, explosion
  damage/size, burn, burn spread. [STAT-S9]
- **Structure Attack Speed is a separate secondary stat.** Clockwork Wasp +10%; Improved Tools
  converts 50% of your Attack Speed into Structure Attack Speed. [STAT-S8, STAT-S9]
- Base turret fire rates: Turret 0.73s, Incendiary 0.28s, Laser 0.87s, Explosive 0.87s, Medical
  2.2s, Tyler 2.2s — each shot randomised to 70–130% of that, so these are averages. [STAT-S8, STAT-S9]
- 1.1.0.0 removed a hidden ~3 shots/sec structure cap. [STAT-S16]
- Incendiary Turret's burn scales with Engineering and **not** % Damage. [STAT-S14]

## Other stats that bear on damage math

- **Range:** ranged weapons get `weapon range + Range`; melee get `weapon range + Range/2`. Minimum
  25 range, no cap. Higher Range slightly increases melee cooldown. [STAT-S1, STAT-S12, STAT-S5, STAT-S6]
- **Luck does not affect crit or damage directly.** It increases consumable drop count, loot-crate
  conversion, and the tier of items/upgrades in crates, shop and level-ups:
  `Enemy_Box_Drop_Chance * (100% + Luck) / (1 + Box_Spawned_This_Wave)`. Rarity gains saturate;
  ~290 Luck to max out Legendary offers. [STAT-S15]
- **Life Steal:** capped at one trigger per 0.1s = max 10 HP/s. Character Life Steal is added to
  each weapon individually. Burn cannot life steal. [STAT-S1, STAT-S14]
- **Armor:** each point means it takes 6.66% more damage to kill you. No cap. [STAT-S1]
- **Dodge cap 60%** (70% Cryptid, 90% Ghost). [STAT-S1]
- **Curse (Abyssal Terrors):** cursed enemies get +25% Damage, +15% Speed, +150% HP +2% per Curse
  point, and drop 33% more materials. Caps: 50% cursed-enemy chance, 15% cursed-shop-item chance,
  HP scaling maxes at 300 Curse. Cannot be negative. [STAT-S1]
- **Heavy class:** +5/10/15/20/25% Damage at 2/3/4/5/6 Heavy weapons. [STAT-S3]
- 1.1.0.0: effects to enemy damage and health from all sources are now applied as a multiplier
  rather than additively. [STAT-S16]

## What this topic still doesn't know

Open questions STAT-Q1–STAT-Q8 in `RESOURCES.md`. The big ones: the actual Attack Speed cooldown expression,
whether a 12-attacks/second cap exists, and every rounding rule.
