#!/usr/bin/env python3
"""Step 4: pick distinct variants from the ranked list and export them (PDB per theozyme + selected_variants.csv).

The raw ranking is dominated by near-identical combinations, so variants are chosen as the best-scoring candidate that satisfies a
design-relevant condition (lineage of the base, stacker identity, stabiliser type). Every theozyme is written in the common TSA frame:
chain A = 6NT, B = base (C = dyad Asp), D = pi stacker, E = nitro stabiliser; REMARK lines carry scores, geometry and fix-atom hints.
"""
import csv, json, math, os, pickle
import numpy as np
from common import *

rows = pickle.load(open(os.path.join(HERE, "report", "rows.pkl"), "rb"))
ATOMS = json.load(open(os.path.join(HERE, "templates", "template_atoms.json"))); NATOMS = json.load(open(os.path.join(HERE, "templates", "nitro_atoms.json")))
tsa_list = parse_pdb(os.path.join(HERE, "templates", "tsa_6NT.pdb")); tsa = {a["name"]: a["xyz"] for a in tsa_list}
bic = np.array([tsa[k] for k in CORE]); bic_c, bic_n = ring_frame(bic)
OUT = os.path.join(HERE, "candidates"); os.makedirs(OUT, exist_ok=True)
for f in os.listdir(OUT):
    if f.endswith(".pdb"): os.remove(os.path.join(OUT, f))

def fam(t): return set(t["families"].split(";"))
HGF, KE59F, DESF, KE70F, TIMF, A532F = "HG / xylanase 1GOR", "KE59 / IGPS", "Des27 / IGPS chimera", "KE70 / DERA", "KempTIM", "1A53-2 / IGPS"
def first(pred):
    for r in rows:
        if pred(r): return r
    return None
bf = lambda r: fam(r["_b"]); pf = lambda r: fam(r["_p"])
SLOTS = [
    ("top_overall", "Top-ranked theozyme overall", lambda r: True),
    ("top_with_stabiliser", "Best candidate that has a nitro stabiliser", lambda r: r["nitro_class"] != "none"),
    ("native_HG_triple", "HG-series native set: Asp127 + Trp44 + Met237 backbone NH, all three co-observed in the same crystal structure", lambda r: bf(r) == {HGF} and pf(r) == {HGF} and r["nitro"].startswith("MET") and (set(r["_b"]["members"].split()) & set(r["_p"]["members"].split()) & set(r["_n"]["members"].split()) if r["_n"] else False)),
    ("HG_base_best_stack", "HG Asp127 base with the best-scoring stacker (any lineage), no stabiliser", lambda r: bf(r) == {HGF} and r["nitro_class"] == "none"),
    ("Des27_as_designed", "Des27.7 as designed: Asp162 + Phe113, no polar stabiliser", lambda r: bf(r) == {DESF} and pf(r) == {DESF} and r["nitro_class"] == "none"),
    ("Des27_plus_stabiliser", "Des27.7-type Asp162 + Phe113 with the best nitro stabiliser", lambda r: bf(r) == {DESF} and pf(r) == {DESF} and r["nitro_class"] != "none"),
    ("KE59_native", "KE59-type: Glu231 + Trp110, no stabiliser", lambda r: bf(r) == {KE59F} and pf(r) == {KE59F} and r["nitro_class"] == "none"),
    ("KE59_plus_bbNH", "KE59-type Glu231 + Trp110 with a backbone-NH stabiliser", lambda r: bf(r) == {KE59F} and pf(r) == {KE59F} and r["nitro_class"] == "backbone NH"),
    ("KE59_plus_sidechain", "KE59-type Glu231 + Trp110 with a side-chain stabiliser (His/Tyr/Asn/Ser ...)", lambda r: bf(r) == {KE59F} and pf(r) == {KE59F} and r["nitro_class"] == "side chain"),
    ("His_Asp_dyad", "His-Asp dyad (KE70-core) + best stacker, no stabiliser", lambda r: r["_b"]["kind"] == "dyad" and r["nitro_class"] == "none"),
    ("His_Asp_dyad_stab", "His-Asp dyad with the best nitro stabiliser", lambda r: r["_b"]["kind"] == "dyad" and r["nitro_class"] != "none"),
    ("N1_Asp_KempTIM", "Alternate binding mode: Asp base on the N1 side (KempTIM1)", lambda r: r["base_class"] == "Asp (N1)"),
    ("N1_Glu_1A53", "Alternate binding mode: Glu base on the N1 side (1A53-2)", lambda r: r["base_class"] == "Glu (N1)"),
    ("Phe_stack_best", "Best candidate whose stacker is Phe", lambda r: r["pi"].startswith("PHE")),
    ("Tyr_stack_best", "Best candidate whose stacker is Tyr", lambda r: r["pi"].startswith("TYR")),
]
# Pareto front of geometric quality (geometry-only total) vs published evidence (s_evidence)
_pts = sorted(rows, key=lambda r: (-r["T_geometry_only"], -r["s_evidence"])); _front, _be = [], -1
for r in _pts:
    if r["s_evidence"] > _be + 1e-9: _front.append(r); _be = r["s_evidence"]
for i, r in enumerate(_front, 1):
    SLOTS.append((f"pareto{i}", f'Pareto front {i}/{len(_front)}: geometry {r["T_geometry_only"]:.3f} vs evidence {r["s_evidence"]:.3f}', lambda x, rid=r["id"]: x["id"] == rid))
