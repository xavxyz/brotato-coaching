# Research: shop economy

Researched 2026-08-30 against installed **Brotato v1.1.15.4**. Source ids `SHOP-S1`–`SHOP-S15` and
open questions `SHOP-Q1`–`SHOP-Q7` are defined in `RESOURCES.md`; read the access notes there
before trusting a constant.

Endless Mode is out of scope per the spec; the endless formulas are kept only as contrast.

## Materials — drops, caps, carryover

- Materials are green blobs dropped by killed enemies; base drop chance **100%**, with a
  predetermined base material value per enemy. [SHOP-S2]
- **Drop-chance decay:** from wave 5 onward, drop chance is reduced by **1.5% × wave number**, down
  to a **50%** floor. Wave 5 = 92.5%, wave 10 = 85%, wave 20 = 70%. [SHOP-S2, SHOP-S4]
- **Horde waves apply ×0.65** to material drops (35% fewer). [SHOP-S2]
- **Ground cap: 50 material blobs on the map at once.** Beyond that, new material value merges into
  an existing blob rather than spawning a new one. [SHOP-S2]
- **Uncollected materials are not lost:** at wave end, materials still on the ground are "bagged",
  and on later waves one unit is extracted from the bag and added to each dropped blob. [SHOP-S2, SHOP-S12]
- **Unspent materials carry over** as run currency — confirmed indirectly but strongly by Piggy
  Bank, which grants "+20% of your materials at the start of waves (stops working at wave 20)",
  i.e. compounding interest on carried materials. [SHOP-S9]
- **No documented cap on materials held.** The only cap found anywhere is the 50-blob ground limit.
  [SHOP-S2]
- Picking up materials grants **both XP and currency** (same number). Bag and Piggy Bank give
  currency only, no XP — unlike Harvesting. [SHOP-S2, SHOP-S9]
- DLC: cursed enemies drop **+33% materials** (was +20% before 1.1.2.0). [SHOP-S7, SHOP-S8]

## Harvesting

- At the end of each wave you receive materials **and** XP equal to your Harvesting stat, 1:1 for
  each. [SHOP-S3]
- **Interest:** after the payout, Harvesting grows by **5%, rounded up** —
  `new = ceil(current × 1.05)`. Because of the round-up, 5 Harvesting → 6, and it takes **21**
  Harvesting before the tick is +2. [SHOP-S3]
- **Rate modifiers:** Farmer +3% (→8%, and starts with +20 Harvesting); Crown +8% (→13%, stacking
  with Farmer for 16%, limit 1 per run). Entrepreneur applies ×50% to *all* Harvesting
  modifications, including the interest gain. [SHOP-S3]
- **Negative Harvesting** loses materials and XP at wave end (you cannot lose a level), and the 5%
  interest does not apply while negative. [SHOP-S3]
- Crown and Piggy Bank were **banned from appearing after wave 20** in patch 1.1.13.0. [SHOP-S7]

## Item and weapon pricing

- **Base prices are authored per item and per weapon tier, not derived from a formula.** Weapons
  carry a 4-value tier array — Knife **10 / 22 / 45 / 91**. Patch 1.1.15 retuned several (Hatchet
  15/31/61/122 → 10/22/45/91; Wand 12/26/52/105 → 10/22/45/91; Quarterstaff 17/34/66/130 →
  15/31/61/122). [SHOP-S5, SHOP-S14]
- Observed item price bands by tier — a range, not a rule: T1 ≈ 8–30, T2 ≈ 30–75, T3 ≈ 50–92,
  T4 ≈ 90–130. [SHOP-S6]
- **Wave inflation formula:**
  `Final Price = (Base_Price + Wave + (Base_Price × 0.1 × Wave)) × Shop_Price`
  rounded **down**, minimum **1** material. `Wave` is the wave just completed; `Shop_Price` is the
  secondary stat modified by Coupon and character traits. Worked example: SMG (base 20) in shop 1 →
  `20 + 1 + 2 = 23`. [SHOP-S1]
- **Recycling/selling refund:** base **25%**; Recycling Machine +35% → 60%; Entrepreneur +25%,
  stacking to a maximum **85%**. The refund is computed from the item's **current** shop price, so
  it rises with inflation and *falls* if you have Coupons. [SHOP-S1, SHOP-S10]

## Rerolls

- **First reroll cost:** `floor(Wave × 0.75) + Reroll_Increase`
- **Reroll increase**, added for each subsequent reroll in the same shop: `floor(0.40 × Wave)`,
  minimum 1. [SHOP-S1]
