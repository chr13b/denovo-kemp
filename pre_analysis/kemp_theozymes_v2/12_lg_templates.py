#!/usr/bin/env python3
"""Step 12 (idea 1): leaving-group / oxyanion stabiliser templates.

The TSA N1 stands in for the substrate ring oxygen O1, the atom that becomes the phenolate oxygen in the product. Any N-H or O-H donor within
3.6 A of it, in the aligned TSA structures (kemp_eliminase/structures/aligned_on_substrate/{direct,extended}) and in the real-substrate complexes
(structures/aligned_real/, measured at the substrate O1), is a template. Backbone carbonyl O and carboxylate O are excluded (acceptors do not
stabilise developing negative charge). Outputs: templates/lg_templates.csv, lg_atoms.json.
"""
import csv, glob, json, math, os
import numpy as np
from common2 import *

tsa = {a["name"]: a["xyz"] for a in parse_pdb(os.path.join(V1T, "tsa_6NT.pdb"))}
N1, N2, C7A = tsa["N1"], tsa["N2"], tsa["C7A"]
bic = np.array([tsa[k] for k in CORE]); bic_c, bic_n = ring_frame(bic)
res_of = {r["pdb_id"]: r["resolution_A"] for r in csv.DictReader(open(os.path.join(KEMP, "metadata", "entries.csv")))}
DONORS = {"N", "NE2", "NE1", "ND2", "NZ", "NE", "NH1", "NH2", "ND1", "OG", "OG1", "OH"}
def d(a, b): return float(np.linalg.norm(a - b))
raw = []
files = [(f, False) for f in sorted(glob.glob(os.path.join(ALIGNED, "direct", "*.pdb")) + glob.glob(os.path.join(ALIGNED, "extended", "*.pdb")))] + \
        [(f, True) for f in sorted(glob.glob(os.path.join(HERE2, "structures", "aligned_real", "*.pdb")))]
for f, real in files:
    pid = os.path.basename(f)[:-4]; src = pid.rsplit("_", 1)[0] if not real else pid.split("_")[0]
    atoms = parse_pdb(f)
    if real:
        lig = {a["name"]: a["xyz"] for a in atoms if a["res"] == "5NB"}; site = lig["O1"]
        prot = [a for a in atoms if a["res"] in AA]
    else:
        site = N1; prot = [a for a in atoms if a["res"] in AA]
    R = residues(prot)
    for (ch, num, rn), ats in R.items():
        best = None
        for a in ats:
            if a["name"] in DONORS and a["el"] in ("N", "O"):
                if rn in ("ASP", "GLU") or (a["el"] == "O" and a["name"] not in ("OG", "OG1", "OH")): continue
                dd = d(a["xyz"], site)
                if dd <= 3.6 and (best is None or dd < best[0]): best = (dd, a)
        if best:
            dd, a = best
            raw.append(dict(src=src, real=real, res=rn, resid=f"{ch}{num}", partner=a["name"], d=dd, ang_N2=angle(N2, site, a["xyz"]), ang_C7A=angle(C7A, site, a["xyz"]),
                            elev=abs(math.degrees(math.asin(max(-1, min(1, float(unit(a["xyz"] - site) @ bic_n)))))),
                            contact="bb_NH" if a["name"] == "N" else "sidechain", atoms=[(x["name"], x["el"], x["xyz"].tolist()) for x in ats],
                            resolution=float(res_of[src]) if src in res_of and res_of[src] not in ("", None) else None))
print(len(raw), "donor contacts within 3.6 A of the N1/O1 site")
def key(t): return {a[0]: np.array(a[2]) for a in t["atoms"]}
def rm(t1, t2):
    k1, k2 = key(t1), key(t2); c = [k for k in k1 if k in k2]
    return math.sqrt(sum(float((k1[k] - k2[k]) @ (k1[k] - k2[k])) for k in c) / len(c)) if len(c) >= 3 else 99
raw.sort(key=lambda t: (not t["real"], t["resolution"] is None, t["resolution"] or 9))   # real-substrate first, then best resolution
reps = []
for t in raw:
    for r in reps:
        if r["res"] == t["res"] and r["partner"] == t["partner"] and rm(r, t) < 0.8: r["members"].add(t["src"]); break
    else: t["members"] = {t["src"]}; reps.append(t)
reps.sort(key=lambda t: (-len(t["members"]), t["res"]))
for i, t in enumerate(reps, 1): t["id"] = f"L{i:02d}"
with open(os.path.join(T2, "lg_templates.csv"), "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["id", "residue", "resid", "partner_atom", "contact", "source", "real_substrate", "d_A", "ang_N2_N1_X", "ang_C7A_N1_X", "elev_deg", "n_equivalent", "members"])
    for t in reps: w.writerow([t["id"], t["res"], t["resid"], t["partner"], t["contact"], t["src"], t["real"], round(t["d"], 2), round(t["ang_N2"], 1), round(t["ang_C7A"], 1), round(t["elev"], 1), len(t["members"]), " ".join(sorted(t["members"]))])
json.dump({t["id"]: dict(res=t["res"], resid=t["resid"], partner=t["partner"], contact=t["contact"], src=t["src"], real=t["real"], d=t["d"], ang_N2=t["ang_N2"], ang_C7A=t["ang_C7A"], elev=t["elev"],
                         atoms=t["atoms"], members=sorted(t["members"])) for t in reps}, open(os.path.join(T2, "lg_atoms.json"), "w"))
print(f'{"id":4}{"res":5}{"resid":8}{"atom":6}{"src":8}{"real":6}{"d":>5}{"angN2":>7}{"angC7A":>7}{"elev":>6}{"n":>4}')
for t in reps: print(f'{t["id"]:4}{t["res"]:5}{t["resid"]:8}{t["partner"]:6}{t["src"]:8}{str(t["real"]):6}{t["d"]:5.2f}{t["ang_N2"]:7.0f}{t["ang_C7A"]:7.0f}{t["elev"]:6.0f}{len(t["members"]):4}')
