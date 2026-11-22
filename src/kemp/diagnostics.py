"""Informational chemistry around the active site. **Never part of the score.**

These quantities are not among the organizers' criteria. They are reported as
numbers with no verdict attached, because turning an unscored observation into a
pass/fail would invent a criterion nobody is ranked on. `tests/test_diagnostics.py`
asserts that no key here appears in `kemp.scoring.WEIGHTS`, so the separation is
enforced by the test suite rather than by a comment.

Why they are worth measuring anyway:

* **Charge environment, on both sides.** `check_base_burial` (criterion 4) counts
  CA atoms, which says how enclosed the base is but nothing about whether the
  carboxylate can actually be deprotonated at pH 7. A buried carboxylate with no
  counter-charge has a strongly raised pKa. Maximising burial without looking at
  this can select designs whose base is protonated and therefore inert — the two
  quantities pull against each other. Measured for the base **and** for the
  hydrogen-bond donor.
* **Nearest pi system, any aromatic.** Deliberately not restricted to tryptophan:
  some designs carry no Trp at the motif position at all, and LigandMPNN often
  places a Phe, Tyr or His there instead.
* **Hydrogen bonds to the nitro group.** In 6NT that is O11/O21 on NO1. The nitro
  group withdraws electron density and helps delocalise the developing negative
  charge, so a hydrogen bond to it is real extra stabilisation that no scored
  criterion sees.

Counting is **per residue, not per atom**: one aspartate is one negative charge,
not two. The earlier atom-wise version double-counted every carboxylate.
"""

from __future__ import annotations

import math

import numpy as np

BENZO_RING = ("C4", "C5", "C6", "C7", "C3A", "C7A")
NITRO_OXYGENS = ("O11", "O21")

#: Aromatic side-chain rings, by residue name. Any of these counts as a pi system.
AROMATIC_RINGS = {
    "TRP": ("CG", "CD1", "CD2", "NE1", "CE2", "CE3", "CZ2", "CZ3", "CH2"),
    "PHE": ("CG", "CD1", "CD2", "CE1", "CE2", "CZ"),
    "TYR": ("CG", "CD1", "CD2", "CE1", "CE2", "CZ"),
    "HIS": ("CG", "ND1", "CD2", "CE1", "NE2"),
}

#: Formal charge at pH 7 and the atoms that carry it. His is 0 and reported apart,
#: because its protonation state near pH 7 is genuinely ambiguous.
CHARGED_GROUPS = {
    "ARG": (+1, ("NE", "NH1", "NH2")),
    "LYS": (+1, ("NZ",)),
    "ASP": (-1, ("OD1", "OD2")),
    "GLU": (-1, ("OE1", "OE2")),
    "HIS": (0, ("ND1", "NE2")),
}

#: Heavy atoms that carry a hydrogen and can donate a bond.
DONOR_HEAVY_ATOMS = frozenset(
    {"N", "NE", "NH1", "NH2", "NZ", "NE1", "ND1", "NE2", "ND2", "OG", "OG1", "OH", "SG"}
)

RADIUS_ELECTROSTATIC = 6.0  # A, for the charge environment
RADIUS_HBOND = 3.5  # A, heavy-atom donor to acceptor

#: The keys this module produces. Asserted disjoint from kemp.scoring.WEIGHTS.
DIAGNOSTIC_KEYS = frozenset({"charge_base", "charge_donor", "nearest_pi", "nitro_hbonds"})


def ring_plane(coords) -> tuple[np.ndarray, np.ndarray]:
    """Best-fit plane normal and centroid of a ring."""
    c = np.asarray(coords, dtype=float)
    return np.linalg.svd(c - c.mean(axis=0))[2][2], c.mean(axis=0)


def interplanar_angle(normal_a, normal_b) -> float:
    """Angle between two ring planes in degrees, always 0-90.

    Uses `abs` of the dot product because a plane normal has no preferred
    direction: a normal and its negation describe the same plane.
    """
    cos = abs(float(np.dot(normal_a, normal_b)))
    return math.degrees(math.acos(max(0.0, min(1.0, cos))))


def charge_environment(residues, centre_coords, radius=RADIUS_ELECTROSTATIC) -> dict:
    """Net formal charge near a site, counted per residue.

    `residues` is an iterable of (res_name, res_id, {atom_name: coord}). Returns
    counts and a net; **no verdict** — a net of -3 is reported as -3, not as "bad".
    """
    pos = neg = his = 0
    nearby = []
    for res_name, res_id, atoms in residues:
        spec = CHARGED_GROUPS.get(res_name)
        if spec is None:
            continue
        charge, names = spec
        pts = [atoms[n] for n in names if n in atoms]
        if not pts:
            continue
        dmin = min(
            min(float(np.linalg.norm(np.asarray(p) - np.asarray(c))) for c in centre_coords) for p in pts
        )
        if dmin > radius:
            continue
        if charge > 0:
            pos += 1
        elif charge < 0:
            neg += 1
        else:
            his += 1
        nearby.append((f"{res_name}{res_id}", round(dmin, 2)))
    return {
        "positive": pos,
        "negative": neg,
        "histidine": his,
        "net": pos - neg,
        "nearby": sorted(nearby, key=lambda x: x[1]),
    }


def nearest_pi_system(residues, ligand_ring_coords) -> dict | None:
    """Closest aromatic ring to the ligand ring: residue, centroid distance, angle.

    Any of Trp/Phe/Tyr/His qualifies — see the module docstring for why this is
    not restricted to tryptophan.
    """
    lig_normal, lig_centre = ring_plane(ligand_ring_coords)
    best = None
    for res_name, res_id, atoms in residues:
        names = AROMATIC_RINGS.get(res_name)
        if not names:
            continue
        pts = [atoms[n] for n in names if n in atoms]
        if len(pts) < 5:
            continue
        normal, centre = ring_plane(pts)
        d = float(np.linalg.norm(centre - lig_centre))
        if best is None or d < best["distance"]:
            best = {
                "residue": f"{res_name}{res_id}",
                "distance": round(d, 2),
                "interplanar_angle": round(interplanar_angle(normal, lig_normal), 1),
            }
    return best


def nitro_hbonds(residues, nitro_coords, radius=RADIUS_HBOND) -> list[dict]:
    """Protein hydrogen-bond donors within `radius` of a nitro oxygen.

    Heavy-atom distance only — no angle criterion and no hydrogens, since Boltz-2
    does not output them. A hit is therefore a *candidate* hydrogen bond. Distances
    well under ~2.4 A are too short for one and indicate a steric clash instead;
    they are reported as measured rather than filtered out.
    """
    out = []
    for res_name, res_id, atoms in residues:
        for atom_name, coord in atoms.items():
            if atom_name not in DONOR_HEAVY_ATOMS:
                continue
            d = min(float(np.linalg.norm(np.asarray(coord) - np.asarray(o))) for o in nitro_coords)
            if d <= radius:
                out.append({"residue": f"{res_name}{res_id}", "atom": atom_name, "distance": round(d, 2)})
    return sorted(out, key=lambda x: x["distance"])
