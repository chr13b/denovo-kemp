"""Measure catalytic geometry for every Boltz-2 prediction in a batch.

Runs ON THE CLUSTER inside env-rfd3 (biotite + numpy, same stack the organizers' verify_boltz.py uses).

    python measure_boltz_outputs.py <run_root> <reference_backbone.pdb|-> <out.tsv>

<run_root> holds queries.json (from build_boltz_queries.py) and boltz/boltz_results_queries/.

Two independent measurements per structure, because they answer different questions:

  pinned    - the organizers' measurement, reproduced atom for atom from verify_boltz.py:
              the residue at the KNOWN fixed position, its OD2 / NE2, to 6NT N3 / N1.
              This is the number that gets scored. Needs the fixed positions, so designs only.

  scan      - the measurement used on the 23 crystal structures in scripts/32: the closest
              ASP/GLU carboxylate oxygen to 6NT N3 and the closest donor atom to 6NT N1,
              over the whole protein. Numbering-agnostic, so it also works on natural-enzyme
              controls, and it is directly comparable to results/kemp_family_geometry.tsv.

They should agree on a design. Where they disagree, the pocket has rearranged and a
*different* residue is now the nearest base - worth knowing, and invisible to `pinned`.
"""

import json
import sys
from pathlib import Path

import numpy as np
from biotite.structure.io import pdb, pdbx

BASE_ATOMS = {"OD1", "OD2", "OE1", "OE2"}
BASE_RES = {"ASP", "GLU"}
DONOR_ATOMS = {"NE2", "ND2", "OG", "OG1", "OH", "NZ", "NH1", "NH2", "OD1"}
DONOR_RES = {"GLN", "ASN", "SER", "THR", "TYR", "LYS", "ARG"}

# Measured across 26 engaged ligand copies from 23 crystal structures (scripts/32).
BASE_WINDOW = (2.41, 2.69)
DONOR_WINDOW = (2.92, 3.60)

run = Path(sys.argv[1])
reference_path = sys.argv[2]
out_path = Path(sys.argv[3])

records = json.loads((run / "queries.json").read_text())
predictions = run / "boltz/boltz_results_queries/predictions"

reference_ca = None
if reference_path != "-":
    reference = pdb.get_structure(pdb.PDBFile.read(reference_path), model=1)
    reference_ca = reference[(~reference.hetero) & (reference.atom_name == "CA")]


def kabsch_rmsd(mobile, target):
    """CA RMSD after optimal superposition - identical to verify_boltz.py's calculation."""
    mobile_center, target_center = mobile.mean(axis=0), target.mean(axis=0)
    u, _, vt = np.linalg.svd((mobile - mobile_center).T @ (target - target_center))
    rotation = u @ np.diag([1.0, 1.0, np.linalg.det(u @ vt)]) @ vt
    aligned = (mobile - mobile_center) @ rotation + target_center
    return float(np.sqrt(np.mean(np.sum((aligned - target) ** 2, axis=1))))


def closest(atoms, residues, names, point):
    """Shortest distance from any `names` atom of any `residues` residue to `point`."""
    selected = atoms[np.isin(atoms.res_name, list(residues)) & np.isin(atoms.atom_name, list(names))]
    if len(selected) == 0:
        return float("nan"), ""
    distances = np.linalg.norm(selected.coord - point, axis=-1)
    index = int(np.argmin(distances))
    atom = selected[index]
    return float(distances[index]), f"{atom.res_name}{atom.res_id}:{atom.atom_name}"


