"""The two ways this package fails: no directory, or no save in it."""

from __future__ import annotations


class SaveUnavailable(Exception):
    """No save could be read, and the message says what to do about it.

    The message is written for the player and is what the CLI prints instead of
    a traceback. It never echoes the Steam ID: that is the one value in this
    system that should not travel, and an error message is the most-pasted text
    there is.
    """


class SaveDirectoryUnavailable(SaveUnavailable):
    """This player's Brotato directory could not be found.

    A subclass, because failing to find the directory is one way of failing to
    read a save, and a caller that only wants "is there a save to report on?"
    should keep catching one thing. The distinction is for the caller that does
    not want a save at all: `runlog` needs this same directory to find the live
    run state, and a missing save is none of its business.
    """
