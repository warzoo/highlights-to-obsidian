#!/usr/bin/env python3
"""Build an installable calibre plugin zip for Highlights to Obsidian.

calibre installs a plugin from a single zip whose *root* holds the import-name
marker and the plugin code. So this script flattens the contents of ``h2o/``
into the zip root (e.g. ``h2o/config.py`` -> ``config.py``, ``h2o/images/icon.png``
-> ``images/icon.png``) and adds the repo's LICENSE and README.md alongside it.

Build artifacts (``__pycache__``, ``*.pyc``) and the editable icon source
(``*.pdn``) are never included, so the installable zip stays minimal.

Output: ``zip/highlights-to-obsidian-<version>.zip`` (version from h2o/__init__.py)

Usage:  python build.py
"""

import ast
import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "h2o"
OUT_DIR = ROOT / "zip"

# repo-root files to include at the zip root, alongside the flattened plugin code
EXTRA_ROOT_FILES = ["LICENSE", "README.md"]

# things that must never end up in the installable plugin
EXCLUDE_DIRS = {"__pycache__"}
EXCLUDE_SUFFIXES = {".pyc", ".pyo", ".pdn"}  # .pdn is the Paint.NET icon source


def read_version() -> str:
    """Parse ``_version = (x, y, z)`` from h2o/__init__.py without importing it
    (importing requires calibre, which isn't available outside the app)."""
    text = (SRC / "__init__.py").read_text(encoding="utf-8")
    m = re.search(r"^_version\s*=\s*(\([^)]*\))", text, re.MULTILINE)
    if not m:
        raise SystemExit("could not find _version in h2o/__init__.py")
    return ".".join(str(x) for x in ast.literal_eval(m.group(1)))


def iter_src_files():
    """Yield (path, arcname) for every file under h2o/ that belongs in the zip,
    with arcname relative to h2o/ so the contents land at the zip root."""
    for path in sorted(SRC.rglob("*")):
        if path.is_dir():
            continue
        rel = path.relative_to(SRC)
        if any(part in EXCLUDE_DIRS for part in rel.parts):
            continue
        if path.suffix in EXCLUDE_SUFFIXES:
            continue
        yield path, rel.as_posix()


def main():
    version = read_version()
    OUT_DIR.mkdir(exist_ok=True)
    out = OUT_DIR / f"highlights-to-obsidian-{version}.zip"

    added = []
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for path, arcname in iter_src_files():
            z.write(path, arcname)
            added.append(arcname)
        for name in EXTRA_ROOT_FILES:
            src = ROOT / name
            if src.exists():
                z.write(src, name)
                added.append(name)

    print(f"built {out.relative_to(ROOT).as_posix()}  ({len(added)} files)")
    for name in added:
        print(f"  {name}")


if __name__ == "__main__":
    main()
