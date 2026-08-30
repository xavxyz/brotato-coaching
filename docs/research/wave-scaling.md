# Research: wave structure, enemy scaling and Danger

Researched 2026-08-30 against installed **Brotato v1.1.15.4**. Source ids `WAVE-S1`–`WAVE-S14` and
open questions `WAVE-Q1`–`WAVE-Q7` are defined in `RESOURCES.md`; read the access notes there
before trusting a constant.

Vocabulary follows `CONTEXT.md`: **wave**, **Danger**, **zone**, **run**.

## Wave structure

- A normal run is **20 waves**; clearing wave 20 ends the run. [WAVE-S1, WAVE-S13]
- **Durations:** wave 1 = 20s, then +5s per wave until it caps at 60s — so wave 2 = 25s, wave 3 =
  30s, wave 9 = 60s, and waves 9–19 are all 60s. **Wave 20 = 90s.** [WAVE-S1, WAVE-S13]
- **Wave 20:** one boss spawns from that zone's pool. **On Danger 5, both bosses spawn instead,
  each with −25% HP.** [WAVE-S1, WAVE-S2, WAVE-S13]
- Spawns are telegraphed by a red X; the enemy appears **1 second** later. Hard cap of **100
  enemies on screen**; past that a random non-elite, non-boss enemy is deleted without dropping
  loot. [WAVE-S4]

## Elite and horde waves

- Gated by Danger: **D0–D1 none, D2–D3 one, D4–D5 three.** [WAVE-S2, WAVE-S3]
- Slots: **wave 11 or 12**, **wave 14 or 15**, **wave 17 or 18**. The first two roll
  **60% Elite / 40% Horde**; the third is **always Elite**. [WAVE-S1, WAVE-S3]
- One elite per Elite wave, and an elite cannot repeat later in the same run. Elites spawning on
  **wave 11 or 12 have only 75% HP**. [WAVE-S3, WAVE-S4]
- Elite kill → Legendary crate (guaranteed Tier 4 item) + 100 HP heal. [WAVE-S2, WAVE-S3]
- Horde waves: many extra enemies, and **all enemies drop 35% fewer materials**. [WAVE-S3, WAVE-S13]
- The wave *slots* are identical in the Crash Zone and the Abyss; only the elite and boss rosters
  differ (the DLC adds 9 Abyss elites and 2 Abyss bosses, Dead Whale and Eel). [WAVE-S3, WAVE-S7]

## Enemy scaling per wave

- **The rule is per-enemy, not global.** Each enemy has a base HP and a **`+hp/wave`** increment,
  gained for each wave after the first. Wiki example: a Tree has 10 HP with +5/wave, so on wave 11
  it has `10 + (5 × 10) = 60`. **Damage works the same way** with its own `+dmg/wave`. [WAVE-S4]
- **Speed does not scale** — "their Speed doesn't change with Wave or Danger level." [WAVE-S4]
- Danger multipliers apply on top, multiplicatively with the accessibility sliders. [WAVE-S2, WAVE-S4]
- Aggregate per-wave difficulty, datamined at v1.1.15.3 in the Abyss: total wave HP grows roughly
  geometrically — W1 ≈ 60, W5 ≈ 2,486, W12 ≈ 20,397, W14 ≈ 32,348, W19 ≈ 89,001, W20 ≈ 134,865
  (two bosses × 37,950). Enemy counts scale too: W5 ≈ 42 spawns, W12 ≈ 121, W14 ≈ 151, W19 ≈ 190 in
  the sampled composition. [WAVE-S10]
- Materials per wave scale similarly: Abyss W1 = 27, W5 = 137, W19 = 541; a run starts with 30
  materials. [WAVE-S10]

## Danger 0–5

Each row is the **total** for that tier, not cumulative on top of the previous. [WAVE-S2]

| Danger | Enemy HP & damage | Elite/Horde waves | Other | Unlocks |
| --- | --- | --- | --- | --- |
| 0 | baseline | none | — | One Armed |
| 1 | baseline | none | new enemy types added to the pool | Bull |
| 2 | baseline | 1 (wave 11 or 12) | elites drop guaranteed Legendary crates | Soldier |
| 3 | **+12% HP, +12% damage** | 1 (wave 11 or 12) | more new enemies | Masochist |
| 4 | **+26% HP, +26% damage** | 3 (11/12, 14/15, 17/18) | more new enemies | Knight |
| 5 | **+40% HP, +40% damage** | 3 | **two bosses** on wave 20, each at −25% HP | Demon |

The Danger 3/4/5 attribution is contested — see open question WAVE-Q1 in `RESOURCES.md`.

- Danger also changes **when** enemies first appear, not just whether. Enemy tables use notation
  like `13 D1:8`, meaning first spawn at wave 13 on Danger 0 but wave 8 on Danger 1+. [WAVE-S4]
