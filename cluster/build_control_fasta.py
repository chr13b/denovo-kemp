"""Build the natural-enzyme control FASTA for the instrument check.

    python build_control_fasta.py <kemp_pdb_dir> <out.fasta> [PDBID ...]

Why this control is necessary. We compare our designs against catalytic distances measured
from crystal structures (results/kemp_family_geometry.tsv) but we *measure* our designs with
Boltz-2. Those are two different instruments, and nothing so far tells us they agree. If
Boltz-2, handed the sequence of the protein in 4BS0, reproduces 4BS0's measured 2.53 A, then
the window is reachable and our designs genuinely miss it. If Boltz-2 reports 3.3 A for the
real enzyme, then seed 4 is already at parity with HG3.17 and the target is miscalibrated.

Taking the sequence from the deposited structure - not from a database entry or a paper -
keeps the comparison exact: it is the sequence of the very molecule whose geometry we measured.

Reads the mmCIF `_entity_poly` loop for the one-letter sequence of each polymer entity, and
falls back to the observed CA residues when that loop is absent.
"""

import sys
from pathlib import Path

THREE_TO_ONE = {
    "ALA": "A",
    "ARG": "R",
    "ASN": "N",
    "ASP": "D",
    "CYS": "C",
    "GLN": "Q",
    "GLU": "E",
    "GLY": "G",
    "HIS": "H",
    "ILE": "I",
    "LEU": "L",
    "LYS": "K",
    "MET": "M",
    "PHE": "F",
    "PRO": "P",
    "SER": "S",
    "THR": "T",
    "TRP": "W",
    "TYR": "Y",
    "VAL": "V",
    "MSE": "M",
    "SEC": "U",
    "PYL": "O",
}


def entity_sequences(path):
    """One-letter sequences from the mmCIF _entity_poly loop, in file order."""
    text = path.read_text(errors="ignore")
    sequences, columns, in_loop, rows = [], [], False, []
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("_entity_poly."):
            columns.append(line.split(".", 1)[1].split()[0])
            in_loop = True
            continue
        if in_loop:
            if line in ("#", "loop_", ""):
                break
            rows.append(line)
    if "pdbx_seq_one_letter_code_can" not in columns:
        return []
    # The canonical sequence is frequently a multi-line semicolon block; flatten everything
    # and pick out the residue letters between the markers.
    blob = "\n".join(rows)
    index = columns.index("pdbx_seq_one_letter_code_can")
    for chunk in blob.split(";"):
        candidate = "".join(chunk.split())
        if len(candidate) > 30 and set(candidate) <= set("ACDEFGHIKLMNPQRSTVWYUOXBZ"):
            sequences.append(candidate)
    if not sequences and index >= 0:
        for row in rows:
            fields = row.split()
            if len(fields) > index:
                candidate = fields[index].strip("'\"")
                if len(candidate) > 30:
                    sequences.append(candidate)
    return sequences


def observed_sequence(path):
    """Fall back to the residues actually present in chain A of the model."""
    columns, seen, order, in_loop = [], set(), [], False
    for raw in path.read_text(errors="ignore").splitlines():
        line = raw.strip()
        if line.startswith("_atom_site."):
            columns.append(line.split(".", 1)[1])
            in_loop = True
            continue
        if in_loop and (line.startswith("ATOM") or line.startswith("HETATM")):
            fields = line.split()
            if len(fields) < len(columns):
                continue
            atom = dict(zip(columns, fields, strict=False))
            if atom.get("label_atom_id") != "CA" or atom.get("group_PDB") != "ATOM":
                continue
            chain = atom.get("auth_asym_id")
            key = (chain, atom.get("auth_seq_id"))
            if chain != "A" or key in seen:
                continue
            seen.add(key)
            order.append(THREE_TO_ONE.get(atom.get("label_comp_id", ""), "X"))
        elif in_loop and line.startswith("#"):
            break
    return "".join(order)


source = Path(sys.argv[1])
out = Path(sys.argv[2])
wanted = sys.argv[3:] or ["4BS0", "3NYD", "7K4U"]

lines, report = [], []
for pdb_id in wanted:
    path = source / f"{pdb_id}.cif"
    if not path.is_file():
        report.append(f"  {pdb_id}: MISSING at {path}")
        continue
    candidates = entity_sequences(path) or [observed_sequence(path)]
    sequence = max(candidates, key=len) if candidates else ""
    if len(sequence) < 30:
        report.append(f"  {pdb_id}: no usable sequence")
        continue
    lines.append(f">{pdb_id}\n{sequence}")
    report.append(f"  {pdb_id}: {len(sequence)} residues")

out.write_text("\n".join(lines) + "\n")
print(f"wrote {out} with {len(lines)} control sequences")
print("\n".join(report))
