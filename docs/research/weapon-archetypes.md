# Research: weapon classes and their scaling

Researched 2026-08-30 against installed **Brotato v1.1.15.4**. Source ids `S1`–`S18` in this file
are `WEAP-S1`–`WEAP-S18` in `RESOURCES.md`; read the access notes there before trusting a constant.

Note on vocabulary: the game calls these **weapon classes** or **sets**. `CONTEXT.md` reserves
**archetype** for a family of *characters*, so this file says "class" throughout.

## The single most important structural fact

**A class's set bonus and the stat its weapons scale with are different things, and scaling is a
per-weapon property, not a class property.** Tool grants +Engineering *and* its weapons scale with
Engineering — but Blunt grants Armor and HP while its weapons still scale with Melee Damage, and
Precise grants Crit Chance while its members scale with Melee, Ranged or Elemental Damage depending
on the individual weapon. [S4]

Any "class X scales with stat Y" table — including the one below — is an inference from member
weapon lists, not something a source publishes. Label it as such wherever it is used.

## Classes and set bonuses

Bonuses scale at **2, 3, 4, 5 and 6** copies — **not** 2/4/6. [S2, S14, and every per-class page]
Carrying a class also biases shop rolls toward more weapons of that class. [S5]

| Class | 2 | 3 | 4 | 5 | 6 | Source |
| --- | --- | --- | --- | --- | --- | --- |
| Blade | +1 Melee Dmg, 1% Lifesteal | +2 / 2% | +3 / 3% | +4 / 4% | +5 Melee Dmg, 5% Lifesteal | S3, S14 |
| Blunt | +1 Armor, −2% Speed | +1 Armor, +3 Max HP, −4% | +2 Armor, +3 HP, −6% | +2 Armor, +6 HP, −8% | +3 Armor, +6 HP, −10% Speed | S2, S14 |
| Elemental | +1 Elem Dmg | +2 | +3 | +4 | +5 Elemental Damage | S2, S14 |
| Ethereal | +6% Dodge, −1 Armor | +12% / −2 | +18% / −3 | +24% / −4 | +30% Dodge, −5 Armor | S2, S14 |
| Explosive | +5% Explosion Size | +10% | +15% | +20% | +25% | S2, S14 |
| Gun | +10 Range | +20 | +30 | +40 | +50 Range | S2, S14 |
| Heavy | +5% Damage | +10% | +15% | +20% | +25% Damage | S2, S14 |
| Legendary | −20 Max HP | −40 | −60 | −80 | −100 Max HP | S2, S14 |
| Medical | +1 HP Regeneration | +2 | +3 | +4 | +5 | S2, S14 |
| Medieval | +1 Armor | +1 Armor, +3% Dodge | +2 Armor, +3% Dodge | +2 Armor, +6% Dodge | +3 Armor, +6% Dodge | S2, S14 |
| **Musical** (DLC) | +5 Luck | +10 | +15 | +20 | +25 Luck | S6, S14 |
| **Naval** (DLC) | +1 Curse | +2 | +3 | +4 | +5 Curse | S7, S14 |
| Precise | +3% Crit Chance | +6% | +9% | +12% | +15% | S4, S14 |
| Primitive | +3 Max HP | +6 | +9 | +12 | +15 Max HP | S2, S14 |
| Support | +5 Harvesting | +10 | +15 | +20 | +25 Harvesting | S5 (**conflict — see below**) |
| Tool | +1 Engineering | +2 | +3 | +4 | +5 Engineering | S2, S14 |
| Unarmed | +3% Dodge | +6% | +9% | +12% | +15% Dodge | S2, S14 |

**17 classes** in the current game. [S14] The Support row conflicts: S5 (Nov 2024) says
+5/10/15/20/25 Harvesting, S14 says +3/6/9/12/15 — open question 23.

**Class membership is many-to-many.** A weapon can carry two or three classes: Circular Saw =
Blade + Medical; Thunder Sword = Blade + Elemental; Captain's Sword = Blade + Naval; Lute =
Musical + Support; Drill = Precise + Legendary. [S3, S4, S5]

## Class → dominant scaling stat (inferred, not sourced)

Derived from member weapon lists in S3–S8:

- **Melee Damage:** Blade, Blunt, Unarmed, Primitive, Medieval, most of Precise
- **Ranged Damage (+ Range):** Gun
- **Elemental Damage:** Elemental
- **Engineering:** Tool — also Plank, Screwdriver, Brick, Chain Gun, Chainsaw, DEX-troyer, Drill,
  Particle Accelerator, War Hammer [S8]
- **Curse:** Naval — Anchor and Captain's Sword scale ~75–100%+ with Curse, Trident 15–50% [S7]
- **Mixed / no single stat:** Explosive, Heavy, Legendary, Medical, Support, Musical

Per-weapon scaling is genuinely individual. From the Precise page alone: Claw scales with Attack
Speed *and* Melee Damage; Crossbow with Ranged Damage *and* Range; Icicle with Elemental Damage;
Sharp Tooth with Melee Damage *and* Life Steal; Drill with Melee Damage *and* Engineering. [S4]

## How scaling is displayed, and the rounding trap

- The in-game tooltip shows stat icons with a **percentage**: 80% Melee Damage means each point of
  Melee Damage gives +0.8 damage. Worked example: 20 base + 80% scaling at 30 Melee Damage →
  `20 + (30 × 0.8) = 44`. [S1]
- Other sources render the same quantity as a **multiplier** — "Melee damage ×1.0", Laser Gun
  "×4.0" [S15] — with published coefficients from **×2.0** (Excalibur, Hammer) down to **×0.5**
  (Shuriken, Thief Dagger). [S16] ×1.0 = 100%; ranged weapons can far exceed 100%.
