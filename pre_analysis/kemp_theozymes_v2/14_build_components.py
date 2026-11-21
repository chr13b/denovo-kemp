#!/usr/bin/env python3
"""Step 14 (idea 7 + assembly of all libraries): builds templates/components.json.

Observed components: v1 templates (15 base, 17 ring, 88 nitro H-bond) + v2 (18 nitro-pi, 12 leaving-group) + real-substrate-derived ones.
Sampled components (continuous sampling, no crystal precedent):
  base  : carboxylate placed on a parameter grid (d, angle A, torsion A, angle B, in-plane azimuth, syn/anti) around the TSA N3; the observed
          Asp/Glu rotamers (clustered from all project structures) are superposed on the target carboxylate group, so side-chain geometry is real.
  ring  : Trp/Phe/Tyr ring on a grid of height, lateral offset, tilt and face above the TSA bicycle, same rotamer superposition.
  hb / lg / npi : small rigid-body perturbations (<= 12 deg, <= 0.25 A) of the observed templates about their contact atom.
"""
import csv, glob, json, math, os, time
import numpy as np
from lib2 import *

t0 = time.time()
rng = np.random.default_rng(7)
SC = {"ASP": ["CB", "CG", "OD1", "OD2"], "GLU": ["CB", "CG", "CD", "OE1", "OE2"], "PHE": ["CB", "CG", "CD1", "CD2", "CE1", "CE2", "CZ"],
      "TYR": ["CB", "CG", "CD1", "CD2", "CE1", "CE2", "CZ", "OH"], "TRP": ["CB", "CG", "CD1", "CD2", "NE1", "CE2", "CE3", "CZ2", "CZ3", "CH2"]}
SWAP = {"ASP": [("OD1", "OD2")], "GLU": [("OE1", "OE2")], "PHE": [("CD1", "CD2"), ("CE1", "CE2")], "TYR": [("CD1", "CD2"), ("CE1", "CE2")], "TRP": []}

# ------------------------------------------------------------------ rotamer library
def collect():
    srcs = glob.glob(os.path.join(ALIGNED, "direct", "*.pdb")) + glob.glob(os.path.join(ALIGNED, "extended", "*.pdb")) + glob.glob(os.path.join(HERE2, "structures", "aligned_real", "*.pdb"))
    for f in srcs:
        yield residues([a for a in parse_pdb(f) if a["res"] in SC])
    for f in sorted(glob.glob(os.path.join(NITRO, "structures", "*.cif"))):
        yield residues([a for a in read_cif_atoms(f) if a["res"] in SC and not a["het"]])
REF = None; lib_raw = {k: [] for k in SC}
for R in collect():
    for (ch, num, rn), ats in R.items():
        xs = {a["name"]: a["xyz"] for a in ats}
        if not all(k in xs for k in ["N", "CA", "C", "O"] + SC[rn]): continue
        P = np.array([xs["N"], xs["CA"], xs["C"]])
        if REF is None: REF = P - P[1]
        Rm, tv, _ = kabsch(P, REF)
        lib_raw[rn].append({k: Rm @ xs[k] + tv for k in ["N", "CA", "C", "O"] + SC[rn]})
def srm(r1, r2, rn):
    best = 99
    for sw in range(2 ** len(SWAP[rn])):
        k2 = dict(r2)
        for i, (a, b) in enumerate(SWAP[rn]):
            if sw >> i & 1: k2[a], k2[b] = r2[b], r2[a]
        best = min(best, math.sqrt(sum(float((r1[k] - k2[k]) @ (r1[k] - k2[k])) for k in SC[rn]) / len(SC[rn])))
    return best
LIB = {}
for rn, rows in lib_raw.items():
    reps = []
    for r in rows:
        if all(srm(r, q, rn) > 0.5 for q in reps): reps.append(r)
    LIB[rn] = reps
print("rotamer library (residues -> clusters at 0.5 A):", {k: (len(lib_raw[k]), len(LIB[k])) for k in LIB}, f"{time.time()-t0:.0f}s")

def place(a, b, c, l, theta, phi):
    th, ph = math.radians(theta), math.radians(phi)
    bc = unit(c - b); u = -bc; p = unit((a - b) - ((a - b) @ bc) * bc); q = np.cross(bc, p)
    return c + l * (math.cos(th) * u + math.sin(th) * (math.cos(ph) * p + math.sin(ph) * q))
def realise(rot, rn, src_pts, dst_pts):
    R, t, rms = kabsch(np.array(src_pts), np.array(dst_pts))
    return [(k, ("C" if k in ("CA", "C") or k[0] == "C" else k[0]), (R @ v + t).tolist()) for k, v in rot.items()], rms