- **No material penalty is attached to Danger in any source found.** The only
  documented material penalty is the −35% on Horde waves. Treat "Danger reduces materials" as
  unsupported. [WAVE-S3]
- No extra environmental hazards at Danger 0–5; hazards are a Nightmare feature. [WAVE-S2, WAVE-S9]
- Accessibility sliders sit outside the Danger system — damage and HP 25–200%, speed 25–150% —
  multiplying with Danger. [WAVE-S2]

## Nightmare (above Danger 5, patch 1.1.15, May 2026)

- Unlocked by beating Danger 5; the official notes say **10 times across different zones or
  characters** (a secondary summary said "once" — take the patch-note wording). [WAVE-S9]
- Two new wave-level event types beyond a stat bump [WAVE-S9]:
  - **Environmental projectiles** ("bullet hell"): bullets cross the map, growing in speed and
    quantity as waves progress, static past wave 20.
  - **Obscuring fog / darkness**: reduced visibility on waves (5 or 6 or 7), (10 or 11 or 12),
    (16 or 17 or 18); later fog waves are darker. Marked on the wave timeline like Elite/Horde.
- New bestiary: 6 extra Crash Zone enemies, 10 extra Abyss enemies. [WAVE-S9]
- Datamined wave-type split: 3 darkness, 7 bullet-hell, 6 normal — which sums to 16, not 20, and is
  unexplained (open question WAVE-Q6). [WAVE-S10, WAVE-S11]
- **Enraged** enemy modifier: +25% damage, +50% speed, +150% HP. [WAVE-S10]

Nightmare is above the mission's Danger 5 bar and is recorded for context only.

## Abyssal Terrors / the Abyss

- Released **2024-10-25** with patch **1.1.0.0**, alongside local co-op. [WAVE-S8, WAVE-S14]
- The Abyss is a full parallel zone: **20 waves**, same structure, with ~25 regular enemies, 9
  elites and 2 bosses. [WAVE-S7, WAVE-S8]
- **Curse** is the DLC's headline mechanic and a new primary stat [WAVE-S5]:
  - Cursed-enemy chance = `50 × Curse / (50 + Curse)`
  - Cursed enemy (purple outline): **+25% damage, +15% speed, +150% HP + 2% per Curse point**,
    capped at 300 Curse (→ +750% HP). Drops **+33% materials**. [WAVE-S5, WAVE-S10]
  - Cursed shop item chance = `15 × Curse / (50 + Curse)`
  - Cursed item: positives × Curse Ratio, negatives ÷ Curse Ratio, each effect rolled
    independently, where `Curse Ratio = 1.4 + rand(−0.3, 0.3) + 0.02 × min(current_wave, 20)`. [WAVE-S5]
- Zone differences (community-observed, not datamined): the Abyss has guaranteed curse-inflicting
  enemies (Sea Cucumbers, from wave 4) that the Crash Zone lacks; Crash Zone waves are strongly
  themed with a specific challenger per wave, while Abyss waves mix enemy types. [WAVE-S10, WAVE-S11]
- **No evidence of "portal waves" or "abyss waves" was found** — see open question WAVE-Q3.
- Per-wave HP totals differ between zones but neither is uniformly higher (Crash Zone W15 = 28,964
  vs Abyss W15 = 23,903). **No source documents a different scaling formula or Danger table for the
  Abyss**; the difficulty difference comes from enemy composition. [WAVE-S4, WAVE-S10]

## Where players actually die

- The only *measured* source found is a run tracker with 10,310 submitted runs: wave 6 = 1,125
  deaths (13%), wave 7 = 923 (11%), wave 11 = 768 (9%), wave 9 = 688 (8%), wave 5 = 600 (7%),
  wave 4 = 574 (7%). **Waves 6–7 alone ≈ 24% of deaths.** [WAVE-S12]
- Caveats: aggregated across all characters, zones, Dangers and modes with no version stamp, from
  self-selected tracker users. Do not treat it as a measurement of this player — the save data is
  the honest source for that (ticket #5).
- Qualitative agreement: Crash Zone hurdles at waves 6–7 (Slasher Eggs, Horn Spitters), 11, and 18
  ("probably the hardest wave in the game"); Abyss hurdles at wave 9 (a DPS check), 15 if it rolls
  elite/horde, and 17 (Stonefish stalkers). The 6–7 spike matches the tracker. [WAVE-S11]

## What this topic still doesn't know

Open questions WAVE-Q1–WAVE-Q7 in `RESOURCES.md`. Most load-bearing for the mission: which Danger tier first
adds enemy stats (16), since Danger 4 → 5 is exactly the step this player is trying to close.