rows = []
for record in records:
    name = record["name"]
    row = dict(record)
    row["status"] = "missing"
    structure_path = predictions / name / f"{name}_model_0.cif"
    if not structure_path.is_file():
        rows.append(row)
        continue
    with structure_path.open() as stream:
        atoms = pdbx.get_structure(pdbx.CIFFile.read(stream), model=1, use_author_fields=True)
    if not np.isfinite(atoms.coord).all():
        row["status"] = "non_finite_coordinates"
        rows.append(row)
        continue

    ligand = atoms[(atoms.res_name == "6NT") & (atoms.element != "H")]
    protein = atoms[(~atoms.hetero) & (atoms.chain_id == "A")]
    ca = protein[protein.atom_name == "CA"]
    if len(ligand) != 12 or len(ca) == 0:
        row["status"] = f"bad_structure_ligand{len(ligand)}_ca{len(ca)}"
        rows.append(row)
        continue
    n3 = ligand[ligand.atom_name == "N3"].coord[0]
    n1 = ligand[ligand.atom_name == "N1"].coord[0]

    # Numbering-agnostic scan, comparable to the crystal-structure table.
    row["scan_base"], row["scan_base_residue"] = closest(protein, BASE_RES, BASE_ATOMS, n3)
    row["scan_donor"], row["scan_donor_residue"] = closest(protein, DONOR_RES, DONOR_ATOMS, n1)

    # The organizers' pinned measurement, for designs whose fixed positions we know.
    for label, position, protein_atom, ligand_point, expected in (
        ("base", record.get("base_position"), "OD2", n3, "D"),
        ("donor", record.get("donor_position"), "NE2", n1, "Q"),
    ):
        row[f"pinned_{label}"] = float("nan")
        if not isinstance(position, int) or not 1 <= position <= len(ca):
            continue
        # Guard the silent off-by-one CLAUDE.md warns about: verify the residue identity.
        residue = ca[position - 1]
        if record["sequence"][position - 1] != expected:
            row["status"] = (
                f"{label}_position_{position}_is_{record['sequence'][position - 1]}_not_{expected}"
            )
            continue
        selected = atoms[
            (atoms.chain_id == "A")
            & (atoms.res_id == residue.res_id)
            & (atoms.ins_code == residue.ins_code)
            & (atoms.atom_name == protein_atom)
        ]
        if len(selected) == 1:
            row[f"pinned_{label}"] = float(np.linalg.norm(selected.coord[0] - ligand_point))

    protein_heavy = atoms[(~atoms.hetero) & (atoms.element != "H")]
    distances = np.linalg.norm(protein_heavy.coord[:, None] - ligand.coord[None, :], axis=-1)
    row["min_protein_ligand"] = float(distances.min())
    row["clashes_below_2_2"] = int(np.sum(distances < 2.2))

    row["ca_rmsd"] = float("nan")
    if reference_ca is not None and len(reference_ca) == len(ca):
        row["ca_rmsd"] = kabsch_rmsd(ca.coord, reference_ca.coord)

    confidence_path = predictions / name / f"confidence_{name}_model_0.json"
    confidence = json.loads(confidence_path.read_text()) if confidence_path.is_file() else {}
    for key in ("iptm", "complex_plddt", "complex_ipde", "ptm", "confidence_score"):
        row[key] = confidence.get(key, float("nan"))

    base = row["pinned_base"] if np.isfinite(row["pinned_base"]) else row["scan_base"]
    donor = row["pinned_donor"] if np.isfinite(row["pinned_donor"]) else row["scan_donor"]
    row["in_base_window"] = bool(BASE_WINDOW[0] <= base <= BASE_WINDOW[1])
    row["in_donor_window"] = bool(DONOR_WINDOW[0] <= donor <= DONOR_WINDOW[1])
    if row["status"] == "missing":
        row["status"] = "measured"
    rows.append(row)

columns = [
    "name",
    "kind",
    "source",
    "temperature",
    "ligandmpnn_id",
    "length",
    "pinned_base",
    "pinned_donor",
    "scan_base",
    "scan_donor",
    "scan_base_residue",
    "scan_donor_residue",
    "in_base_window",
    "in_donor_window",
    "ca_rmsd",
    "iptm",
    "complex_plddt",
    "complex_ipde",
    "ligand_confidence",
    "overall_confidence",
    "seq_rec",
    "min_protein_ligand",
    "clashes_below_2_2",
    "duplicates",
    "status",
]


def cell(value):
    if isinstance(value, float):
        return "" if value != value else f"{value:.4f}"
    if isinstance(value, bool):
        return "yes" if value else "no"
    return "" if value is None else str(value)


with out_path.open("w") as stream:
    stream.write("\t".join(columns) + "\n")
    for row in rows:
        stream.write("\t".join(cell(row.get(column)) for column in columns) + "\n")

measured = [r for r in rows if r.get("status") == "measured"]
# Count DESIGNS and CONTROLS separately. Reporting one combined number is actively misleading:
# a batch where a natural enzyme landed in the window and no design did reported "1 inside BOTH
# crystal windows", which reads as a design hit. The controls are the instrument, not the result.
designs = [r for r in measured if r.get("kind") == "design"]
controls = [r for r in measured if r.get("kind") == "control"]


def in_both(items):
    return [r for r in items if r.get("in_base_window") and r.get("in_donor_window")]


print(f"measured {len(measured)} of {len(rows)} structures")
print(f"  DESIGNS:  {len(in_both(designs))} of {len(designs)} inside BOTH crystal windows")
if controls:
    names = ", ".join(sorted(str(r["name"]).replace("c_", "") for r in in_both(controls)))
    print(
        f"  controls: {len(in_both(controls))} of {len(controls)} inside both"
        f"{' (' + names + ')' if names else ''} — instrument check, not a result"
    )
print(f"wrote {out_path}")
if measured:
    header = f"{'name':<10}{'src':<10}{'base':>8}{'donor':>8}{'CA RMSD':>9}{'iptm':>7}  window"
    print(header)
    print("-" * len(header))
    for row in sorted(
        measured,
        key=lambda r: (
            r.get("pinned_base")
            if np.isfinite(r.get("pinned_base", float("nan")))
            else r.get("scan_base", 99)
        ),
    ):
        b = row["pinned_base"] if np.isfinite(row["pinned_base"]) else row["scan_base"]
        d = row["pinned_donor"] if np.isfinite(row["pinned_donor"]) else row["scan_donor"]
        mark = (
            "BOTH"
            if row["in_base_window"] and row["in_donor_window"]
            else ("base" if row["in_base_window"] else ("donor" if row["in_donor_window"] else ""))
        )
        print(
            f"{row['name']:<10}{str(row['source'])[:9]:<10}{b:>8.2f}{d:>8.2f}"
            f"{row['ca_rmsd']:>9.2f}{row['iptm']:>7.3f}  {mark}"
        )
