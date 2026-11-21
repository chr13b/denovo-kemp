#!/usr/bin/env python3
"""Per-structure catalytic geometry from the substrate-aligned files -> figures/data/geometry.csv

base_dist : closest Asp/Glu carboxylate O to a TSA ring N (substrate models: to the reactive C3)
base_side : which TSA ring N that is (N1 / N2 / N3)
pi_res, pi_dist, pi_angle : nearest Trp/Phe/Tyr 6-ring centroid to the TSA/substrate benzo-ring centroid, ring-normal angle
Kinetics are attached from the published values collected in theozyme/THEOZYME_ORIGIN.md.
"""
import csv, math, os
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
AL = os.path.join(ROOT, "structures", "aligned_on_substrate")
RING_N = {"6NT": {"N1": "N1", "N2": "N2", "N3": "N3"}, "3NY": {"N1": "N1", "N2": "N2", "N3": "N3"},
          "0CU": {"N1": "NAG", "N2": "NAE", "N3": "NAF"}, "0CT": {"N1": "NAG", "N2": "NAE", "N3": "NAF"}}
BENZO = {"6NT": ["C3A", "C4", "C5", "C6", "C7", "C7A"], "3NY": ["C3A", "C4", "C5", "C6", "C7", "C7A"],
         "0CU": ["CAJ", "CAD", "CAH", "CAC", "CAI", "CAK"], "0CT": ["CAI", "CAD", "CAB", "CAA", "CAC", "CAH"]}
AR6 = {"PHE": ["CG", "CD1", "CE1", "CZ", "CE2", "CD2"], "TYR": ["CG", "CD1", "CE1", "CZ", "CE2", "CD2"],
       "TRP": ["CD2", "CE2", "CZ2", "CH2", "CZ3", "CE3"]}
ACID = {"ASP": ("OD1", "OD2"), "GLU": ("OE1", "OE2")}
# kcat/KM (M-1 s-1) of the exact variant in each structure, from the papers (see THEOZYME_ORIGIN.md)
KIN = {  # file: (variant label, kcat/KM, source, caveat)
    "direct/7K4Q_A": ("HG3 + 6NT", 125, "JACS 2024 abstract (HG3)", ""),
    "direct/5RGA_A": ("HG3 + 6NT (277 K)", 125, "JACS 2024 abstract (HG3)", ""),
    "direct/3NYD_A": ("HG-2 + 3NY", 123.2, "Privett 2012 Table 1", ""),
    "direct/7K4Z_A": ("HG3.17 + 6NT", 2.3e5, "web-search summary of Blomberg 2013 (not read directly)", "value not verified in the paper text"),
    "extended/5RGE_A": ("HG3.17 + 6NT (277 K)", 2.3e5, "web-search summary of Blomberg 2013 (not read directly)", "value not verified in the paper text"),
    "direct/3NZ1_A": ("1A53-2 + 3NY", 64.2, "Privett 2012 Table 1", ""),
    "extended/3UZ5_A": ("KE59 R13-3/11H + 0CU", 60430, "Khersonsky 2012 Table 1 (5-nitrobenzisoxazole)", ""),
    "direct/3UZJ_A": ("KE59 R13-3/11H + 0CT", 60430, "Khersonsky 2012 Table 1 (5-nitrobenzisoxazole)", ""),
    "direct/Des27.7_sub": ("Des27.7 + substrate (model)", 12700, "Listov 2025", "modelled MD starting pose, not a crystal"),
    "direct/Des27_sub": ("Des27 + substrate (model)", 130, "Listov 2025", "modelled MD starting pose, not a crystal"),
}
def parse(f):
    A = []
    for l in open(f):
        if l.startswith(("ATOM", "HETATM")):
            A.append(dict(rec=l[:6].strip(), n=l[12:16].strip(), res=l[17:20].strip(), ch=l[21], num=int(l[22:26]),
                          el=(l[76:78].strip() or l[12:16].strip()[0]), xyz=[float(l[30:38]), float(l[38:46]), float(l[46:54])]))
    return A
def cen(p): return [sum(x[i] for x in p) / len(p) for i in range(3)]
def sub(a, b): return [a[i] - b[i] for i in range(3)]
def cross(a, b): return [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]
def unit(v):
    n = math.sqrt(sum(x*x for x in v)); return [x / n for x in v]
def normal(p):
    c = cen(p); n = [0, 0, 0]
    for i in range(len(p)):
        v = cross(sub(p[i], c), sub(p[(i + 1) % len(p)], c)); n = [n[k] + v[k] for k in range(3)]
    return unit(n)
rows = []
for key, (label, kin, src, cav) in KIN.items():
    A = parse(os.path.join(AL, key + ".pdb"))
    AA = {"ALA","ARG","ASN","ASP","CYS","GLN","GLU","GLY","HIS","ILE","LEU","LYS","MET","PHE","PRO","SER","THR","TRP","TYR","VAL","HID","HIE","HIP","HSD","HSE","HSP","CYX","CYM","ASH","GLH","LYN","MSE"}
    lig = [a for a in A if a["res"] not in AA]        # the Zenodo models write the substrate as ATOM records
    prot = [a for a in A if a["res"] in AA]
    resn = lig[0]["res"]
    if resn == "MOL":   # substrate model: reactive C3 = carbon bonded to the ring N (N with exactly one O neighbour)
        ringN = [a for a in lig if a["el"] == "N" and sum(1 for o in lig if o["el"] == "O" and math.dist(a["xyz"], o["xyz"]) < 1.6) == 1][0]
        c3 = [a for a in lig if a["el"] == "C" and math.dist(a["xyz"], ringN["xyz"]) < 1.5][0]
        sites = {"N3": c3["xyz"]}
        benzo = [a["xyz"] for a in lig if a["el"] == "C" and a is not c3]   # the six benzo carbons remain once C3 is removed
    else:
        sites = {k: next(a["xyz"] for a in lig if a["n"] == v) for k, v in RING_N[resn].items()}
        benzo = [next(a["xyz"] for a in lig if a["n"] == v) for v in BENZO[resn]]
    best = (99, "-", "-")
    for a in prot:
        if a["res"] in ACID and a["n"] in ACID[a["res"]]:
            for k, xyz in sites.items():
                d = math.dist(a["xyz"], xyz)
                if d < best[0]: best = (d, f'{a["res"].title()}{a["num"]}', k)
    bc, bn = cen(benzo), normal(benzo)
    pi = (99, "-", 0)
    groups = {}
    for a in prot:
        if a["res"] in AR6 and a["n"] in AR6[a["res"]]: groups.setdefault((a["res"], a["num"]), []).append(a["xyz"])
    for (r, num), p in groups.items():
        if len(p) == 6:
            d = math.dist(cen(p), bc)
            if d < pi[0]:
                ang = math.degrees(math.acos(min(1, abs(sum(x*y for x, y in zip(normal(p), bn))))))
                pi = (d, f"{r.title()}{num}", ang)
    rows.append(dict(structure=key.split("/")[1], variant=label, kcat_KM=kin, base_res=best[1], base_dist=round(best[0], 2),
                     base_contacts=("C3 (reactive C)" if resn == "MOL" else best[2]), pi_res=pi[1], pi_dist=round(pi[0], 2),
                     pi_angle=round(pi[2]), source=src, caveat=cav))
with open(os.path.join(ROOT, "figures", "data", "geometry.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
for r in rows: print(r["structure"], "|", r["kcat_KM"], "|", r["base_res"], r["base_dist"], r["base_contacts"], "|", r["pi_res"], r["pi_dist"], r["pi_angle"])
