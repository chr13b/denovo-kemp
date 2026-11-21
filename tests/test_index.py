from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_index_is_complete_and_links_resolve():
    out = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "check_index.py")],
        capture_output=True,
        text=True,
    )
    assert out.returncode == 0, out.stdout + out.stderr
