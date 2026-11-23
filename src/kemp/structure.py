"""Structure-based filters (numpy + biotite) for the design funnel.

Separate from `kemp.filters` so the sequence/score filters stay dependency-free.
Everything here returns a `FilterResult` from `kemp.filters`, with `passed=None`
when a measurement could not be made.

Reads .pdb, .cif and .cif.gz, so it works on RFdiffusion output (`*.cif.gz`),
Boltz-2 output (`*_model_0.cif`) and ordinary PDB files without the caller caring.
"""

from __future__ import annotations

import gzip
from pathlib import Path

import numpy as np
from biotite.structure import AtomArray, annotate_sse, superimpose
from biotite.structure.io import pdb as pdbio
from biotite.structure.io import pdbx

from kemp.filters import FilterResult, _ok, split_residue_id, unevaluated

BACKBONE = ("N", "CA", "C", "O")


# ------------------------------------------------------------------------- loading


def load_structure(path: str | Path, model: int = 1) -> AtomArray:
    """Load .pdb / .cif / .cif.gz into a biotite AtomArray (first model)."""
    path = Path(path)
    name = path.name.lower()
    if name.endswith(".cif.gz"):
        with gzip.open(path, "rt") as fh:
            return pdbx.get_structure(pdbx.CIFFile.read(fh), model=model, use_author_fields=True)
    if name.endswith((".cif", ".mmcif", ".bcif")):
        return pdbx.get_structure(pdbx.CIFFile.read(str(path)), model=model, use_author_fields=True)
    if name.endswith((".pdb", ".ent")):
        return pdbio.get_structure(pdbio.PDBFile.read(str(path)), model=model)
    raise ValueError(f"unsupported structure format: {path.name}")


def protein_heavy(atoms: AtomArray) -> AtomArray:
    return atoms[(~atoms.hetero) & (atoms.element != "H")]


def ligand_heavy(atoms: AtomArray, resname: str | None = None) -> AtomArray:
    sel = atoms.hetero & (atoms.element != "H")
    if resname is not None:
        sel = sel & (atoms.res_name == resname)
    return atoms[sel]


def select_atoms(atoms: AtomArray, chain: str, resid: int, names: tuple[str, ...] | None = None):
    sel = (atoms.chain_id == chain) & (atoms.res_id == resid)
    if names is not None:
        sel = sel & np.isin(atoms.atom_name, list(names))
    return atoms[sel]


# ---------------------------------------------------------------- geometry filters


def radius_of_gyration(atoms: AtomArray) -> float:
    """Mass-agnostic RoG over CA atoms (the usual compactness proxy)."""
    ca = atoms[(~atoms.hetero) & (atoms.atom_name == "CA")]
    if len(ca) == 0:
        raise ValueError("no CA atoms")
    centre = ca.coord.mean(axis=0)
    return float(np.sqrt(((ca.coord - centre) ** 2).sum(axis=1).mean()))


def expected_rog(n_residues: int) -> float:
    """Flory-style expectation for a compact globular protein: ~2.2 * N^0.38 A.

    Used only to scale the RoG threshold with length, so one cutoff works for a
    150-mer and a 300-mer. It is an empirical rule of thumb, not a hard law.
    """
    return 2.2 * (n_residues**0.38)


def check_radius_of_gyration(atoms: AtomArray, tolerance: float = 1.25) -> FilterResult:
    """Compact/globular check: RoG must be within `tolerance` x the expected value."""
    try:
        rog = radius_of_gyration(atoms)
    except ValueError as exc:
        return unevaluated("radius_of_gyration", str(exc))
    n = int((~atoms.hetero & (atoms.atom_name == "CA")).sum())
    limit = expected_rog(n) * tolerance
    passed = rog <= limit
    return _ok(
        "radius_of_gyration",
        round(rog, 2),
        round(limit, 2),
        passed,
        "" if passed else f"RoG {rog:.1f} A > {limit:.1f} A for {n} residues (extended)",
        n_residues=n,
        expected=round(expected_rog(n), 2),
    )


