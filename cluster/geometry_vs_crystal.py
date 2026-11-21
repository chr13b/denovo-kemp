"""Full catalytic geometry of Boltz-2 structures, against the ranges seen in crystal structures.

Runs ON THE CLUSTER inside env-rfd3 (biotite + numpy):

    python geometry_vs_crystal.py <kemp_pdb_dir> <out.tsv> <label>=<sweep_root> [<label>=<sweep_root> ...]

Why this exists. Everything before it judged designs on the two contact DISTANCES. The organizers say
the geometry term is more than that: "each contact is also judged on the angle it approaches the ring
at and on whether it lies in the ring plane ... the angle and the in-plane terms do not average, the
worse of the two decides". Geometry outweighs everything else combined and the terms multiply, so a
design that is perfect on distance and wrong on approach can still score badly.

Quantities, for the base contact (carboxylate O -> 6NT N3) and the donor contact (donor N -> 6NT N1):
  distance          contact length
  approach angle    angle at the ring nitrogen between the contact atom and the ring centroid.
                    ~180 deg = coming straight in along the ring's outward direction; small = skimming.
  out-of-plane      angle between the contact vector and the plane of the benzotriazole.
                    0 deg = in the ring plane; 90 deg = coming in end-on, perpendicular to it.
plus five bond angles and two dihedrals used earlier as stand-ins (A1-A5, D1-D2).

The scorer's exact atom definitions and targets are not published, so the ranges here are the span of
what 25 engaged crystal copies actually show. Treat "inside the crystal range" as the best available
proxy, not as the scorer's rule.

<sweep_root> holds queries.json (name, kind, base_position, donor_position) and
boltz/boltz_results_queries/predictions/<name>/<name>_model_0.cif, as written by oversample.sbatch.
Only records with kind == "design" are measured, at their DECLARED positions - the scorer's choice,
not the nearest atom anywhere in the protein.
"""

import glob
import json
import math
import sys
from pathlib import Path

import numpy as np
from biotite.structure.io import pdbx

RING9 = ["C3A", "C4", "C5", "C6", "C7", "C7A", "N1", "N2", "N3"]
RING5 = ["N1", "N2", "N3", "C3A", "C7A"]
DONOR_NEIGHBOUR = {
    ("GLN", "NE2"): "CD",
    ("ASN", "ND2"): "CG",
    ("SER", "OG"): "CB",
    ("THR", "OG1"): "CB",
    ("TYR", "OH"): "CZ",
    ("LYS", "NZ"): "CE",
    ("ARG", "NH1"): "CZ",
    ("ARG", "NH2"): "CZ",
}
DISTANCES = ["base_d", "donor_d"]
APPROACH = ["base_approach", "base_oop", "donor_approach", "donor_oop"]
STANDINS = ["A1", "A2", "A3", "A4", "A5", "D1", "D2"]
ALL_KEYS = DISTANCES + APPROACH + STANDINS


def load(path):
    with open(path) as handle:
        atoms = pdbx.get_structure(pdbx.CIFFile.read(handle), model=1, use_author_fields=True)
    return atoms[atoms.element != "H"]


def point(residue, name):
    hit = residue[residue.atom_name == name]
    return hit[0].coord if len(hit) else None


def angle(a, b, c):
    v1, v2 = a - b, c - b
    cosine = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
    return math.degrees(math.acos(max(-1.0, min(1.0, cosine))))


def dihedral(p0, p1, p2, p3):
    b0, b1, b2 = p0 - p1, p2 - p1, p3 - p2
    unit = b1 / np.linalg.norm(b1)
    v, w = b0 - np.dot(b0, unit) * unit, b2 - np.dot(b2, unit) * unit
    return math.degrees(math.atan2(np.dot(np.cross(unit, v), w), np.dot(v, w)))


def out_of_plane(contact_atom, ring_atom, normal):
    """Angle between the contact vector and the ring plane: 0 = in plane, 90 = perpendicular."""
    vector = contact_atom - ring_atom
    sine = abs(np.dot(vector / np.linalg.norm(vector), normal))
    return math.degrees(math.asin(max(0.0, min(1.0, sine))))


