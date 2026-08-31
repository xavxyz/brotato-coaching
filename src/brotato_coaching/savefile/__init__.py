"""The player's own save: what they have cleared, what has killed them, what they buy.

Everything about *where* the player's files live and *how* the save is stored is
hidden here: the ``STEAM_ID`` lookup, the shape of a Steam save directory, the
``_v3_0`` schema version, and the shape of ``difficulties_unlocked``.

`save_directory()` is the one answer to "where does this player's Brotato live",
and it is public because it is not only this package's question: the live run
state sits in the same directory, and `runlog` composes its own filename onto
this answer rather than going looking a second time.

Ids come out **raw**. `killed_by_enemies` and `items_bought` are keyed by integer
hashes, and resolving those to names needs the installed game, which is another
package's business. A save is readable without the game installed, and that stays
true: `Progress.as_json_object` will borrow a function from id to name if a caller
has one, and reports digits if it does not.
"""

from ._internal._discovery import save_directory, save_file
from ._internal._errors import SaveDirectoryUnavailable, SaveUnavailable
from ._internal._progress import CharacterProgress, Progress, ZoneProgress, read_progress

__all__ = [
    "CharacterProgress",
    "Progress",
    "SaveDirectoryUnavailable",
    "SaveUnavailable",
    "ZoneProgress",
    "read_progress",
    "save_directory",
    "save_file",
]