def count_clashes(atoms: AtomArray, cutoff: float = 2.2, skip_neighbours: int = 2) -> int:
    """Heavy-atom pairs closer than `cutoff`, ignoring atoms within the same or
    adjacent residues (whose short distances are bonds, not clashes)."""
    heavy = atoms[atoms.element != "H"]
    coord = heavy.coord
    if len(coord) < 2:
        return 0
    d = np.linalg.norm(coord[:, None] - coord[None, :], axis=-1)
    close = d < cutoff
    np.fill_diagonal(close, False)
    # same chain AND near-in-sequence -> bonded, not a clash
    same_chain = heavy.chain_id[:, None] == heavy.chain_id[None, :]
    seq_gap = np.abs(heavy.res_id[:, None].astype(int) - heavy.res_id[None, :].astype(int))
    bonded = same_chain & (seq_gap <= skip_neighbours)
    return int(np.triu(close & ~bonded, k=1).sum())


def check_clashes(atoms: AtomArray, max_clashes: int = 0, cutoff: float = 2.2) -> FilterResult:
    n = count_clashes(atoms, cutoff=cutoff)
    passed = n <= max_clashes
    return _ok(
        "steric_clashes",
        n,
        max_clashes,
        passed,
        "" if passed else f"{n} heavy-atom pairs < {cutoff} A",
        cutoff=cutoff,
    )


# Coarse favoured (phi, psi) boxes in degrees. NOT MolProbity contours - a design
# flagged here is worth a look, not automatically wrong.
_RAMA_BOXES = (
    (-180.0, -20.0, -120.0, 50.0),  # alpha-R / bridge
    (-180.0, -20.0, 60.0, 180.0),  # beta / PPII
    (-180.0, -20.0, -180.0, -150.0),  # beta wrapped
    (20.0, 100.0, -10.0, 100.0),  # alpha-L
)


def ramachandran_outlier_fraction(atoms: AtomArray) -> tuple[float, int, int]:
    """-> (fraction, n_outliers, n_scored). Glycine is exempt (it is genuinely free)."""
    from biotite.structure import dihedral_backbone

    prot = atoms[~atoms.hetero]
    phi, psi, _ = dihedral_backbone(prot)
    phi = np.degrees(phi)
    psi = np.degrees(psi)
    res_names = prot[prot.atom_name == "CA"].res_name
    n_out = n_scored = 0
    for i, (a, b) in enumerate(zip(phi, psi, strict=False)):
        if np.isnan(a) or np.isnan(b):
            continue  # chain termini
        if i < len(res_names) and res_names[i] == "GLY":
            continue
        n_scored += 1
        if not any(lo <= a <= hi and plo <= b <= phi_hi for lo, hi, plo, phi_hi in _RAMA_BOXES):
            n_out += 1
    return (n_out / n_scored if n_scored else 0.0), n_out, n_scored


def check_ramachandran(atoms: AtomArray, max_fraction: float = 0.05) -> FilterResult:
    try:
        frac, n_out, n_scored = ramachandran_outlier_fraction(atoms)
    except Exception as exc:  # noqa: BLE001 - biotite raises several types here
        return unevaluated("ramachandran", f"could not compute backbone dihedrals: {exc}")
    if n_scored == 0:
        return unevaluated("ramachandran", "no scorable residues")
    passed = frac <= max_fraction
    return _ok(
        "ramachandran",
        round(frac, 4),
        max_fraction,
        passed,
        "" if passed else f"{n_out}/{n_scored} residues outside coarse favoured regions",
        n_outliers=n_out,
        n_scored=n_scored,
        method="coarse boxes, not MolProbity",
    )


def secondary_structure(atoms: AtomArray) -> dict:
    """Helix/sheet/coil fractions via biotite `annotate_sse` (P-SEA).

    NOT DSSP - no DSSP binary is installed on this cluster. P-SEA infers SSE from
    CA geometry and agrees with DSSP on most regular elements.
    """
    prot = atoms[~atoms.hetero]
    chains = np.unique(prot.chain_id)
    counts = {"a": 0, "b": 0, "c": 0}
    for ch in chains:
        sse = annotate_sse(prot[prot.chain_id == ch])
        for code in ("a", "b", "c"):
            counts[code] += int((sse == code).sum())
    total = sum(counts.values())
    if total == 0:
        raise ValueError("annotate_sse returned nothing")
    return {
        "helix": counts["a"] / total,
        "sheet": counts["b"] / total,
        "coil": counts["c"] / total,
        "n_residues": total,
        "method": "biotite annotate_sse (P-SEA), not DSSP",
    }


