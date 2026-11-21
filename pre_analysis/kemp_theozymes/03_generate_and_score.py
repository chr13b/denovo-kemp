#!/usr/bin/env python3
"""Step 3: assemble theozyme candidates from the template libraries, score, rank, test rank stability.

Rules (from the brief):
  1. TSA (6-nitrobenzotriazole) in the centre: it stands in for the substrate.
  2. A catalytic base: carboxylate (Asp/Glu) or a His-Asp dyad.
  3. A pi-stacking aromatic (Trp/Phe/Tyr) on top of the TSA.
  4. Optionally a nitro stabiliser whose residue, distance and angles come from nitro_enzymes/motif_table.csv.

Score components (each 0-1; all targets come from data in this project, see README):
  base      approach geometry of the base vs the Listov-2025 Rosetta constraint (theozime.cst; syn/anti carboxylate both accepted) and the observed TSA-complex distance;
            His-Asp dyad: His N...TSA N and Asp O...His N H-bond distances; N1-side bases take a x0.75 mode penalty (see README)
  pi        centroid distance, ring tilt and lateral offset vs the tight stackers seen in the crystal structures
  nitro     (only if present) typicality of d(O...X), angle N-O...X and elevation within its residue/contact class in the nitro data,
            class frequency, support in Kemp eliminase entries, aromatic-nitro source
  compat    steric compatibility of the assembled components (hard clashes are rejected)
  evidence  best published kcat/KM of the lineage(s) the base and stacker come from + whether the components were seen together
Total = weighted mean of the components that are present, so adding a stabiliser only helps if it scores above the rest.
"""
import csv, json, math, os, itertools, collections
import numpy as np
from common import *

TPL = os.path.join(HERE, "templates")
tsa_list = parse_pdb(os.path.join(TPL, "tsa_6NT.pdb")); tsa = {a["name"]: a["xyz"] for a in tsa_list}
tsa_el = {a["name"]: a["el"] for a in tsa_list}
bic = np.array([tsa[k] for k in CORE]); bic_c, bic_n = ring_frame(bic)
ATOMS = json.load(open(os.path.join(TPL, "template_atoms.json"))); NATOMS = json.load(open(os.path.join(TPL, "nitro_atoms.json")))
rd = lambda f: list(csv.DictReader(open(os.path.join(TPL, f))))
BASE, PI, NIT = rd("base_templates.csv"), rd("pi_templates.csv"), rd("nitro_templates.csv")
for _n in NIT:
    for _k in ("d", "ang", "elev"): _n[_k] = float(_n[_k])
NSTAT = {(r["residue"], r["contact_type"]): r for r in rd("nitro_stats.csv")}
KINETICS = {  # lineage label -> best published kcat/KM (kemp_eliminase/theozyme/THEOZYME_ORIGIN.md section 3b)
    "HG / xylanase 1GOR": 2.3e5, "KE59 / IGPS": 60430, "1A53-2 / IGPS": 64.2, "KE70 / DERA": 55000, "KempTIM": 32000, "Des27 / IGPS chimera": 12700, "KABLE": None}
LO, HI = math.log10(64.2), math.log10(2.3e5)
def act(fams):
    v = [KINETICS.get(f) for f in fams]; v = [x for x in v if x]
    return 0.3 if not v else max(0.0, min(1.0, (math.log10(max(v)) - LO) / (HI - LO)))
g = lambda z2: math.exp(-0.5 * z2)
def wrap180(x): return (x + 180) % 360 - 180
def adiff(a, b): return abs(wrap180(a - b))

