#!/usr/bin/env python3
"""Lint the knowledge layer: the automated version of the "lint" step in Karpathy's LLM wiki.

    python tools/check_index.py

Exits 1 on:
  dead link: a relative link in a tracked .md file points to a path that doesn't exist
             (LOG.md is exempt because it is append-only and history may mention removed files)
  orphan:    a tracked file that INDEX.md doesn't cover

Coverage rule: files under STRICT_DIRS need their own link in INDEX.md. Any other file is covered by
a link to itself or to one of its parent directories (e.g. `tests/`).
"""

from __future__ import annotations

import posixpath
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STRICT_DIRS = ("wiki/", "raw/", "src/", "scripts/", "tools/", "configs/", "results/", ".claude/skills/")
EXEMPT_FILES = {"INDEX.md", "uv.lock"}  # the index itself; generated lockfile
EXEMPT_NAMES = {".gitkeep", "__init__.py"}
NO_LINK_CHECK = {"LOG.md"}
CODE = re.compile(r"```.*?```|`[^`\n]*`", re.S)
LINK = re.compile(r"\]\(\s*<?([^)>\s]+)")
URL = re.compile(r"^[a-z][a-z0-9+.-]*:", re.I)


def tracked_files() -> list[str]:
    """Files git tracks or would track (respects .gitignore)."""
    cmd = ["git", "ls-files", "--cached", "--others", "--exclude-standard"]
    out = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, check=True).stdout
    return sorted(f for f in out.splitlines() if (ROOT / f).is_file())


def links(md: Path) -> list[str]:
    """Relative link targets in a markdown file, ignoring code spans, URLs and pure anchors."""
    text = CODE.sub("", md.read_text(encoding="utf-8"))
    targets = (t.split("#")[0] for t in LINK.findall(text) if not URL.match(t))
    return [t for t in targets if t]


def norm(path: str) -> str:
    return posixpath.normpath(path.replace("\\", "/")).rstrip("/")


def main() -> int:
    try:
        files = tracked_files()
    except (OSError, subprocess.CalledProcessError) as e:
        print(f"check_index: needs git and a git repo ({e})")
        return 1
    problems = []

    for f in files:
        if f.endswith(".md") and f not in NO_LINK_CHECK:
            for target in links(ROOT / f):
                if not ((ROOT / f).parent / target).exists():
                    problems.append(f"dead link  {f} -> {target}")

    indexed = {norm(t) for t in links(ROOT / "INDEX.md")}
    for f in files:
        if f in EXEMPT_FILES or posixpath.basename(f) in EXEMPT_NAMES or f in indexed:
            continue
        parents = {norm(str(p)) for p in Path(f).parents} - {"."}
        if f.startswith(STRICT_DIRS) or not parents & indexed:
            problems.append(f"orphan     {f}  (add a one-line entry to INDEX.md)")

    for p in problems:
        print(p)
    print(f"check_index: {len(files)} files, {len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
