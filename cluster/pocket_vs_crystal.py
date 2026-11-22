"""What does the ligand's ENVIRONMENT look like in the crystals, and do our designs reproduce it?

Runs ON THE CLUSTER inside env-rfd3, next to geometry_vs_crystal.py (it imports from it):

    python pocket_vs_crystal.py <kemp_pdb_dir> <geometry_full.tsv> <label>=<sweep_root> [...]

Distances and angles to the two catalytic residues are not the whole story of why a ligand sits where it
does. The rest of the pocket (what packs against the ring, whether an aromatic side chain stacks on it) holds
it in place. The crystals are the only evidence we have of what a working pocket looks like, so this learns
that description from them and then asks the same of our designs.

Per structure, over protein atoms within 4.5 A of any ligand heavy atom:
  residues      how many residues touch the ligand
  aromatic      how many of those are F / W / Y
  stacked       whether an aromatic ring is stacked on the ligand's benzene ring: ring centroids within
                5.0 A and ring planes within 35 degrees of parallel (a strict test: Trp44 touches the ligand
                in all 25 crystal copies but passes it in only 10, so treat 'stacked' as a lower bound)
  classes       counts of aliphatic-hydrophobic, polar and charged residues

For the crystals it also lists which residues (by crystal number) touch the ligand in most copies: the pocket
map. Designs are compared in three groups: the ligand is roughly in place (base <= 4.5 A and donor <= 5 A),
the 15 best by geometry D, and everything.
"""

import csv
import math
import sys
from collections import Counter
from pathlib import Path

import numpy as np
from geometry_vs_crystal import load, measure

CUTOFF = 4.5
AROMATIC_RINGS = {
    "PHE": [["CG", "CD1", "CD2", "CE1", "CE2", "CZ"]],
    "TYR": [["CG", "CD1", "CD2", "CE1", "CE2", "CZ"]],
    "TRP": [["CD2", "CE2", "CE3", "CZ2", "CZ3", "CH2"], ["CG", "CD1", "NE1", "CE2", "CD2"]],
}
LIGAND_BENZENE = ["C3A", "C4", "C5", "C6", "C7", "C7A"]
CLASSES = {
    "aliphatic": {"ALA", "VAL", "ILE", "LEU", "MET", "CYS"},
    "polar": {"SER", "THR", "ASN", "GLN", "HIS"},
    "charged": {"ASP", "GLU", "LYS", "ARG"},
}
RANGES = {
    "base_d": (2.41, 2.69, 0.25, 2.0),
    "donor_d": (2.92, 3.24, 0.25, 2.0),
    "base_approach": (167.1, 175.8, 15, 1.0),
    "base_oop": (1.0, 11.7, 15, 1.0),
    "donor_approach": (162.1, 173.0, 15, 1.0),
    "donor_oop": (0.6, 16.1, 15, 1.0),
}


def deviation(row):
    total = 0.0
    for key, (low, high, tolerance, weight) in RANGES.items():
        value = float(row[key])
        if value < low:
            total += weight * (low - value) / tolerance
        elif value > high:
            total += (value - high) / tolerance
    return total


def plane(coords):
    centre = coords.mean(axis=0)
    return centre, np.linalg.svd(coords - centre)[2][-1]


def environment(atoms):
    """Describe what touches the ligand in one structure, or None if there is no usable ligand."""
    ligand = atoms[atoms.res_name == "6NT"]
    protein = atoms[~atoms.hetero]
    rows = [ligand[ligand.atom_name == name] for name in LIGAND_BENZENE]
    if len(ligand) < 12 or any(len(r) == 0 for r in rows):
        return None
    lig_centre, lig_normal = plane(np.array([r[0].coord for r in rows]))
    near = np.linalg.norm(protein.coord[:, None] - ligand.coord[None, :], axis=-1).min(axis=1) <= CUTOFF
    touching = {
        (c, i): n
        for c, i, n, hit in zip(protein.chain_id, protein.res_id, protein.res_name, near, strict=True)
        if hit
    }
    stacked, aromatic = False, 0
    for (chain, residue), name in touching.items():
        if name not in AROMATIC_RINGS:
            continue
        aromatic += 1
        sub = protein[(protein.chain_id == chain) & (protein.res_id == residue)]
        for ring in AROMATIC_RINGS[name]:
            pts = [sub[sub.atom_name == a] for a in ring]
            if any(len(p) == 0 for p in pts):
                continue
            centre, normal = plane(np.array([p[0].coord for p in pts]))
            tilt = math.degrees(math.acos(min(1.0, abs(float(np.dot(normal, lig_normal))))))
            if np.linalg.norm(centre - lig_centre) <= 5.0 and tilt <= 35:
                stacked = True
    counts = Counter(touching.values())
    out = {"residues": len(touching), "aromatic": aromatic, "stacked": stacked}
    for label, members in CLASSES.items():
        out[label] = sum(n for name, n in counts.items() if name in members)
    out["_touching"] = touching
    return out