# ---------------------------------------------------------------- per-template scores
def base_score(b):
    at = {a[0]: np.array(a[2]) for a in ATOMS[b["id"]]["atoms"]}
    if b["kind"] == "carboxylate":
        A1, A2 = (tsa["N3"], tsa["C3A"]) if b["side"] == "N3" else (tsa["N1"], tsa["C7A"]); A3 = tsa["N2"]
        names = ("OD1", "OD2") if b["residue"] == "ASP" else ("OE1", "OE2"); C = "CG" if b["residue"] == "ASP" else "CD"; Bp = "CB" if b["residue"] == "ASP" else "CG"
        o = min(names, key=lambda n: np.linalg.norm(at[n] - A1)); O = at[o]
        m = dict(d=float(np.linalg.norm(O - A1)), angA=angle(A2, A1, O), angB=angle(A1, O, at[C]), torA=dihedral(A3, A2, A1, O), torB=dihedral(A1, O, at[C], at[Bp]))
        z = [((m["d"] - 2.6) / 0.3, 1.0), ((m["angA"] - 127.6) / 10, 1.0), ((m["angB"] - 120) / 12, 1.0), (adiff(m["torA"], 180) / 15, 1.0), (min(adiff(m["torB"], 180), adiff(m["torB"], 0)) / 20, 0.5)]   # carboxylate in plane, syn (0) or anti (180) both accepted; the cst prefers anti but HG3.17 is syn
        s = g(sum(w * x * x for x, w in z) / sum(w for _, w in z))
        base_atom = o
    else:   # His-Asp dyad: His N nearest the reactive N and the Asp O to the other His N
        hn = {n: at[n] for n in ("ND1", "NE2") if n in at}
        site = tsa["N3"] if b["side"] == "N3" else tsa["N1"]
        near = min(hn, key=lambda n: np.linalg.norm(hn[n] - site)); other = [n for n in hn if n != near][0]
        acid = [a for a in ATOMS[b["id"]]["atoms"][ATOMS[b["id"]]["his_atoms"]:] if a[0] in ("OD1", "OD2", "OE1", "OE2")]
        d2 = min(np.linalg.norm(np.array(a[2]) - hn[other]) for a in acid)
        A2 = tsa["C3A"] if b["side"] == "N3" else tsa["C7A"]
        m = dict(d=float(np.linalg.norm(hn[near] - site)), d_dyad=float(d2), angA=angle(A2, site, hn[near]), torA=dihedral(tsa["N2"], A2, site, hn[near]))
        z = [((m["d"] - 3.0) / 0.3, 1.0), ((d2 - 2.75) / 0.25, 1.0), ((m["angA"] - 127.6) / 15, 1.0), (adiff(m["torA"], 180) / 25, 1.0)]
        s = g(sum(w * x * x for x, w in z) / sum(w for _, w in z)); base_atom = near
    mode = 0.75 if b["side"] == "N1" else 1.0
    return s * mode, m, base_atom, mode
def pi_score(p):
    zd, zt, zl = (float(p["centroid_dist_A"]) - 3.8) / 0.5, max(0.0, float(p["tilt_deg"]) - 10) / 15, max(0.0, float(p["lateral_A"]) - 1.5) / 1.0
    return g((zd * zd + zt * zt + zl * zl) / 3)
def nitro_score(n):
    st = NSTAT[(n["residue"], n["contact_type"])]
    z = [(n["d"] - float(st["d_med"])) / float(st["d_sd"]), (n["ang"] - float(st["ang_med"])) / float(st["ang_sd"]), (n["elev"] - float(st["elev_med"])) / float(st["elev_sd"])]
    geom = g(sum(x * x for x in z) / 3)
    freq = math.sqrt(float(st["share_of_all_hbonds"]) / 0.244)
    kemp = 1.0 if any("Kemp" in f for f in NATOMS[n["id"]]["fams"]) else 0.0
    return 0.5 * geom + 0.2 * min(1, freq) + 0.15 * kemp + 0.15 * (1.0 if n["arom_source_nitro"] == "True" else 0.6), geom, freq, kemp

BS = {b["id"]: base_score(b) for b in BASE}
PS = {p["id"]: pi_score(p) for p in PI}
NS = {n["id"]: nitro_score(n) for n in NIT}

# ---------------------------------------------------------------- geometry arrays and clash test
def arr(tid, which):
    src = ATOMS if which in ("b", "p") else NATOMS
    return [(a[0], a[1], np.array(a[2])) for a in src[tid]["atoms"]]
