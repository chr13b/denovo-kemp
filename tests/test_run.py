from __future__ import annotations

import json
from dataclasses import dataclass

from kemp.run import start_run


@dataclass
class C:
    seed: int = 0


def test_start_run_writes_provenance(tmp_path):
    run = start_run("t", C(), seed=0, runs_dir=tmp_path)
    run.log(step=0, x=1.0)
    run.finish(ok=True)

    assert run.dir.parent == tmp_path and run.dir.name.endswith("_t")
    assert json.loads((run.dir / "config.json").read_text()) == {"seed": 0}
    meta = json.loads((run.dir / "meta.json").read_text())
    expected = {
        "git_commit",
        "git_branch",
        "git_dirty",
        "uv_lock_sha256",
        "argv",
        "python",
        "host",
        "gpus",
        "seed",
    }
    assert expected <= meta.keys()
    assert len((run.dir / "metrics.jsonl").read_text().splitlines()) == 1
    assert json.loads((run.dir / "summary.json").read_text())["ok"] is True
