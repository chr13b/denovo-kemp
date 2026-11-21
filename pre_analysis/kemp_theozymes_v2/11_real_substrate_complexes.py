#!/usr/bin/env python3
"""Step 11: cross-check with real-substrate crystal complexes (H5J = 5-nitro-1,2-benzisoxazole).

6DNJ (KE07 round 5), 7EPO (ketosteroid isomerase), 7Y9J (P450 BM3-TMK). Each H5J copy is superposed on the substrate model in the TSA frame
(same atom correspondence as step 10), the protein is moved with it, and we measure what surrounds the real substrate:
  base candidate : closest Asp/Glu carboxylate O or His N to the reactive C3, and the C3-H...O geometry using the model H
  pi             : aromatic ring distance/tilt to the benzo ring and to the nitro group
  nitro contacts : N/O donors-acceptors within 3.5 A of a nitro O (d, angle N-O...X, elevation), as in nitro_enzymes
  O1 (N1) side   : N/O within 3.5 A of the ring oxygen
Outputs: structures/aligned_real/<PDB>_<chain>.pdb, real_substrate_contacts.csv, templates/real_*.json (residues for later steps).
"""
import csv, json, math, os
import numpy as np
from common2 import *

SUB = json.load(open(os.path.join(T2, "substrate.json"))); sub = {a[0]: np.array(a[2]) for a in SUB["atoms"]}
H5J = {"OAB": "O51", "NAL": "N5", "OAA": "O52", "CAI": "C5", "CAF": "C4", "CAJ": "C3A", "CAE": "C3", "NAG": "N2", "OAH": "O1", "CAK": "C7A", "CAD": "C7", "CAC": "C6"}
FIT = ["C3", "N2", "O1", "C3A", "C7A", "C4", "C5", "C6", "C7", "N5"]
benzo = np.array([sub[k] for k in ("C3A", "C4", "C5", "C6", "C7", "C7A")]); bz_c, bz_n = ring_frame(benzo)
nit_N = sub["N5"]; nit_n = unit(np.cross(sub["O51"] - nit_N, sub["O52"] - nit_N))
OUT = os.path.join(HERE2, "structures", "aligned_real"); os.makedirs(OUT, exist_ok=True)
SRC = {"6DNJ": os.path.join(KEMP, "structures", "extended", "6DNJ.cif"), "7EPO": os.path.join(HERE2, "structures", "7EPO.cif"), "7Y9J": os.path.join(HERE2, "structures", "7Y9J.cif")}
TITLE = {"6DNJ": "KE07 round 5 (designed Kemp eliminase)", "7EPO": "ketosteroid isomerase", "7Y9J": "P450 BM3-TMK"}