def check_topology(
    atoms: AtomArray, min_helix: float = 0.0, min_sheet: float = 0.0, max_coil: float = 0.6
) -> FilterResult:
    """Fold check: enough regular secondary structure, not loop spaghetti."""
    try:
        sse = secondary_structure(atoms)
    except Exception as exc:  # noqa: BLE001
        return unevaluated("topology", f"secondary structure unavailable: {exc}")
    reasons = []
    if sse["helix"] < min_helix:
        reasons.append(f"helix {sse['helix']:.2f} < {min_helix}")
    if sse["sheet"] < min_sheet:
        reasons.append(f"sheet {sse['sheet']:.2f} < {min_sheet}")
    if sse["coil"] > max_coil:
        reasons.append(f"coil {sse['coil']:.2f} > {max_coil}")
    return _ok(
        "topology",
        {k: round(v, 3) for k, v in sse.items() if isinstance(v, float)},
        {"min_helix": min_helix, "min_sheet": min_sheet, "max_coil": max_coil},
        not reasons,
        "; ".join(reasons),
        method=sse["method"],
    )


# ----------------------------------------------------------------------- RMSD


def paired_rmsd(mobile: AtomArray, fixed: AtomArray, superimposed: bool = True) -> float:
    """RMSD between two equal-length, index-matched atom selections."""
    if len(mobile) != len(fixed):
        raise ValueError(f"atom count mismatch: {len(mobile)} vs {len(fixed)}")
    if len(mobile) == 0:
        raise ValueError("no atoms to compare")
    if superimposed:
        mobile, _ = superimpose(fixed, mobile)
    diff = mobile.coord - fixed.coord
    return float(np.sqrt((diff**2).sum(axis=1).mean()))


def motif_atom_selection(atoms: AtomArray, spec: dict[str, tuple[str, ...]]) -> AtomArray:
    """Gather motif atoms in a DETERMINISTIC order so two structures pair up.

    `spec` maps a residue id ("A127") to the atom names to take ("OD1","CG","OD2").
    Order follows the spec, never file order, because index-matched RMSD is
    meaningless if the two selections are ordered differently.
    """
    picked = []
    for res_token in sorted(spec):
        chain, resid = split_residue_id(res_token)
        for name in spec[res_token]:
            sel = select_atoms(atoms, chain, resid, (name,))
            if len(sel) != 1:
                raise ValueError(f"expected exactly one {res_token}:{name}, found {len(sel)}")
            picked.append(sel)
    if not picked:
        raise ValueError("empty motif spec")
    out = picked[0]
    for part in picked[1:]:
        out += part
    return out


def check_motif_rmsd(
    design: AtomArray,
    reference: AtomArray,
    spec: dict[str, tuple[str, ...]],
    max_rmsd: float = 1.0,
    design_spec: dict[str, tuple[str, ...]] | None = None,
) -> FilterResult:
    """Motif-RMSD against the ideal transition-state motif.

    `design_spec` lets the design use different residue numbering (RFdiffusion
    renumbers; use its `diffused_index_map`) while keeping the same atom order.
    """
    try:
        ref_sel = motif_atom_selection(reference, spec)
        des_sel = motif_atom_selection(design, design_spec or spec)
        rmsd = paired_rmsd(des_sel, ref_sel)
    except ValueError as exc:
        return unevaluated("motif_rmsd", str(exc), max_rmsd)
    passed = rmsd <= max_rmsd
    return _ok(
        "motif_rmsd",
        round(rmsd, 4),
        max_rmsd,
        passed,
        "" if passed else f"motif RMSD {rmsd:.2f} A > {max_rmsd} A",
        n_atoms=len(ref_sel),
    )