def summarise(label, items):
    if not items:
        print(f"  {label:<34} (none)")
        return
    n = len(items)
    mean = lambda key: sum(i[key] for i in items) / n  # noqa: E731
    stacked = sum(1 for i in items if i["stacked"])
    print(
        f"  {label:<34}{n:>4}{mean('residues'):>9.1f}{mean('aromatic'):>9.1f}{100 * stacked / n:>9.0f}%"
        f"{mean('aliphatic'):>9.1f}{mean('polar'):>7.1f}{mean('charged'):>9.1f}"
    )


def main():
    directory, tsv = sys.argv[1], sys.argv[2]
    roots = dict(item.split("=", 1) for item in sys.argv[3:])

    crystals, pocket_map = [], Counter()
    for path in sorted(Path(directory).glob("*.cif")):
        try:
            atoms = load(path)
        except Exception:  # a malformed download should not stop the run
            continue
        for chain, residue in sorted({(a.chain_id, a.res_id) for a in atoms[atoms.res_name == "6NT"]}):
            keep = ~((atoms.res_name == "6NT") & ~((atoms.chain_id == chain) & (atoms.res_id == residue)))
            sub = atoms[keep & (atoms.chain_id == chain)]
            found = measure(sub)
            if not (found and found["base_d"] <= 2.69 and found["donor_d"] <= 3.60):
                continue
            env = environment(sub)
            if env:
                crystals.append(env)
                pocket_map.update(f"{name}{res}" for (_, res), name in env["_touching"].items())

    designs = []
    with open(tsv) as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            root = roots.get(row["sweep"])
            if not root or row["sweep"].startswith("rep"):
                continue
            cif = (
                Path(root)
                / f"boltz/boltz_results_queries/predictions/{row['name']}/{row['name']}_model_0.cif"
            )
            if not cif.exists():
                continue
            env = environment(load(cif))
            if env:
                env.update(
                    D=deviation(row), in_place=float(row["base_d"]) <= 4.5 and float(row["donor_d"]) <= 5.0
                )
                designs.append(env)

    print(
        f"{'':<36}{'n':>4}{'residues':>9}{'aromatic':>9}{'stacked':>10}{'aliph.':>9}{'polar':>7}{'charged':>9}"
    )
    print(
        "per-structure means, residues within 4.5 A of the ligand; 'stacked' = an aromatic ring stacked on it"
    )
    summarise("25 crystal copies", crystals)
    ranked = sorted(designs, key=lambda d: d["D"])
    summarise("designs, ligand roughly in place", [d for d in designs if d["in_place"]])
    summarise("15 best designs by D", ranked[:15])
    summarise("all designs", designs)

    print("\nPOCKET MAP learned from the crystals: residues touching the ligand in most copies")
    for name, count in pocket_map.most_common(14):
        print(f"  {name:<8}{count:>3} of {len(crystals)} copies")

    placed = [d for d in designs if d["in_place"]]
    with_stack = [d["D"] for d in placed if d["stacked"]]
    without = [d["D"] for d in placed if not d["stacked"]]
    print(
        f"\nAmong designs with the ligand roughly in place ({len(placed)}): stacked aromatic present in "
        f"{len(with_stack)}, absent in {len(without)}"
    )
    if with_stack and without:
        mid = lambda v: sorted(v)[len(v) // 2]  # noqa: E731
        print(
            f"  median D with a stacked aromatic {mid(with_stack):.1f}   without {mid(without):.1f}"
            "   (lower is better)"
        )
    anywhere = [d for d in designs if d["stacked"]]
    print(
        f"Across ALL {len(designs)} designs a stacked aromatic exists in {len(anywhere)}"
        + (f"; their median D {sorted(d['D'] for d in anywhere)[len(anywhere) // 2]:.1f}" if anywhere else "")
    )


if __name__ == "__main__":
    main()
