"""The one failure this package has: it could not read a save."""

from __future__ import annotations


class SaveUnavailable(Exception):
    """No save could be read, and the message says what to do about it.

    Every way of failing to reach a save — no Brotato directory, no save in it,
    two saves and no way to choose, a file that is empty or is not a save — is
    the same failure to a caller: there is nothing to report on. The distinction
    that matters is in the message, which is written for the player and is what
    the CLI prints instead of a traceback.
    """