- Stats a weapon can scale with: Melee Damage, Ranged Damage, Elemental Damage, Engineering, Attack
  Speed, Life Steal, Max HP, Curse, Harvesting, Luck, Player Level, Range, Dodge, Speed, Armor.
  [S17]
- **Rounding is a real gameplay trap.** The float sum is cast to an integer once [S16]. So
  "+1 Melee Damage on an 80% scaling weapon = +0 actual damage", while −1 rounds *away* from zero
  to −1. Minimum damage per hit is 1. [S9] At 1.1.15.4, **only 34 of 79 weapons gain any DPS from a
  single Melee Damage point**; the rest need 2+, and 29 weapon families show no change across a +30
  range. There is also a **second rounding after the global multiplier**. [S16]
- Exceptions worth memorising: **all melee weapons scale with Melee Damage except Spiky Shield,
  which scales with Armor**; the **Shuriken is a ranged weapon that scales with Melee Damage**. [S9]

## Tiers 1–4

- Four tiers: Common / Uncommon / Rare / Legendary. Two identical same-tier weapons combine into one
  of the next tier. [S1]
- Higher tiers raise damage, cut cooldown, and often raise crit chance. [S15] Examples: Fist damage
  8 → 64 with cooldown 13 → 2 frames; Laser Gun 40 → 100 damage, cooldown 95 → 75; Chopper
  6/12/18/30 damage with attack speed 0.99s → 0.89s; Sword 30 → 45 → 65. [S15, S3]
- **Not every weapon exists at every tier** — some are Tier II–IV, III–IV, or Tier IV only. [S17]
  Excalibur has a single tier (200 damage) [S3], and all Naval weapons are said to appear only at
  Tier 2+ (single-sourced, open question 30) [S7].
- Tiered *effects* also scale: Plank's explode chance goes 25/30/35/40% across tiers. [S18]

## Melee versus ranged

- Melee swings at close range and can **hit multiple enemies at once**; ranged fires projectiles
  that hit **one enemy** unless given pierce or bounce. [S1]
- Melee uses one of two attack patterns: **Thrust** (straight line) or **Sweep** (wide curve around
  the player). [S1]
- **Gun is the only unambiguously all-ranged class.** Blade, Blunt, Unarmed, Primitive and Medieval
  read as all-melee from their member lists; Elemental, Explosive, Heavy, Precise, Support, Medical,
  Tool, Legendary and Naval span both. (Inference, not stated by a source.)
- Weapon counts disagree by source: 62 [S15] vs 79 at 1.1.15.4 [S17] vs 76 [S18]. Use 79 for
  base + DLC — but see open question 26.

## Weapon-specific mechanics

**Attack speed, cooldown, animation.** +100% Attack Speed halves cooldown. [S10] The wiki
distinguishes **cooldown** from the **animation time melee weapons have** — with Ball and Chain a
melee weapon's minimum cooldown exceeds 0.75s "depending on the weapon's range", i.e. longer-reach
melee has a longer swing floor. Fast weapons hit diminishing returns; at −100% Attack Speed a Fist
attacks only 14% less often while a Nuclear Launcher attacks 46% less often, and fast *ranged*
degrades more steeply than fast melee. [S10] Melee Range slightly reduces melee attack speed. [S1]

**Piercing.** Default damage falloff **50% per pierce**. Exceptions: Crossbow 0%, Double Barrel
Shotgun 30%, Gatling Laser / Laser Gun / Minigun 25%, Shredder none, Flamethrower pierces 99 enemies
for 1 damage each. Innate piercers: Crossbow, Chain Gun, Double Barrel Shotgun, Flamethrower,
Gatling Laser, Laser Gun, Minigun, Obliterator, Pistol, Shredder. The **Bandana** item grants +1
pierce to all projectile weapons. DLC Naval guns pierce: Blunderbuss 2–5, Harpoon Gun 3–5. [S12, S7]

**Knockback.** Always pushes enemies **directly away from the player**, regardless of hit direction,
identically for melee and ranged. Piercing hits each apply knockback — **unless the projectile has
bounced; once it bounces it can no longer knock back**. Explosion damage never knocks back. Hammer
has the highest base knockback (30–50 by tier) and grants +Knockback to all your weapons. **Harpoon
Gun has −30 knockback**, pulling enemies in, and uniquely ignores knockback resistance. [S12, S13]

**Bounce.** When a projectile has both bounce and pierce, **bounce resolves first**. Explosive
ranged weapons explode on every bounce. [S12, S1]

**Lifesteal is not proportional healing.** "Your attacks have an x% chance to heal you for 1 HP per
hit", with a **0.1s internal cooldown capping healing at 10 HP/sec** — hard diminishing returns at
high percentages. Triggers on direct hits, pierces, bounces and spawned projectiles; does **not**
trigger on explosions, burning, turrets or cyberballs. Innate-lifesteal weapons: Medical Gun 50–65%,
Scissors 40–60%, Circular Saw 45–60%, Chainsaw 15–30%, Scythe 100%, Sharp Tooth scaling with missing
health. [S11]

**Engineering and structures.** Engineering increases the damage and healing of structures, and
**structures do not scale with any other primary stat**. Published coefficients: Landmines +100%,
basic Turret +80%, Laser Turret +125%, Explosive Turret +150%. Structures also include Incendiary
Turret, Medical Turret and Tyler. Historical note: structures used to scale with Range until a bug
fix in patch 0.8.0.03. [S8]

## What this topic still doesn't know

Open questions 23–30 in `RESOURCES.md`. Most load-bearing: the Support bonus conflict (23) and the
fact that the class → scaling-stat mapping above is inference (25).
