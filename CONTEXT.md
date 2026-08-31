# Brotato Coaching

A teaching workspace for learning Brotato deeply enough to reach Danger 5 solo on every
character, backed by tooling that reads what the game already writes to disk.

Two vocabularies meet here: the game's, and the workspace's. Several words collide across
them, so this file picks one meaning for each.

## The game

**Run**:
One playthrough, from wave 1 until death or victory. The unit a review examines.
_Avoid_: game, attempt, session, playthrough

**Session**:
One sitting at the game, in which one or more runs are played.
_Avoid_: run, sitting

**Wave**:
One timed combat round within a run, followed by a shop.
_Avoid_: round, level, stage

**Danger**:
The difficulty tier a run is played at, 0 through 5. Stored in the save as
`difficulty_value`, which is the storage form, not the name.
_Avoid_: difficulty, difficulty level, level, tier

**Zone**:
One of the game's settings, selected before a run. The base game and Abyssal Terrors are
different zones, and progress is tracked per zone.
_Avoid_: map, area, world, DLC

**Character**:
A playable potato with its own stat modifiers and starting weapon. Identified in save data
by a **character id** such as `character_mage`.
_Avoid_: class, hero, potato

**Archetype**:
A family of characters that reward the same reasoning — the unit of transferable
understanding, and what breadth is measured in.
_Avoid_: build type, playstyle, category

**Build**:
The weapons, items and stats a character has accumulated at a given point in a run.
_Avoid_: loadout, setup, kit

## The data

**Save data**:
What the game records about the player: progress per character, death counts, purchase
counts, lifetime totals. Belongs to the player.
_Avoid_: save game, profile, stats

**Game data**:
What the game records about itself: character modifiers, weapon stats, item effects,
extracted from the installed game. Belongs to the publisher, and is never committed.
_Avoid_: game files, assets, static data

**Save directory**:
The per-player directory the game writes into, named by the player's Steam ID. Holds both
the save data and the live run state. Where it is, is discovered; a caller is handed it,
and never spells it out.
_Avoid_: save folder, profile directory, user directory

**Live run state**:
The file the game keeps the current run in while it is being played, and erases when the
run ends. The thing a snapshot is taken of, not the snapshot itself. Shortens to **live
state** in code, where the run is already implied.
_Avoid_: run state, current run, live save

**Snapshot**:
One capture of the live run state, taken while a run is in progress. Snapshots are grouped
by the run they belong to, and outlive the game erasing that state on death.
_Avoid_: save, capture, dump

## The workspace

**Mission**:
The reason for learning, against which every lesson is judged. Recorded once and revised
deliberately.
_Avoid_: goal, objective

**Lesson**:
One short, self-contained teaching artefact built around retrieval practice. Read before or
after a session, never during one.
_Avoid_: tutorial, exercise, module

**Reference doc**:
A compressed, printable page covering one concept, written to be reread rather than worked
through. Always about a concept, never about a single character.
_Avoid_: cheat sheet, guide, notes

**Learning record**:
A note written when the player's model of the game changes — a heuristic disproved, an
assumption corrected. Not written for an ordinary mistake.
_Avoid_: log, journal entry, retro

**Run record**:
The written outcome of reviewing one run: what happened, the player's hypothesis, the
diagnosis, and the single change to try next.
_Avoid_: report, post-mortem, review

**Drill**:
One pass through `/brotato-prep`: a character's modifiers shown with its name withheld,
four predictions committed, then the reveal and the scoring. The unit the prediction hit
rate is counted in.
_Avoid_: exercise, quiz, practice

**Prediction**:
A committed answer given before a reveal in a prep drill. Scored individually, and tracked
over time as the measure of whether the coaching works.
_Avoid_: guess, answer

**Reveal**:
The moment a drill names the character and scores what was predicted. Everything before it
is withheld; nothing after it can change what was committed.
_Avoid_: answer, solution

**Spec**:
The document describing what is being built and why. One per body of work.
_Avoid_: design doc, RFC

**Ticket**:
One vertical slice of a spec, sized to be completed and verified on its own.
_Avoid_: issue, task, story
