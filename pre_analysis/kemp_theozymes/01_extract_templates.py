#!/usr/bin/env python3
"""Step 1: base and pi-stacker templates from the substrate-aligned Kemp structures.

Everything lives in the common frame of kemp_eliminase/structures/aligned_on_substrate (reference TSA = 6NT of 7K4Q chain A).
Outputs (templates/):
  tsa_6NT.pdb          the central TSA (our "substrate")
  base_templates.csv   carboxylate (Asp/Glu) and His-Asp dyad templates, de-duplicated
  pi_templates.csv     Trp/Phe/Tyr stacking templates, de-duplicated
  template_atoms.json  residue coordinates for every template (all heavy atoms)
"""
import csv, glob, json, os, math
import numpy as np
from common import *

OUT = os.path.join(HERE, "templates")
ref = parse_pdb(os.path.join(ALIGNED, "direct", "7K4Q_A.pdb"))
tsa = {a["name"]: a["xyz"] for a in ref if a["res"] == "6NT"}
tsa_elements = {a["name"]: a["el"] for a in ref if a["res"] == "6NT"}
write_pdb(os.path.join(OUT, "tsa_6NT.pdb"), [("A", 1, "6NT", True, [(n, tsa_elements[n].title(), x) for n, x in tsa.items()])],
          ["Central TSA: 6-nitrobenzotriazole from 7K4Q chain A (HG3), kemp_eliminase substrate-aligned frame"])
bic = np.array([tsa[k] for k in ["N1", "N2", "N3", "C3A", "C7A", "C4", "C5", "C6", "C7"]])
bic_c, bic_n = ring_frame(bic)
benzo = np.array([tsa[k] for k in ["C3A", "C4", "C5", "C6", "C7", "C7A"]])
benzo_c, benzo_n = ring_frame(benzo)

# metadata: resolution and lineage (kemp_eliminase/metadata + published best kcat/KM, see THEOZYME_ORIGIN.md section 3b)
res_of = {r["pdb_id"]: r["resolution_A"] for r in csv.DictReader(open(os.path.join(KEMP, "metadata", "entries.csv")))}
HG = set("3NYD 3O2L 4BS0 5RGA 5RGB 5RGC 5RGD 5RGE 5RGF 6SRW 6SRY 6SRZ 6SS1 6SS3 6TU6 7K4Q 7K4U 7K4X 7K4Z 8FOS 8KH3 8RD5 8USF 8USH 8USJ 8USL".split())
LINEAGE = {  # family -> (label, best kcat/KM, note)
    "HG": ("HG / xylanase 1GOR", 2.3e5, "HG3.17; value not verified in paper text"),
    "KE59": ("KE59 / IGPS", 60430, "R13-3/11H, 5-nitrobenzisoxazole"),
    "A532": ("1A53-2 / IGPS", 64.2, "design only"),
    "KE70": ("KE70 / DERA", 55000, "evolved + computational redesign"),
    "TIM": ("KempTIM", 32000, "best of family (related variant)"),
    "DES27": ("Des27 / IGPS chimera", 12700, "Des27.7"),
    "KABLE": ("KABLE", None, "no kinetics found"),
}
def family(pid):
    if pid in HG: return "HG"
    if pid in ("3UXD", "3UZJ", "3UZ5"): return "KE59"
    if pid in ("3NZ1", "8FOQ", "6NW4"): return "A532"
    if pid in ("8FOR", "3Q2D"): return "KE70"
    if pid == "9TZD": return "TIM"
    if pid.startswith("Des27"): return "DES27"
    if pid in ("9N0J", "29SB"): return "KABLE"
    return "other"

N1, N3, N2 = tsa["N1"], tsa["N3"], tsa["N2"]
def d(a, b): return float(np.linalg.norm(a - b))

