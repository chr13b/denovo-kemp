"""PDB reading and catalytic-site geometry, with no third-party dependencies.

    from kemp.geometry import parse_pdb, primary_altloc, contact_geometry
    atoms = primary_altloc(parse_pdb(Path("x.pdb").read_text()))

Standard library only on purpose: this has to run on a laptop, on the cluster head node and in
CI without adding NumPy, Biopython or RDKit to the lockfile.

Two kinds of thing live here. First, enough PDB parsing to pull named atoms out of a structure.
Second, the geometry the organizers score: the separation of a catalytic partner from a ligand
ring atom, split into the terms their scoring keeps apart.

The angular decomposition is the part worth understanding. A hydrogen bond onto an aromatic ring
can be wrong in two independent ways, and `wiki/challenge.md` records that the scorer keeps the
*worse* of the two rather than averaging them:

    in-plane      swing around the ring's own plane: is the partner straight out from the ring
                  atom, or off to one side?
    out-of-plane  rise above that plane: is the partner level with the ring, or approaching its
                  face? 0 deg is level; 90 deg is straight down onto the ring.

So both are reported separately and nothing here averages them.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

Vec = tuple[float, float, float]


@dataclass
class Atom:
    """One ATOM/HETATM record, with only the fields we use."""

    record: str
    serial: int
    name: str
    alt_loc: str
    res_name: str
    chain: str
    res_seq: int
    i_code: str
    x: float
    y: float
    z: float
    occupancy: float
    b_factor: float
    element: str

    @property
    def xyz(self) -> Vec:
        return (self.x, self.y, self.z)

    @property
    def res_key(self) -> tuple[str, int, str, str]:
        return (self.chain, self.res_seq, self.i_code, self.res_name)

    def is_hydrogen(self) -> bool:
        return self.element in ("H", "D")


def parse_pdb(text: str) -> list[Atom]:
    """Parse ATOM/HETATM records from PDB text. Stops at the first ENDMDL, so model 1 only."""
    atoms: list[Atom] = []
    for line in text.splitlines():
        if line.startswith("ENDMDL"):
            break
        if not line.startswith(("ATOM  ", "HETATM")):
            continue
        try:
            atoms.append(
                Atom(
                    record=line[0:6].strip(),
                    serial=int(line[6:11]),
                    name=line[12:16].strip(),
                    alt_loc=line[16].strip(),
                    res_name=line[17:20].strip(),
                    chain=line[21].strip() or "A",
                    res_seq=int(line[22:26]),
                    i_code=line[26].strip(),
                    x=float(line[30:38]),
                    y=float(line[38:46]),
                    z=float(line[46:54]),
                    occupancy=float(line[54:60]) if line[54:60].strip() else 1.0,
                    b_factor=float(line[60:66]) if line[60:66].strip() else 0.0,
                    element=(line[76:78].strip() or line[12:16].strip()[:1]).upper(),
                )
            )
        except (ValueError, IndexError):
            continue  # a malformed line is skipped rather than killing the run
    return atoms


def primary_altloc(atoms: list[Atom]) -> list[Atom]:
    """Keep one position per atom: the highest occupancy.

    High-resolution structures model flexible side chains in two conformations. Measuring a
    contact across a mixture of them gives a distance that belongs to neither.
    """
    best: dict[tuple, Atom] = {}
    for atom in atoms:
        key = (atom.chain, atom.res_seq, atom.i_code, atom.name)
        if key not in best or atom.occupancy > best[key].occupancy:
            best[key] = atom
    return sorted(best.values(), key=lambda a: a.serial)


def group_by_residue(atoms: list[Atom]) -> dict[tuple, list[Atom]]:
    grouped: dict[tuple, list[Atom]] = {}
    for atom in atoms:
        grouped.setdefault(atom.res_key, []).append(atom)
    return grouped


def format_atom(atom: Atom, serial: int, res_seq: int) -> str:
    """Render one record back to fixed-column PDB, renumbered."""
    name = atom.name if len(atom.name) >= 4 else f" {atom.name:<3}"
    return (
        f"{atom.record:<6}{serial:>5} {name:<4}{atom.alt_loc:1}"
        f"{atom.res_name:>3} {atom.chain:1}{res_seq:>4}{atom.i_code:1}   "
        f"{atom.x:>8.3f}{atom.y:>8.3f}{atom.z:>8.3f}"
        f"{1.00:>6.2f}{atom.b_factor:>6.2f}          {atom.element:>2}"
    )


# --- vectors ---------------------------------------------------------------------------------


def sub(a: Vec, b: Vec) -> Vec:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def dot(a: Vec, b: Vec) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def cross(a: Vec, b: Vec) -> Vec:
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def norm(a: Vec) -> float:
    return math.sqrt(dot(a, a))


def unit(a: Vec) -> Vec:
    n = norm(a)
    if n == 0:
        raise ValueError("cannot normalise a zero-length vector")
    return (a[0] / n, a[1] / n, a[2] / n)


def distance(a: Vec, b: Vec) -> float:
    return norm(sub(a, b))


def angle(a: Vec, b: Vec, c: Vec) -> float:
    """Angle a-b-c in degrees, with b at the vertex."""
    v1, v2 = sub(a, b), sub(c, b)
    return math.degrees(math.acos(max(-1.0, min(1.0, dot(v1, v2) / (norm(v1) * norm(v2))))))


def centroid(points: list[Vec]) -> Vec:
    n = len(points)
    return (sum(p[0] for p in points) / n, sum(p[1] for p in points) / n, sum(p[2] for p in points) / n)


def plane_normal(points: list[Vec]) -> Vec:
    """Best-fit plane normal by Newell's method.

    Newell's uses every point rather than three of them, so a slightly puckered ring still gives
    a stable normal.
    """
    nx = ny = nz = 0.0
    count = len(points)
    for i, cur in enumerate(points):
        nxt = points[(i + 1) % count]
        nx += (cur[1] - nxt[1]) * (cur[2] + nxt[2])
        ny += (cur[2] - nxt[2]) * (cur[0] + nxt[0])
        nz += (cur[0] - nxt[0]) * (cur[1] + nxt[1])
    return unit((nx, ny, nz))


# --- the scored geometry ---------------------------------------------------------------------


def contact_geometry(
    ring_atom: Vec, ring_neighbours: list[Vec], ring_normal: Vec, partner: Vec, partner_root: Vec
) -> dict[str, float]:
    """Decompose a partner's approach to a ring atom into the terms the scorer keeps apart.

    `ring_neighbours` are the two ring atoms bonded to `ring_atom`; their midpoint defines the
    exocyclic direction that an ideal head-on approach follows. `partner_root` is the heavy atom
    the partner hangs off (Gln CD for NE2, Asp CG for OD2), which says whether the partner's own
    geometry points at the ligand or merely lands near it.
    """
    v = sub(partner, ring_atom)

    cos_to_normal = abs(dot(unit(v), ring_normal))
    out_of_plane = 90.0 - math.degrees(math.acos(max(-1.0, min(1.0, cos_to_normal))))

    def flatten(w: Vec) -> Vec:
        """Drop the component along the ring normal, leaving the part inside the ring plane."""
        scale = dot(w, ring_normal)
        return sub(w, (ring_normal[0] * scale, ring_normal[1] * scale, ring_normal[2] * scale))

    in_plane_v = flatten(v)
    outward = flatten(sub(ring_atom, centroid(ring_neighbours)))
    if norm(in_plane_v) < 1e-6 or norm(outward) < 1e-6:
        in_plane = float("nan")
    else:
        in_plane = math.degrees(math.acos(max(-1.0, min(1.0, dot(unit(in_plane_v), unit(outward))))))

    return {
        "distance_a": round(distance(partner, ring_atom), 2),
        "in_plane_deg": round(in_plane, 1),
        "out_of_plane_deg": round(out_of_plane, 1),
        "partner_angle_deg": round(angle(partner_root, partner, ring_atom), 1),
    }


def count_ca_within(atoms: list[Atom], centre: Vec, radius: float = 12.0) -> int:
    """Burial, as the organizers define it: CA atoms within `radius` of the catalytic base."""
    return sum(1 for a in atoms if a.name == "CA" and distance(a.xyz, centre) <= radius)


def nearest_atom(target: Vec, residues: dict[tuple, list[Atom]], allowed: dict[str, tuple[str, ...]]):
    """Closest allowed side-chain atom to `target`, searching the whole structure.

    `allowed` maps residue name to the atom names that can play the role, so a search for a
    catalytic base cannot return a backbone oxygen or the wrong residue type.
    Returns (distance, res_key, atom) or None.
    """
    best = None
    for key, atoms in residues.items():
        wanted = allowed.get(key[3])
        if not wanted:
            continue
        for atom in atoms:
            if atom.name in wanted:
                d = distance(atom.xyz, target)
                if best is None or d < best[0]:
                    best = (d, key, atom)
    return best