def check_backbone_rmsd(design: AtomArray, reference: AtomArray, max_rmsd: float = 2.0) -> FilterResult:
    """CA RMSD of the whole backbone, e.g. Boltz-2 model vs the RFdiffusion design."""
    a = design[(~design.hetero) & (design.atom_name == "CA")]
    b = reference[(~reference.hetero) & (reference.atom_name == "CA")]
    try:
        rmsd = paired_rmsd(a, b)
    except ValueError as exc:
        return unevaluated("backbone_rmsd", str(exc), max_rmsd)
    passed = rmsd <= max_rmsd
    return _ok(
        "backbone_rmsd",
        round(rmsd, 4),
        max_rmsd,
        passed,
        "" if passed else f"CA RMSD {rmsd:.2f} A > {max_rmsd} A",
        n_ca=len(a),
    )


# ------------------------------------------------------------ packing and contacts


def packing_density(atoms: AtomArray, radius: float = 8.0, burial_cutoff: int = 16) -> dict:
    """Neighbour-count proxy for core packing. NOT Rosetta PackStat.

    For each residue's CB (CA for glycine), count heavy atoms within `radius`.
    Buried residues (count >= `burial_cutoff`) should be densely packed; a buried
    residue with an unusually low count sits next to a cavity. Rosetta is not
    available on this cluster, so this is a defensible proxy, not the real metric.
    """
    prot = protein_heavy(atoms)
    if len(prot) == 0:
        raise ValueError("no protein heavy atoms")
    is_cb = prot.atom_name == "CB"
    is_gly_ca = (prot.res_name == "GLY") & (prot.atom_name == "CA")
    centres = prot[is_cb | is_gly_ca]
    if len(centres) == 0:
        raise ValueError("no CB/CA centres")
    d = np.linalg.norm(centres.coord[:, None] - prot.coord[None, :], axis=-1)
    counts = (d <= radius).sum(axis=1) - 1  # drop self
    buried = counts >= burial_cutoff
    n_buried = int(buried.sum())
    return {
        "n_centres": len(centres),
        "n_buried": n_buried,
        "mean_neighbours": float(counts.mean()),
        "mean_buried_neighbours": float(counts[buried].mean()) if n_buried else 0.0,
        "buried_fraction": n_buried / len(centres),
        "method": "neighbour-count proxy, NOT Rosetta PackStat",
    }


def check_packing(
    atoms: AtomArray, min_buried_fraction: float = 0.25, min_mean_buried_neighbours: float = 20.0
) -> FilterResult:
    """Reject designs with a hollow or under-packed core (proxy metric)."""
    try:
        p = packing_density(atoms)
    except ValueError as exc:
        return unevaluated("packing", str(exc))
    reasons = []
    if p["buried_fraction"] < min_buried_fraction:
        reasons.append(f"buried fraction {p['buried_fraction']:.2f} < {min_buried_fraction}")
    if p["mean_buried_neighbours"] < min_mean_buried_neighbours:
        reasons.append(
            f"mean buried neighbours {p['mean_buried_neighbours']:.1f} < {min_mean_buried_neighbours}"
        )
    return _ok(
        "packing",
        {k: round(v, 3) for k, v in p.items() if isinstance(v, float)},
        {"buried_fraction": min_buried_fraction, "mean_buried_neighbours": min_mean_buried_neighbours},
        not reasons,
        "; ".join(reasons),
        method=p["method"],
    )


def residue_plddt(atoms: AtomArray, residues: list[tuple[str, int]]) -> dict:
    """Mean pLDDT over the given residues, read from the B-factor column.

    Boltz-2 writes per-atom pLDDT there. Returns a dict of per-residue means plus
    the overall mean, normalised to a 0-100 scale.
    """
    if not hasattr(atoms, "b_factor"):
        raise ValueError("structure has no B-factor/pLDDT column")
    out: dict[str, float] = {}
    for chain, resid in residues:
        sel = select_atoms(atoms, chain, resid)
        if len(sel) == 0:
            raise ValueError(f"residue {chain}{resid} not found")
        v = float(np.mean(sel.b_factor))
        out[f"{chain}{resid}"] = v * 100.0 if v <= 1.0 else v
    out["mean"] = float(np.mean(list(out.values())))
    return out


