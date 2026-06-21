"""
Pure helper functions with no calibre or Qt dependencies.

Keeping these here (instead of scattered across button_actions.py / config.py / highlight_sender.py)
means the time-parsing, dedup, and file-writing logic lives in one place and can be unit-tested
standalone, without a running calibre.
"""
import os
import re
import string
import subprocess
import sys
import time
from typing import Dict, List, Tuple

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


def yaml_safe(value) -> str:
    """quote a value so it is safe to use as a YAML frontmatter value (e.g. a book title containing
    ':'). wraps it in double quotes and escapes characters that would break a double-quoted scalar."""
    escaped = (str(value).replace("\\", "\\\\")
                         .replace('"', '\\"')
                         .replace("\n", "\\n")
                         .replace("\r", "\\r"))
    return '"' + escaped + '"'


class _PluginFormatter(string.Formatter):
    """str.format-style formatter that adds a ':yaml' format spec for frontmatter-safe values."""

    def format_field(self, value, format_spec):
        if format_spec == "yaml":
            return yaml_safe(value)
        return super().format_field(value, format_spec)


_FORMATTER = _PluginFormatter()


def format_with(template: str, mapping) -> str:
    """like template.format_map(mapping), but also supports a ':yaml' format spec (e.g. {title:yaml})
    that makes a value safe to use inside Obsidian YAML frontmatter.

    mapping should be a SafeDict (or similar) so unknown placeholders are left intact.
    """
    return _FORMATTER.vformat(template, (), mapping)


def parse_color_labels(text: str) -> Dict[str, str]:
    """parses lines of 'color = label' into a {color: label} dict for the {colorlabel} option.

    blank lines and lines without '=' are ignored. colors are matched case-insensitively, so they
    are stored lowercased.
    """
    labels = {}
    for line in text.splitlines():
        if "=" not in line:
            continue
        color, _, label = line.partition("=")
        color = color.strip().lower()
        if color:
            labels[color] = label.strip()
    return labels


def parse_color_filter(text: str) -> List[str]:
    """parses a comma-separated list of colors into a list of lowercased names.

    empty text -> [] which means "send all colors".
    """
    return [c.strip().lower() for c in text.split(",") if c.strip()]


def note_path(vault_path: str, note_file: str) -> str:
    """builds the absolute .md path for a note inside the vault.

    note_file may contain '/' to indicate subfolders, the same convention obsidian note titles use.

    each folder/file component is stripped of surrounding whitespace, so a stray space (e.g. a title
    template like "Folder /{title}") doesn't create a separate, identical-looking folder with a
    trailing space -- which the filesystem treats as distinct from one without.
    """
    parts = [p.strip() for p in note_file.split("/")]
    parts = [p for p in parts if p != ""]
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


# ---- insert-in-order merge mode (issue #13) ----
# each highlight written to a note is prefixed with a hidden marker that records its position so new
# highlights can be inserted in the right place later, without disturbing the user's manual edits.
# %%...%% is Obsidian's comment syntax: hidden in reading view, and unlike HTML comments it has no
# "--" restriction.
MARKER_RE = re.compile(r'%%h2o uuid="([^"]*)" sort="([^"]*)"%%')


def encode_sort_value(value) -> str:
    """encodes a sort key into a string that compares in the same order, stays small, and is safe
    inside an h2o marker. tuples of ints (e.g. the location sort key) become fixed-width zero-padded
    digits so lexicographic order matches numeric order; other values become a sanitized string."""
    if isinstance(value, tuple):
        return "".join(f"{int(n):010d}" for n in value)
    return str(value).replace('"', "").replace("%", "")[:200]


def make_block(uuid: str, sort_value, body: str) -> Dict[str, str]:
    """builds a note block for one highlight: a hidden marker line (recording uuid + encoded sort
    position) followed by the formatted body. returns {uuid, sort, text}."""
    sort = encode_sort_value(sort_value)
    text = f'%%h2o uuid="{uuid}" sort="{sort}"%%\n{body}'
    if not text.endswith("\n"):
        text += "\n"
    return {"uuid": uuid, "sort": sort, "text": text}


def parse_note(text: str):
    """splits an existing note into (preamble, blocks).

    blocks is a list of {uuid, sort, text} where text is the full block (its marker line through just
    before the next marker, or the end). preamble is everything before the first h2o marker (e.g. the
    header and any content the user added above the highlights); it is preserved untouched.
    """
    matches = list(MARKER_RE.finditer(text))
    if not matches:
        return text, []
    preamble = text[:matches[0].start()]
    blocks = []
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        blocks.append({"uuid": m.group(1), "sort": m.group(2), "text": text[m.start():end]})
    return preamble, blocks


def merge_note(existing_text: str, header: str, new_blocks) -> str:
    """merges new_blocks into an existing note, keeping all h2o blocks sorted by their recorded sort
    value while preserving the preamble and each block's content (including the user's manual edits).

    dedup/update is by uuid: a new block replaces an existing one with the same uuid (so edited
    highlights are updated in place). new uuids are inserted in sorted position.
    """
    if existing_text:
        preamble, blocks = parse_note(existing_text)
    else:
        preamble, blocks = header, []

    by_uuid = {b["uuid"]: b for b in blocks}
    for nb in new_blocks:
        by_uuid[nb["uuid"]] = nb  # add new, or update an edited highlight in place

    merged = sorted(by_uuid.values(), key=lambda b: b["sort"])  # sorted() is stable
    if not merged:
        return preamble

    if preamble and not preamble.endswith("\n"):
        preamble += "\n"
    body = "".join(b["text"] if b["text"].endswith("\n") else b["text"] + "\n" for b in merged)
    return preamble + body


def read_note_file(vault_path: str, note_file: str) -> str:
    """returns the current content of the note's .md file inside the vault, or '' if it doesn't exist."""
    path = note_path(vault_path, note_file)
    if not os.path.isfile(path):
        return ""
    with open(path, encoding="utf-8") as f:
        return f.read()
