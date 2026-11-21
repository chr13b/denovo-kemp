"""Smoke test: shows that the environment and the run bookkeeping work end to end.

    uv run python scripts/00_smoke.py --n=5

It is also the TEMPLATE for every pipeline script. Copy it to scripts/NN_verb_noun.py, keep the shape:
docstring with a usage line -> Config dataclass -> main(cfg) -> start_run -> write outputs into run.dir.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from kemp.config import parse
from kemp.run import start_run


@dataclass
class Config:
    name: str = "smoke"  # suffix of the run directory
    seed: int = 0
    n: int = 3  # number of fake steps to log


def main(cfg: Config) -> None:
    run = start_run(cfg.name, cfg, seed=cfg.seed)
    values = [random.random() for _ in range(cfg.n)]
    for step, value in enumerate(values):
        run.log(step=step, value=value)
    run.finish(ok=True, mean_value=sum(values) / len(values) if values else None)


if __name__ == "__main__":
    main(parse(Config))
