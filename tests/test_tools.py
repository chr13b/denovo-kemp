"""The naming tools and the index lint must agree, otherwise parallel branches drift apart."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "tools" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


new, check_index = load("new"), load("check_index")


def test_generated_names_pass_the_lint():
    now = time.localtime()
    log_name = new.log_name("chris", "experiment", "Chris-01: Baseline scoring!", now)
    assert check_index.NAMING["log/"].match(log_name), log_name
    assert check_index.NAMING["wiki/experiments/"].match("chris-01_baseline-scoring.md")
    assert check_index.NAMING["wiki/experiments/"].match("_template.md")
    # global counters are rejected: they collide across branches
    assert not check_index.NAMING["wiki/experiments/"].match("E-001_baseline.md")


def test_experiment_ids_count_per_handle(tmp_path):
    for name in ["chris-01_a.md", "chris-02_b.md", "alex-07_c.md", "_template.md"]:
        (tmp_path / name).write_text("x")
    assert new.next_exp_id("chris", tmp_path) == "chris-03"
    assert new.next_exp_id("alex", tmp_path) == "alex-08"
    assert new.next_exp_id("sam", tmp_path) == "sam-01"


def test_strict_dirs_need_file_or_subdir_links():
    assert check_index.covered("wiki/experiments/chris-01_a.md", {"wiki/experiments"})
    assert not check_index.covered("wiki/notes.md", {"wiki"})
    assert check_index.covered("tests/test_x.py", {"tests"})


def test_index_is_complete_and_links_resolve():
    out = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "check_index.py")], capture_output=True, text=True
    )
    assert out.returncode == 0, out.stdout + out.stderr


def test_status_runs():
    out = subprocess.run([sys.executable, str(ROOT / "tools" / "status.py")], capture_output=True, text=True)
    assert out.returncode == 0 and "## Experiments" in out.stdout, out.stderr