SLOTS.append(("best_mean_rank", "Best mean rank over the five weightings", lambda x, rid=min(rows, key=lambda x: x["rank_mean"])["id"]: x["id"] == rid))
FIXH = {"bb_NH": "backbone N,CA,C,O", "bb+sidechain": "all heavy atoms", "sidechain": "side chain + CA"}
def face(t_atoms):   # which side of the TSA plane the residue's CA is on (+1 / -1)
    ca = next((np.array(a[2]) for a in t_atoms if a[0] == "CA"), None)
    return None if ca is None else int(np.sign(float((ca - bic_c) @ bic_n)))
def ring_height(p):
    at = {a[0]: np.array(a[2]) for a in ATOMS[p["id"]]["atoms"]}
    ring = max((r for r in AR_RINGS[p["residue"]] if all(n in at for n in r)), key=lambda r: -np.linalg.norm(ring_frame(np.array([at[n] for n in r]))[0] - bic_c))
    return int(np.sign(float((ring_frame(np.array([at[n] for n in ring]))[0] - bic_c) @ bic_n)))

def export(r, path, slot=None):
    b, p, n = r["_b"], r["_p"], r["_n"]; blocks = [("A", 1, "6NT", True, [(k, tsa_list[[a["name"] for a in tsa_list].index(k)]["el"].title(), v.tolist()) for k, v in tsa.items()])]
    ba = ATOMS[b["id"]]["atoms"]
    if b["kind"] == "dyad":
        h = ba[:ATOMS[b["id"]]["his_atoms"]]; ac = ba[ATOMS[b["id"]]["his_atoms"]:]
        blocks += [("B", 1, "HIS", False, [(a[0], a[1].title(), a[2]) for a in h]), ("C", 1, b["residue"].split("+")[1], False, [(a[0], a[1].title(), a[2]) for a in ac])]
    else: blocks.append(("B", 1, b["residue"], False, [(a[0], a[1].title(), a[2]) for a in ba]))
    blocks.append(("D", 1, p["residue"], False, [(a[0], a[1].title(), a[2]) for a in ATOMS[p["id"]]["atoms"]]))
    if n: blocks.append(("E", 1, n["residue"], False, [(a[0], a[1].title(), a[2]) for a in NATOMS[n["id"]]["atoms"]]))
    rem = [f'Kemp theozyme {r["id"]}  rank {r["rank"]} of {len(rows)}  total {r["T_default"]:.3f}' + (f'  [{slot}]' if slot else ""),
           f'components: base {r["base"]} ({r["base_src"]}), pi {r["pi"]} ({r["pi_src"]}), stabiliser {r["nitro"]} ({r["nitro_src"]})',
           f'scores: base {r["s_base"]} pi {r["s_pi"]} nitro {r["s_nitro"] or "-"} compat {r["s_compat"]} evidence {r["s_evidence"]}',
           f'geometry: {r["geometry"]}', "chains: A=6NT TSA, B=base (C=dyad Asp), D=pi stacker, E=nitro stabiliser",
           "fix atoms (motif scaffolding): base/dyad/pi = side chain + CA; " + (f'stabiliser = {FIXH[n["contact_type"]]}' if n else "no stabiliser")]
    write_pdb(path, blocks, rem)

picked, seen = [], set()
for key, desc, pred in SLOTS:
    r = first(pred)
    if r is None: print("slot", key, "-> no valid candidate"); continue
    picked.append((key, desc, r))
fields = ["slot", "description", "id", "rank", "T_geometry_only", "rank_mean", "rank_geometry_only", "T_default", "base", "base_src", "base_class", "pi", "pi_src", "nitro", "nitro_src", "s_base", "s_pi", "s_nitro", "s_compat", "s_evidence", "stable_top25", "rank_worst", "pi_face", "base_CA_face", "geometry"]
with open(os.path.join(HERE, "selected_variants.csv"), "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(fields)
    for key, desc, r in picked:
        pface, bface = ring_height(r["_p"]), face(ATOMS[r["_b"]["id"]]["atoms"])
        r["pi_face"], r["base_CA_face"] = pface, bface
        w.writerow([key, desc, r["id"], r["rank"], r["T_geometry_only"], r["rank_mean"], r["rank_geometry_only"], r["T_default"], r["base"], r["base_src"], r["base_class"], r["pi"], r["pi_src"], r["nitro"], r["nitro_src"], r["s_base"], r["s_pi"], r["s_nitro"], r["s_compat"], r["s_evidence"], r["stable_top25"], r["rank_worst"], pface, bface, r["geometry"]])
        export(r, os.path.join(OUT, f'variant_{key}__{r["id"]}.pdb'), key)
for r in rows[:20]:
    export(r, os.path.join(OUT, f'top{r["rank"]:02d}__{r["id"]}.pdb'))
pickle.dump(picked, open(os.path.join(HERE, "report", "picked.pkl"), "wb"))
print(f'{"slot":24}{"id":8}{"rank":>6}{"score":>7}  base / pi / stabiliser   [stable]  faces(pi,baseCA)')
for key, desc, r in picked:
    print(f'{key:24}{r["id"]:8}{r["rank"]:>6}{r["T_default"]:7.3f}  {r["base"]} {r["base_src"]} / {r["pi"]} {r["pi_src"]} / {r["nitro"]} {r["nitro_src"]}   [{r["stable_top25"]}/5] ({r["pi_face"]},{r["base_CA_face"]})')