def cluster(items, key_atoms, cap, cutoff):
    reps = []
    for it in items:
        k1 = {a[0]: np.array(a[2]) for a in it["atoms"]}
        if all(math.sqrt(sum(float((k1[n] - {a[0]: np.array(a[2]) for a in q["atoms"]}[n]) @ (k1[n] - {a[0]: np.array(a[2]) for a in q["atoms"]}[n])) for n in key_atoms) / len(key_atoms)) > cutoff for q in reps if q["res"] == it["res"]):
            reps.append(it)
            if len(reps) >= cap * 3: break
    return reps

comps = []
# ------------------------------------------------------------------ observed components
def fams(s): return set(x for x in s.split(";") if x)
rd = lambda p: list(csv.DictReader(open(p)))
BA = json.load(open(os.path.join(V1T, "template_atoms.json")))
for r in rd(os.path.join(V1T, "base_templates.csv")):
    a = BA[r["id"]]
    comps.append(dict(id=r["id"], kind="base", bkind=r["kind"], res=a["res"] if "+" not in a["res"] else a["res"], resid=r["resid"], src=r["source"], side=r["side"],
                      atoms=[(x[0], x[1], x[2]) for x in a["atoms"]], his_atoms=a.get("his_atoms"), families=sorted(fams(r["families"])), members=r["members"].split(), modelled=r["modelled"] == "True",
                      real=False, sampled=False, kemp=True))
for r in rd(os.path.join(V1T, "pi_templates.csv")):
    a = BA[r["id"]]
    comps.append(dict(id=r["id"], kind="ring", res=a["res"], resid=r["resid"], src=r["source"], atoms=[tuple(x) for x in a["atoms"]], families=sorted(fams(r["families"])), members=r["members"].split(),
                      modelled=r["modelled"] == "True", real=False, sampled=False, kemp=True))
NA = json.load(open(os.path.join(V1T, "nitro_atoms.json")))
for r in rd(os.path.join(V1T, "nitro_templates.csv")):
    a = NA[r["id"]]
    comps.append(dict(id=r["id"], kind="hb", res=a["residue"], contact=a["contact_type"], partner=a["partner_atom"], resid=a["resid"], src=a["src"], atoms=[tuple(x) for x in a["atoms"]], families=[], members=r["members"].split(),
                      modelled=False, real=False, sampled=False, kemp=any("Kemp" in f for f in a["fams"]), arom=r["arom_source_nitro"] == "True"))
NPI = json.load(open(os.path.join(T2, "nitro_pi_atoms.json")))
for i, a in NPI.items():
    comps.append(dict(id=i, kind="npi", res=a["res"], resid=a["resid"], src=a["src"], atoms=[tuple(x) for x in a["atoms"]], families=[], members=a["members"], modelled=False, real=False, sampled=False,
                      kemp=any("Kemp" in f for f in a["fams"])))
LG = json.load(open(os.path.join(T2, "lg_atoms.json")))
for i, a in LG.items():
    comps.append(dict(id=i, kind="lg", res=a["res"], contact=a["contact"], partner=a["partner"], resid=a["resid"], src=a["src"], atoms=[tuple(x) for x in a["atoms"]], families=[], members=a["members"],
                      modelled=False, real=a["real"], sampled=False, kemp=not a["real"]))
RT = json.load(open(os.path.join(T2, "real_templates.json")))
for k, t in enumerate(RT["nitro_hb"]):
    comps.append(dict(id=f"RH{k+1}", kind="hb", res=t["res"], contact=t["contact"], partner=t["partner"], resid=t["resid"], src=t["src"], atoms=[tuple(x) for x in t["atoms"]], families=[], members=[t["src"]],
                      modelled=False, real=True, sampled=False, kemp=False, arom=True))
for k, t in enumerate(RT["base_O1"]):
    comps.append(dict(id=f"RB{k+1}", kind="base", bkind="carboxylate", res=t["res"], resid=t["resid"], src=t["src"], side="N1", atoms=[tuple(x) for x in t["atoms"]], his_atoms=None, families=[], members=[t["src"]],
                      modelled=False, real=True, sampled=False, kemp=False))
for k, t in enumerate(RT["ring"]):
    comps.append(dict(id=f"RR{k+1}", kind="ring", res=t["res"], resid=t["resid"], src=t["src"], atoms=[tuple(x) for x in t["atoms"]], families=[], members=[t["src"]], modelled=False, real=True, sampled=False, kemp=False))
