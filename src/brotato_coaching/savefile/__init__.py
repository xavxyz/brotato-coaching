"""The player's own save: what they have cleared, what has killed them, what they buy.

Everything about *where* the save lives and *how* it is stored is hidden here:
the ``STEAM_ID`` lookup, the glob that finds the save directory without one, the
``_v3_0`` schema version, and the shape of ``difficulties_unlocked``.

Ids come out **raw**. `killed_by_enemies` and `items_bought` are keyed by integer
hashes, and resolving those to names needs the installed game, which is another
package's business. A save is readable without the game installed, and that stays
true.
"""

from ._internal._errors import SaveUnavailable
from ._internal._progress import CharacterProgress, Progress, ZoneProgress, read_progress

__all__ = [
    "CharacterProgress",
    "Progress",
    "SaveUnavailable",
    "ZoneProgress",
    "read_progress",
]
