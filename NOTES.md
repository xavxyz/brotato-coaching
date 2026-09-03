# Notes

Working preferences for this workspace, and the named sources whose claims appear in it.
Anything written here is a standing decision: lessons, reference docs and skills follow it
without asking again.

## Preferences

**Lessons are read before or after a session, never during one.**
Playing is hacking time. Nothing in this workspace may ask for attention while a run is in
progress — that is why the run watcher is silent and why no lesson is ever "consult mid-wave".

**Everything is written in English.**
The workspace, the lessons, the run records and the commit messages, throughout.

**Reference docs are about concepts, never about a single character.**
One page per concept — stat math, shop economy, wave scaling, weapon classes. Never 64
lookup tables. A page that can only be applied to one character has failed the mission, which
is to derive a plan for a character never played.

**Claims are cited or derived, and every page is patch-stamped.**
A cited claim in a lesson or reference doc names its source; a derived claim names the field
of extracted game data it comes from; and every page carries the patch stamp saying which
build it was written against. See `RESOURCES.md` for the source list.

**JPot's heuristics are recorded and attributed, never silently merged.**
When a heuristic of JPot's and the extracted game data disagree, both are shown and the
disagreement is named. A contradiction is a learning moment; averaging it away destroys one.

## Named sources

### JPot

The friend who coached the Danger 5 Abyssal Terrors win described in `MISSION.md`.
300+ hours played, every character cleared at Danger 5. Human, experience-based, unversioned:
high trust on judgement and priorities, no trust on exact numbers, and possibly anchored on an
older patch than the one in `MISSION.md`.

Cite as `[JPot]` inline. A heuristic is recorded here only once it has been stated in those
terms, and it stays here verbatim even after data contradicts it — the contradiction is the
lesson.

JPot is this workspace's sole wisdom source, and the reason the mission exists: the coached
Danger 5 wins measure *their* model, not the player's. Writing their heuristics down is how that
model becomes transferable.

A heuristic is a **hypothesis, not a source**. It is tested against `RESOURCES.md` and against
extracted game data, and it is never listed in `RESOURCES.md` as a row.

#### Heuristics recorded

_None recorded yet — tracked by ticket #16._ They are captured as JPot states them, each with
the context it was given in and the wave or decision it applies to. Where one is later
contradicted by the extracted game data, the contradiction is written under the heuristic and
the heuristic stays as stated.

The hooks below mirror the four research topics in `RESOURCES.md`, so a heuristic can be dropped
next to the mechanics it bears on.

##### On stats and damage

_Not yet captured._ See `docs/research/stat-mechanics.md`.

##### On the shop

_Not yet captured._ See `docs/research/shop-economy.md`. Worth asking about specifically: when to
stop rerolling, and whether they lock items to hedge against price inflation.

##### On waves and Danger

_Not yet captured._ See `docs/research/wave-scaling.md`. Worth asking about specifically: open
question `WAVE-Q1` in `RESOURCES.md` — which Danger tier first adds enemy HP and damage. A
300-hour player answers that in one sentence, and it is the exact step this player is trying to
close.

##### On weapons and classes

_Not yet captured._ See `docs/research/weapon-classes.md`. Worth asking about specifically: how
they decide a weapon's scaling is worth committing to, given that only 34 of 79 weapons gain
anything from a single point of Melee Damage.

##### On reading an unfamiliar character

_Not yet captured._ This is the highest-value hook of the five: user story 2 of the spec is being
able to derive a plan for a character never played, which is precisely what the player currently
cannot do without JPot in the room.

Open questions have one home, and it is not this file: disagreements between sources — JPot
included — are recorded under _Open questions_ in `RESOURCES.md`.
