#!/usr/bin/env python3
"""Create correctly named entries that can't collide across parallel branches.

    python tools/new.py log <type> "<title>"  # -> log/YYYY-MM-DD_HHMM_<handle>_<type>_<slug>.md
    python tools/new.py exp <slug>            # -> wiki/experiments/<handle>-NN_<slug>.md (prints the ID)

<handle> is $KEMP_HANDLE if set, else the first word of `git config user.name`, lowercased.
Experiment numbers count per handle, so two people can never take the same ID. There is no global counter.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / "log"
EXP_DIR = ROOT / "wiki" / "experiments"
LOG_TYPES = ("setup", "ingest", "experiment", "decision", "fix", "lint", "merge", "submit")


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:50] or "entry"


def handle() -> str:
    name = os.environ.get("KEMP_HANDLE", "")
    if not name:
        try:
            out = subprocess.run(["git", "config", "user.name"], cwd=ROOT, capture_output=True, text=True)
            name = (out.stdout.split() or [""])[0]
        except OSError:
            pass
    h = re.sub(r"[^a-z0-9]", "", name.lower())
    if not h:
        raise SystemExit("new: set KEMP_HANDLE (e.g. in .env) or `git config user.name`")
    return h


def log_name(h: str, kind: str, title: str, now: time.struct_time) -> str:
    return f"{time.strftime('%Y-%m-%d_%H%M', now)}_{h}_{kind}_{slugify(title)}.md"


def new_log(kind: str, title: str) -> Path:
    if kind not in LOG_TYPES:
        raise SystemExit(f"new: log type must be one of: {' '.join(LOG_TYPES)}")
    h, now = handle(), time.localtime()
    path = _unique(LOG_DIR / log_name(h, kind, title, now))
    stamp = time.strftime("%Y-%m-%d %H:%M", now)
    path.write_text(f"# [{stamp}] {kind} | {title} ({h})\n\n- TODO\n", encoding="utf-8")
    return path


def next_exp_id(h: str, exp_dir: Path = EXP_DIR) -> str:
    nums = [int(m.group(1)) for p in exp_dir.glob("*.md") if (m := re.match(rf"{h}-(\d+)_", p.name))]
    return f"{h}-{max(nums, default=0) + 1:02d}"


def new_exp(slug: str) -> Path:
    h = handle()
    exp_id = next_exp_id(h)
    path = EXP_DIR / f"{exp_id}_{slugify(slug)}.md"
    text = (EXP_DIR / "_template.md").read_text(encoding="utf-8")
    for key, val in {
        "<id>": exp_id,
        "<title>": slugify(slug).replace("-", " "),
        "<handle>": h,
        "<date>": time.strftime("%Y-%m-%d"),
    }.items():
        text = text.replace(key, val)
    path.write_text(text, encoding="utf-8")
    return path


def _unique(path: Path) -> Path:
    i = 2
    candidate = path
    while candidate.exists():
        candidate = path.with_name(f"{path.stem}-{i}{path.suffix}")
        i += 1
    return candidate


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="what", required=True)
    lg = sub.add_parser("log", help="new log entry")
    lg.add_argument("type", choices=LOG_TYPES)
    lg.add_argument("title")
    ex = sub.add_parser("exp", help="new experiment page")
    ex.add_argument("slug")
    args = p.parse_args()
    path = new_log(args.type, args.title) if args.what == "log" else new_exp(args.slug)
    rel = path.relative_to(ROOT).as_posix()
    print(rel if args.what == "log" else f"{rel}\nid: {path.name.split('_')[0]}")


if __name__ == "__main__":
    main()
