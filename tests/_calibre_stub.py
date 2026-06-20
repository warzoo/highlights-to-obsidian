"""
Lets the plugin's pure logic be imported in unit tests without a running calibre.

highlight_sender.py does `from calibre_plugins.highlights_to_obsidian.config import prefs`, and the
real config.py imports qt.core (only available inside calibre). install() registers a fake package
and a fake config module in sys.modules so the real, qt-free modules (utils.py, highlight_sender.py)
can be imported directly. utils.py and highlight_sender.py themselves are loaded for real from h2o/.
"""
import os
import sys
import types

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
H2O = os.path.join(ROOT, "h2o")

# the defaults HighlightSender.__init__ reads from prefs.defaults
_DEFAULTS = {
    "library_name": "Calibre Library",
    "vault_name": "My Vault",
    "title_format": "Books/{title} by {authors}",
    "body_format": "\n{blockquote}\n\n{notes}\n\n---\n",
    "no_notes_format": "\n{blockquote}\n\n---\n",
    "header_format": "\n{title}\n\n---\n",
    "sort_key": "location",
}

_installed = False


def install():
    global _installed
    if _installed:
        return

    calibre_plugins = sys.modules.get("calibre_plugins") or types.ModuleType("calibre_plugins")
    calibre_plugins.__path__ = []
    sys.modules["calibre_plugins"] = calibre_plugins

    pkg = types.ModuleType("calibre_plugins.highlights_to_obsidian")
    pkg.__path__ = [H2O]  # so submodules (utils, highlight_sender) load from the real plugin dir
    sys.modules["calibre_plugins.highlights_to_obsidian"] = pkg

    config = types.ModuleType("calibre_plugins.highlights_to_obsidian.config")

    class _Prefs(dict):
        pass

    config.prefs = _Prefs()
    config.prefs.defaults = dict(_DEFAULTS)
    sys.modules["calibre_plugins.highlights_to_obsidian.config"] = config

    _installed = True
