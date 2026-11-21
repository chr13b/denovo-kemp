#!/usr/bin/env python3
"""Step 2: nitro-stabiliser templates from nitro_enzymes/motif_table.csv.

For every observed H-bond residue (role contains 'hbond', backbone-carbonyl acceptors excluded) the source nitro group is
superposed on the TSA nitro group (C5, NO1, O11, O21) of our central TSA, in both O assignments (the nitro group is symmetric,
so each observation gives two mirror placements). The residue then sits exactly where it sat around the real nitro group,
and d(O...X), angle N-O...X and elevation are re-measured on the TSA to check they reproduce the tabulated values.

Outputs (templates/): nitro_templates.csv, nitro_atoms.json, nitro_stats.csv
"""
import csv, json, math, os, collections
import numpy as np
from common import *

OUT = os.path.join(HERE, "templates")
tsa_atoms = {a["name"]: a["xyz"] for a in parse_pdb(os.path.join(OUT, "tsa_6NT.pdb"))}
T_C, T_N, T_O1, T_O2 = tsa_atoms["C5"], tsa_atoms["NO1"], tsa_atoms["O11"], tsa_atoms["O21"]
nz_t = unit(np.cross(T_O1 - T_N, T_O2 - T_N))                       # nitro-plane normal on the TSA
tsa_heavy = {k: v for k, v in tsa_atoms.items()}
res_of = {r["pdb_id"]: r["resolution_A"] for r in csv.DictReader(open(os.path.join(NITRO, "curated.csv")))}
rows = [r for r in csv.DictReader(open(os.path.join(NITRO, "motif_table.csv"))) if "hbond" in r["role"] and r["contact_type"] != "bb_O" and r["d_O_X"]]
print(len(rows), "H-bond motif rows (backbone-carbonyl acceptors excluded)")

def f(x): return float(x) if x not in ("", None) else float("nan")
cache = {}
def load(pid):
    if pid not in cache: cache[pid] = read_cif_atoms(os.path.join(NITRO, "structures", f"{pid}.cif"))
    return cache[pid]

def nitro_with_O(atoms, ch, lres, lnum, oname):
    lig = [a for a in atoms if a["chain"] == ch and a["res"] == lres and a["num"] == lnum]
    for n in lig:
        if n["el"] != "N": continue
        Os = [b for b in lig if b["el"] == "O" and np.linalg.norm(b["xyz"] - n["xyz"]) < 1.5]
        oth = [b for b in lig if b is not n and b["el"] != "O" and np.linalg.norm(b["xyz"] - n["xyz"]) < 1.7]
        if len(Os) == 2 and len(oth) == 1 and any(o["name"] == oname for o in Os):
            C = oth[0]
            nb = [b for b in lig if b["el"] == "C" and b is not C and np.linalg.norm(b["xyz"] - C["xyz"]) < 1.6]
            ccl = [float(np.linalg.norm(b["xyz"] - C["xyz"])) for b in nb]
            aromatic = C["el"] == "C" and len(nb) >= 2 and np.mean(ccl) < 1.46
            return n, Os, C, aromatic
    return None

def measure(xyz_X, xyz_O, xyz_N, nz, atoms_Y=None):
    d = float(np.linalg.norm(xyz_X - xyz_O)); ang = angle(xyz_N, xyz_O, xyz_X)
    v = xyz_X - xyz_O; el = math.degrees(math.asin(max(-1, min(1, float(unit(v) @ nz)))))
    return d, ang, abs(el)

out, skipped = [], collections.Counter()
for r in rows:
    pid = r["pdb_id"]; atoms = load(pid)
    ch, lig = r["nitro_ligand_site"].split(":"); lres = lig.rstrip("0123456789"); lnum = int(lig[len(lres):])
    first = r["contact_atoms"].split(";")[0].strip(); xname, oname = first.split("-")
    nit = nitro_with_O(atoms, ch, lres, lnum, oname)
    if nit is None: skipped["nitro not found"] += 1; continue
    N, Os, C, arom = nit
    resn = HISN.get(r["resname"], r["resname"])
    res_atoms = [a for a in atoms if a["chain"] == r["chain"] and a["num"] == int(r["resnum"]) and a["res"] == resn and not a["het"]]
    X = next((a for a in res_atoms if a["name"] == xname), None)
    if X is None: skipped["partner atom missing"] += 1; continue
    contacted = next(o for o in Os if o["name"] == oname); other = next(o for o in Os if o is not contacted)
    P = np.array([C["xyz"], N["xyz"], contacted["xyz"], other["xyz"]])
    for tag, (To_c, To_o) in (("on_O11", (T_O1, T_O2)), ("on_O21", (T_O2, T_O1))):
        Q = np.array([T_C, T_N, To_c, To_o])
        R, t, rms = kabsch(P, Q)
        new = [(a["name"], a["el"], (R @ a["xyz"] + t)) for a in res_atoms]
        Xn = next(x for n, e, x in new if n == xname)
        d, ang, el = measure(Xn, To_c, T_N, nz_t)
        # clash screen against the TSA (everything but the nitro group being contacted)
        bad = False
        for nm, el_, x in new:
            for tn, tx in tsa_heavy.items():
                dd = float(np.linalg.norm(x - tx))
                if tn in ("O11", "O21", "NO1") and nm == xname: continue
                lim = 2.6 if (tn in ("O11", "O21", "NO1") and el_ in "NO") else 3.0
                if dd < lim and not (nm == xname and tn == ("O11" if tag == "on_O11" else "O21")): bad = True
        out.append(dict(src=pid, family=r["family"], resolution=f(res_of.get(pid)), residue=resn, contact_type=r["contact_type"], partner_atom=xname,
                        placement=tag, nitro_rmsd=round(rms, 3), arom_source_nitro=bool(arom), src_d=f(r["d_O_X"]), src_ang=f(r["ang_N_O_X"]), src_angX=f(r["ang_X"]),
                        src_elev=f(r["elev_deg"]), d=round(d, 2), ang=round(ang, 1), elev=round(el, 1), clash=bad,
                        atoms=[(n, e, x.tolist()) for n, e, x in new], resid=f'{r["chain"]}{r["resnum"]}'))
