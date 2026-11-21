"""Build RFD3 motif files from the Kemp eliminase family's own crystal structures.

Runs ON THE CLUSTER inside env-rfd3 (biotite + numpy).

    python build_family_motifs.py <kemp_pdb_dir> <out_dir> [n_representatives]

Idea C. We have been designing against ONE arrangement of base + donor + ligand, lifted from
4BS0. The family search (scripts/32) found 26 engaged ligand copies across 23 independent
crystal structures, and 25 of them use the same residue types at the same numbers --
ASP127 + GLN50 -- so their coordinates drop straight into the organizers' launcher with no
change to `unindex` or `select_fixed_atoms`. Only the 3D arrangement differs, which is exactly
the variable we have never varied.

Representative selection. The quantity RFD3 actually has to satisfy is the set of mutual
distances between the pinned atoms: `prepare_ligandmpnn.py` scores a design by
`max |reference_distance - design_distance|` over those atoms. So we cluster the copies with
that same metric and pick farthest-point representatives, giving the most distinct design
problems the family offers rather than 25 near-duplicates of 4BS0.

Writes, per representative:
    <out_dir>/<pdbid>_<chain>/HG3_17_kemp_motif.pdb   base + donor + 6NT, renumbered to A127/A50
    <out_dir>/<pdbid>_<chain>/Kemp.json               the launcher spec, byte-identical to ours
    <out_dir>/selection.tsv                           every copy, its distances, and why it was picked
"""

import json
import sys
from pathlib import Path

import numpy as np
from biotite.structure import array as struct_array
from biotite.structure.io import pdb, pdbx

# The atoms the launcher pins, in a fixed order so the distance matrices are comparable.
BASE_FIXED = ["OD1", "CG", "OD2"]
DONOR_FIXED = ["OE1", "CD", "NE2"]
LIGAND_ATOMS = ["O21", "NO1", "O11", "C5", "C6", "C7", "C7A", "N1", "C3A", "C4", "N3", "N2"]
# Full residues, because RFD3 and the LigandMPNN bridge need the backbone too.
BASE_ALL = ["N", "CA", "C", "O", "CB", "CG", "OD1", "OD2"]
DONOR_ALL = ["N", "CA", "C", "O", "CB", "CG", "CD", "OE1", "NE2"]

source = Path(sys.argv[1])
out_root = Path(sys.argv[2])
n_wanted = int(sys.argv[3]) if len(sys.argv) > 3 else 4
out_root.mkdir(parents=True, exist_ok=True)

LAUNCHER_SPEC = {
    "Kemp_HG3_17_base_donor": {
        "input": "HG3_17_kemp_motif.pdb",
        "ligand": "6NT",
        "contig": "260-260",
        "unindex": "A50,A127",
        "select_fixed_atoms": {"A127": "OD1,CG,OD2", "A50": "OE1,CD,NE2", "6NT": "ALL"},
    }
}


def load(path):
    with path.open() as stream:
        atoms = pdbx.get_structure(pdbx.CIFFile.read(stream), model=1, use_author_fields=True)
    return atoms[atoms.element != "H"]


def residue_atoms(atoms, chain, res_id, names):
    """One atom per requested name, in order, or None if any is missing."""
    selected = atoms[(atoms.chain_id == chain) & (atoms.res_id == res_id)]
    picked = []
    for name in names:
        hit = selected[selected.atom_name == name]
        if len(hit) != 1:
            return None
        picked.append(hit[0])
    return picked


candidates = []
for path in sorted(source.glob("*.cif")):
    pdb_id = path.stem
    try:
        atoms = load(path)
    except Exception as error:  # a malformed download should not stop the sweep
        print(f"  {pdb_id}: unreadable ({type(error).__name__})")
        continue
    ligands = atoms[atoms.res_name == "6NT"]
    if len(ligands) == 0:
        continue
    for chain, res_id in sorted({(a.chain_id, a.res_id) for a in ligands}):
        copy = residue_atoms(ligands, chain, res_id, LIGAND_ATOMS)
        if copy is None:
            continue
        n3 = next(a.coord for a in copy if a.atom_name == "N3")
        n1 = next(a.coord for a in copy if a.atom_name == "N1")
        protein = atoms[(atoms.chain_id == chain) & (atoms.res_name == "ASP")]
        donors = atoms[(atoms.chain_id == chain) & (atoms.res_name == "GLN")]
        if len(protein) == 0 or len(donors) == 0:
            continue
        od2 = protein[protein.atom_name == "OD2"]
        ne2 = donors[donors.atom_name == "NE2"]
        if len(od2) == 0 or len(ne2) == 0:
            continue
        base_distances = np.linalg.norm(od2.coord - n3, axis=-1)
        donor_distances = np.linalg.norm(ne2.coord - n1, axis=-1)
        base_id = int(od2[int(np.argmin(base_distances))].res_id)
        donor_id = int(ne2[int(np.argmin(donor_distances))].res_id)
        base_distance = float(base_distances.min())
        donor_distance = float(donor_distances.min())
        # Engaged only: both contacts within the window measured across the family.
        if not (base_distance <= 2.69 and donor_distance <= 3.60):
            continue
        base_full = residue_atoms(atoms, chain, base_id, BASE_ALL)
        donor_full = residue_atoms(atoms, chain, donor_id, DONOR_ALL)
        if base_full is None or donor_full is None:
            continue
        pinned = (
            [a.coord for a in base_full if a.atom_name in BASE_FIXED]
            + [a.coord for a in donor_full if a.atom_name in DONOR_FIXED]
            + [a.coord for a in copy]
        )
        pinned = np.asarray(pinned)
        candidates.append(
            {
                "pdb": pdb_id,
                "chain": chain,
                "ligand_res": res_id,
                "base_id": base_id,
                "donor_id": donor_id,
                "base": base_distance,
                "donor": donor_distance,
                "matrix": np.linalg.norm(pinned[:, None] - pinned[None, :], axis=-1),
                "base_full": base_full,
                "donor_full": donor_full,
                "ligand": copy,
            }
        )