def d(a, b): return float(np.linalg.norm(a - b))
rows, store = [], {}
for pid, path in SRC.items():
    atoms = read_cif_atoms(path)
    copies = {}
    for a in atoms:
        if a["raw"] == "H5J": copies.setdefault((a["chain"], a["num"]), []).append(a)
    print(pid, TITLE[pid], "| H5J copies:", list(copies))
    for (ch, num), lig in copies.items():
        nm = {a["name"]: a["xyz"] for a in lig}
        if not all(k in nm for k in H5J): print("   incomplete ligand", ch, num); continue
        P = np.array([nm[k] for k, v in H5J.items() if v in FIT]); Q = np.array([sub[v] for k, v in H5J.items() if v in FIT])
        R, t, rms = kabsch(P, Q)
        T = lambda x: R @ x + t
        # protein atoms in the common frame
        prot = [dict(a, xyz=T(a["xyz"])) for a in atoms if a["raw"] in AA]
        ligT = {H5J[k]: T(v) for k, v in nm.items()}
        # keep residues with any atom within 12 A of the substrate for the aligned file
        keep = {(a["chain"], a["num"]) for a in prot if min(d(a["xyz"], ligT[k]) for k in ("C3", "N5")) < 12}
        blocks = [("L", 1, "5NB", True, [(k, ("N" if k[0] == "N" else "O" if k[0] == "O" else "C"), v.tolist()) for k, v in ligT.items()])]
        byres = residues([a for a in prot if (a["chain"], a["num"]) in keep])
        for (c2, n2, r2), ats in byres.items(): blocks.append((c2 if len(c2) == 1 else c2[0], n2 % 10000, r2, False, [(a["name"], a["el"].title(), a["xyz"].tolist()) for a in ats]))
        write_pdb(os.path.join(OUT, f"{pid}_{ch}{num}.pdb"), blocks, [f"{pid} {TITLE[pid]}; H5J {ch}{num} superposed on the substrate model (RMSD {rms:.2f} A)"])
        # ---- measurements
        C3, O1, H3 = ligT["C3"], ligT["O1"], sub["H3"]
        R_ = residues(prot); base = []
        for (c2, n2, r2), ats in R_.items():
            if r2 in ("ASP", "GLU"):
                for a in ats:
                    if a["name"] in ("OD1", "OD2", "OE1", "OE2"):
                        dd = d(a["xyz"], C3)
                        if dd < 5.0: base.append((dd, f"{r2}{n2}{c2}:{a['name']}", d(a["xyz"], H3), angle(C3, H3, a["xyz"])))
            if r2 == "HIS":
                for a in ats:
                    if a["name"] in ("ND1", "NE2"):
                        dd = d(a["xyz"], C3)
                        if dd < 5.0: base.append((dd, f"HIS{n2}{c2}:{a['name']}", d(a["xyz"], H3), angle(C3, H3, a["xyz"])))
        base.sort()
        pis = []
        for (c2, n2, r2), ats in R_.items():
            if r2 in AR_RINGS:
                xs = {a["name"]: a["xyz"] for a in ats}
                for ring in AR_RINGS[r2]:
                    if all(k in xs for k in ring):
                        c, n = ring_frame(np.array([xs[k] for k in ring])); dist = d(c, bz_c)
                        if dist < 6.5:
                            tilt = math.degrees(math.acos(min(1, abs(float(n @ bz_n))))); rel = c - nit_N
                            zN = abs(float(rel @ nit_n)); latN = float(np.linalg.norm(rel - (rel @ nit_n) * nit_n))
                            pis.append((dist, f"{r2}{n2}{c2}", round(tilt), round(zN, 2), round(latN, 2)))
        pis.sort()
        nitro = []
        for a in prot:
            if a["el"] in ("N", "O"):
                for on in ("O51", "O52"):
                    dd = d(a["xyz"], ligT[on])
                    if 2.4 <= dd <= 3.5: nitro.append((round(dd, 2), f"{a['res']}{a['num']}{a['chain']}:{a['name']}", on))
        o1side = sorted((round(d(a["xyz"], O1), 2), f"{a['res']}{a['num']}{a['chain']}:{a['name']}") for a in prot if a["el"] in ("N", "O") and d(a["xyz"], O1) <= 3.5)
        rows.append(dict(pdb=pid, enzyme=TITLE[pid], copy=f"{ch}{num}", fit_rmsd=round(rms, 3),
                         nearest_base=("; ".join(f"{b[1]} C3...O {b[0]:.2f} H...O {b[2]:.2f} C-H...O {b[3]:.0f}deg" for b in base[:3]) or "none within 5 A"),
                         pi_rings="; ".join(f"{p[1]} {p[0]:.2f}A tilt {p[2]} | over nitro z {p[3]} lat {p[4]}" for p in pis[:3]) or "none within 6.5 A",
                         nitro_contacts="; ".join(f"{n[1]}..{n[2]} {n[0]}" for n in sorted(nitro)[:4]) or "none", o1_contacts="; ".join(f"{x[1]} {x[0]}" for x in o1side[:3]) or "none"))
        store[f"{pid}_{ch}{num}"] = dict(pdb=pid, base=[b[1] for b in base[:3]], pi=[p[1] for p in pis[:3]])
        print(f"  {ch}{num}: fit {rms:.2f} A")
        print("     base  :", rows[-1]["nearest_base"]); print("     pi    :", rows[-1]["pi_rings"]); print("     nitro :", rows[-1]["nitro_contacts"]); print("     O1    :", rows[-1]["o1_contacts"])
with open(os.path.join(HERE2, "real_substrate_contacts.csv"), "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
json.dump(store, open(os.path.join(T2, "real_complexes.json"), "w"), indent=1)