n_obs = len(comps)
print("observed components:", {k: sum(c["kind"] == k for c in comps) for k in ("base", "ring", "npi", "hb", "lg")})

# ------------------------------------------------------------------ sampled bases
site, A2, A3 = TSA["N3"], TSA["C3A"], TSA["N2"]
sb = {"ASP": [], "GLU": []}; n_try = 0
for dd in (2.45, 2.65, 2.85):
    for angA in (118, 128, 138):
        for torA in (180, 163, -163):
            for angB in (110, 125):
                for phi in (0, 180, 90, -90):
                    for psi in (0, 180):
                        O1 = place(A3, A2, site, dd, angA, torA); C = place(A2, site, O1, 1.26, angB, phi); O2 = place(site, O1, C, 1.26, 120, psi)
                        if d(C, TSA["C3A"]) < 2.6 or min(d(O2, TSA[k]) for k in TSA) < 2.5: continue
                        for rn, names in (("ASP", ("CG", "OD1", "OD2")), ("GLU", ("CD", "OE1", "OE2"))):
                            for rot in LIB[rn]:
                                for sw in (0, 1):
                                    src = [rot[names[0]], rot[names[1]], rot[names[2]]]; dst = [C, O1, O2] if not sw else [C, O2, O1]
                                    atoms, rms = realise(rot, rn, src, dst); n_try += 1
                                    c = dict(id="", kind="base", bkind="carboxylate", res=rn, resid="sampled", src="sampled", side="N3", atoms=atoms, his_atoms=None, families=[], members=[], modelled=False, real=False, sampled=True, kemp=False)
                                    if vs_tsa_hard(c) and False: continue
                                    Xc = np.array([a[2] for a in atoms]); nm = [a[0] for a in atoms]
                                    mask = np.array([n not in ("OD1", "OD2", "OE1", "OE2") for n in nm])
                                    if np.linalg.norm(Xc[mask][:, None, :] - TSA_XYZ[None, :, :], axis=2).min() < 2.7: continue
                                    s = score_base(c)
                                    if s >= 0.80: c["_s"] = s; sb[rn].append(c)
print(f"sampled base placements tried {n_try:,}; kept (score >= 0.8, no TSA clash): ASP {len(sb['ASP']):,}, GLU {len(sb['GLU']):,}  {time.time()-t0:.0f}s")
sampled_b = []
for rn in ("ASP", "GLU"):
    items = sorted(sb[rn], key=lambda c: -c["_s"])
    reps = []
    keyn = ["CA", "CB", "CG"] + (["CD"] if rn == "GLU" else [])
    for c in items:
        k1 = {a[0]: np.array(a[2]) for a in c["atoms"]}
        if all(math.sqrt(sum(float((k1[n] - {a[0]: np.array(a[2]) for a in q["atoms"]}[n]) @ (k1[n] - {a[0]: np.array(a[2]) for a in q["atoms"]}[n])) for n in keyn) / len(keyn)) > 1.0 for q in reps): reps.append(c)
        if len(reps) >= 70: break
    sampled_b += reps
for i, c in enumerate(sampled_b, 1): c["id"] = f"SB{i:03d}"; c.pop("_s", None)
comps += sampled_b
print("sampled bases after clustering (1.0 A):", len(sampled_b))

# ------------------------------------------------------------------ sampled ring stackers
def basis(n):
    e1 = unit(np.cross(n, [1, 0, 0] if abs(n[0]) < 0.9 else [0, 1, 0])); return e1, np.cross(n, e1)
u0, v0 = basis(BIC_N); sr = {"PHE": [], "TYR": [], "TRP": []}; n_try = 0
for face in (1, -1):
    for h in (3.4, 3.8, 4.2):
        for (r, th) in [(0, 0)] + [(r_, t_) for r_ in (1.2, 2.2) for t_ in (0, 90, 180, 270)]:
            for tilt, tdir in [(0, 0)] + [(15, t_) for t_ in (0, 90, 180, 270)]:
                cen = BIC_C + face * h * BIC_N + r * (math.cos(math.radians(th)) * u0 + math.sin(math.radians(th)) * v0)
                nrm = face * BIC_N
                if tilt:   # tilt the ring normal toward an in-plane direction
                    td = math.cos(math.radians(tdir)) * u0 + math.sin(math.radians(tdir)) * v0
                    nrm = unit(math.cos(math.radians(tilt)) * nrm + math.sin(math.radians(tilt)) * td)
                e1, e2 = basis(nrm)
                verts = [cen + 1.40 * (math.cos(math.radians(60 * k)) * e1 + math.sin(math.radians(60 * k)) * e2) for k in range(6)]
                for rn in ("PHE", "TYR", "TRP"):
                    ring = AR_RINGS[rn][0]
                    for rot in LIB[rn]:
                        src = [rot[k] for k in ring]
                        for rev in (0, 1):
                            for s_ in range(6):
                                order = [(s_ + (k if not rev else -k)) % 6 for k in range(6)]
                                atoms, rms = realise(rot, rn, src, [verts[o] for o in order]); n_try += 1
                                if rms > 0.12: continue
                                c = dict(id="", kind="ring", res=rn, resid="sampled", src="sampled", atoms=atoms, families=[], members=[], modelled=False, real=False, sampled=True, kemp=False)
                                Xc = np.array([a[2] for a in atoms])
                                if np.linalg.norm(Xc[:, None, :] - TSA_XYZ[None, :, :], axis=2).min() < 2.8: continue
                                s = score_ring(c)
                                if s >= 0.5: c["_s"] = s; sr[rn].append(c)
