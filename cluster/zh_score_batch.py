"""Score our five-seed refolds with Zonghu's K1-K5 scorer (his code, unmodified), as a second opinion.

Runs ON THE CLUSTER'S HEAD NODE with env-rfd3's python (biotite + numpy); it only measures, it does not model.

His scorer lives on his branch, not on ours. Export the two files read-only, beside this script, then run it:

    mkdir -p zh/kemp
    git show origin/zonghu:src/kemp/scoring.py            > zh/kemp/scoring.py
    git show origin/zonghu:scripts/40_score_metrics_pack.py > zh/score40.py
    cp cluster/zh_score_batch.py zh/
    /mnt/ref/software/envs/env-rfd3/bin/python zh/zh_score_batch.py OUT.tsv [job-substring ...]

The three project modules his script imports (`kemp.config`, `kemp.paths`, `kemp.run`) are stubbed because the
cluster does not have the `kemp` package; none of them touches the maths. Check against his published numbers:
for our s010 (job replicate-100) it gives K1 0.75, K2 0.52, K3 0.99, K4 0.96, K5 0.69, K1-K5 0.729, the values
in his `ranking_all_k1_k6.md`.

Per design the columns are the mean over the five seeds of K1 (distance), K2 (approach), K3 (iPDE) and
K4 (burial); K5 (consistency, one number from the spread of the two contact distances over the seeds); the
mean over seeds of the weighted K1-K5 total (his ranking column); the same with his extra ipTM term (K1-K6,
a quality control only: ipTM is not an organizer criterion); and the worst seed's K1-K5 total.
"""

import importlib.util
import json
import math
import os
import sys
import types
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np  # noqa: E402

for name, attrs in (
    ("kemp.config", {"parse": None}),
    ("kemp.paths", {"RESULTS": Path(".")}),
    ("kemp.run", {"start_run": None}),
):
    sys.modules[name] = types.ModuleType(name)
    sys.modules[name].__dict__.update(attrs)
from kemp import scoring as S  # noqa: E402

spec = importlib.util.spec_from_file_location("score40", os.path.join(HERE, "score40.py"))
Z = importlib.util.module_from_spec(spec)
sys.modules["score40"] = Z
spec.loader.exec_module(Z)
sys.path.insert(0, "/mnt/work/projects/chris_autopilot/src")
import autopilot as ap  # noqa: E402

out = sys.argv[1]
only = sys.argv[2:]
IPTM_BASE, IPTM_SIGMA = 0.8372, 0.1
table = {}
for label, dirs in ap.replicate_dirs():
    if only and not any(o in label for o in only):
        continue
    for d in dirs:
        qp = d + "/queries.json"
        if not os.path.exists(qp):
            continue
        recs = {r["name"]: r for r in json.load(open(qp)) if r.get("kind") == "design"}
        pinned = (
            {r["name"]: r for r in ap.read_tsv(d + "/geometry.tsv")}
            if os.path.exists(d + "/geometry.tsv")
            else {}
        )
        for name, r in recs.items():
            cif = Path("%s/boltz/boltz_results_queries/predictions/%s/%s_model_0.cif" % (d, name, name))
            if not cif.exists() or name not in pinned:
                continue
            m = Z.measure(cif, r["base_position"], r["donor_position"], Z.BASE_ATOMS)
            if m is None:
                continue
            dev = max(abs(m[c][k] - S.CRYSTAL[c][k]) for c in ("base", "donor") for k in ("angle", "oop"))
            ip = pinned[name].get("complex_ipde")
            ipde = float(ip) if ip else None
            parts = {
                "dist": min(S.score_distance(m[c]["d"], S.CRYSTAL[c]["dist"]) for c in ("base", "donor")),
                "approach": S.score_angle(dev),
                "ipde": S.score_ipde(ipde) if ipde is not None else None,
                "burial": S.score_burial(m["burial"]),
            }
            iptm = Z.read_iptm(cif)
            parts["iptm"] = (
                None
                if iptm is None
                else (1.0 if iptm >= IPTM_BASE else math.exp(-(((IPTM_BASE - iptm) / IPTM_SIGMA) ** 2)))
            )
            e = table.setdefault((label, r["sequence"]), {"label": label, "name": name, "r": r, "seeds": []})
            e["seeds"].append({"m": m, "parts": parts, "dev": dev, "iptm": iptm})


def seed_mean(seeds, key):
    """Mean over seeds of one sub-score, skipping seeds where it is not defined."""
    return float(np.mean([v["parts"][key] for v in seeds if v["parts"][key] is not None]))


rows = []
for (label, seq), e in table.items():
    s = e["seeds"]
    if len(s) < 5:
        continue
    stds = [float(np.std([v["m"][c]["d"] for v in s], ddof=1)) for c in ("base", "donor")]
    k5 = S.score_consistency(stds)
    tot, tot6 = [], []
    for v in s:
        p = dict(v["parts"])
        p["consistency"] = k5
        k15 = {k: x for k, x in p.items() if k != "iptm"}
        tot.append(S.weighted_total(k15))
        tot6.append(Z.total_with_iptm(p, 0.15))
    rows.append(
        {
            "job": label,
            "name": e["name"],
            "n": len(s),
            "K1": seed_mean(s, "dist"),
            "K2": seed_mean(s, "approach"),
            "K3": seed_mean(s, "ipde"),
            "K4": seed_mean(s, "burial"),
            "K5": k5,
            "iptm": float(np.mean([v["iptm"] for v in s if v["iptm"] is not None])),
            "K1_K5": float(np.mean(tot)),
            "K1_K6": float(np.mean(tot6)),
            "worst_seed_K1_K5": float(min(tot)),
            "sequence": seq,
        }
    )
rows.sort(key=lambda r: -r["K1_K5"])
cols = [
    "job",
    "name",
    "n",
    "K1",
    "K2",
    "K3",
    "K4",
    "K5",
    "iptm",
    "K1_K5",
    "K1_K6",
    "worst_seed_K1_K5",
    "sequence",
]
with open(out, "w") as h:
    h.write("\t".join(cols) + "\n")
    for r in rows:
        h.write("\t".join(("%.4f" % r[c]) if isinstance(r[c], float) else str(r[c]) for c in cols) + "\n")
print(len(rows), "designs scored ->", out)
for r in rows[:14]:
    print(
        "%-12s %-22s K1 %.2f K2 %.2f K3 %.2f K4 %.2f K5 %.2f  K1-K5 %.3f  worst-seed %.3f"
        % (
            r["job"][-12:],
            r["name"][-22:],
            r["K1"],
            r["K2"],
            r["K3"],
            r["K4"],
            r["K5"],
            r["K1_K5"],
            r["worst_seed_K1_K5"],
        )
    )