print("placements:", len(out), "| skipped:", dict(skipped), "| nitro-fit RMSD median %.3f max %.3f" % (np.median([o["nitro_rmsd"] for o in out]), max(o["nitro_rmsd"] for o in out)))
good = [o for o in out if not o["clash"] and o["nitro_rmsd"] < 0.12 and abs(o["d"] - o["src_d"]) <= 0.2]
print("after clash and fit filter:", len(good), "| max |d - source d| = %.2f" % max(abs(o["d"] - o["src_d"]) for o in good))

# de-duplicate: same residue/contact type, same placement side, side-chain RMSD < 0.8 A -> keep best resolution
def key_atoms(o): return {a[0]: np.array(a[2]) for a in o["atoms"]}
def rm(o1, o2):
    k1, k2 = key_atoms(o1), key_atoms(o2); c = [k for k in k1 if k in k2 and k not in ("N", "C", "O")]
    if len(c) < 2: c = [k for k in k1 if k in k2]
    return math.sqrt(sum(float((k1[k] - k2[k]) @ (k1[k] - k2[k])) for k in c) / len(c)) if c else 99
good.sort(key=lambda o: (o["resolution"] if o["resolution"] == o["resolution"] else 9, o["src"]))
reps = []
for o in good:
    for r in reps:
        if r["residue"] == o["residue"] and r["contact_type"] == o["contact_type"] and r["placement"] == o["placement"] and rm(r, o) < 0.8:
            r["members"].add(o["src"]); r["fams"].add(o["family"]); break
    else:
        o["members"] = {o["src"]}; o["fams"] = {o["family"]}; reps.append(o)
reps.sort(key=lambda o: (o["residue"], o["contact_type"], o["placement"], -len(o["members"])))
for i, o in enumerate(reps, 1): o["id"] = f"N{i:03d}"
print(len(reps), "de-duplicated nitro-stabiliser templates")
with open(os.path.join(OUT, "nitro_templates.csv"), "w", newline="") as fh:
    cols = ["id", "residue", "contact_type", "partner_atom", "placement", "src", "resid", "family", "resolution", "arom_source_nitro", "src_d", "src_ang", "src_angX", "src_elev", "d", "ang", "elev", "nitro_rmsd", "n_equivalent", "members"]
    w = csv.writer(fh); w.writerow(cols)
    for o in reps: w.writerow([o["id"], o["residue"], o["contact_type"], o["partner_atom"], o["placement"], o["src"], o["resid"], o["family"], o["resolution"], o["arom_source_nitro"], o["src_d"], o["src_ang"], o["src_angX"], o["src_elev"], o["d"], o["ang"], o["elev"], o["nitro_rmsd"], len(o["members"]), " ".join(sorted(o["members"]))])
json.dump({o["id"]: dict(residue=o["residue"], contact_type=o["contact_type"], atoms=o["atoms"], partner_atom=o["partner_atom"], placement=o["placement"], resid=o["resid"], src=o["src"], family=o["family"],
                         d=o["d"], ang=o["ang"], elev=o["elev"], arom=o["arom_source_nitro"], fams=sorted(o["fams"]), n=len(o["members"])) for o in reps}, open(os.path.join(OUT, "nitro_atoms.json"), "w"))

# empirical distribution per (residue, contact_type) over ALL observed H-bond rows (not only placed ones) -> typicality for scoring
allr = collections.defaultdict(list)
for r in rows: allr[(HISN.get(r["resname"], r["resname"]), r["contact_type"])].append((f(r["d_O_X"]), f(r["ang_N_O_X"]), f(r["elev_deg"])))
glob_all = [x for v in allr.values() for x in v]
def stats(v):
    a = np.array(v, float); med = np.nanmedian(a, 0); mad = np.nanmedian(np.abs(a - med), 0) * 1.4826
    return med, mad
gm, gs = stats(glob_all)
with open(os.path.join(OUT, "nitro_stats.csv"), "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["residue", "contact_type", "n", "d_med", "d_sd", "ang_med", "ang_sd", "elev_med", "elev_sd", "share_of_all_hbonds", "pooled"])
    for k, v in sorted(allr.items(), key=lambda kv: -len(kv[1])):
        pooled = len(v) < 5
        m, s = (gm, gs) if pooled else stats(v)
        s = np.maximum(s, [0.10, 6.0, 8.0])
        w.writerow([k[0], k[1], len(v), *np.round([m[0], s[0], m[1], s[1], m[2], s[2]], 2), round(len(v) / len(glob_all), 3), pooled])
print(); print("template counts by residue/contact:")
for k, v in collections.Counter((o["residue"], o["contact_type"]) for o in reps).most_common(): print(" ", k, v)
