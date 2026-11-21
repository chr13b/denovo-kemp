#!/usr/bin/env python3
"""Step 15: assemble, score and rank v2 theozymes (staged beam search over the component libraries).

Required: TSA centre, a base (carboxylate or His-Asp dyad), a primary pi stacker (on the TSA ring, or on the nitro group).
Optional, added in stages: a second stacker on the other site (sandwich), a nitro H-bond donor, a leaving-group (N1/O1) donor.
Scores (0-1): base, pi (mean of stackers present), subs (real-substrate crosscheck), fit (steric), evidence, hb, lg.
Total = weighted mean of the components present; six weightings are ranked for stability.
"""
import csv, json, math, os, pickle, time
import numpy as np
from lib2 import *

t0 = time.time()
comps = json.load(open(os.path.join(T2, "components.json")))
HG = set("3NYD 3O2L 4BS0 5RGA 5RGB 5RGC 5RGD 5RGE 5RGF 6SRW 6SRY 6SRZ 6SS1 6SS3 6TU6 7K4Q 7K4U 7K4X 7K4Z 8FOS 8KH3 8RD5 8USF 8USH 8USJ 8USL 8USE 8USG 8USI 8USK 7K4P 7K4R 7K4S".split())
def lineage(src):
    s = src.rstrip("~").split("_")[0]
    if s in HG: return "HG / xylanase 1GOR"
    if s in ("3UXD", "3UZJ", "3UZ5"): return "KE59 / IGPS"
    if s in ("3NZ1", "8FOQ", "6NW4"): return "1A53-2 / IGPS"
    if s in ("8FOR", "3Q2D"): return "KE70 / DERA"
    if s == "9TZD": return "KempTIM"
    if s.startswith("Des27"): return "Des27 / IGPS chimera"
    return None
KIN = {"HG / xylanase 1GOR": 2.3e5, "KE59 / IGPS": 60430, "1A53-2 / IGPS": 64.2, "KE70 / DERA": 55000, "KempTIM": 32000, "Des27 / IGPS chimera": 12700}
LO, HI = math.log10(64.2), math.log10(2.3e5)
def is_grid(c): return c["sampled"] and not c["src"].endswith("~")      # grid-sampled (no crystal precedent); "~" = small perturbation of an observed template
def act_of(c):
    if is_grid(c): return 0.15
    lin = set(c["families"]) or ({lineage(c["src"])} - {None})
    v = [KIN[l] for l in lin if l in KIN]
    return 0.3 if not v else max(0.0, min(1.0, (math.log10(max(v)) - LO) / (HI - LO)))
def mem(c): return set() if is_grid(c) else (set(c["members"]) | {c["src"].rstrip("~")})

# ---- standalone scores and pre-filters
for c in comps:
    c.pop("_a", None)
SC = {"base": score_base, "ring": score_ring, "npi": score_npi, "hb": score_hb, "lg": score_lg}
keep = {k: [] for k in SC}
for c in comps:
    if vs_tsa_hard(c): continue
    try: c["_s"] = SC[c["kind"]](c)
    except Exception as e: continue
    keep[c["kind"]].append(c)
print({k: len(v) for k, v in keep.items()}, "components after TSA-clash filter")
for k in ("hb", "lg"):   # candidate lists for the optional stages: best standalone, diverse by residue type
    keep[k].sort(key=lambda c: -c["_s"])

SCHEMES = {
    "default":            dict(base=.28, pi=.20, subs=.12, fit=.08, evidence=.17, hb=.05, lg=.05),
    "geometry_only":      dict(base=.35, pi=.25, subs=.12, fit=.10, evidence=0.0, hb=.06, lg=.06),
    "evidence_heavy":     dict(base=.18, pi=.12, subs=.08, fit=.05, evidence=.45, hb=.05, lg=.05),
    "base_first":         dict(base=.50, pi=.12, subs=.10, fit=.05, evidence=.10, hb=.04, lg=.04),
    "substrate_heavy":    dict(base=.20, pi=.15, subs=.32, fit=.06, evidence=.12, hb=.05, lg=.05),
    "ignore_optional":    dict(base=.30, pi=.22, subs=.13, fit=.08, evidence=.18, hb=0.0, lg=0.0),
}
def evidence(group, pen_pairs=None):
    base = next(c for c in group if c["kind"] == "base"); pis = [c for c in group if c["kind"] in ("ring", "npi")]
    act = np.mean([act_of(base)] + [act_of(p) for p in pis])
    nat = [1.0 if mem(base) & mem(p) else (0.5 if lineage(base["src"]) and lineage(base["src"]) == lineage(p["src"]) else 0.0) for p in pis]
    for c in group:
        if c["kind"] in ("hb", "lg"):
            nat.append(1.0 if mem(base) & mem(c) else (0.5 if c.get("kemp") else 0.0))
    ev = 0.6 * act + 0.4 * float(np.mean(nat))
    if any(c.get("modelled") for c in group): ev *= 0.85
    return ev