print(f"engaged ASP/GLN copies found: {len(candidates)}")
if not candidates:
    sys.exit("no usable motif copies")


# Farthest-point selection under the launcher's own geometry metric. 4BS0 chain A seeds the
# set because it is the arrangement every design so far has used - so the others are chosen
# for how much NEW design problem they add.
def spread(a, b):
    return float(np.max(np.abs(a["matrix"] - b["matrix"])))


start = next((i for i, c in enumerate(candidates) if c["pdb"] == "4BS0" and c["chain"] == "A"), 0)
chosen = [start]
while len(chosen) < min(n_wanted, len(candidates)):
    best, best_distance = None, -1.0
    for index, candidate in enumerate(candidates):
        if index in chosen:
            continue
        nearest = min(spread(candidate, candidates[j]) for j in chosen)
        if nearest > best_distance:
            best, best_distance = index, nearest
    if best is None:
        break
    chosen.append(best)
    picked = candidates[best]
    print(f"  picked {picked['pdb']}_{picked['chain']}: {best_distance:.2f} A from the chosen set")

rows = []
for index, candidate in enumerate(candidates):
    nearest = min((spread(candidate, candidates[j]) for j in chosen if j != index), default=float("nan"))
    rows.append((candidate, index in chosen, nearest))

with (out_root / "selection.tsv").open("w") as stream:
    stream.write("pdb\tchain\tbase_res\tdonor_res\tbase_dist\tdonor_dist\tselected\tgeometry_spread_to_set\n")
    for candidate, selected, nearest in rows:
        stream.write(
            f"{candidate['pdb']}\t{candidate['chain']}\tASP{candidate['base_id']}\tGLN{candidate['donor_id']}\t"
            f"{candidate['base']:.3f}\t{candidate['donor']:.3f}\t"
            f"{'yes' if selected else 'no'}\t{nearest:.3f}\n"
        )

for index in chosen:
    candidate = candidates[index]
    tag = f"{candidate['pdb']}_{candidate['chain']}"
    directory = out_root / tag
    directory.mkdir(parents=True, exist_ok=True)
    # Renumber onto the launcher's expected identifiers so the spec needs no edits at all.
    pieces = []
    for atoms_list, res_name, res_id in (
        (candidate["donor_full"], "GLN", 50),
        (candidate["base_full"], "ASP", 127),
        (candidate["ligand"], "6NT", 1305),
    ):
        for atom in atoms_list:
            copy = atom.copy()
            copy.chain_id = "A"
            copy.res_id = res_id
            copy.res_name = res_name
            copy.ins_code = ""
            copy.hetero = res_name == "6NT"
            pieces.append(copy)
    structure = struct_array(pieces)
    structure.box = None
    pdb_file = pdb.PDBFile()
    pdb_file.set_structure(structure)
    pdb_file.write(directory / "HG3_17_kemp_motif.pdb")
    (directory / "Kemp.json").write_text(json.dumps(LAUNCHER_SPEC, indent=2) + "\n")
    # Round-trip check: a motif RFD3 cannot read is worse than no motif at all.
    back = pdb.get_structure(pdb.PDBFile.read(directory / "HG3_17_kemp_motif.pdb"), model=1)
    ligand_count = int(np.sum(back.res_name == "6NT"))
    ok = ligand_count == 12 and len(back) == len(structure)
    print(
        f"  wrote {directory.name}: {len(structure)} atoms, {ligand_count} ligand atoms, "
        f"base {candidate['base']:.2f} donor {candidate['donor']:.2f} {'OK' if ok else 'ROUND-TRIP FAILED'}"
    )

print(f"\n{len(chosen)} motifs in {out_root}; full table in {out_root / 'selection.tsv'}")
