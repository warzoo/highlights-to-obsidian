"""
Lightweight logging for Highlights to Obsidian.

get_logger() returns a configured logger that writes to calibre's debug output (visible by running
`calibre-debug -g`) and, when running inside calibre, to a small rotating log file next to the
plugin's config (highlights_to_obsidian.log). This gives a place to look -- with full tracebacks --
when a send fails, instead of guessing.

It is import-safe outside calibre (e.g. in unit tests): the calibre-only bits are imported lazily and
any failure is swallowed, so importing this module never requires a running calibre.
"""
import logging
import os

_LOGGER_NAME = "highlights_to_obsidian"
_configured = False


def _log_file_path():
    """path to the plugin's log file inside calibre's config dir, or None when not in calibre."""
    try:
        from calibre.constants import config_dir
    except Exception:
        return None  # not running inside calibre -> no file logging
    try:
        plugins_dir = os.path.join(config_dir, "plugins")
        os.makedirs(plugins_dir, exist_ok=True)
        return os.path.join(plugins_dir, "highlights_to_obsidian.log")
    except Exception:
        return None


def get_logger() -> logging.Logger:
    """returns the shared plugin logger, configuring its handlers once on first use."""
    global _configured
    logger = logging.getLogger(_LOGGER_NAME)
    if _configured:
        return logger

    logger.setLevel(logging.DEBUG)
    logger.propagate = False  # don't double-log through the root logger
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] h2o: %(message)s")

    # always log to the stream so messages show up in calibre's debug output.
    stream = logging.StreamHandler()
    stream.setFormatter(fmt)
    logger.addHandler(stream)

    # additionally log to a small rotating file when running inside calibre. best-effort: never let a
    # logging problem stop highlights from being sent.
    log_path = _log_file_path()
    if log_path:
        try:
            from logging.handlers import RotatingFileHandler
            file_handler = RotatingFileHandler(log_path, maxBytes=512 * 1024, backupCount=2,
                                               encoding="utf-8")
            file_handler.setFormatter(fmt)
            logger.addHandler(file_handler)
        except Exception:
            pass

    _configured = True
    return logger
