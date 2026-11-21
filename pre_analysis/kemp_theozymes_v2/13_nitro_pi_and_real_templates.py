#!/usr/bin/env python3
"""Step 13 (idea 4 + real-substrate templates).

A) nitro-pi templates: aromatic rings stacked ON THE NITRO GROUP (role 'pi' in nitro_enzymes/motif_table.csv: ring 3.0-4.6 A above the nitro
   plane, <= 2.5 A lateral, tilt <= 40 deg). Each observation is superposed on the TSA nitro group (both O assignments) like the nitro H-bond
   templates in v1, and z / lateral offset / tilt are re-measured on the TSA.
B) real-substrate-derived templates, lifted from structures/aligned_real/ (6DNJ, 7EPO, 7Y9J): nitro donors, ring stackers, and a carboxylate at O1.
Outputs: templates/nitro_pi_templates.csv + nitro_pi_atoms.json, templates/real_templates.json
"""
import csv, json, math, os, glob
import numpy as np
from common2 import *

tsa = {a["name"]: a["xyz"] for a in parse_pdb(os.path.join(V1T, "tsa_6NT.pdb"))}
T_C, T_N, T_O1, T_O2 = tsa["C5"], tsa["NO1"], tsa["O11"], tsa["O21"]
nz_t = unit(np.cross(T_O1 - T_N, T_O2 - T_N))
res_of = {r["pdb_id"]: r["resolution_A"] for r in csv.DictReader(open(os.path.join(NITRO, "curated.csv")))}
def f(x): return float(x) if x not in ("", None) else float("nan")
def d(a, b): return float(np.linalg.norm(a - b))
def ring_atoms(res, xs):
    best = None
    for ring in AR_RINGS[res]:
        if all(k in xs for k in ring):
            c, n = ring_frame(np.array([xs[k] for k in ring]))
            if best is None or abs(float((c - T_N) @ nz_t)) < best[0]: best = (abs(float((c - T_N) @ nz_t)), ring)
    return best[1] if best else None
def nitro_stack(xs, ring, N, nz):
    c, n = ring_frame(np.array([xs[k] for k in ring])); rel = c - N
    z = abs(float(rel @ nz)); lat = float(np.linalg.norm(rel - (rel @ nz) * nz)); tilt = math.degrees(math.acos(min(1, abs(float(n @ nz)))))
    return z, lat, tilt

# ------------------------------------------------------------------ A) nitro-pi from the nitro dataset
rows = [r for r in csv.DictReader(open(os.path.join(NITRO, "motif_table.csv"))) if "pi" in r["role"] and r["pi_z_lat_ang"]]
print(len(rows), "pi-on-nitro observations in motif_table.csv")
cache, out = {}, []
for r in rows:
    pid = r["pdb_id"]; atoms = cache.setdefault(pid, read_cif_atoms(os.path.join(NITRO, "structures", f"{pid}.cif")))
    ch, lig = r["nitro_ligand_site"].split(":"); lres = lig.rstrip("0123456789"); lnum = int(lig[len(lres):])
    resn = HISN.get(r["resname"], r["resname"])
    res_atoms = [a for a in atoms if a["chain"] == r["chain"] and a["num"] == int(r["resnum"]) and a["res"] == resn and not a["het"]]
    xs = {a["name"]: a["xyz"] for a in res_atoms}
    ring = ring_atoms(resn, xs)
    if ring is None: continue
    rc = np.mean([xs[k] for k in ring], 0)
    lig_atoms = [a for a in atoms if a["chain"] == ch and a["res"] == lres and a["num"] == lnum]
    best = None
    for n in lig_atoms:
        if n["el"] != "N": continue
        Os = [b for b in lig_atoms if b["el"] == "O" and d(b["xyz"], n["xyz"]) < 1.5]
        oth = [b for b in lig_atoms if b is not n and b["el"] != "O" and d(b["xyz"], n["xyz"]) < 1.7]
        if len(Os) == 2 and len(oth) == 1:
            dd = d(n["xyz"], rc)
            if best is None or dd < best[0]: best = (dd, n, Os, oth[0])
    if best is None: continue
    _, N, Os, C = best
    zs, ls, ts = (f(x) for x in r["pi_z_lat_ang"].split("/"))
    P = np.array([C["xyz"], N["xyz"], Os[0]["xyz"], Os[1]["xyz"]])
    for tag, (a_, b_) in (("A", (T_O1, T_O2)), ("B", (T_O2, T_O1))):
        R, t, rms = kabsch(P, np.array([T_C, T_N, a_, b_]))
        new = [(a["name"], a["el"], R @ a["xyz"] + t) for a in res_atoms]
        nx = {n: x for n, e, x in new}
        z, lat, tilt = nitro_stack(nx, ring, T_N, nz_t)
        clash = any(d(x, tsa[tn]) < (2.6 if e in "NO" and tn in ("N1", "N2", "N3", "NO1", "O11", "O21") else 3.0) for n, e, x in new if n not in ("N", "O") for tn in tsa)
        out.append(dict(src=pid, family=r["family"], resolution=f(res_of.get(pid)), residue=resn, resid=f'{r["chain"]}{r["resnum"]}', placement=tag, nitro_rmsd=round(rms, 3),
                        src_z=zs, src_lat=ls, src_tilt=ts, z=round(z, 2), lat=round(lat, 2), tilt=round(tilt, 1), clash=bool(clash), ring=ring,
                        atoms=[(n, e, x.tolist()) for n, e, x in new]))
