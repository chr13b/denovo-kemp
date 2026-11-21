#!/usr/bin/env python3
"""Extract theozyme features around bound Kemp transition-state analogs (TSAs).

For every structure in structures/core/*.pdb that contains a benzotriazole-type
TSA, report per ligand copy:
  * base              : Asp/Glu carboxylate O (or His imidazole N) within 3.6 A of a ring N (not the nitro N)
  * pi-stack          : Trp/Phe/Tyr/His ring centroid within 5.5 A of the TSA
                        benzo-ring centroid, ring normals within 40 deg
  * nitro H-bonds     : N/O polar atoms within 3.5 A of the nitro oxygens
  * shell             : all residues with any atom within 4.5 A
Outputs: extracted/theozyme_summary.csv, extracted/shell_residues.csv and
extracted/<PDB>_<chain><resseq>_shell.pdb (TSA + shell residues, native frame).
Pure python (no numpy) so it runs anywhere.
"""
import csv, glob, math, os

TSA = {"6NT", "3NY", "0CU", "0CT", "VWF"}   # benzotriazole TS analogs
HERE = os.path.dirname(os.path.abspath(__file__))
CORE = os.path.join(HERE, "..", "structures", "core")
OUT = os.path.join(HERE, "extracted")
AROM = {"TRP": ["CG", "CD1", "NE1", "CE2", "CD2", "CE3", "CZ3", "CH2", "CZ2"],  # indole (use 6-ring + 5-ring)
        "PHE": ["CG", "CD1", "CD2", "CE1", "CE2", "CZ"],
        "TYR": ["CG", "CD1", "CD2", "CE1", "CE2", "CZ"],
        "HIS": ["CG", "ND1", "CD2", "CE1", "NE2"]}
ACID_O = {"ASP": ["OD1", "OD2"], "GLU": ["OE1", "OE2"], "HIS": ["ND1", "NE2"]}  # HIS = imidazole base (KE70 His17-Asp45 dyad)


def sub(a, b): return [a[i] - b[i] for i in range(3)]
def dist(a, b): return math.sqrt(sum(x * x for x in sub(a, b)))
def cross(a, b): return [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]
def norm(v):
    n = math.sqrt(sum(x * x for x in v)) or 1.0
    return [x / n for x in v]
def centroid(pts): return [sum(p[i] for p in pts) / len(pts) for i in range(3)]


def ring_normal(pts):
    c = centroid(pts)
    # plane normal from best of a few triples (adequate for planar rings)
    n = [0, 0, 0]
    for i in range(len(pts)):
        v = cross(sub(pts[i], c), sub(pts[(i + 1) % len(pts)], c))
        n = [n[k] + v[k] for k in range(3)]
    return norm(n)


def parse(path):
    atoms = []
    for l in open(path):
        if l.startswith(("ATOM", "HETATM")):
            alt = l[16]
            if alt not in (" ", "A"):
                continue
            atoms.append(dict(rec=l[:6].strip(), name=l[12:16].strip(), res=l[17:20].strip(),
                              chain=l[21], num=int(l[22:26]), icode=l[26].strip(),
                              xyz=[float(l[30:38]), float(l[38:46]), float(l[46:54])],
                              el=(l[76:78].strip() or l[12:16].strip()[0]), line=l.rstrip("\n")))
    return atoms


def main():
    os.makedirs(OUT, exist_ok=True)
    summ, shell_rows = [], []
    for path in sorted(glob.glob(os.path.join(CORE, "*.pdb"))):
        pid = os.path.basename(path)[:4]
        atoms = parse(path)
        prot = [a for a in atoms if a["rec"] == "ATOM"]
        ligs = {}
        for a in atoms:
            if a["rec"] == "HETATM" and a["res"] in TSA:
                ligs.setdefault((a["res"], a["chain"], a["num"]), []).append(a)
        for (lname, lch, lnum), la in ligs.items():
            ringN, nitroO, ringC = [], [], []
            for a in la:
                if a["el"] == "N":
                    nb = [b for b in la if b["el"] == "O" and dist(a["xyz"], b["xyz"]) < 1.6]
                    if len(nb) >= 2:
                        nitroO += nb
                    else:
                        ringN.append(a)
                elif a["el"] == "C":
                    ringC.append(a)
            # benzo ring = 6 carbons (all ring C of benzotriazole are in fused system; use all C+ring N centroid)
            benzo_pts = [a["xyz"] for a in ringC]
            lig_c = centroid(benzo_pts) if benzo_pts else centroid([a["xyz"] for a in la])
            lig_n = ring_normal([a["xyz"] for a in la if a not in nitroO and a["el"] in "CN"][:9])
            # residues in shell
            res = {}
            for a in prot:
                d = min(dist(a["xyz"], b["xyz"]) for b in la)
                if d <= 4.5:
                    k = (a["chain"], a["num"], a["icode"], a["res"])
                    res[k] = min(res.get(k, 99), d)
            base, stack, hb = [], [], []
            for a in prot:
                if a["res"] in ACID_O and a["name"] in ACID_O[a["res"]]:
                    for n in ringN:
                        d = dist(a["xyz"], n["xyz"])
                        if d <= 3.6:
                            base.append(f'{a["res"]}{a["num"]}{a["chain"]}:{a["name"]}..{n["name"]} {d:.2f}')
                for o in nitroO:
                    if a["el"] in "NO" and a["res"] not in TSA:
                        d = dist(a["xyz"], o["xyz"])
                        if d <= 3.5:
                            hb.append(f'{a["res"]}{a["num"]}{a["chain"]}:{a["name"]}..{o["name"]} {d:.2f}')
            seen = set()
            for (ch, num, ic, rn) in res:
                if rn in AROM and (ch, num) not in seen:
                    seen.add((ch, num))
                    pts = [a["xyz"] for a in prot if a["chain"] == ch and a["num"] == num and a["name"] in AROM[rn]]
                    if len(pts) >= 5:
                        c = centroid(pts); d = dist(c, lig_c)
                        ang = math.degrees(math.acos(min(1, abs(sum(x*y for x, y in zip(ring_normal(pts), lig_n))))))
                        if d <= 5.5 and ang <= 40:
                            stack.append(f"{rn}{num}{ch} {d:.1f}A/{ang:.0f}deg")
            tag = f"{pid}_{lch}{lnum}"
            summ.append([pid, lname, f"{lch}{lnum}", len(res), "; ".join(sorted(set(base))) or "-",
                         "; ".join(stack) or "-", "; ".join(sorted(set(hb))) or "-"])
            for (ch, num, ic, rn), d in sorted(res.items()):
                shell_rows.append([pid, lname, f"{lch}{lnum}", f"{rn}{num}{ch}", round(d, 2)])
            keep = {(c, n) for (c, n, _, _) in res}
            with open(os.path.join(OUT, f"{tag}_shell.pdb"), "w") as f:
                for a in la: f.write(a["line"] + "\n")
                for a in prot:
                    if (a["chain"], a["num"]) in keep: f.write(a["line"] + "\n")
                f.write("END\n")
    with open(os.path.join(OUT, "theozyme_summary.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["pdb", "tsa", "tsa_id", "n_shell_res", "base_Asp/Glu/His(<=3.6A to ring N)", "pi_stack", "nitro_polar_contacts(<=3.5A)"])
        w.writerows(summ)
    with open(os.path.join(OUT, "shell_residues.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["pdb", "tsa", "tsa_id", "residue", "min_dist_A"]); w.writerows(shell_rows)
    for r in summ: print(" | ".join(map(str, r)))


if __name__ == "__main__":
    main()
