"""The derivation drill: predict a character's plan before being told who it is.

The mission this workspace serves is derivation, not results, so the thing it
has to make impossible is recall. A drill shows a character's extracted
modifiers and its starting weapon with every trace of its name removed, takes
four committed predictions — primary stat, secondary stat, weapon class, and the
wave the build is expected to break at — and only then names it and scores each
prediction on its own.

    drills = PrepDrills(Path("drills"))
    opened = drills.open_drill(read_catalog(Path("data")))
    drills.commit(opened["drill_id"], primary_stat=..., secondary_stat=...,
                  weapon_class=..., weakest_wave=...)
    drills.reveal(opened["drill_id"])

Everything about *how* a drill stays honest is hidden here: which fields of a
character record may be shown, how its name is struck out of the ones that are,
that the predictions are scored against answers written down at the moment the
drill opens so a patch
cannot move them, and that a reveal is refused until four predictions exist.

Three predictions are scored against the game's own data at the reveal. The
fourth is about a run that has not happened yet, so it stays `pending` until
`settle` is given the wave the run actually broke at — `history` reports the hit
rate per dimension, counting only what could have been wrong.

Every method returns the JSON document the matching CLI mode prints, and every
refusal is a `PrepRefused` carrying the sentence to show the player.

Ticket #10 calls the third prediction a "weapon archetype". `CONTEXT.md` reserves
**archetype** for a family of characters, so this package says **weapon class**
throughout, as `docs/research/weapon-classes.md` does.
"""

from ._internal._drills import PrepDrills, PrepRefused

__all__ = ["PrepDrills", "PrepRefused"]