good = [o for o in out if not o["clash"] and o["nitro_rmsd"] < 0.15 and abs(o["z"] - o["src_z"]) < 0.3 and abs(o["lat"] - o["src_lat"]) < 0.5]
print(len(out), "placements;", len(good), "reproduce the observed z/lateral and are clash-free with the TSA")
good.sort(key=lambda o: (o["resolution"] if o["resolution"] == o["resolution"] else 9))
def kk(o): return {a[0]: np.array(a[2]) for a in o["atoms"]}
def rm(o1, o2):
    k1, k2 = kk(o1), kk(o2); c = [k for k in k1 if k in k2 and k not in ("N", "C", "O")]
    return math.sqrt(sum(float((k1[k] - k2[k]) @ (k1[k] - k2[k])) for k in c) / len(c)) if len(c) >= 3 else 99
reps = []
for o in good:
    for r in reps:
        if r["residue"] == o["residue"] and rm(r, o) < 0.8: r["members"].add(o["src"]); r["fams"].add(o["family"]); break
    else: o["members"] = {o["src"]}; o["fams"] = {o["family"]}; reps.append(o)
reps.sort(key=lambda o: (o["residue"], o["z"]))
for i, o in enumerate(reps, 1): o["id"] = f"X{i:02d}"
with open(os.path.join(T2, "nitro_pi_templates.csv"), "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["id", "residue", "resid", "source", "family", "placement", "z_A", "lateral_A", "tilt_deg", "src_z", "src_lat", "src_tilt", "n_equivalent", "members"])
    for o in reps: w.writerow([o["id"], o["residue"], o["resid"], o["src"], o["family"], o["placement"], o["z"], o["lat"], o["tilt"], o["src_z"], o["src_lat"], o["src_tilt"], len(o["members"]), " ".join(sorted(o["members"]))])
json.dump({o["id"]: dict(res=o["residue"], resid=o["resid"], src=o["src"], ring=o["ring"], z=o["z"], lat=o["lat"], tilt=o["tilt"], fams=sorted(o["fams"]), members=sorted(o["members"]),
                         atoms=o["atoms"]) for o in reps}, open(os.path.join(T2, "nitro_pi_atoms.json"), "w"))
print(len(reps), "nitro-pi templates:")
for o in reps: print(f'  {o["id"]} {o["residue"]:4}{o["resid"]:7}{o["src"]:6}{o["placement"]} z={o["z"]:.2f} lat={o["lat"]:.2f} tilt={o["tilt"]:.0f}  {sorted(o["fams"])[0][:28]} n={len(o["members"])}')

# ------------------------------------------------------------------ B) templates from real-substrate complexes
real = {"nitro_hb": [], "ring": [], "base_O1": []}
SUBJ = json.load(open(os.path.join(T2, "substrate.json"))); sub = {a[0]: np.array(a[2]) for a in SUBJ["atoms"]}
S_N, S_O1, S_O2 = sub["N5"], sub["O51"], sub["O52"]
bz = np.array([sub[k] for k in ("C3A", "C4", "C5", "C6", "C7", "C7A")]); bz_c, bz_n = ring_frame(bz)
for f_ in sorted(glob.glob(os.path.join(HERE2, "structures", "aligned_real", "*.pdb"))):
    pid = os.path.basename(f_)[:-4]; atoms = parse_pdb(f_); prot = [a for a in atoms if a["res"] in AA]; R = residues(prot)
    L = {a["name"]: a["xyz"] for a in atoms if a["res"] == "5NB"}                      # the crystal ligand's own (possibly twisted) nitro group
    S_N, S_O1, S_O2 = L["N5"], L["O51"], L["O52"]; nz_l = unit(np.cross(S_O1 - S_N, S_O2 - S_N))
    for (ch, num, rn), ats in R.items():
        at = [(a["name"], a["el"], a["xyz"].tolist()) for a in ats]; xs = {a["name"]: a["xyz"] for a in ats}
        for a in ats:   # nitro donors (exclude backbone carbonyl and carboxylate acceptors)
            if a["el"] in ("N", "O") and not (rn in ("ASP", "GLU")) and not (a["el"] == "O" and a["name"] in ("O", "OXT")):
                for on, oxyz in [min((("O51", S_O1), ("O52", S_O2)), key=lambda p: d(a["xyz"], p[1]))]:   # the two nitro O are interchangeable: use the nearer
                    dd = d(a["xyz"], oxyz)
                    if 2.4 <= dd <= 3.5:
                        real["nitro_hb"].append(dict(src=pid, res=rn, resid=f"{ch}{num}", partner=a["name"], d=dd, ang=angle(S_N, oxyz, a["xyz"]),
                                                     elev=abs(math.degrees(math.asin(max(-1, min(1, float(unit(a["xyz"] - oxyz) @ nz_l)))))), contact="bb_NH" if a["name"] == "N" else "sidechain", atoms=at))
        if rn in AR_RINGS and rn != "HIS":
            for ring in AR_RINGS[rn]:
                if all(k in xs for k in ring):
                    c, n = ring_frame(np.array([xs[k] for k in ring])); dist = d(c, bz_c); tilt = math.degrees(math.acos(min(1, abs(float(n @ bz_n)))))
                    if dist <= 6.0 and tilt <= 45: real["ring"].append(dict(src=pid, res=rn, resid=f"{ch}{num}", dist=dist, tilt=tilt, atoms=at)); break
        if rn in ("ASP", "GLU"):
            ox = [xs[k] for k in (("OD1", "OD2") if rn == "ASP" else ("OE1", "OE2")) if k in xs]
            if ox and min(d(o, sub["O1"]) for o in ox) <= 3.6: real["base_O1"].append(dict(src=pid, res=rn, resid=f"{ch}{num}", d=min(d(o, sub["O1"]) for o in ox), atoms=at))
json.dump(real, open(os.path.join(T2, "real_templates.json"), "w"))
print("\nreal-substrate-derived templates:")
for k, v in real.items():
    for t in v: print(f'  {k:9} {t["src"]:10} {t["res"]}{t["resid"]} ' + " ".join(f"{a}={t[a]:.2f}" for a in ("d", "ang", "elev", "dist", "tilt") if a in t) + (f' {t["partner"]}' if "partner" in t else ""))