def evaluate(group, pen):
    base = next(c for c in group if c["kind"] == "base"); pis = [c for c in group if c["kind"] in ("ring", "npi")]
    hb = next((c for c in group if c["kind"] == "hb"), None); lg = next((c for c in group if c["kind"] == "lg"), None)
    sc = dict(base=base["_s"], pi=float(np.mean([p["_s"] for p in pis])), fit=g(pen / 0.4), evidence=evidence(group),
              hb=hb["_s"] if hb else None, lg=lg["_s"] if lg else None)
    sub = substrate_check(group); sc["subs"] = sub["subs"]
    return sc, sub
def totals(sc):
    out = {}
    for k, w in SCHEMES.items():
        ws = {n: w[n] for n in sc if sc[n] is not None and w.get(n, 0) > 0}
        out[k] = sum(sc[n] * ws[n] for n in ws) / sum(ws.values())
    return out
def make(group, pen):
    sc, sub = evaluate(group, pen)
    return dict(group=group, pen=pen, sc=sc, sub=sub, tot=totals(sc))

# ---- stage 1: base x primary pi
t1 = time.time(); stage1 = []
pi_primary = keep["ring"] + keep["npi"]
for b in keep["base"]:
    for p in pi_primary:
        h, pen = pair_clash(b, p)
        if h: continue
        stage1.append(make([b, p], pen))
print(f"stage 1: {len(keep['base'])} bases x {len(pi_primary)} primary stackers -> {len(stage1):,} valid pairs  {time.time()-t1:.0f}s")
def top(cands, n, scheme="default"): return sorted(cands, key=lambda c: -c["tot"][scheme])[:n]
def select(cands, n_def=1600, n_alt=250):
    sel = {id(c): c for c in top(cands, n_def)}
    for s in SCHEMES:
        if s != "default":
            for c in top(cands, n_alt, s): sel[id(c)] = c
    # class retention: every base class (and every observed base) stays represented so no class is pruned away by score alone
    byc, byb = {}, {}
    for c in cands:
        b = c["group"][0]
        byc.setdefault((b["bkind"], b["res"], b["side"], is_grid(b), c["group"][1]["kind"], is_grid(c["group"][1])), []).append(c)
        if not is_grid(b): byb.setdefault(b["id"], []).append(c)
    for v in byc.values():
        for c in sorted(v, key=lambda c: -c["tot"]["default"])[:120]: sel[id(c)] = c
    for v in byb.values():
        for c in sorted(v, key=lambda c: -c["tot"]["default"])[:30]: sel[id(c)] = c
    return list(sel.values())
keep1 = select(stage1)
# keep every observed base represented
for b in [b for b in keep["base"] if not b["sampled"]]:
    for c in sorted([c for c in stage1 if c["group"][0] is b], key=lambda c: -c["tot"]["default"])[:25]: keep1.append(c)
keep1 = list({id(c): c for c in keep1}.values()); print("stage 1 survivors:", len(keep1))

# ---- stage 2: sandwich (second stacker on the other site)
t1 = time.time(); stage2 = []
ring_c = sorted(keep["ring"], key=lambda c: -c["_s"])[:30]; npi_c = sorted(keep["npi"], key=lambda c: -c["_s"])[:30]
for c in keep1:
    b, p = c["group"]; cand = npi_c if p["kind"] == "ring" else ring_c
    for q in cand:
        h1, p1 = pair_clash(b, q); h2, p2 = pair_clash(p, q)
        if h1 or h2: continue
        stage2.append(make([b, p, q], c["pen"] + p1 + p2))
print(f"stage 2: {len(stage2):,} sandwich candidates  {time.time()-t1:.0f}s")
pool2 = select(keep1 + stage2, 1700, 250)

# ---- stage 3: nitro H-bond donor
t1 = time.time(); stage3 = []
hb_c = []; seen = {}
for c in keep["hb"]:
    key = (c["res"], c["contact"])
    if seen.get(key, 0) < 6: hb_c.append(c); seen[key] = seen.get(key, 0) + 1
hb_c = hb_c[:90]
for c in pool2:
    for q in hb_c:
        pen = c["pen"]; ok = True
        for g_ in c["group"]:
            h, p = pair_clash(q, g_)
            if h: ok = False; break
            pen += p
        if ok: stage3.append(make(c["group"] + [q], pen))
print(f"stage 3: {len(hb_c)} nitro-donor candidates -> {len(stage3):,} candidates  {time.time()-t1:.0f}s")
pool3 = select(pool2 + stage3, 1700, 250)

