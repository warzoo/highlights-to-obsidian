"""
Pure helper functions with no calibre or Qt dependencies.

Keeping these here (instead of scattered across button_actions.py / config.py / highlight_sender.py)
means the time-parsing, dedup, and file-writing logic lives in one place and can be unit-tested
standalone, without a running calibre.
"""
import os
import subprocess
import sys
import time
from typing import Dict, Tuple

# format used for prefs like last_send_time, e.g. "2022-09-10 20:32:08"
SEND_TIME_FORMAT = "%Y-%m-%d %H:%M:%S"
# calibre stores highlight timestamps like "2022-09-10T20:32:08.820Z" (the trailing "Z" means UTC)
CALIBRE_TIME_FORMAT = "%Y-%m-%dT%H:%M:%S"


def parse_send_time(send_time: str) -> float:
    """parse a 'YYYY-MM-DD HH:MM:SS' string (as stored in prefs) into a unix timestamp."""
    return time.mktime(time.strptime(send_time, SEND_TIME_FORMAT))


def parse_highlight_time(timestamp: str) -> float:
    """parse a calibre annotation timestamp (e.g. '2022-09-10T20:32:08.820Z') into a unix timestamp.

    milliseconds and the trailing 'Z' are ignored by only looking at the first 19 characters.
    """
    return time.mktime(time.strptime(timestamp[:19], CALIBRE_TIME_FORMAT))


def annotation_user(web_user: bool, web_user_name: str) -> Tuple[str, str]:
    """returns the (type, name) tuple used for calibre's all_annotations(restrict_to_user=...)."""
    return ("web", web_user_name) if web_user else ("local", "viewer")


def is_unsent_or_edited(uuid: str, timestamp: str, sent_highlights: Dict[str, str]) -> bool:
    """returns True if a highlight should be treated as new.

    A highlight is "new" if it has never been sent, or if its timestamp is newer than when it was
    last sent (i.e. it was edited since). This is what makes repeated sends idempotent instead of
    relying purely on a last-send time.

    :param uuid: the highlight's calibre uuid
    :param timestamp: the highlight's current calibre timestamp
    :param sent_highlights: dict of {uuid: timestamp} for highlights already sent
    """
    if uuid not in sent_highlights:
        return True
    return parse_highlight_time(timestamp) > parse_highlight_time(sent_highlights[uuid])


def note_path(vault_path: str, note_file: str) -> str:
    """builds the absolute .md path for a note inside the vault.

    note_file may contain '/' to indicate subfolders, the same convention obsidian note titles use.
    """
    parts = [p for p in note_file.split("/") if p != ""]
    return os.path.join(vault_path, *parts) + ".md"


def write_note_to_file(vault_path: str, note_file: str, note_content: str, append: bool = True) -> str:
    """writes note_content to a .md file inside the vault folder, creating subfolders as needed.

    This is the filesystem alternative to the obsidian:// URI: it has no length limit, doesn't need
    Obsidian to be open, and can't silently drop notes.

    :param append: if True, append to the file when it already exists; otherwise overwrite it.
    :return: the path that was written to.
    """
    path = note_path(vault_path, note_file)
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "a" if append else "w", encoding="utf-8") as f:
        f.write(note_content)
    return path


def native_open(uri, platform=None, startfile=None, run=None) -> str:
    """opens a uri with the OS's default handler using a native command instead of Python's
    webbrowser: os.startfile on Windows, `open` on macOS, `xdg-open` on Linux/other.

    This avoids opening a web browser and may allow longer uris (larger notes) on some systems --
    though that isn't guaranteed; the reliable way to avoid the uri length limit is to write notes
    directly to vault files.

    startfile/run are injectable so this can be unit-tested without actually opening anything.

    :return: a short string naming the method used ("startfile", "open", or "xdg-open").
    """
    platform = platform if platform is not None else sys.platform
    if platform.startswith("win32"):
        (startfile or os.startfile)(uri)
        return "startfile"
    if platform.startswith("darwin"):
        (run or subprocess.run)(["open", uri])
        return "open"
    (run or subprocess.run)(["xdg-open", uri])
    return "xdg-open"