def measure(atoms, base_resid=None, donor_resid=None):
    ligand = atoms[atoms.res_name == "6NT"]
    if len(ligand) < 12:
        return None
    ring = {name: point(ligand, name) for name in RING9}
    if any(value is None for value in ring.values()):
        return None
    n1, n2, n3, c3a = ring["N1"], ring["N2"], ring["N3"], ring["C3A"]
    centroid = np.mean([ring[name] for name in RING5], axis=0)
    coords = np.array([ring[name] for name in RING9])
    normal = np.linalg.svd(coords - coords.mean(axis=0))[2][-1]

    protein = atoms[~atoms.hetero]
    carboxylates = protein[
        np.isin(protein.res_name, ["ASP", "GLU"]) & np.isin(protein.atom_name, ["OD1", "OD2", "OE1", "OE2"])
    ]
    if base_resid is not None:
        carboxylates = carboxylates[carboxylates.res_id == base_resid]
    donors = protein[
        np.isin(protein.res_name, ["GLN", "ASN", "SER", "THR", "TYR", "LYS", "ARG"])
        & np.isin(protein.atom_name, ["NE2", "ND2", "OG", "OG1", "OH", "NZ", "NH1", "NH2"])
    ]
    if donor_resid is not None:
        donors = donors[donors.res_id == donor_resid]
    if len(carboxylates) == 0 or len(donors) == 0:
        return None
    base_d = np.linalg.norm(carboxylates.coord - n3, axis=-1)
    donor_d = np.linalg.norm(donors.coord - n1, axis=-1)
    oxygen, nitrogen = carboxylates[int(np.argmin(base_d))], donors[int(np.argmin(donor_d))]
    base_res = protein[protein.res_id == oxygen.res_id]
    donor_res = protein[protein.res_id == nitrogen.res_id]
    base_carbon = point(base_res, "CG" if oxygen.atom_name.startswith("OD") else "CD")
    neighbour = DONOR_NEIGHBOUR.get((nitrogen.res_name, nitrogen.atom_name))
    donor_carbon = point(donor_res, neighbour) if neighbour else None
    if base_carbon is None or donor_carbon is None:
        return None
    return {
        "base_d": float(base_d.min()),
        "donor_d": float(donor_d.min()),
        "base_approach": angle(oxygen.coord, n3, centroid),
        "base_oop": out_of_plane(oxygen.coord, n3, normal),
        "donor_approach": angle(nitrogen.coord, n1, centroid),
        "donor_oop": out_of_plane(nitrogen.coord, n1, normal),
        "A1": angle(base_carbon, oxygen.coord, n3),
        "A2": angle(oxygen.coord, n3, n2),
        "A3": angle(oxygen.coord, n3, c3a),
        "A4": angle(donor_carbon, nitrogen.coord, n1),
        "A5": angle(nitrogen.coord, n1, n2),
        "D1": dihedral(base_carbon, oxygen.coord, n3, n2),
        "D2": dihedral(donor_carbon, nitrogen.coord, n1, n2),
    }


def crystal_ranges(directory):
    """Min / median / max of every quantity over the engaged crystal copies."""
    copies = []
    for path in sorted(glob.glob(f"{directory}/*.cif")):
        try:
            atoms = load(path)
        except Exception:  # a malformed download should not stop the run
            continue
        for chain, residue in sorted({(a.chain_id, a.res_id) for a in atoms[atoms.res_name == "6NT"]}):
            keep = ~((atoms.res_name == "6NT") & ~((atoms.chain_id == chain) & (atoms.res_id == residue)))
            found = measure(atoms[keep & (atoms.chain_id == chain)])
            if found and found["base_d"] <= 2.69 and found["donor_d"] <= 3.60:
                copies.append(found)
    ranges = {}
    for key in ALL_KEYS:
        values = sorted(copy[key] for copy in copies)
        ranges[key] = (values[0], values[len(values) // 2], values[-1])
    return copies, ranges


def main():
    directory, out_path = sys.argv[1], Path(sys.argv[2])
    sweeps = [item.split("=", 1) for item in sys.argv[3:]]
    copies, ranges = crystal_ranges(directory)
    print(f"engaged crystal copies: {len(copies)}")
    print(f"{'quantity':<16}{'min':>9}{'median':>9}{'max':>9}")
    for key in ALL_KEYS:
        low, mid, high = ranges[key]
        print(f"{key:<16}{low:>9.1f}{mid:>9.1f}{high:>9.1f}")

    rows = []
    for label, root in sweeps:
        queries = Path(root) / "queries.json"
        if not queries.exists():
            print(f"  skip {label}: no queries.json")
            continue
        for record in json.loads(queries.read_text()):
            if record.get("kind") != "design":
                continue
            name = record["name"]
            cif = Path(root) / f"boltz/boltz_results_queries/predictions/{name}/{name}_model_0.cif"
            if not cif.exists():
                continue
            found = measure(load(cif), record.get("base_position"), record.get("donor_position"))
            if found:
                rows.append((label, name, found))

    columns = ["sweep", "name", *ALL_KEYS, "n_inside", "n_approach_inside"]
    with out_path.open("w") as stream:
        stream.write("\t".join(columns) + "\n")
        for label, name, found in rows:
            inside = sum(1 for key in ALL_KEYS if ranges[key][0] <= found[key] <= ranges[key][2])
            approach = sum(1 for key in APPROACH if ranges[key][0] <= found[key] <= ranges[key][2])
            cells = [label, name, *[f"{found[key]:.3f}" for key in ALL_KEYS], str(inside), str(approach)]
            stream.write("\t".join(cells) + "\n")
    print(f"\nmeasured {len(rows)} structures -> {out_path}")


if __name__ == "__main__":
    main()
