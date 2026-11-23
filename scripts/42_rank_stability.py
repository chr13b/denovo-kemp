"""Rank stability of the K1-K5 / K1-K6 ranking under scoring variants.

    uv run python scripts/42_rank_stability.py --base="P=runs/..._rs-nearest-P/weighted_scores.tsv,..." \
        --od2="P=runs/..._rs-od2-P/weighted_scores.tsv,..."

Inputs are `weighted_scores.tsv` files of `scripts/40_score_metrics_pack.py` (one per set; run
it with `--base_atom=nearest` for --base, `--base_atom=od2` for --od2). Only designs with 5 seeds are ranked.
Variants (each re-ranks all designs; the table shows the baseline top 15 and who stays in the top 8):
  base     mean over seeds of the per-seed K1-K5 total (the headline score)
  K1_od2   base contact = OD2/OE2 only (also the burial origin)
  K2_med   angle term from the angle AT the heteroatom (A1 base, A4 donor), degrees outside the crystal range
           (A1 125.13-133.08, A4 130.40-145.01; medians 128.4 / 134.0); worse of that and the ring-plane term
  K1-K6    ipTM term on (quality control only, not an organizer criterion)
  meanM    score of the mean metrics (not mean of per-seed scores)
  worst    worst single seed's K1-K5 total
"""

from __future__ import annotations

import csv
import statistics as st
from dataclasses import dataclass

from kemp import scoring as S
from kemp.config import parse
from kemp.paths import RESULTS
from kemp.run import start_run

A1_RANGE, A4_RANGE = (125.13, 133.08), (130.40, 145.01)
RENAME = {
    "best__seed4__s068": "s068",
    "best__seed4__s006": "s006",
    "best__seed4__s004": "s004",
    "best__seed4__s042": "s042",
    "s042": "s042",
    "replicated__s024": "s024",
}


@dataclass
class Config:
    name: str = "rank-stability"
    seed: int = 0
    base: str = ""  # "label=path,label=path": nearest-oxygen runs
    od2: str = ""  # the same sets scored with --base_atom=od2
    top: int = 15
    keep: int = 8


def load(spec: str) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    for item in spec.split(","):
        label, path = item.split("=", 1)
        for r in csv.DictReader(open(path), delimiter="\t"):
            if "__seed" not in r["id"]:
                continue
            n = r["id"].rsplit("__seed", 1)[0]
            if label == "PK" and not n.startswith("replicated__s024"):
                continue
            n = RENAME.get(n, n)
            n = n[2:] if label == "CR" and n.startswith("d_") else n
            n = n[5:] if label == "N" and n.startswith("ns4__") else n
            out.setdefault(n, []).append(r)
    return {n: v for n, v in out.items() if len(v) == 5}


def f(r, k):
    return float(r[k])


def total(parts):
    return S.weighted_total(parts)


def parts_from(r, dist_base, dist_donor, dev, ipde, burial, k5):
    return {
        "dist": min(
            S.score_distance(dist_base, S.CRYSTAL["base"]["dist"]),
            S.score_distance(dist_donor, S.CRYSTAL["donor"]["dist"]),
        ),
        "approach": S.score_angle(dev),
        "ipde": S.score_ipde(ipde),
        "burial": S.score_burial(burial),
        "consistency": k5,
    }


def over(a, rng):
    return max(0.0, rng[0] - a, a - rng[1])


def main(cfg: Config) -> None:
    run = start_run(cfg.name, cfg, seed=cfg.seed)
    base, od2 = load(cfg.base), load(cfg.od2)
    sc: dict[str, dict[str, float]] = {}
    for n, v in base.items():
        k5 = f(v[0], "K5")

        def mean(k, v=v):
            return st.mean(f(r, k) for r in v)

        w = od2[n]
        k2m = [
            S.score_angle(max(over(f(r, "A1"), A1_RANGE), over(f(r, "A4"), A4_RANGE), f(r, "dev_oop")))
            for r in v
        ]
        per_k2m = [
            total(
                {
                    "dist": f(r, "s_dist"),
                    "approach": a,
                    "ipde": f(r, "s_ipde"),
                    "burial": f(r, "s_burial"),
                    "consistency": k5,
                }
            )
            for r, a in zip(v, k2m, strict=True)
        ]
        mean_metrics = total(
            parts_from(
                None, mean("base_d"), mean("donor_d"), mean("approach_dev"), mean("ipde"), mean("burial"), k5
            )
        )
        sc[n] = {
            "base": mean("WEIGHTED"),
            "K1_od2": st.mean(f(r, "WEIGHTED") for r in w),
            "K2_med": st.mean(per_k2m),
            "K1-K6": mean("WEIGHTED_K6"),
            "meanM": mean_metrics,
            "worst": min(f(r, "WEIGHTED") for r in v),
            "K5": k5,
        }
    variants = ["base", "K1_od2", "K2_med", "K1-K6", "meanM", "worst"]
    rank = {x: {n: i + 1 for i, n in enumerate(sorted(sc, key=lambda n: -sc[n][x]))} for x in variants}
    order = sorted(sc, key=lambda n: -sc[n]["base"])
    stay = [n for n in sc if all(rank[x][n] <= cfg.keep for x in variants)]
    out = RESULTS / "criteria" / "rank_stability.tsv"
    with open(out, "w", newline="") as fh:
        w = csv.writer(fh, delimiter="\t")
        w.writerow(["design", "K5"] + [f"{x}_score" for x in variants] + [f"{x}_rank" for x in variants])
        for n in order:
            w.writerow(
                [n, f"{sc[n]['K5']:.3f}"]
                + [f"{sc[n][x]:.3f}" for x in variants]
                + [rank[x][n] for x in variants]
            )
    print(f"{'design':26}" + "".join(f"{x:>14}" for x in variants))
    for n in order[: cfg.top]:
        print(f"{n:26}" + "".join(f"{sc[n][x]:8.3f} (#{rank[x][n]:>2})" for x in variants))
    print(
        f"\nin the top {cfg.keep} under ALL variants: {', '.join(sorted(stay, key=lambda n: -sc[n]['base']))}"
    )
    run.finish(ok=True, n_designs=len(sc), stay_top=stay)


if __name__ == "__main__":
    main(parse(Config))
