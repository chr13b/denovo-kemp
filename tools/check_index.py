#!/usr/bin/env python3
"""Lint the knowledge layer: the automated version of the "lint" step in Karpathy's LLM wiki.

    python tools/check_index.py

Exits 1 on:
  dead link:  a relative link in a tracked .md file points to a missing path (log/ is exempt: it's history)
  orphan:     a tracked file that INDEX.md doesn't cover
  duplicate:  INDEX.md lists the same path twice (typical after a union merge, see CONTRIBUTING.md)
  bad name:   a log/ or wiki/experiments/ file that breaks the collision-free naming scheme

Coverage rule: a file is covered by a link to itself or to a parent directory. In STRICT_DIRS the
top-level link (e.g. `src/`) is not enough. Link the file itself, or a subdirectory such as
`wiki/experiments/`.
"""

from __future__ import annotations

import posixpath
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STRICT_DIRS = ("wiki/", "raw/", "src/", "scripts/", "tools/", "results/", ".claude/skills/")
EXEMPT_FILES = {"INDEX.md"}
EXEMPT_NAMES = {".gitkeep", "__init__.py"}
NAMING = {  # dir -> filename pattern (keeps parallel branches from colliding)
    "log/": re.compile(r"^\d{4}-\d{2}-\d{2}_\d{4}_[a-z0-9]+_[a-z]+_[a-z0-9-]+\.md$"),
    "wiki/experiments/": re.compile(r"^(_template|[a-z0-9]+-\d{2,}_[a-z0-9-]+)\.md$"),
}
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


def covered(f: str, indexed: set[str]) -> bool:
    if f in indexed:
        return True
    parents = {norm(str(p)) for p in Path(f).parents} - {"."}
    strict_roots = {norm(d) for d in STRICT_DIRS if f.startswith(d)}
    return bool((parents - strict_roots) & indexed)


def main() -> int:
    try:
        files = tracked_files()
    except (OSError, subprocess.CalledProcessError) as e:
        print(f"check_index: needs git and a git repo ({e})")
        return 1
    problems = []

    for f in files:
        if f.endswith(".md") and not f.startswith("log/"):
            for target in links(ROOT / f):
                if not ((ROOT / f).parent / target).exists():
                    problems.append(f"dead link  {f} -> {target}")

    index_links = [norm(t) for t in links(ROOT / "INDEX.md")]
    for path, count in Counter(index_links).items():
        if count > 1:
            problems.append(f"duplicate  INDEX.md lists {path} {count}x (merge leftover? keep one line)")
    indexed = set(index_links)

    for f in files:
        name = posixpath.basename(f)
        if f in EXEMPT_FILES or name in EXEMPT_NAMES:
            continue
        if not covered(f, indexed):
            problems.append(f"orphan     {f}  (add a one-line entry to INDEX.md)")
        for d, pattern in NAMING.items():
            if posixpath.dirname(f) + "/" == d and not pattern.match(name):
                problems.append(f"bad name   {f}  (create it with tools/new.py, see CONTRIBUTING.md)")

    for p in problems:
        print(p)
    print(f"check_index: {len(files)} files, {len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