def polar(e): return e in ("N", "O")
def compat(comps):
    """comps: list of atom lists. returns (hard_fail, penalty)"""
    pen = 0.0
    for i in range(len(comps)):
        for j in range(i + 1, len(comps)):
            for n1, e1, x1 in comps[i]:
                for n2, e2, x2 in comps[j]:
                    d = float(np.linalg.norm(x1 - x2))
                    if d < 2.2: return True, 9.0
                    if n1 == "CA" and n2 == "CA" and d < 3.6: return True, 9.0
                    lim = 2.6 if (polar(e1) and polar(e2)) else 3.3
                    if d < lim: pen += (lim - d) ** 2
    return False, pen
def vs_tsa(comp):
    pen = 0.0
    for n1, e1, x1 in comp:
        for tn, tx in tsa.items():
            d = float(np.linalg.norm(x1 - tx)); lim = 2.6 if (polar(e1) and polar(tsa_el[tn])) else 3.2
            if d < 2.1: return True
    return False
BA = {b["id"]: arr(b["id"], "b") for b in BASE}; PA = {p["id"]: arr(p["id"], "p") for p in PI}; NA = {n["id"]: arr(n["id"], "n") for n in NIT}
PEN_PI_BASE = {}
cand = []
n_total = n_hard = 0
for b in BASE:
    for p in PI:
        n_total += 1
        h, pen_bp = compat([BA[b["id"]], PA[p["id"]]])
        if h or vs_tsa(PA[p["id"]]): n_hard += 1; continue
        for n in [None] + NIT:
            if n is None: pen, hard = pen_bp, False
            else:
                n_total += 0
                h2, pen_n = compat([BA[b["id"]], PA[p["id"]], NA[n["id"]]]); hard, pen = h2, pen_n
            if hard: n_hard += 1; continue
            cand.append((b, p, n, pen))
print(f"{len(BASE)} bases x {len(PI)} stackers x (none + {len(NIT)} stabilisers): {len(cand)} sterically valid theozymes ({n_hard} rejected as clashing)")

# ---------------------------------------------------------------- evidence
def native(b, p, n):
    members_b = set(b["members"].split()); members_p = set(p["members"].split()); parts = []
    parts.append(1.0 if members_b & members_p else (0.5 if set(b["families"].split(";")) & set(p["families"].split(";")) else 0.0))
    if n is not None:
        mn = set(n["members"].split()); kemp = any("Kemp" in f for f in NATOMS[n["id"]]["fams"])
        parts.append(1.0 if (mn & members_b) else (0.5 if kemp else 0.0))
    return sum(parts) / len(parts)
def evidence(b, p, n):
    a = (act(b["families"].split(";")) + act(p["families"].split(";"))) / 2
    e = 0.6 * a + 0.4 * native(b, p, n)
    if b["modelled"] == "True" or p["modelled"] == "True": e *= 0.85
    return e, a

SCHEMES = {  # weights for (base, pi, compat, evidence, nitro-if-present)
    "default":       dict(base=.35, pi=.25, compat=.10, evidence=.20, nitro=.10),
    "geometry_only": dict(base=.45, pi=.30, compat=.15, evidence=.00, nitro=.10),
    "evidence_heavy": dict(base=.25, pi=.15, compat=.05, evidence=.45, nitro=.10),
    "base_first":    dict(base=.60, pi=.15, compat=.05, evidence=.10, nitro=.10),
    "ignore_nitro":  dict(base=.35, pi=.25, compat=.10, evidence=.20, nitro=.00),
}
def total(c, w):
    parts = {k: v for k, v in c.items() if k in w and v is not None}
    ws = {k: w[k] for k in parts if w[k] > 0}
    return sum(parts[k] * ws[k] for k in ws) / sum(ws.values())