def check_active_site_plddt(
    atoms: AtomArray, residues: list[tuple[str, int]], min_plddt: float = 85.0
) -> FilterResult:
    """A confident fold with a floppy active site is useless - check it separately."""
    try:
        p = residue_plddt(atoms, residues)
    except ValueError as exc:
        return unevaluated("active_site_plddt", str(exc), min_plddt)
    passed = p["mean"] >= min_plddt
    return _ok(
        "active_site_plddt",
        {k: round(v, 2) for k, v in p.items()},
        min_plddt,
        passed,
        "" if passed else f"active-site pLDDT {p['mean']:.1f} < {min_plddt}",
    )


def check_ligand_contacts(
    atoms: AtomArray,
    contacts: list[tuple[str, str, str, float, float]],
    ligand_resname: str | None = None,
) -> FilterResult:
    """Catalytic contact geometry.

    `contacts` is a list of (residue_token, protein_atom, ligand_atom, lo, hi):
    the distance must fall inside [lo, hi]. A window, not a minimum - too short is
    a clash and in Kemp scoring is punished harder than too long.
    """
    lig = ligand_heavy(atoms, ligand_resname)
    if len(lig) == 0:
        return unevaluated("ligand_contacts", "no ligand atoms found")
    measured, bad = {}, []
    for res_token, p_atom, l_atom, lo, hi in contacts:
        try:
            chain, resid = split_residue_id(res_token)
        except ValueError as exc:
            return unevaluated("ligand_contacts", str(exc))
        psel = select_atoms(atoms, chain, resid, (p_atom,))
        lsel = lig[lig.atom_name == l_atom]
        if len(psel) != 1 or len(lsel) != 1:
            return unevaluated(
                "ligand_contacts",
                f"cannot measure {res_token}:{p_atom} -> {l_atom} (found {len(psel)} and {len(lsel)} atoms)",
            )
        d = float(np.linalg.norm(psel.coord[0] - lsel.coord[0]))
        measured[f"{res_token}_{p_atom}_to_{l_atom}"] = round(d, 3)
        if not (lo <= d <= hi):
            bad.append(f"{res_token}:{p_atom}->{l_atom} {d:.2f} A outside [{lo}, {hi}]")
    return _ok("ligand_contacts", measured, {c[0]: (c[3], c[4]) for c in contacts}, not bad, "; ".join(bad))


# ---------------------------------------------------- Kriterium 2: Anflug-Geometrie

# 7K4U, in dieser Session zweimal unabhaengig gemessen (siehe wiki/experiments/zonghu-03).
CRYSTAL_APPROACH = {
    "base": {"angle": 133.1, "out_of_plane": -6.7},
    "donor": {"angle": 140.8, "out_of_plane": -10.4},
}
TRIAZOLE = ("N1", "N2", "N3", "C3A", "C7A")


def angle_between(a, b, c) -> float:
    """Angle a-b-c in degrees."""
    v1, v2 = np.asarray(a) - np.asarray(b), np.asarray(c) - np.asarray(b)
    cos = float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))
    return float(np.degrees(np.arccos(max(-1.0, min(1.0, cos)))))


def out_of_plane_angle(point, ring_coords) -> float:
    """Degrees out of the best-fit plane of `ring_coords`, seen from its centroid.

    0 means the atom lies in the ring plane. The N3-H of the TS analogue lies IN
    that plane, so a base approaching from the ring FACE is not on the proton
    transfer axis however good its distance looks.
    """
    ring = np.asarray(ring_coords)
    centre = ring.mean(axis=0)
    normal = np.linalg.svd(ring - centre)[2][2]
    v = np.asarray(point) - centre
    return float(np.degrees(np.arcsin(max(-1.0, min(1.0, float(np.dot(v / np.linalg.norm(v), normal)))))))


