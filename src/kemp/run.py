"""Run bookkeeping: every execution gets its own runs/<timestamp>_<name>/ directory with full provenance.

    run = start_run("baseline", cfg, seed=cfg.seed)  # -> runs/20261121-101500_baseline/
    ...                                              # write outputs into run.dir
    run.log(step=0, score=1.23)                      # one JSON line per call -> metrics.jsonl
    run.finish(best_score=1.23)                      # -> summary.json

Files in the run directory:
    config.json    the exact config
    meta.json      git commit + dirty flag, argv, Python, platform, seed, start time
    metrics.jsonl  streamed metrics
    summary.json   final numbers; the only numbers quoted in the wiki
"""

from __future__ import annotations

import dataclasses
import json
import os
import platform
import random
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from kemp.paths import ROOT, RUNS


@dataclasses.dataclass
class Run:
    dir: Path

    def log(self, **metrics: Any) -> None:
        with open(self.dir / "metrics.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps({"t": round(time.time(), 3), **metrics}) + "\n")

    def finish(self, **summary: Any) -> None:
        _write_json(self.dir / "summary.json", {"finished": _now(), **summary})
        print(f"[run] done -> {self.dir}")


def start_run(name: str, cfg: Any = None, seed: int | None = None, runs_dir: Path = RUNS) -> Run:
    """Create the run directory, write the config and provenance, and seed the RNGs."""
    run_dir = Path(runs_dir) / f"{time.strftime('%Y%m%d-%H%M%S')}_{name}"
    run_dir.mkdir(parents=True, exist_ok=False)
    if seed is not None:
        seed_everything(seed)
    config = dataclasses.asdict(cfg) if dataclasses.is_dataclass(cfg) else dict(cfg or {})
    _write_json(run_dir / "config.json", config)
    _write_json(
        run_dir / "meta.json",
        {
            "name": name,
            "started": _now(),
            "git_commit": _git("rev-parse", "HEAD"),
            "git_dirty": bool(_git("status", "--porcelain")),
            "argv": sys.argv,
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "seed": seed,
        },
    )
    print(f"[run] {run_dir}")
    return Run(run_dir)


def seed_everything(seed: int) -> None:
    """Seed Python, NumPy and PyTorch (whichever are installed)."""
    random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    try:
        import numpy as np

        np.random.seed(seed)
    except ImportError:
        pass
    try:
        import torch

        torch.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass


def _git(*args: str) -> str | None:
    try:
        out = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=True)
        return out.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")


def _write_json(path: Path, obj: Any) -> None:
    path.write_text(json.dumps(obj, indent=2, default=str) + "\n", encoding="utf-8")
