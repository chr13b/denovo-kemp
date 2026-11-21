"""Every project path, defined once. Import from here and never hardcode paths.

Put data/ or runs/ on a big scratch disk by setting the env vars below in .env
(`uv run --env-file .env ...`) or in your shell.
"""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # src/kemp/paths.py -> repo root (editable install)

RAW = ROOT / "raw"  # immutable sources (brief, papers)
WIKI = ROOT / "wiki"  # maintained knowledge
CONFIGS = ROOT / "configs"  # reusable run configs
RESULTS = ROOT / "results"  # curated, tracked outputs
DATA = Path(os.environ.get("KEMP_DATA_DIR", ROOT / "data"))  # bulk inputs, gitignored
RUNS = Path(os.environ.get("KEMP_RUNS_DIR", ROOT / "runs"))  # one dir per execution, gitignored
