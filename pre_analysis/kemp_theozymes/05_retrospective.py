#!/usr/bin/env python3
"""Step 5: retrospective sanity check. Does the geometry-only score of each lineage's *native* base + stacker pair
(both seen together in the same crystal structure, no stabiliser) rank the lineages like their measured best kcat/KM?
No kinetics enter the geometry-only score, so this is not circular. n is tiny; read it as a sanity check, not validation."""
import pickle, os, math
from common import *
rows = pickle.load(open(os.path.join(HERE, "report", "rows.pkl"), "rb"))
LIN = {"HG / xylanase 1GOR": 2.3e5, "KE59 / IGPS": 60430, "KE70 / DERA": 55000, "Des27 / IGPS chimera": 12700, "1A53-2 / IGPS": 64.2}
best = {}
for r in rows:
    b, p = r["_b"], r["_p"]
    if r["nitro_class"] != "none": continue
    if set(b["members"].split()) & set(p["members"].split()):
        fam = b["families"].split(";")[0]
        if fam in LIN and (fam not in best or r["T_geometry_only"] > best[fam]["T_geometry_only"]): best[fam] = r
print(f'{"lineage":24}{"native base + stacker":38}{"geom-only":>10}{"base":>7}{"pi":>7}{"best kcat/KM":>14}')
tab = []
for fam, r in sorted(best.items(), key=lambda kv: -LIN[kv[0]]):
    print(f'{fam:24}{r["base"]+" + "+r["pi"]:38}{r["T_geometry_only"]:10.3f}{r["s_base"]:7.2f}{r["s_pi"]:7.2f}{LIN[fam]:14,.0f}'); tab.append((fam, r["T_geometry_only"], LIN[fam]))
def rank(v): o = sorted(range(len(v)), key=lambda i: v[i]); r = [0] * len(v); [r.__setitem__(i, k) for k, i in enumerate(o)]; return r
a, b = rank([t[1] for t in tab]), rank([t[2] for t in tab]); n = len(tab)
rho = 1 - 6 * sum((x - y) ** 2 for x, y in zip(a, b)) / (n * (n * n - 1))
print(f"\nSpearman rho = {rho:.2f} (n = {n} lineages)")
import json; json.dump(dict(rho=rho, n=n, table=[dict(lineage=t[0], geometry_only=round(t[1], 3), kcat_KM=t[2]) for t in tab]), open(os.path.join(HERE, "report", "retrospective.json"), "w"), indent=1)