rows = []
for b, p, n, pen in cand:
    comp_s = g(pen / 0.4)
    e, a = evidence(b, p, n)
    ns = NS[n["id"]][0] if n else None
    c = dict(base=BS[b["id"]][0], pi=PS[p["id"]], compat=comp_s, evidence=e, nitro=ns)
    nt = ("none" if n is None else ("backbone NH" if n["contact_type"] == "bb_NH" else "side chain"))
    base_cls = f'{b["residue"].replace("HIS+ASP", "His-Asp dyad").title() if b["kind"]=="dyad" else b["residue"].title()} ({b["side"]})'
    rows.append(dict(base_id=b["id"], base=f'{b["residue"]} {b["resid"]}', base_src=b["source"], base_class=base_cls, pi_id=p["id"], pi=f'{p["residue"]} {p["resid"]}', pi_src=p["source"],
                     nitro_id=n["id"] if n else "", nitro=(f'{n["residue"]}({n["contact_type"]})' if n else "none"), nitro_src=(n["src"] if n else ""), nitro_class=nt,
                     s_base=round(c["base"], 3), s_pi=round(c["pi"], 3), s_nitro=round(ns, 3) if ns is not None else "", s_compat=round(comp_s, 3), s_evidence=round(e, 3), clash_penalty=round(pen, 3),
                     lineage_activity=round(a, 3), **{f"T_{k}": round(total(c, w), 4) for k, w in SCHEMES.items()}, _c=c, _b=b, _p=p, _n=n))
rows.sort(key=lambda r: -r["T_default"])
for k in SCHEMES:
    for i, r in enumerate(sorted(rows, key=lambda r: -r[f"T_{k}"]), 1): r[f"rank_{k}"] = i
for i, r in enumerate(rows, 1):
    r["rank"] = i; r["id"] = f"T{i:05d}"
    ranks = [r[f"rank_{k}"] for k in SCHEMES]
    r["stable_top25"] = sum(x <= 25 for x in ranks); r["rank_worst"] = max(ranks); r["rank_mean"] = round(sum(ranks) / len(ranks), 1)

def meas(r):
    b, p, n = r["_b"], r["_p"], r["_n"]; m = BS[b["id"]][1]
    s = f'base d={m["d"]:.2f}A' + (f' angA={m["angA"]:.0f} torA={m["torA"]:.0f}' + (f' angB={m["angB"]:.0f} torB={m["torB"]:.0f}' if "angB" in m else f' dyad d={m["d_dyad"]:.2f}'))
    s += f'; pi d={p["centroid_dist_A"]}A tilt={p["tilt_deg"]} lat={p["lateral_A"]}'
    if n: s += f'; nitro {n["residue"]} {n["partner_atom"]} d={n["d"]}A ang={n["ang"]} elev={n["elev"]}'
    return s
for r in rows: r["geometry"] = meas(r)

# ---------------------------------------------------------------- write
cols = ["id", "rank", "T_default", "base_id", "base", "base_src", "base_class", "pi_id", "pi", "pi_src", "nitro_id", "nitro", "nitro_src", "nitro_class", "s_base", "s_pi", "s_nitro", "s_compat", "s_evidence",
        "lineage_activity", "clash_penalty", *[f"rank_{k}" for k in SCHEMES], "rank_mean", "rank_worst", "stable_top25", "geometry"]
with open(os.path.join(HERE, "candidates_scored.csv"), "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(cols)
    for r in rows: w.writerow([r[c] for c in cols])
json.dump({"n_valid": len(rows), "schemes": SCHEMES}, open(os.path.join(HERE, "scoring_meta.json"), "w"), indent=1)
import pickle; pickle.dump(rows, open(os.path.join(HERE, "report", "rows.pkl"), "wb"))
print(f"{len(rows)} candidates scored; top 15:")
for r in rows[:15]:
    print(r["id"], f'{r["T_default"]:.3f}', "|", r["base"], r["base_class"], "|", r["pi"], "|", r["nitro"], f'| base {r["s_base"]} pi {r["s_pi"]} nit {r["s_nitro"]} cmp {r["s_compat"]} evd {r["s_evidence"]} | stable {r["stable_top25"]}/5')