base_raw, pi_raw = [], []
files = sorted(glob.glob(os.path.join(ALIGNED, "direct", "*.pdb")) + glob.glob(os.path.join(ALIGNED, "extended", "*.pdb")))
for f in files:
    pid = os.path.basename(f)[:-4]; src = pid.rsplit("_", 1)[0] if pid[-2:] in ("_A", "_B", "_P") else pid
    if pid.endswith("_sub"): src = pid
    atoms = parse_pdb(f); R = residues([a for a in atoms if a["res"] in AA])
    meta = dict(src=src, family=family(src), resolution=float(res_of[src]) if src in res_of and res_of[src] not in ("", None) else None,
                modelled=pid.endswith("_sub"))
    for (ch, num, rn), ats in R.items():
        xyz = {a["name"]: a["xyz"] for a in ats}
        full = [(a["name"], a["el"], a["xyz"].tolist()) for a in ats]
        if rn in ("ASP", "GLU"):
            ox = [xyz[n] for n in (("OD1", "OD2") if rn == "ASP" else ("OE1", "OE2")) if n in xyz]
            if not ox: continue
            dn3, dn1 = min(d(o, N3) for o in ox), min(d(o, N1) for o in ox)
            if min(dn3, dn1) <= 3.6:
                base_raw.append(dict(meta, kind="carboxylate", res=rn, resid=f"{ch}{num}", side="N3" if dn3 <= dn1 else "N1", atoms=full, partner=None))
            # acid as potential dyad partner handled below
        if rn == "HIS":
            nn = [xyz[n] for n in ("ND1", "NE2") if n in xyz]
            if nn and min(min(d(n, N3), d(n, N1)) for n in nn) <= 3.6:
                # dyad partner: Asp/Glu O within 3.4 A of the *other* His N
                near = min(nn, key=lambda n: min(d(n, N3), d(n, N1))); other = [n for n in nn if n is not near][0]
                for (ch2, num2, rn2), ats2 in R.items():
                    if rn2 in ("ASP", "GLU") and (ch2, num2) != (ch, num):
                        for a2 in ats2:
                            if a2["name"] in ("OD1", "OD2", "OE1", "OE2") and d(a2["xyz"], other) <= 3.4:
                                base_raw.append(dict(meta, kind="dyad", res="HIS+" + rn2, resid=f"{ch}{num}+{ch2}{num2}", side="N3" if min(d(n, N3) for n in nn) <= min(d(n, N1) for n in nn) else "N1",
                                                     atoms=full + [(a["name"], a["el"], a["xyz"].tolist()) for a in ats2], partner=f"{rn2}{num2}{ch2}", his_atoms=len(full)))
                                break
                        else: continue
                        break
        if rn in ("TRP", "PHE", "TYR"):
            best = None
            for ring in AR_RINGS[rn]:
                if not all(n in xyz for n in ring): continue
                c, n = ring_frame(np.array([xyz[x] for x in ring]))
                dist = d(c, bic_c)
                tilt = math.degrees(math.acos(min(1, abs(float(n @ bic_n)))))
                rel = c - bic_c; lat = float(np.linalg.norm(rel - (rel @ bic_n) * bic_n)); h = float(rel @ bic_n)
                if best is None or dist < best[0]: best = (dist, tilt, lat, h, len(ring))
            if best and best[0] <= 6.2 and best[1] <= 45:
                pi_raw.append(dict(meta, kind="pi", res=rn, resid=f"{ch}{num}", dist=round(best[0], 2), tilt=round(best[1], 1), lateral=round(best[2], 2),
                                   height=round(best[3], 2), ring_size=best[4], atoms=full))

def side_atoms(t):
    return {a[0]: np.array(a[2]) for a in t["atoms"] if a[0] not in BB and a[0] != "CA"} or {a[0]: np.array(a[2]) for a in t["atoms"]}
SWAPS = {"ASP": [("OD1", "OD2")], "GLU": [("OE1", "OE2")], "PHE": [("CD1", "CD2"), ("CE1", "CE2")], "TYR": [("CD1", "CD2"), ("CE1", "CE2")]}
def _rm(k1, k2):
    common = [k for k in k1 if k in k2]
    if len(common) < 3: return 99.0
    return math.sqrt(sum(float((k1[k] - k2[k]) @ (k1[k] - k2[k])) for k in common) / len(common))