def check_approach_geometry(
    atoms: AtomArray,
    contacts: list[tuple[str, str, str, str]],
    max_deviation: float = 30.0,
    ligand_resname: str | None = None,
) -> FilterResult:
    """Criterion 2: angle AND in-plane, **the worse of the two decides**.

    `contacts` is (label, residue_token, root_atom, contact_atom): the angle is
    root-contact...ligand_atom, e.g. ("base", "A127", "CG", "OD2").

    The organizers are explicit: "The angle and the in-plane terms do not average -
    the worse of the two decides." So this reports a max of deviations, never a mean.
    """
    lig = ligand_heavy(atoms, ligand_resname)
    ring = [lig[lig.atom_name == n].coord[0] for n in TRIAZOLE if len(lig[lig.atom_name == n]) == 1]
    if len(ring) < 3:
        return unevaluated("approach_geometry", "ligand ring atoms not found", max_deviation)

    measured, worst, worst_what = {}, 0.0, ""
    for label, res_token, root, contact in contacts:
        ref = CRYSTAL_APPROACH.get(label)
        try:
            chain, resid = split_residue_id(res_token)
        except ValueError as exc:
            return unevaluated("approach_geometry", str(exc), max_deviation)
        a_root = select_atoms(atoms, chain, resid, (root,))
        a_cont = select_atoms(atoms, chain, resid, (contact,))
        target = "N3" if label == "base" else "N1"
        a_lig = lig[lig.atom_name == target]
        if len(a_root) != 1 or len(a_cont) != 1 or len(a_lig) != 1:
            return unevaluated(
                "approach_geometry",
                f"cannot measure {label} ({res_token}:{root}/{contact} -> {target})",
                max_deviation,
            )
        ang = angle_between(a_root.coord[0], a_cont.coord[0], a_lig.coord[0])
        oop = out_of_plane_angle(a_cont.coord[0], ring)
        d_ang = abs(ang - ref["angle"]) if ref else 0.0
        d_oop = abs(oop - ref["out_of_plane"]) if ref else 0.0
        measured[label] = {
            "angle": round(ang, 1),
            "out_of_plane": round(oop, 1),
            "d_angle": round(d_ang, 1),
            "d_out_of_plane": round(d_oop, 1),
        }
        for d, what in ((d_ang, f"{label} angle"), (d_oop, f"{label} out-of-plane")):
            if d > worst:
                worst, worst_what = d, what
    passed = worst <= max_deviation
    return _ok(
        "approach_geometry",
        measured,
        max_deviation,
        passed,
        "" if passed else f"worst deviation {worst:.0f} deg ({worst_what})",
        worst_deviation=round(worst, 1),
        rule="max, not mean - the worse decides",
    )


# ------------------------------------------------- Kriterium 4: Active-site packing


def base_burial(atoms: AtomArray, residue: str, atom_name: str = "OD2", radius: float = 12.0) -> int:
    """CA atoms within `radius` of the catalytic base - the organizers' exact definition.

    challenge.md: "number of CA atoms close to the catalytic base (up to 12 A)".
    """
    chain, resid = split_residue_id(residue)
    sel = select_atoms(atoms, chain, resid, (atom_name,))
    if len(sel) != 1:
        raise ValueError(f"{residue}:{atom_name} not found")
    ca = atoms[(~atoms.hetero) & (atoms.atom_name == "CA")]
    return int((np.linalg.norm(ca.coord - sel.coord[0], axis=1) <= radius).sum())


def check_base_burial(atoms: AtomArray, residue: str, min_ca: int = 45) -> FilterResult:
    """Criterion 4: is the base enclosed rather than solvent-exposed?

    Default 45 from the observed spread (20-55 over 14 designs): the collapsed or
    surface-exposed ones sit at 20-29, folded ones at 44-55. Empirical, not physics.
    """
    try:
        n = base_burial(atoms, residue)
    except ValueError as exc:
        return unevaluated("base_burial", str(exc), min_ca)
    passed = n >= min_ca
    return _ok(
        "base_burial",
        n,
        min_ca,
        passed,
        "" if passed else f"only {n} CA within 12 A of the base (solvent-exposed)",
    )
