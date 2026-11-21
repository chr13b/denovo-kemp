"""Why do some sequences on one backbone place the ligand better than others? Two read-only checks.

Runs ON THE CLUSTER inside env-rfd3 (biotite + numpy):

    python pocket_and_smoothness.py <geometry_full.tsv> <designed_backbone.pdb> <queries.json> <sweep_label>

1. POCKET. Which residues sit within 5 A of the ligand is decided on the DESIGNED backbone (RFD3's
   own coordinates), not on the refolded structure. Defining it on the refold would be circular: a
   ligand that ends up in the wrong place touches different residues, so "more Gly/Pro near the ligand
   goes with worse geometry" can appear for that reason alone. (It did: +0.68 on the refold-defined pocket,
   +0.07 on the designed one.)
2. SMOOTHNESS. If designs similar to a good design were also good, resampling around the winners would beat
   blind sampling. Correlate each design's geometry with its sequence identity to the best ones.

Geometry is the continuous deviation D computed from cluster/geometry_vs_crystal.py's table: the overshoot
beyond the crystal range in tolerance units, with too-short distances counted double. D is our own proxy and
not the scorer's function.
"""

import csv
import json
import math
import sys
from collections import Counter

import numpy as np
from biotite.structure.io import pdb

# (low, high, tolerance, weight when below low)
RANGES = {
    "base_d": (2.41, 2.69, 0.25, 2.0),
    "donor_d": (2.92, 3.24, 0.25, 2.0),
    "base_approach": (167.1, 175.8, 15, 1.0),
    "base_oop": (1.0, 11.7, 15, 1.0),
    "donor_approach": (162.1, 173.0, 15, 1.0),
    "donor_oop": (0.6, 16.1, 15, 1.0),
}
CLASSES = {
    "G or P": "GP",
    "aromatic FWY": "FWY",
    "hydrophobic AVILMC": "AVILMC",
    "polar STNQH": "STNQH",
    "charged DEKR": "DEKR",
}
CUTOFF = 5.0


def deviation(row):
    total = 0.0
    for key, (low, high, tolerance, weight) in RANGES.items():
        value = float(row[key])
        if value < low:
            total += weight * (low - value) / tolerance
        elif value > high:
            total += (value - high) / tolerance
    return total


def ranks(values):
    order = sorted(range(len(values)), key=lambda i: values[i])
    out = [0.0] * len(values)
    for rank, index in enumerate(order, 1):
        out[index] = rank
    return out


def spearman(x, y):
    a, b = ranks(x), ranks(y)
    n = len(a)
    ma, mb = sum(a) / n, sum(b) / n
    cov = sum((p - ma) * (q - mb) for p, q in zip(a, b, strict=True))
    return cov / math.sqrt(sum((p - ma) ** 2 for p in a) * sum((q - mb) ** 2 for q in b))


def identity(a, b):
    return sum(x == y for x, y in zip(a, b, strict=True)) / len(a)


def main():
    tsv, backbone, queries, label = sys.argv[1:5]
    dev = {}
    with open(tsv) as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            if row["sweep"] == label:
                dev[row["name"]] = deviation(row)
    records = {
        q["name"]: q for q in json.load(open(queries)) if q.get("kind") == "design" and q["name"] in dev
    }
    pinned = {next(iter(records.values()))["base_position"], next(iter(records.values()))["donor_position"]}

    atoms = pdb.get_structure(pdb.PDBFile.read(backbone), model=1)
    atoms = atoms[atoms.element != "H"]
    ligand, protein = atoms[atoms.res_name == "6NT"], atoms[~atoms.hetero]
    order = []
    for residue in protein.res_id:
        if not order or order[-1] != residue:
            order.append(residue)
    near = []
    for position, residue in enumerate(order, 1):
        sub = protein[protein.res_id == residue]
        if np.linalg.norm(sub.coord[:, None] - ligand.coord[None, :], axis=-1).min() <= CUTOFF:
            near.append(position)
    free = [p for p in near if p not in pinned]
    print(f"designed backbone: {len(order)} residues, {len(near)} within {CUTOFF} A of the ligand: {near}")
    print(f"{len(free)} are free for LigandMPNN to choose ({sorted(pinned)} are pinned)\n")

    names = sorted(records)
    scores = [dev[n] for n in names]
    print(f"{len(names)} designs: Spearman of D with the residue classes at the free pocket positions")
    print("(positive = more of this class at the pocket goes with WORSE geometry)")
    for cls, letters in CLASSES.items():
        counts = [sum(1 for p in free if records[n]["sequence"][p - 1] in letters) for n in names]
        print(f"  {cls:<22}{spearman(counts, scores):>+7.2f}   mean count {sum(counts) / len(counts):.1f}")
    print("\nLigandMPNN's own scores vs D (does the designer know?):")
    for field in ("overall_confidence", "ligand_confidence", "seq_rec", "temperature"):
        print(f"  {field:<22}{spearman([records[n][field] for n in names], scores):>+7.2f}")

    best = sorted(names, key=lambda n: dev[n])
    print("\nfree pocket positions where the 12 best designs agree on one residue (>= 9 of 12):")
    for p in free:
        top = Counter(records[n]["sequence"][p - 1] for n in best[:12]).most_common(1)[0]
        bottom = Counter(records[n]["sequence"][p - 1] for n in best[-12:]).most_common(1)[0]
        if top[1] >= 9:
            print(
                f"  pos {p:>3}: best -> {top[0]} ({top[1]}/12)   "
                f"worst-12 modal -> {bottom[0]} ({bottom[1]}/12)"
            )

    print(
        f"\nSMOOTHNESS. median D {sorted(scores)[len(scores) // 2]:.1f}; the 5 best: "
        + ", ".join(f"{n} {dev[n]:.1f}" for n in best[:5])
    )
    for reference in best[:3]:
        others = [n for n in names if n != reference]
        ids = [identity(records[reference]["sequence"], records[n]["sequence"]) for n in others]
        rho = spearman(ids, [dev[n] for n in others])
        print(
            f"  identity to {reference} (D {dev[reference]:.1f}): {min(ids):.2f}-{max(ids):.2f}, "
            f"Spearman(identity, D) = {rho:+.2f}   (negative = similar is better)"
        )


if __name__ == "__main__":
    main()
