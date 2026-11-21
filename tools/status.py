#!/usr/bin/env python3
"""Where are we? Prints the experiments table and the most recent log entries. Read-only.

    python tools/status.py        # all experiments + the last 10 log entries
    python tools/status.py -n 30  # more log entries

Both are computed from one-file-per-entry directories, so there is no shared table to conflict on merges.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXP_DIR = ROOT / "wiki" / "experiments"
LOG_DIR = ROOT / "log"


def field(text: str, name: str) -> str:
    m = re.search(rf"^\s*-\s*\*\*{name}:\*\*\s*(.*)$", text, re.M)
    return m.group(1).strip() if m else "?"


def experiments() -> list[tuple[str, str, str, str]]:
    rows = []
    for p in sorted(EXP_DIR.glob("*.md")):
        if p.name.startswith("_"):
            continue
        text = p.read_text(encoding="utf-8")
        rows.append((p.name.split("_")[0], field(text, "Status"), field(text, "Question"), p.name))
    return rows


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("-n", type=int, default=10, help="number of recent log entries")
    n = p.parse_args().n

    rows = experiments()
    print(f"## Experiments ({len(rows)})  wiki/experiments/\n")
    if rows:
        print("| ID | Status | Question | File |\n|----|--------|----------|------|")
        for row in rows:
            print("| " + " | ".join(row) + " |")
    else:
        print("_none yet: `python tools/new.py exp <slug>`_")

    entries = sorted(LOG_DIR.glob("*.md"))[-n:]
    print(f"\n## Last {len(entries)} log entries  log/\n")
    for e in entries:
        print(e.read_text(encoding="utf-8").strip() + "\n")


if __name__ == "__main__":
    main()