def sc_rmsd(t1, t2):
    """side-chain RMSD by atom name, minimised over the chemically equivalent label swaps (OD1/OD2, CD1/CD2 ...)"""
    if t1["res"] != t2["res"]: return 99.0
    if t1["kind"] == "dyad":
        k1 = {a[0]: np.array(a[2]) for a in t1["atoms"]}; k2 = {a[0]: np.array(a[2]) for a in t2["atoms"]}
    else:
        k1, k2 = side_atoms(t1), side_atoms(t2)
    best = _rm(k1, k2)
    for resn in (t1["res"].split("+")):
        for a, b in SWAPS.get(resn, []):
            if a in k2 and b in k2:
                k3 = dict(k2); k3[a], k3[b] = k2[b], k2[a]; best = min(best, _rm(k1, k3))
    if t1["res"] in ("PHE", "TYR"):    # ring flip swaps both pairs together
        k3 = dict(k2)
        for a, b in SWAPS["PHE"]:
            if a in k3 and b in k3: k3[a], k3[b] = k2[b], k2[a]
        best = min(best, _rm(k1, k3))
    return best
def dedupe(rows, cutoff=0.6):
    rows = sorted(rows, key=lambda t: (t["resolution"] is None, t["resolution"] or 9, t["modelled"]))
    reps = []
    for t in rows:
        for r in reps:
            if r["kind"] == t["kind"] and r["res"] == t["res"] and r.get("side") == t.get("side") and sc_rmsd(r, t) < cutoff:
                r["members"].append(t["src"]); r["families"].add(t["family"]); break
        else:
            t["members"] = [t["src"]]; t["families"] = {t["family"]}; reps.append(t)
    return reps

base = dedupe(base_raw); pi = dedupe(pi_raw)
for i, t in enumerate(sorted(base, key=lambda t: (t["kind"], t["res"], t["side"], -len(t["members"]))), 1): t["id"] = f'B{i:02d}'
for i, t in enumerate(sorted(pi, key=lambda t: (t["res"], t["dist"])), 1): t["id"] = f'P{i:02d}'

def row(t, extra):
    r = dict(id=t["id"], kind=t["kind"], residue=t["res"], resid=t["resid"], source=t["src"], source_family=LINEAGE.get(t["family"], ("other",))[0],
             resolution_A=t["resolution"], modelled=t["modelled"], n_equivalent_structures=len(t["members"]),
             families=";".join(sorted(LINEAGE.get(f, (f,))[0] for f in t["families"])), members=" ".join(sorted(set(t["members"]))))
    r.update(extra); return r
with open(os.path.join(OUT, "base_templates.csv"), "w", newline="") as f:
    rows = [row(t, dict(side=t["side"], partner=t["partner"] or "")) for t in sorted(base, key=lambda t: t["id"])]
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
with open(os.path.join(OUT, "pi_templates.csv"), "w", newline="") as f:
    rows2 = [row(t, dict(centroid_dist_A=t["dist"], tilt_deg=t["tilt"], lateral_A=t["lateral"], height_A=t["height"], ring_size=t["ring_size"])) for t in sorted(pi, key=lambda t: t["id"])]
    w = csv.DictWriter(f, fieldnames=list(rows2[0])); w.writeheader(); w.writerows(rows2)
json.dump({t["id"]: dict(kind=t["kind"], res=t["res"], resid=t["resid"], atoms=t["atoms"], his_atoms=t.get("his_atoms")) for t in base + pi},
          open(os.path.join(OUT, "template_atoms.json"), "w"))
print(len(base_raw), "base hits ->", len(base), "templates;", len(pi_raw), "pi hits ->", len(pi), "templates")
for r in rows: print(r["id"], r["kind"], r["residue"], r["resid"], r["side"], r["source"], r["n_equivalent_structures"], r["families"])
print()
for r in rows2: print(r["id"], r["residue"], r["resid"], r["source"], f'd={r["centroid_dist_A"]} tilt={r["tilt_deg"]} lat={r["lateral_A"]} h={r["height_A"]}', r["n_equivalent_structures"], r["families"])