# ---- stage 4: leaving-group donor
t1 = time.time(); stage4 = []
lg_c = []; seen = {}
for c in keep["lg"]:
    key = (c["res"], c["partner"])
    if seen.get(key, 0) < 4: lg_c.append(c); seen[key] = seen.get(key, 0) + 1
lg_c = lg_c[:24]
for c in pool3:
    for q in lg_c:
        pen = c["pen"]; ok = True
        for g_ in c["group"]:
            h, p = pair_clash(q, g_)
            if h: ok = False; break
            pen += p
        if ok: stage4.append(make(c["group"] + [q], pen))
print(f"stage 4: {len(lg_c)} leaving-group candidates -> {len(stage4):,} candidates  {time.time()-t1:.0f}s")
final = list({id(c): c for c in (pool3 + stage4)}.values())
# drop candidates whose base has no real-substrate-compatible geometry? keep but flag. Hard failures (non-base atoms inside the substrate) are removed.
final = [c for c in final if not c["sub"]["hard"]]
print("final candidates:", len(final), f"| total {time.time()-t0:.0f}s")

for s in SCHEMES:
    for i, c in enumerate(sorted(final, key=lambda c: -c["tot"][s]), 1): c.setdefault("rank", {})[s] = i
for c in final:
    r = list(c["rank"].values()); c["rank_mean"] = float(np.mean(r)); c["rank_worst"] = max(r); c["stable_top25"] = sum(x <= 25 for x in r)
final.sort(key=lambda c: c["rank"]["default"])
for i, c in enumerate(final, 1): c["id"] = f"V{i:05d}"
pickle.dump(final, open(os.path.join(HERE2, "report", "final.pkl"), "wb"))

def desc(c, kind):
    x = next((q for q in c["group"] if q["kind"] == kind), None)
    return None if x is None else x
rows = []
for c in final:
    b = desc(c, "base"); ps = [q for q in c["group"] if q["kind"] in ("ring", "npi")]; hb = desc(c, "hb"); lg = desc(c, "lg")
    pistr = " + ".join(f'{q["res"]} {q["resid"]}({"nitro" if q["kind"]=="npi" else "ring"}){"*" if is_grid(q) else ("~" if q["sampled"] else "")}' for q in ps)
    rows.append(dict(id=c["id"], rank=c["rank"]["default"], total=round(c["tot"]["default"], 4),
                     base=f'{b["res"]} {b["resid"]}{"*" if is_grid(b) else ""}', base_src=b["src"], base_side=b["side"], pi=pistr, hb=(f'{hb["res"]} {hb["partner"]} {hb["src"]}{"*" if is_grid(hb) else ""}' if hb else ""),
                     lg=(f'{lg["res"]} {lg["partner"]} {lg["src"]}{"*" if is_grid(lg) else ""}' if lg else ""),
                     s_base=round(c["sc"]["base"], 3), s_pi=round(c["sc"]["pi"], 3), s_subs=round(c["sc"]["subs"], 3), s_fit=round(c["sc"]["fit"], 3), s_evidence=round(c["sc"]["evidence"], 3),
                     s_hb=("" if c["sc"]["hb"] is None else round(c["sc"]["hb"], 3)), s_lg=("" if c["sc"]["lg"] is None else round(c["sc"]["lg"], 3)),
                     subs_H_O=round(c["sub"]["h_o"], 2), subs_CHO_angle=round(c["sub"]["ang"], 0), subs_retraction_A=round(c["sub"]["retraction"], 2), subs_pt=round(c["sub"]["pt"], 3),
                     **{f"T_{s}": round(c["tot"][s], 4) for s in SCHEMES}, **{f"rank_{s}": c["rank"][s] for s in SCHEMES}, rank_mean=round(c["rank_mean"], 1), stable_top25=c["stable_top25"],
                     n_components=len(c["group"]), any_grid_sampled=any(is_grid(q) for q in c["group"]), any_perturbed=any(q["sampled"] and not is_grid(q) for q in c["group"]), n_observed_only=all(not q["sampled"] for q in c["group"])))
with open(os.path.join(HERE2, "candidates_v2.csv"), "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
json.dump(SCHEMES, open(os.path.join(HERE2, "schemes.json"), "w"), indent=1)
print("top 20 (default):")
for r in rows[:20]:
    print(r["id"], r["total"], "|", r["base"], r["base_src"], r["base_side"], "|", r["pi"], "|", r["hb"], "|", r["lg"], f'| base {r["s_base"]} pi {r["s_pi"]} subs {r["s_subs"]} evd {r["s_evidence"]}  stable {r["stable_top25"]}')
