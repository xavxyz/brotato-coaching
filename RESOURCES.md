# Resources

The sources this workspace's claims are grounded in. Every claim in a lesson or a reference
doc cites an id from this file, so that a claim can be checked and so that a stale claim is
traceable when a patch lands. Numeric claims should come from extracted game data instead — a
source here is for *how the numbers work*, not *what the numbers are*.

## Patch stamp

| What | Value |
| --- | --- |
| Installed game | **Brotato 1.1.12.0.beta-3** (`CFBundleShortVersionString`, see `MISSION.md`) |
| Steam build id | `23429717`, last updated **2026-08-26** |
| Zones installed | Base game + Abyssal Terrors (`BrotatoAbyssalTerrors.pck` present) |
| Latest live patch | 1.1.15.4, released **2026-05-27**, on top of 1.1.15.0 "All Pain No Gain" (2026-05-12) |
| Research performed | **2026-08-30** |

**The install is a beta branch that trails the current live patch.** Nothing below was read
against the installed build; each source was read against whatever patch it names, and several
name a patch *newer* than the install. Each row says which. Two consequences: a claim sourced from
1.1.15.x may not hold on this install, and a claim checked against a beta may not survive the
stable release of the same version — `MISSION.md` makes the same point.

**How these numbers were obtained**, so they can be re-derived when the patch moves. This is a
hand check, not tooling — `extract` (#6) should supersede it:

```sh
# Installed version. This is the authoritative read: the bundle's own declared version.
plutil -p ~/Library/Application\ Support/Steam/steamapps/common/Brotato/Brotato.app/Contents/Info.plist \
  | grep CFBundleShortVersionString

# Build id and install date, from Steam's manifest for app 1942280.
grep -Ei 'buildid|lastupdated' \
  ~/Library/Application\ Support/Steam/steamapps/appmanifest_1942280.acf
date -r <lastupdated-epoch> -u +%Y-%m-%d
```

**Do not read the version out of `Brotato.pck`.** Grepping that container for version-shaped
strings returns `1.1.15.4`, `1.1.13.2` and `1.3.5.9` — the last is not a Brotato version at all,
so "take the highest" is not a sound rule. Those strings are incidental data, not the build stamp.
The DLC container (`BrotatoAbyssalTerrors.pck`) carries no version string; its presence on disk is
all that is checked. The "latest live patch" row is not from disk — it comes from `SHOP-S13`, the
official Steam announcements hub, read on 2026-08-30.

## How a source is recorded

One row per source, in the table under the topic it covers. The columns carry the fields every
entry must have: **Source** (name and link), **Date / version** (when it was last checked and the
game version it describes), **Why trusted** (what makes it authoritative — extracted game data,
developer output, maintained wiki, a named human with stated experience), and **Covers** (which
claims it is cited for). Known limits are recorded where they bite: in the date column when a
source is stale, and in _Access notes_ and _Open questions_ otherwise.

Each row also carries an **Id** (`STAT-S1`, `WAVE-S4`, …), because lessons and reference docs cite
by id rather than by name.

Rules that hold for every entry:

- **No Reddit.** The search tool blocks the domain outright, so a Reddit link cannot be
  re-checked later and is not admissible here.
- **Dated or versioned, always.** An undated source cannot be told apart from a stale one. Where a
  source publishes no date, the row says `undated` and gives an inferential anchor.
- **Disagreements are recorded, not resolved.** Where two sources conflict, the conflict goes
  in _Open questions_ below and stays there until data settles it.
- **JPot is not listed here.** JPot's heuristics live in `NOTES.md` as a named source, and
  are cited from there where they bear on a topic.

## How to read the trust column

| Tier | Meaning |
| --- | --- |
| **A** | Official Blobfish output: patch notes, Steam announcements. Authoritative. |
| **B** | Community wiki transcribing in-game tooltip strings and datamined tables. Reliable for mechanics, dated per page. |
| **C** | Datamined calculators or spreadsheets that publish their coefficients **and** state the patch they parsed. Reliable only for the patch named. |
| **D** | Written guides and measured trackers. Corroboration only; never the sole support for a claim. |

Two rows carry a qualifier because official material was only reachable second-hand:
**A (mirrored)** means a wiki or SteamDB transcription of official patch notes; **A (reproduced)**
means an outlet reprinting the official notes verbatim. Both are official *content* via an
unofficial *channel* — trust the substance, but see the access notes.

## Access notes — read before trusting anything below

- **`brotato.wiki.gg`, the official wiki, could not be read.** It returned HTTP 401 to every
  automated fetch, as did `brotato.fandom.com` (402). All wiki-sourced rows below were read from
  **`brotato.wiki.spellsandguns.com`**, which serves the same page titles, edit timestamps and
  formula tables and is treated here as a mirror — but this was **not** byte-verified against the
  original. Anywhere a precise constant matters, re-check in a browser.
- **No official Blobfish page was read verbatim.** Steam news bodies are JavaScript-rendered and
  returned navigation chrome only. Tier A rows below are mirrors of official notes, not the notes.
- **No Reddit sources**, per the ticket — the search tool blocks the domain outright.
- The definitive route past all of this is the one the project already plans: decompile the `.pck`
  and read `weapon_service.gd` and friends directly (ticket #6). Several open questions below
  dissolve the moment that lands.

---

## Stat mechanics and damage math

Cited as `STAT-Sn`; the same numbering is used in `docs/research/stat-mechanics.md`.

| Id | Source | Date / version | Trust | Why trusted | Covers |
| --- | --- | --- | --- | --- | --- |
| STAT-S1 | [Stats](https://brotato.wiki.spellsandguns.com/Stats) | undated; includes DLC Curse stat, so ≥1.1.0 | B | Reproduces in-game tooltip strings verbatim, including the limit and negative-behaviour columns | All primary stats, caps, negative-stat behaviour |
| STAT-S2 | [Weapons](https://brotato.wiki.spellsandguns.com/Weapons) | self-declared **patch 1.1.6.3** | B | Template-driven from datamined weapon data; states the scaling maths with a worked example | Scaling tags, displayed damage formula, crit multiplier column |
| STAT-S3 | [Damage](https://brotato.wiki.spellsandguns.com/Damage) | edited 2024-11-11 | B | Quotes tooltip text, gives a concrete additive-stacking example | % Damage semantics, damage floor |
| STAT-S4 | [Attack Speed](https://brotato.wiki.spellsandguns.com/Attack_Speed) | edited 2025-11-20 | B | Explicitly states what it does *not* know about the formula — good epistemic hygiene — and gives measured examples | Diminishing returns, negative AS, Range interaction |
| STAT-S5 | [User:Darkly77/Notes](https://brotato.wiki.spellsandguns.com/User:Darkly77/Notes) | undated; author is a known Brotato modder | C | Cites exact decompiled source files (`ranged_weapon_stats.gd`, `melee_weapon_stats.gd`) and quotes the literal expressions | Displayed cooldown formulas, `recoil_duration` values |
| STAT-S6 | [Brotato-Attack-Speed-Calculator](https://github.com/BrotatoMods/Brotato-Attack-Speed-Calculator) | data headed **0.6.1.6, Dec 2022**; last push 2023-01-11 | C | Datamined implementation that names its source files in comments; independently reproduces STAT-S5 | Cooldown constants, per-weapon base cooldown tables |
| STAT-S7 | [Community datamined spreadsheet](https://docs.google.com/spreadsheets/d/1-EazozRYAORc9TakikmczGy6pNHIT3oTCQE9peuMyB8/) | undated; ~0.6.1.6 era (it is STAT-S6's source) | C | The upstream data STAT-S6 is built on; shows the range/cooldown deltas it computes | Attack speed × range interaction |
| STAT-S8 | [Engineering](https://brotato.wiki.spellsandguns.com/Engineering) | edited 2024-11-12 | B | Enumerates exactly which items, weapons and structures consume Engineering | Engineering scope and coefficients |
| STAT-S9 | [Structures](https://brotato.wiki.spellsandguns.com/Structures) | undated | B | States the secondary-stat exception rule and the 100-structure cap | What does and does not scale structures |
| STAT-S10 | [Turret](https://brotato.wiki.spellsandguns.com/Turret) | undated | B | Item page mirrors the in-game description string `10 + (80% Engineering)` | The one Engineering coefficient confirmed against raw page source |
| STAT-S11 | [Crit Chance](https://brotato.wiki.spellsandguns.com/Crit_Chance) | undated | B | Mirrors tooltip; enumerates what can and cannot crit | Crit cap, per-weapon multipliers, crit scope |
| STAT-S12 | [Range](https://brotato.wiki.spellsandguns.com/Range) | edited 2024-11-11 | B | States the melee half-range rule, independently corroborated by STAT-S5/S6 code | Range formula, melee cooldown penalty |
| STAT-S13 | [Elemental Damage](https://brotato.wiki.spellsandguns.com/Elemental_Damage) | edited 2025-11-20 | B | Current wiki page | Elemental scope, burn scaling |
| STAT-S14 | [Burn](https://brotato.wiki.spellsandguns.com/Burn) | undated | B | Explains the in-game `5x8 +(100% Elemental)` notation | Burn maths, crit/lifesteal exclusion |
| STAT-S15 | [Luck](https://brotato.wiki.spellsandguns.com/Luck) | undated | B | Gives an explicit drop-chance formula | What Luck does and does not touch |
| STAT-S16 | [Patch 1.1.0.0](https://brotato.wiki.spellsandguns.com/Patch_1.1.0.0) | patch **1.1.0.0** | A (mirrored) | Wiki mirror of Blobfish's official notes, itemised | Rounding change, structure AS cap removal |
| STAT-S17 | [Modding Notes](https://brotato.wiki.spellsandguns.com/Modding_Notes) | edited 2023-07-06 | B | Documents the GDRETools decompilation route; admits the melee cooldown formula is hard | Confirms `weapon_service.gd` holds the AS formula |
| STAT-S18 | [brotato-builds.com/stats](https://brotato-builds.com/stats) | self-labelled "2026", **no patch number** | D | Used *only* as a second voice on the disputed attacks-per-second cap | Attack speed cap claim |
| STAT-S19 | [Steam discussion: weapon type vs scaling](https://steamcommunity.com/app/1942280/discussions/0/3811786447112952913/) | 2023-08-07, no dev reply | D | Player discussion; records a community claim only | Weapon type ≠ scaling stat |
| STAT-S20 | [SteamDB patch notes](https://steamdb.info/app/1942280/patchnotes/) | latest 1.1.15.x, May 2026 | A (mirrored) | Mirrors Steam's own patch-note feed | Establishing the current live version |

## Shop economy

Cited as `SHOP-Sn`; see `docs/research/shop-economy.md`.

| Id | Source | Date / version | Trust | Why trusted | Covers |
| --- | --- | --- | --- | --- | --- |
| SHOP-S1 | [Shop](https://brotato.wiki.spellsandguns.com/Shop) | undated; own change list cites up to **1.1.4.0** | B | States explicit formulas, tables and worked examples rather than prose | Price formula, reroll cost, locking, recycling, merging, tier chances |
| SHOP-S2 | [Materials](https://brotato.wiki.spellsandguns.com/Materials) | undated | B | Gives exact drop-decay percentages and the ground cap | Drops, decay, bagging |
| SHOP-S3 | [Harvesting](https://brotato.wiki.spellsandguns.com/Harvesting) | undated | B | Gives the interest formula with rounding examples | Harvesting conversion and interest |
| SHOP-S4 | [Endless Mode](https://brotato.wiki.spellsandguns.com/Endless_Mode) | undated | B | Gives the endless price and harvesting-decay formulas | Post-wave-20 inflation *(out of scope per #1, kept for contrast)* |
| SHOP-S5 | [Weapons](https://brotato.wiki.spellsandguns.com/Weapons) | self-declared **1.1.6.3** | B | Lists per-tier price arrays and per-character slot limits | Tier pricing, slots, merging |
| SHOP-S6 | [Items](https://brotato.wiki.spellsandguns.com/Items) | undated | B | Per-item price/tier/limit table | Item price bands, purchase limits |
| SHOP-S7 | [Patch pages 1.1.2.0 → 1.1.14.0](https://brotato.wiki.spellsandguns.com/Patch_1.1.2.0) | **2024-10-27 → 2026-02-11** | A (mirrored) | Wiki transcription of official notes, versioned and dated | Reroll history, item ban system |
| SHOP-S8 | [Curse](https://brotato.wiki.spellsandguns.com/Curse) | undated; DLC content | B | Gives explicit curse-chance and curse-ratio formulas | Cursed shop items |
| SHOP-S9 | [Piggy Bank](https://brotato.wiki.spellsandguns.com/Piggy_Bank) | undated | B | Item page with a worked example | Carryover of unspent materials |
| SHOP-S10 | [Recycling Machine](https://brotato.wiki.spellsandguns.com/Recycling_Machine) | undated | B | Item stats | Refund stacking |
| SHOP-S11 | [Luck](https://brotato.wiki.spellsandguns.com/Luck) | undated | B | Luck formulas and caps | Luck × shop tier chance |
| SHOP-S12 | [Waves](https://brotato.wiki.spellsandguns.com/Waves) | undated | B | Current wiki page | End-of-wave sequence |
| SHOP-S13 | [Steam announcements hub](https://steamcommunity.com/app/1942280/announcements/) | read 2026-08-30; newest **1.1.15.4 (2026-05-27)** | A | Official Blobfish announcement hub — the primary source for *which* version is current | Version baseline |
| SHOP-S14 | [1.1.15 patch notes reproduction](https://nintendoeverything.com/brotato-all-pain-no-gain-update-announced-patch-notes-nightmare-difficulty-new-character-weapon-more/) | **v1.1.15, 2026-05-12** | A (reproduced) | Reprints the official notes verbatim; date/version corroborated by SHOP-S13 | Weapon price retuning, shop UI changes |
| SHOP-S15 | [Patch 1.1.4.0 news post](https://store.steampowered.com/news/app/1942280/view/4529024857187287757) | **1.1.4.0, 2024-10-29** | A | Official Steam news post (title/date confirmed via search index; body not fetchable) | "Rerolls are now cheaper" |

## Wave and enemy scaling

Cited as `WAVE-Sn`; see `docs/research/wave-scaling.md`.

| Id | Source | Date / version | Trust | Why trusted | Covers |
| --- | --- | --- | --- | --- | --- |
| WAVE-S1 | [Waves](https://brotato.wiki.spellsandguns.com/Waves) | undated; content matches post-1.1 game | B | Transcribes in-game and datamined values | Wave count, durations, wave 20, elite/horde placement |
| WAVE-S2 | [Danger Levels](https://brotato.wiki.spellsandguns.com/Danger_Levels) | undated | B | Per-Danger modifier list matches the in-game Danger-select text | Danger 0–5 breakdown, accessibility sliders |
| WAVE-S3 | [Elite and Horde Waves](https://brotato.wiki.spellsandguns.com/Elite_and_Horde_Waves) | undated | B | Dedicated mechanics page | Elite/horde slots, probabilities, material penalty |
| WAVE-S4 | [Enemies](https://brotato.wiki.spellsandguns.com/Enemies) | undated | B | Hosts the per-enemy stat tables including the `+hp/wave` columns the scaling rule derives from | Per-wave scaling rule, spawn caps |
| WAVE-S5 | [Curse](https://brotato.wiki.spellsandguns.com/Curse) | undated; ≥1.1.0 | B | Gives explicit formulas, indicating a datamined source | Curse formulas, cursed enemies |
| WAVE-S6 | [Endless Mode](https://brotato.wiki.spellsandguns.com/Endless_Mode) | undated | B | Explicit Endless Factor formula | Post-wave-20 scaling *(out of scope per #1)* |
| WAVE-S7 | [Abyssal Terrors DLC](https://brotato.wiki.spellsandguns.com/Abyssal_Terrors_DLC) | edited **2024-11-13** | B | DLC content list on the release-patch subpage | Abyss enemy/elite/boss counts |
| WAVE-S8 | [Abyssal Terrors store page](https://store.steampowered.com/app/2868390/Brotato_Abyssal_Terrors/) | released **2024-10-25** | A | Official Blobfish store listing | Official DLC scope statement |
| WAVE-S9 | [1.1.15 patch notes reproduction](https://nintendoeverything.com/brotato-all-pain-no-gain-update-announced-patch-notes-nightmare-difficulty-new-character-weapon-more/) | **v1.1.15, 2026-05-12** | A (reproduced) | Reprints Blobfish's notes verbatim | Nightmare tier, fog and projectile waves |
| WAVE-S10 | [Datamined per-wave tables](https://note.com/mmgrr/n/nbf105fb386f9?hl=en) | **v1.1.15.3**, published 2026-05-24 | C | Captured with the "Wave Info" mod; states its version *and* its method | Per-wave total HP and enemy counts, Abyss vs Crash Zone |
| WAVE-S11 | [Wave-by-wave difficulty analysis](https://note.com/mmgrr/n/nd104bfbef9a8?hl=en) | 2026-06-28, Nightmare-era | C | Same author and method as WAVE-S10 | Hardest waves per zone |
| WAVE-S12 | [brotatotracker.com/stats](https://brotatotracker.com/stats) | read **2026-08-30**; 10,310 runs; **no game version stated** | D | The only source found that *measures* deaths per wave from submitted runs rather than asserting them | Death distribution |
| WAVE-S13 | [Ultimate guide to enemies and waves](https://gameplay.tips/guides/brotato-ultimate-guide-to-enemies-and-waves.html) | **2024-07-23**, pre-DLC | D | States its basis (Danger 5) and lists per-wave durations explicitly | Wave duration table, elite/horde gating |
| WAVE-S14 | [GameSpot: co-op update and DLC](https://www.gamespot.com/articles/brotato-co-op-update-and-abyssal-terrors-dlc-are-out-now/) | 2024-10 | D | Reputable outlet; corroborates the DLC/1.1.0.0 release date | Release date |

## Weapon classes

Ticket #4 calls this topic "weapon archetypes". `CONTEXT.md` reserves **archetype** for a family of
*characters*, and the game itself calls these **classes** or **sets**, so the register uses "class".

Cited as `WEAP-Sn`; see `docs/research/weapon-classes.md`.

| Id | Source | Date / version | Trust | Why trusted | Covers |
| --- | --- | --- | --- | --- | --- |
| WEAP-S1 | [Weapons](https://brotato.wiki.spellsandguns.com/Weapons) | self-declared **patch 1.1.6.3** | B | Template-driven from datamined weapon data | Tiers, scaling display, melee vs ranged, thrust/sweep |
| WEAP-S2 | [Weapon Classes](https://brotato.wiki.spellsandguns.com/Weapon_Classes) | edited **2023-07-30** — pre-1.0, pre-DLC, **stale** | B | Same wiki, but explicitly out of date; used only to cross-check base-game classes | Class list and set bonuses (base game only) |
| WEAP-S3 | [Blade](https://brotato.wiki.spellsandguns.com/Blade) | edited 2025-11-19 | B | Current per-class page with per-tier weapon stats | Blade bonus and weapon list |
| WEAP-S4 | [Precise](https://brotato.wiki.spellsandguns.com/Precise) | edited 2024-11-03 | B | Per-class page with per-weapon scaling stats | Precise bonus and scaling |
| WEAP-S5 | [Support](https://brotato.wiki.spellsandguns.com/Support) | edited 2024-11-05 | B | Per-class page | Support bonus |
| WEAP-S6 | [Musical](https://brotato.wiki.spellsandguns.com/Musical) | edited 2024-11-03 | B | Documents a DLC class | Musical bonus |
| WEAP-S7 | [Naval](https://brotato.wiki.spellsandguns.com/Naval) | updated 2025-01-20 | B | Documents a DLC class | Naval bonus, Curse scaling |
| WEAP-S8 | [Engineering](https://brotato.wiki.spellsandguns.com/Engineering) | edited 2024-11-12 | B | Gives explicit per-structure Engineering coefficients | Turrets, structures, Tool class |
| WEAP-S9 | [Melee Damage](https://brotato.wiki.spellsandguns.com/Melee_Damage) | edited 2024-11-12 | B | States the rounding rules | Melee scaling, rounding, Shuriken/Spiky Shield exceptions |
| WEAP-S10 | [Attack Speed](https://brotato.wiki.spellsandguns.com/Attack_Speed) | updated 2025-11-20 | B | Current page | Cooldown vs animation, diminishing returns |
| WEAP-S11 | [Life Steal](https://brotato.wiki.spellsandguns.com/Life_Steal) | updated 2025-11-20 | B | Current page | Lifesteal mechanics and innate-lifesteal weapons |
| WEAP-S12 | [Piercing](https://brotato.wiki.spellsandguns.com/Piercing) | edited 2024-11-19 | B | Per-weapon falloff table | Pierce falloff, bounce interaction |
| WEAP-S13 | [Knockback](https://brotato.wiki.spellsandguns.com/Knockback) | edited 2024-11-19 | B | Current page | Knockback semantics |
| WEAP-S14 | [Steam forum set-bonus reference thread](https://steamcommunity.com/app/1942280/discussions/0/3493130356505192248/) | opened 2022-10; a reply states it is maintained to **2024-05-25** | D | Long-running community reference on the official forum, maintained across patches; valuable as a wiki-independent voice | Full 17-class set-bonus table |
| WEAP-S15 | [Fextralife: Weapons](https://brotato.wiki.fextralife.com/Weapons) | edited **2026-08-20** | D | Independent wiki with per-weapon tier tables; a second opinion on scaling notation | Tier stat progression, `×1.0` notation |
| WEAP-S16 | [brotatobuilds.com/stats/melee-damage](https://www.brotatobuilds.com/stats/melee-damage/) | states **Brotato 1.1.15.4** | C | Datamined calculator that publishes its coefficients and shows its arithmetic — but it is stamped 1.1.15.4, ahead of this install | Scaling coefficients, double-rounding |
| WEAP-S17 | [brotatobuilds.com/weapons](https://www.brotatobuilds.com/weapons/) | "compiled for **1.1.15.4**, updated 2026-08-05" | C | Same calculator, version stated explicitly | Weapon counts, full scaling-stat list |
| WEAP-S18 | [brotato-builds.com/weapons](https://brotato-builds.com/weapons) | "2026", **no patch number** | D | SEO guide site; corroboration only, never sole support | Weapon counts, tier effects |

---

## Open questions

Recorded rather than resolved, per the ticket. Each is a place where sources conflict or fall
silent. Most resolve against extracted game data once ticket #6 lands — those are marked **→ #6**.

### Stat mechanics

1. **STAT-Q1 — Is there a 12-attacks-per-second cap?** `STAT-S1` says "can't attack faster than 12 times per
   second"; `STAT-S18` repeats it. The dedicated Attack Speed page `STAT-S4` describes only
   per-weapon minimum cooldowns with *no* global cap, and the datamined formulas `STAT-S5`/`STAT-S6`
   contain no such constant. **→ #6**
2. **STAT-Q2 — How Attack Speed actually modifies the base cooldown timer.** Every source states the
   "+100% = half cooldown" rule of thumb, but none publishes the expression. `STAT-S5`/`STAT-S6`
   give only the *displayed* cooldown text, whose `cooldown / 60` term carries no Attack Speed
   factor. `STAT-S17` names `weapon_service.gd` as the location without quoting it. **→ #6**
3. **STAT-Q3 — The negative Attack Speed formula is entirely undocumented.** Only two calibration points
   exist: at −100% AS a Tier 4 Fist attacks 14% less often, a Tier 4 Nuclear Launcher 46% less
   often (`STAT-S4`). **→ #6**
4. **STAT-Q4 — Order of operations for crit vs % Damage.** No source states whether crit multiplies before or
   after the % Damage layer. The two commute in pure arithmetic, but 1.1.0.0 explicitly changed
   % Damage from floor to round (`STAT-S16`), so rounding makes the ordering observable. **→ #6**
5. **STAT-Q5 — Rounding of fractional flat scaling.** `STAT-S2`'s example uses clean numbers (30 × 0.8 = 24).
   Nothing documents what happens to e.g. 25 Melee × 85% = 21.25. **→ #6**
6. **STAT-Q6 — Is Luck a weapon scaling stat?** `STAT-S15` says some weapons scale damage with Luck;
   `STAT-S2`'s scaling-icon legend does not list Luck. Either the legend is incomplete or the claim
   covers only characters and items. **→ #6**
7. **STAT-Q7 — Datamined attack-speed constants are three and a half years old.** `STAT-S5`/`STAT-S6` are from
   0.6.1.6 (Dec 2022) against a 1.1.12.0.beta-3 install. The formula *shapes* are corroborated by
   present-day wiki text, but every constant should be treated as unverified. **→ #6**
8. **STAT-Q8 — Per-structure Engineering coefficients.** Only the Turret's `10 + (80% Engineering)` was
   confirmed against raw page source (`STAT-S10`); Landmines/Laser/Explosive/Incendiary/Medical come
   from a rendered table in the same wiki (`STAT-S8`). **→ #6**

### Shop economy

1. **SHOP-Q1 — Reroll formula versus patch note.** `SHOP-S1` states `floor(0.75 × Wave)` base and
   `floor(0.40 × Wave)` increase; the 1.1.4.0 note describes the change as base `Wave → Wave/2` and
   increase `0.5 × Wave → 0.33 × Wave`. Probably reconciled by 1.1.7.1's "reroll price slightly
   increased", but the official bodies were unreadable. **→ #6**
2. **SHOP-Q2 — The tier-chance formula does not reproduce the wiki's own tier table.** With Tier 2 at base 0%
    and 6%/wave, the stated formula yields 0% at wave 3 and 12% at wave 5; the table shows 12% and
    20%. The table's increments are 6,6,4,4,4… not a constant 6%. Trust the table over the formula
    until datamined. **→ #6**
3. **SHOP-Q3 — Tier 2 chance at wave 20.** One reading gives 35% at wave 20 against 40% at wave 10, implying
    Tier 2 *falls* — which contradicts a monotonic formula. Possibly an effective probability after
    Tier 4 and Tier 3 are rolled first (`SHOP-S1` states tiers roll highest-first). **→ #6**
4. **SHOP-Q4 — Does merging two weapons cost materials?** No source states a fee; none states it is free
    either. `SHOP-S5` explicitly declines to say. **→ #6**
5. **SHOP-Q5 — Recycling scope.** `SHOP-S1` says you recycle "Weapons and Items found in Crates". Whether
    shop-*purchased* items can be recycled later is not spelled out.
6. **SHOP-Q6 — Is there a cap on materials held?** None found, but no page affirmatively says "no cap".
    Absence of evidence only.
7. **SHOP-Q7 — Item base price is authored per item, not derived from tier.** `SHOP-S6` prices merely
    correlate with tier, and 1.1.15 retuned several freely (`SHOP-S14`). Any guide presenting a
    tier→price formula should be distrusted — noted so no lesson invents one.

### Wave and enemy scaling

1. **WAVE-Q1 — Which Danger tier first adds enemy stats.** `WAVE-S2`'s body maps +12/+26/+40% to Danger
    3/4/5, and `WAVE-S13` independently confirms Danger 5 = +40%. A search summary of the same wiki
    instead attributed +12% to Danger 1 and +26% to Danger 2. Two sources favour 3/4/5, and D0–D2
    being stat-neutral fits "new enemies" being D1/D2's stated modifier — but this is worth
    confirming in-game, and it matters, because it is the difference between Danger 4 and Danger 5
    being a 26→40% step or something else entirely.
2. **WAVE-Q2 — Boss HP numbers do not reconcile.** `WAVE-S4` gives base 29,250 and "30,712 at Danger 5"
    (≈ 29,250 × 1.4 × 0.75, i.e. the *two-boss* value); `WAVE-S13` gives 31,395 pre-DLC; `WAVE-S10`
    gives 37,950 per boss on Nightmare 1.1.15.3. Different patches and conditions, none stated
    precisely enough to reconcile. **Do not quote a single boss HP number.** **→ #6**
3. **WAVE-Q3 — "Portal waves" / "abyss waves" appear not to exist.** No source describes such a mechanic.
    Possibly a confusion with Curse or the Nightmare fog events. Flagged unresolved, not denied.
4. **WAVE-Q4 — No global enemy-count formula is published.** `WAVE-S10`'s per-wave counts are empirical
    observations from one modded run, not a rule. The only hard number is the 100-on-screen cap
    (`WAVE-S4`). **→ #6**
5. **WAVE-Q5 — Does the Abyss use the same Danger multipliers as the Crash Zone?** No source confirms or
    denies it. Absence of a contrary statement suggests yes; that is inference, not documentation.
6. **WAVE-Q6 — Nightmare wave-type arithmetic doesn't add up.** `WAVE-S10`/`WAVE-S11` report 3 darkness +
    7 bullet-hell + 6 normal = 16 against a 20-wave run. Unexplained.
7. **WAVE-Q7 — `WAVE-S12`'s death distribution is unstamped and self-selected.** It aggregates every
    character, zone, Danger and mode with no version, from players who use a tracker app. The
    waves 6–7 spike (≈24% of deaths) is corroborated qualitatively by `WAVE-S11`, but do not treat
    the percentages as measurements of *this* player's situation — the save data is the honest
    source for that (ticket #5).

### Weapon classes

1. **WEAP-Q1 — Support set bonus conflict.** `WEAP-S5` (Nov 2024) says +5/10/15/20/25 Harvesting;
    `WEAP-S14` says +3/6/9/12/15. The wiki page is newer and more specific, but unconfirmed. **→ #6**
2. **WEAP-Q2 — Set bonuses scale at 2/3/4/5/6 copies, not 2/4/6.** Recorded because the ticket's framing
    assumed 2/4/6 — every per-class page and `WEAP-S14` agree on five steps.
3. **WEAP-Q3 — Class → scaling-stat mapping is an inference.** No source publishes a "this class scales with
    stat X" table, because **scaling is a per-weapon property, not a class property**. Any mapping
    in a lesson is derived from member weapon lists and must be labelled as such. **→ #6**
4. **WEAP-Q4 — Weapon counts disagree:** 62 (`WEAP-S15`), 76 (`WEAP-S18`), 79 (`WEAP-S17`). Likely
    base-game-only versus base+DLC, but none of them says which. **→ #6**
5. **WEAP-Q5 — `WEAP-S2`, the aggregate class page, is stale** (July 2023): it omits Musical and Naval, and
    its Blunt/Medieval numbers may predate later balance passes. Corroboration only.
6. **WEAP-Q6 — Set-bonus values may have drifted between 1.1.6.3 and 1.1.15.4.** No patch note confirming
    either way was readable. Assume some drift. **→ #6**
7. **WEAP-Q7 — "Windup" is not a term the wiki uses.** It distinguishes melee *animation time* from cooldown
    (`WEAP-S10`) but publishes no per-weapon windup values. **→ #6**
8. **WEAP-Q8 — `WEAP-S7`'s claim that all Naval weapons are Tier 2+** is single-sourced. **→ #6**

### Cross-cutting

1. **CROSS-Q1 — The official wiki was never read directly.** Every `B`-tier row rests on a mirror whose
    fidelity was not verified. This is the single largest weakness in this register.
2. **CROSS-Q2 — No official Blobfish page was read verbatim.** All Tier A rows are mirrors or reproductions.

---

## Where JPot's heuristics go

Not here. A heuristic from JPot is a **hypothesis to test against this register**, not a row
in it, so it lives in `NOTES.md` next to the topic it bears on — see that file for the hooks, the
attribution rule, and the current state (**none captured yet**).

`WAVE-Q1` above is the clearest example of why that capture is worth doing: it is exactly the kind
of question a 300-hour player answers in one sentence.
