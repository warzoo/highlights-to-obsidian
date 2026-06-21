"""
Custom exception types for Highlights to Obsidian.

These let button_actions.py tell *why* a send failed -- a configuration problem the user can fix, a
URI that was too long, or a file that couldn't be written -- and show a targeted error dialog instead
of one generic "something went wrong". Pure stdlib, so it can be imported anywhere (including tests).
"""


class H2OError(Exception):
    """Base class for errors this plugin raises and reports to the user."""


class H2OConfigError(H2OError):
    """A configuration problem the user needs to fix (e.g. the vault folder path isn't set)."""


class H2OURIError(H2OError):
    """Sending through the obsidian:// URI failed -- usually the note/URI is too long."""


class H2OWriteError(H2OError):
    """Writing a note directly to a vault file failed (permissions, bad path, disk full, ...)."""
