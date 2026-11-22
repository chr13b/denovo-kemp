"""Write the per-residue bias files for the two LigandMPNN experiment arms.

Runs ON THE CLUSTER inside env-rfd3 (biotite + numpy):

    python make_arm_inputs.py <designed_backbone.pdb> <queries.json> <reference_name> <out_dir> [seed]

Format (LigandMPNN `--bias_AA_per_residue`): {"A12": {"G": 1.1}}, a log-odds shift added to the logits of that
residue, chain letter plus residue number as in the input PDB.

bias_aromatic.json
    Aromatic residues (W, F, Y) favoured at every FREE position within 5 A of the ligand on the DESIGNED
    backbone. Why: across 72 designs no sequence has an aromatic residue at any of those positions, yet the
    crystal ring is stacked by Trp44. That region of sequence space was never sampled, so the data cannot say
    whether it helps. A soft bias lets LigandMPNN decide; hard-pinning Trp44 as a third motif anchor was tried
    by a teammate on one backbone and was inconclusive.

bias_polar_down.json
    Polar residues (S, T, N, Q, H) discouraged at the same free positions. Why: the pocket the crystals show
    is hydrophobic-lined (about 2 polar residues touching the ligand) while ours is about twice as polar, and
    within seed 4 more hydrophobic pocket residues went with better geometry (-0.29). Unlike the aromatic arm
    this lever is read off the crystals rather than guessed.

bias_close_<reference>.json
    A strong push toward the reference design's residue at most positions, with a random ~12 % left free.
    Why: sequence identity to the winners did not predict geometry over 56-74 %. Whether it does at 85-97 % (a
    handful of mutations) is untested, and this tests it.

The two pinned positions (base and donor) are held fixed by `--fixed_residues` and are left out of both files.
"""

import json
import random
import sys
from pathlib import Path

import numpy as np
from biotite.structure.io import pdb

POCKET_CUTOFF = 5.0
# Calibrated on the head node with 12 sequences per setting (LigandMPNN, T 0.3, seed 5):
#   aromatic scale 3: 1.4 aromatics per sequence at the 11 pocket positions, 10 of 12 sequences with >= 1;
#   scale 1.5 gave only 0.2 per sequence (far too weak), scale 5 made 7.8 of 11 aromatic (too aggressive).
#   close push 1.5: 89-93 % identity to the reference; 1.0 gave 83-89 %, 2.5 gave 93-97 %, 4.0 gave 96-97 %.
# Polar residues discouraged at the free pocket positions. Learned from the crystals: within 4.5 A of the
# ligand the 25 crystal copies have 2.1 polar residues (about 1 once the pinned Gln50 donor is removed),
# while our designs with the ligand roughly in place have 4.5. Calibration: baseline 4.1 polar at the 11
# positions; push 1.0 gave 2.2, push 2.0 gave 0.9, push 3.0 gave 0.1; 1.5 is used.
POLAR_DOWN = {aa: -1.5 for aa in "STNQH"}
AROMATIC = {"W": 3.0, "F": 2.25, "Y": 2.25}
CLOSE_PUSH = 1.5
FREE_FRACTION = 0.12


def main():
    backbone, queries, reference, out_dir = sys.argv[1:5]
    seed = int(sys.argv[5]) if len(sys.argv) > 5 else 1
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    records = {r["name"]: r for r in json.loads(Path(queries).read_text()) if r.get("kind") == "design"}
    if reference not in records:
        raise SystemExit(f"{reference} not found in {queries}")
    record = records[reference]
    pinned = {record["base_position"], record["donor_position"]}
    sequence = record["sequence"]

    atoms = pdb.get_structure(pdb.PDBFile.read(backbone), model=1)
    atoms = atoms[atoms.element != "H"]
    ligand, protein = atoms[atoms.res_name == "6NT"], atoms[~atoms.hetero]
    order = []
    for residue in protein.res_id:
        if not order or order[-1] != residue:
            order.append(residue)
    if len(order) != len(sequence):
        raise SystemExit(f"backbone has {len(order)} residues but the reference sequence has {len(sequence)}")

    pocket = []
    for position, residue in enumerate(order, 1):
        sub = protein[protein.res_id == residue]
        if np.linalg.norm(sub.coord[:, None] - ligand.coord[None, :], axis=-1).min() <= POCKET_CUTOFF:
            pocket.append(position)
    free_pocket = [p for p in pocket if p not in pinned]

    aromatic = {f"A{order[p - 1]}": dict(AROMATIC) for p in free_pocket}
    (out / "bias_aromatic.json").write_text(json.dumps(aromatic, indent=1))
    polar_down = {f"A{order[p - 1]}": dict(POLAR_DOWN) for p in free_pocket}
    (out / "bias_polar_down.json").write_text(json.dumps(polar_down, indent=1))

    rng = random.Random(seed)
    candidates = [p for p in range(1, len(sequence) + 1) if p not in pinned]
    free = set(rng.sample(candidates, int(len(candidates) * FREE_FRACTION)))
    close = {f"A{order[p - 1]}": {sequence[p - 1]: CLOSE_PUSH} for p in candidates if p not in free}
    (out / f"bias_close_{reference}.json").write_text(json.dumps(close, indent=1))

    print(f"pocket positions on the designed backbone: {pocket}")
    print(f"bias_polar_down.json: {len(polar_down)} free pocket positions, S/T/N/Q/H shifted by {POLAR_DOWN}")
    print(f"bias_aromatic.json: {len(aromatic)} free pocket positions, W/F/Y shifted by {AROMATIC}")
    print(
        f"bias_close_{reference}.json: {len(close)} positions pushed toward {reference} by +{CLOSE_PUSH}, "
        f"{len(free)} left free (seed {seed})"
    )


if __name__ == "__main__":
    main()