- Wiki table (waves 1–20), first-reroll / increase: 1/1, 2/1, 3/1, 4/1, 5/2, 6/2, 7/2, 9/3, 9/3,
  11/4, 12/4, 13/4, 14/5, 15/5, 17/6, 18/6, 18/6, 20/7, 21/7, 23/8. The flat spots (waves 8–9,
  16–17) look like typos but are consistent with the formula. [SHOP-S1]
- **Reroll cost resets between shops**, and **level-up rerolls are tracked separately from shop
  rerolls**. [SHOP-S1]
- **Buying out the shop** (all 4 items) grants a **free full reroll** — changed in 1.1.0.0 from
  merely zeroing the current reroll cost. [SHOP-S1]
- History: 1.1.4.0 "rerolls are now cheaper"; 1.1.7.1 "reroll price slightly increased". [SHOP-S7, SHOP-S15]

## Locking

- Locking is **free** and can be toggled as often as you like. [SHOP-S1]
- A locked item **survives rerolls** and **persists into the next wave's shop**. [SHOP-S1]
- **A locked item's price does not change** — "locked items are not affected by inflation if you
  keep them locked between shops." Locking is a genuine price hedge, not just a reservation. [SHOP-S1]
- Patch 1.1.13.0 added an **item ban system with 8 ban tokens** plus lock/ban/reroll shortcuts —
  distinct from locking. [SHOP-S7]

## Weapon slots and merging

- Most characters have **6 weapon slots**. Exceptions: One Armed 1, Multitasker 12, Bull cannot use
  weapons, Baby up to 24 (one per level). [SHOP-S5]
- **Merge rule:** two identical weapons of the **same tier** combine into one of the **next tier**,
  manually or automatically when you buy an identical weapon with full slots. **Cannot combine above
  Tier 4.** [SHOP-S1, SHOP-S5]
- Economically, merging is the cheap path to high tiers: two Tier 1 Knives (10 + 10) produce a
  Tier 2 Knife whose shop price would be 22. Whether merging itself costs materials is
  **unconfirmed** — see open question SHOP-Q4. [SHOP-S5]

## Shop tier probabilities and Luck

| Tier | Min wave | Base chance | Chance/wave | Max chance |
| --- | --- | --- | --- | --- |
| 1 | 1 | 100% | 0% | 100% |
| 2 | 2 | 0% | 6% | 60% |
| 3 | 4 | 0% | 2% | 25% |
| 4 | 8 | 0% | 0.23% | 8% |

- Stated formula: `((Chance per Wave × (Current Wave − Min Wave − 1)) + Base Chance) × (100% + Luck)`,
  capped at Max Chance. **Tiers are rolled one at a time starting with Tier 4.** [SHOP-S1]
  This formula does **not** reproduce the table below — see open question SHOP-Q2.
- 0-Luck table, waves 1–10 [SHOP-S1]:

| Wave | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T1 | 100 | 94 | 88 | 82 | 76 | 70 | 64 | 58 | 52 | 46 |
| T2 | 0 | 6 | 12 | 16 | 20 | 24 | 28 | 32 | 36 | 40 |
| T3 | 0 | 0 | 0 | 2 | 4 | 6 | 8 | 9.8 | 11.5 | 13.3 |
| T4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0.2 | 0.5 | 0.7 |

- **Luck multiplies these by `(100% + Luck)` but can never exceed the per-tier max.** Because the
  chances rise with wave number anyway and cap out, **Luck's effect on shop rarity is strongest
  early and largely irrelevant late.** Roughly 290 Luck maxes out Tier 4 rarity. [SHOP-S1, SHOP-S11]
- Luck separately affects crates:
  `Enemy_Box_Drop_Chance × (100% + Luck) / (1 + Boxes_Spawned_This_Wave)`. [SHOP-S11]

## Abyssal Terrors — cursed shop items

- Shop weapons and items can spawn **cursed**: positives multiplied and downsides divided by
  `Curse Ratio = 1.4 + rand(−0.3, +0.3) + 0.02 × min(current_wave, 20)` — so 1.1–1.7 early,
  1.5–2.1 at wave 20. In exchange the item grants Curse depending on its price. [SHOP-S8]
- **Chance a shop item is cursed = `15 × Curse / (50 + Curse)`**, asymptotically capped at 15%.
  (Cursed-*enemy* chance caps at 50%.) [SHOP-S8]
- **Fish Hook** (limit 3): locked items and weapons have a **20% chance to become cursed when
  leaving the shop** — a direct interaction between locking and the DLC economy. 1.1.7.1 added a
  pity system for it. [SHOP-S7, SHOP-S8]

## What this topic still doesn't know

Open questions SHOP-Q1–SHOP-Q7 in `RESOURCES.md`. Most load-bearing: the tier-chance formula contradicting its
own table, and whether merging costs materials.
