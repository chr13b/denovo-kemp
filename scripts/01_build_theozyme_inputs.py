"""Turn the recommended theozyme candidates into RFD4-Proteina design inputs (a condition spec + input CIFs).

    python scripts/01_build_theozyme_inputs.py
    python scripts/01_build_theozyme_inputs.py --slots=A_top_observed,B_minimal --seg_min=160 --seg_max=240

Reads the TS-like candidate PDBs from pre_analysis/kemp_theozymes_v2/candidates/ (6NT transition-state
analogue plus catalytic residues, all in one frame). Writes to results/theozymes/ (tracked, so Euler gets it
through git): one plain mmCIF per candidate (motif residues merged into chain A, 6NT as chain B) and
`theozymes.yaml`, one design per candidate. The spec is the RFD4-Proteina YAML condition spec: `rfd4-generate`
builds the annotated CIF from it.

Per design the spec says: keep the 6NT and the motif residues from the CIF, add one expandable segment (the
scaffold the model designs, seg_min..seg_max residues), fix the coordinates of the 6NT and of the catalytic
atoms, fix the identity of residues whose side chain is fixed, and unindex every motif residue (the model
decides where in the chain it goes, one index group each). Which atoms are fixed comes from the candidate's
own REMARK line: "side chain + CA" (default, also for the base and the dyad) or "backbone N,CA,C,O"
(N-H donors; their identity stays free). Standard library only; the check re-reads every CIF it wrote.
This only authors inputs: RFD4-Proteina has not validated them yet (see wiki/theozyme-inputs.md).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from kemp import paths
from kemp.config import parse
from kemp.run import start_run

# slots recommended in pre_analysis/kemp_theozymes_v2/README.md: V00001, V00009, V00023, V00128, V00236,
# V00367, V10561, V13877, V00189, V64285, V00552
RECOMMENDED = (
    "A_top_observed,C_with_LG,B_minimal,G2_KE59_plus_LG,B2_minimal_nitro_stack,F_sandwich,"
    "H_Des27_type,I_dyad,J_real_substrate_part,K_N1_mode,L_sampled_base"
)
THREE = "ALA ARG ASN ASP CYS GLN GLU GLY HIS ILE LEU LYS MET PHE PRO SER THR TRP TYR VAL".split()
THREE_TO_ONE = dict(zip(THREE, "ARNDCQEGHILKMFPSTWYV", strict=True))
BACKBONE = ("N", "CA", "C", "O")
# CCD entry 6NT (files.rcsb.org/ligands/view/6NT.cif, read 2026-11-21): zwitterionic nitro, rest neutral
LIGAND_CHARGES = {"NO1": 1, "O21": -1}
CARBOXYLATE_O = {
    "ASP": "OD2",
    "GLU": "OE2",
}  # the oxygen that carries the charge when the carboxylate is deprotonated
PROTEIN_CHAIN, LIGAND_CHAIN = "A", "B"  # in the input CIF


@dataclass
class Config:
    name: str = "theozyme-inputs"  # run directory suffix
    seed: int = 0  # unused (deterministic); start_run records it
    candidates: str = "pre_analysis/kemp_theozymes_v2/candidates"  # relative to the repo root
    out_dir: str = "results/theozymes"  # relative to the repo root; tracked
    slots: str = RECOMMENDED  # comma-separated candidate slots (the part of the file name before "__")
    seg_min: int = 160  # designed scaffold length range; with the motif residues the design must stay <= 260
    seg_max: int = 240
    # charge on one carboxylate O of the base and dyad Asp: -1 = deprotonated; 0 = neutral acid, as in the CCD
    # entries of ASP/GLU (and what RFD4 reads from an unknown charge)
    base_charge: int = -1


Atom = tuple[str, str, float, float, float]  # name, element, x, y, z


@dataclass
class Residue:
    chain: str  # in the candidate PDB: B base, C dyad Asp, D/E stackers, F nitro donor, G leaving-group donor
    name: str
    atoms: list[Atom]
    policy: str = (
        "sidechain"  # "sidechain": side chain + CA, identity fixed; "backbone": N,CA,C,O, identity free
    )

    @property
    def fixed(self) -> list[str]:
        names = [a[0] for a in self.atoms]
        if self.policy == "backbone":
            return [n for n in BACKBONE if n in names]
        return [n for n in names if n not in ("N", "C", "O")]  # CA and everything beyond it


def read_candidate(path: Path) -> tuple[list[Atom], list[Residue], dict[str, str]]:
    """The 6NT atoms, the motif residues (in chain order) and the REMARK text, from one candidate PDB."""
    ligand: list[Atom] = []
    residues: dict[str, Residue] = {}
    remarks: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("REMARK") and ":" in line[7:]:
            key, _, val = line[7:].partition(":")
            remarks[key.strip()] = val.strip()
        elif line.startswith(("ATOM", "HETATM")):
            name, res, chain = line[12:16].strip(), line[17:20].strip(), line[21]
            xyz = (float(line[30:38]), float(line[38:46]), float(line[46:54]))
            atom = (name, line[76:78].strip() or name[0], *xyz)
            if res == "6NT":
                ligand.append(atom)
            else:
                residues.setdefault(chain, Residue(chain, res, [])).atoms.append(atom)
    motif = [residues[c] for c in sorted(residues)]
    for r in motif:
        if r.chain in "DEFG":  # the optional contacts say how much of them is fixed
            r.policy = policy_from_remark(remarks.get("fix atoms for motif scaffolding", ""), r.name, path)
    return ligand, motif, remarks


def policy_from_remark(remark: str, res_name: str, path: Path) -> str:
    for part in remark.split(";"):
        name, _, what = part.partition(":")
        if name.strip() == res_name:
            return "backbone" if what.strip().startswith("backbone") else "sidechain"
    raise SystemExit(f"{path.name}: the REMARK 'fix atoms' line has no entry for {res_name}: {remark!r}")


def formal_charge(res: Residue | None, atom_name: str, base_charge: int) -> int:
    """Formal charge of one atom: from the 6NT CCD entry (res is None), else 0 except the base carboxylate."""
    if res is None:
        return LIGAND_CHARGES.get(atom_name, 0)
    if res.name in ("LYS", "ARG"):  # charged in the CCD; none of the recommended candidates has one
        raise SystemExit(f"{res.name} in the motif: its CCD charge is not handled by this script yet")
    if res.chain in "BC" and CARBOXYLATE_O.get(res.name) == atom_name:  # B base, C dyad Asp
        return base_charge
    return 0


def write_cif(
    path: Path, title: str, ligand: list[Atom], motif: list[Residue], base_charge: int = -1
) -> None:
    """A plain mmCIF: motif residues renumbered 1..n in chain A (polymer), 6NT as chain B residue 1."""
    rows: list[str] = []
    fmt = "{} {} {} {} . {} {} {} {} ? {:.3f} {:.3f} {:.3f} 1.00 0.00 {} {} {} {} {} 1"

    def add(group, atom, res, asym, entity, seq, charge):
        name, el, x, y, z = atom
        sign = "0" if charge == 0 else f"{charge:+d}"  # the benchmark CIFs write "+1", "-1" and "0"
        row = (group, len(rows) + 1, el, name, res, asym, entity, seq, x, y, z, seq, res, asym, name, sign)
        rows.append(fmt.format(*row))

    for i, r in enumerate(motif, start=1):
        for atom in r.atoms:
            add("ATOM", atom, r.name, PROTEIN_CHAIN, 1, i, formal_charge(r, atom[0], base_charge))
    for atom in ligand:
        add("HETATM", atom, "6NT", LIGAND_CHAIN, 2, 1, formal_charge(None, atom[0], base_charge))
    # label_seq_id and auth_seq_id are the same on purpose: the spec's res_id resolves against label_seq_id
    seq = "".join(THREE_TO_ONE[r.name] for r in motif)
    lines = [
        f"data_{title}",
        "#",
        "loop_",
        "_entity.id",
        "_entity.type",
        "1 polymer",
        "2 non-polymer",
        "#",
        "_entity_poly.entity_id 1",
        "_entity_poly.type 'polypeptide(L)'",
        f"_entity_poly.pdbx_seq_one_letter_code_can {seq}",
        f"_entity_poly.pdbx_strand_id {PROTEIN_CHAIN}",
        "#",
        "loop_",
        "_entity_poly_seq.entity_id",
        "_entity_poly_seq.num",
        "_entity_poly_seq.mon_id",
        "_entity_poly_seq.hetero",
        *[f"1 {i} {r.name} n" for i, r in enumerate(motif, start=1)],
        "#",
        "loop_",
        "_struct_asym.id",
        "_struct_asym.entity_id",
        f"{PROTEIN_CHAIN} 1",
        f"{LIGAND_CHAIN} 2",
        "#",
        "loop_",
        *[
            f"_atom_site.{c}"
            for c in (
                "group_PDB id type_symbol label_atom_id label_alt_id label_comp_id label_asym_id "
                "label_entity_id label_seq_id pdbx_PDB_ins_code Cartn_x Cartn_y Cartn_z occupancy "
                "B_iso_or_equiv auth_seq_id auth_comp_id auth_asym_id auth_atom_id pdbx_formal_charge "
                "pdbx_PDB_model_num"
            ).split()
        ],
        *rows,
        "#",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def design_entry(key: str, cif_name: str, motif: list[Residue], remarks: dict[str, str], cfg: Config) -> str:
    n = len(motif)
    contig = f"EX1:{cfg.seg_min}-{cfg.seg_max}, A1{f'-{n}' if n > 1 else ''}, /0, {LIGAND_CHAIN}1"
    kept = [f"{i}" for i, r in enumerate(motif, start=1) if r.policy == "sidechain"]
    fixed = [f"        - select: \"sel('{LIGAND_CHAIN}')\"   # all 6NT atoms"]
    fixed += [
        f"        - select: \"sel('{PROTEIN_CHAIN}/*/{i}/[{','.join(r.fixed)}]')\"   # {r.name} ({r.policy})"
        for i, r in enumerate(motif, start=1)
    ]
    unindexed: list[str] = []
    for i, r in enumerate(motif, start=1):
        unindexed.append(f"        - select: \"sel('{PROTEIN_CHAIN}/*/{i}')\"   # {r.name}")
        unindexed.append(f"          group: res{i}")
    return "\n".join(
        [
            f"# {remarks.get('components', '')}",
            f"# {remarks.get('scores', '')}",
            f"{key}:",
            f"  input: {cif_name}",
            f'  contig: "{contig}"',
            "  conditions:",
            "    C_CRD:",
            "      true:",
            *fixed,
            "    C_SEQ:",
            "      true:",
            f"        - select: \"sel('{PROTEIN_CHAIN}/*/[{','.join(kept)}]')\"",
            f"        - select: \"sel('{LIGAND_CHAIN}')\"   # 6NT: fixed coordinates imply a known identity",
            "    C_IDX:",
            "      false:",
            *unindexed,
        ]
    )


def check(out: Path, key: str, ligand: list[Atom], motif: list[Residue]) -> dict:
    """Re-read the CIF written for `key`, compare it with what we meant to write, raise on any difference."""
    cols: list[str] = []
    rows: list[dict[str, str]] = []
    for line in (out / f"{key}.cif").read_text(encoding="utf-8").splitlines():
        if line.startswith("_atom_site."):
            cols.append(line.split(".", 1)[1])
        elif cols and line.strip() and not line.startswith(("#", "_", "loop_")):
            rows.append(dict(zip(cols, line.split(), strict=True)))
    want = [(r.name, a) for r in motif for a in r.atoms] + [("6NT", a) for a in ligand]
    if len(rows) != len(want):
        raise SystemExit(f"{key}: wrote {len(rows)} atoms, expected {len(want)}")
    for row, (res, (name, _el, x, y, z)) in zip(rows, want, strict=True):
        got = (row["label_comp_id"], row["label_atom_id"], float(row["Cartn_x"]), float(row["Cartn_y"]))
        if got != (res, name, round(x, 3), round(y, 3)) or abs(float(row["Cartn_z"]) - z) > 5e-4:
            raise SystemExit(f"{key}: atom {name} of {res} changed in the CIF: {row}")
    for i, r in enumerate(motif, start=1):
        in_res = [
            row for row in rows if row["label_asym_id"] == PROTEIN_CHAIN and row["label_seq_id"] == str(i)
        ]
        have = {row["label_atom_id"] for row in in_res}
        if missing := set(r.fixed) - have:
            raise SystemExit(f"{key}: residue {i} ({r.name}) lacks fixed atoms {sorted(missing)}")
    return {"n_atoms": len(rows)}


def main(cfg: Config) -> None:
    src, out = paths.ROOT / cfg.candidates, paths.ROOT / cfg.out_dir
    out.mkdir(parents=True, exist_ok=True)
    run = start_run(cfg.name, cfg, seed=cfg.seed)
    entries: list[str] = []
    summary: dict[str, dict] = {}
    for slot in [s.strip() for s in cfg.slots.split(",") if s.strip()]:
        files = [p for p in src.glob(f"{slot}__V*.pdb") if not p.stem.endswith("__michaelis")]
        if len(files) != 1:
            found = [p.name for p in files]
            raise SystemExit(f"slot {slot!r}: expected one TS-like PDB in {src}, found {found}")
        key = files[0].stem
        ligand, motif, remarks = read_candidate(files[0])
        if len(motif) + cfg.seg_max > 260:
            raise SystemExit(f"{key}: {len(motif)} motif residues + seg_max {cfg.seg_max} > the 260 limit")
        write_cif(out / f"{key}.cif", key, ligand, motif, cfg.base_charge)
        entries.append(design_entry(key, f"{key}.cif", motif, remarks, cfg))
        summary[key] = {
            "motif": [f"{r.name}:{r.policy}:{'+'.join(r.fixed)}" for r in motif],
            "length_range": [len(motif) + cfg.seg_min, len(motif) + cfg.seg_max],
            **check(out, key, ligand, motif),
        }
    header = [
        "# Kemp-eliminase design inputs for RFD4-Proteina, generated by scripts/01_build_theozyme_inputs.py.",
        "# One design per candidate; do not edit by hand, re-run the script (see wiki/theozyme-inputs.md).",
        "",
    ]
    (out / "theozymes.yaml").write_text("\n".join(header) + "\n\n".join(entries) + "\n", encoding="utf-8")
    print(f"[theozymes] wrote {len(entries)} designs to {out}")
    run.finish(ok=True, out_dir=str(out), n_designs=len(entries), designs=summary)


if __name__ == "__main__":
    main(parse(Config))