print(f"sampled ring placements tried {n_try:,}; kept: " + ", ".join(f"{k} {len(v):,}" for k, v in sr.items()) + f"  {time.time()-t0:.0f}s")
sampled_r = []
for rn in ("PHE", "TYR", "TRP"):
    items = sorted(sr[rn], key=lambda c: -c["_s"]); reps = []
    keyn = ["CA", "CB", "CG"] + (["CZ"] if rn != "TRP" else ["CH2"])
    for c in items:
        k1 = {a[0]: np.array(a[2]) for a in c["atoms"]}
        if all(math.sqrt(sum(float((k1[n] - {a[0]: np.array(a[2]) for a in q["atoms"]}[n]) @ (k1[n] - {a[0]: np.array(a[2]) for a in q["atoms"]}[n])) for n in keyn) / len(keyn)) > 1.3 for q in reps): reps.append(c)
        if len(reps) >= 50: break
    sampled_r += reps
for i, c in enumerate(sampled_r, 1): c["id"] = f"SR{i:03d}"; c.pop("_s", None)
comps += sampled_r
print("sampled ring stackers after clustering (1.3 A):", len(sampled_r))

# ------------------------------------------------------------------ perturbations of hb / lg / npi
def rot_matrix(axis, ang):
    axis = unit(axis); K = np.array([[0, -axis[2], axis[1]], [axis[2], 0, -axis[0]], [-axis[1], axis[0], 0]]); a = math.radians(ang)
    return np.eye(3) + math.sin(a) * K + (1 - math.cos(a)) * K @ K
def perturb(c, pivot, accept, tries=8, keep=3, tag="P"):
    out = []
    for _ in range(tries):
        Rm = rot_matrix(rng.normal(size=3), rng.uniform(4, 12)); tv = unit(rng.normal(size=3)) * rng.uniform(0, 0.25)
        atoms = [(n, e, (Rm @ (np.array(x) - pivot) + pivot + tv).tolist()) for n, e, x in c["atoms"]]
        n = dict(c, atoms=atoms, sampled=True, src=c["src"] + "~", members=[], families=[]); n.pop("_a", None)
        if vs_tsa_hard(n) or not accept(n): continue
        out.append(n)
        if len(out) >= keep: break
    return out
extra = []
for c in [c for c in comps if c["kind"] == "hb" and not c["sampled"]]:
    m0 = measure_hb(c); piv = TSA[m0["o"]]
    extra += perturb(c, piv, lambda n: 2.6 <= measure_hb(n)["d"] <= 3.4, keep=2)
for c in [c for c in comps if c["kind"] == "lg" and not c["sampled"]]:
    extra += perturb(c, TSA["N1"], lambda n: 2.7 <= measure_lg(n)["d"] <= 3.5, keep=3)
for c in [c for c in comps if c["kind"] == "npi" and not c["sampled"]]:
    extra += perturb(c, NIT_N, lambda n: 3.2 <= measure_npi(n)["z"] <= 4.0, keep=2)
for i, c in enumerate(extra, 1): c["id"] = c["id"] + f"~{i}"
comps += extra
print("perturbed variants:", {k: sum(c["kind"] == k for c in extra) for k in ("hb", "lg", "npi")})
for c in comps: c.pop("_a", None)
json.dump(comps, open(os.path.join(T2, "components.json"), "w"))
print("total components:", {k: sum(c["kind"] == k for c in comps) for k in ("base", "ring", "npi", "hb", "lg")}, f"| sampled {sum(c['sampled'] for c in comps)} | {time.time()-t0:.0f}s")
