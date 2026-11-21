#!/usr/bin/env python3
"""Step 10: the REAL substrate (5-nitro-1,2-benzisoxazole, CCD H5J) in the TSA frame.

Atom correspondence substrate -> TSA (same as used for the Des27 substrate models):
  C3(H) -> N3, N2 -> N2, O1 -> N1, C3a -> C3A, C7a -> C7A, C4 -> C4, C5 -> C5, C6 -> C6, C7 -> C7, nitro N -> NO1
The nitro oxygens are assigned to O11/O21 by proximity after the fit. Output: templates/substrate_5NBI.pdb (+ hydrogens), substrate.json.
Also downloads the other two real-substrate complexes (7EPO, 7Y9J) for step 11.
"""
import json, os, urllib.request
import numpy as np
from common2 import *

# H5J_ideal.sdf atom order (see kemp_eliminase/ligands/H5J.cif): 1 OAB,2 NAL,3 OAA,4 CAI,5 CAF,6 CAJ,7 CAE,8 NAG,9 OAH,10 CAK,11 CAD,12 CAC,13..16 H
sdf = [l.split() for l in open(os.path.join(KEMP, "ligands", "H5J_ideal.sdf")).read().split("\n")[4:20]]
xyz = np.array([[float(x) for x in l[:3]] for l in sdf]); el = [l[3] for l in sdf]
NAMES = {1: "O51", 2: "N5", 3: "O52", 4: "C5", 5: "C4", 6: "C3A", 7: "C3", 8: "N2", 9: "O1", 10: "C7A", 11: "C7", 12: "C6", 13: "H4", 14: "H3", 15: "H7", 16: "H6"}
TO_TSA = {7: "N3", 8: "N2", 9: "N1", 6: "C3A", 10: "C7A", 5: "C4", 4: "C5", 12: "C6", 11: "C7", 2: "NO1"}
tsa = {a["name"]: a["xyz"] for a in parse_pdb(os.path.join(V1T, "tsa_6NT.pdb"))}
P = np.array([xyz[i - 1] for i in TO_TSA]); Q = np.array([tsa[t] for t in TO_TSA.values()])
R, t, rms = kabsch(P, Q); new = xyz @ R.T + t
# assign nitro O's to the closest TSA O (planar group: either assignment is a valid superposition)
o_sub = [new[0], new[2]]; o_tsa = [tsa["O11"], tsa["O21"]]
swap = np.linalg.norm(o_sub[0] - o_tsa[0]) + np.linalg.norm(o_sub[1] - o_tsa[1]) > np.linalg.norm(o_sub[0] - o_tsa[1]) + np.linalg.norm(o_sub[1] - o_tsa[0])
print(f"substrate -> TSA superposition on {len(TO_TSA)} atoms: RMSD {rms:.3f} A; nitro O swap = {swap}")
for sub_i, tn in TO_TSA.items(): print(f"   {NAMES[sub_i]:4}-> {tn:4} {np.linalg.norm(new[sub_i-1]-tsa[tn]):.2f} A apart")
atoms = [(NAMES[i + 1], el[i], new[i]) for i in range(16)]
write_pdb(os.path.join(T2, "substrate_5NBI.pdb"), [("A", 1, "5NB", True, [(n, e.title(), x.tolist()) for n, e, x in atoms])],
          ["Real substrate 5-nitro-1,2-benzisoxazole (H5J ideal geometry) superposed on the 6NT TSA frame of kemp_theozymes"])
json.dump(dict(atoms=[(n, e, x.tolist()) for n, e, x in atoms], rmsd_to_tsa=rms, nitro_swap=bool(swap), map_to_tsa={NAMES[i]: v for i, v in TO_TSA.items()}),
          open(os.path.join(T2, "substrate.json"), "w"), indent=1)
c3, h3 = new[6], new[13]
print("reactive C3 at", np.round(c3, 2), "| H3 at", np.round(h3, 2), "| C3-H length %.2f | C3 to TSA N3 %.2f A; H3 to N3 %.2f A" % (np.linalg.norm(h3 - c3), np.linalg.norm(c3 - tsa["N3"]), np.linalg.norm(h3 - tsa["N3"])))

# the other two real-substrate complexes
for pid in ("7EPO", "7Y9J"):
    dst = os.path.join(HERE2, "structures", f"{pid}.cif")
    if not os.path.exists(dst):
        open(dst, "wb").write(urllib.request.urlopen(f"https://files.rcsb.org/download/{pid}.cif", timeout=60).read())
    print("have", pid, os.path.getsize(dst) // 1024, "KB")
