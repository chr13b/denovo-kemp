"""Geometry decides most of our score, so the terms get tests on shapes we can reason about by hand.

The angular cases use a flat hexagon in the xy-plane, where the right answer is obvious: a partner
placed in the plane must read 0 deg out-of-plane, and one placed above the ring centre must read 90.
"""

from __future__ import annotations

import math

from kemp.geometry import (
    angle,
    contact_geometry,
    count_ca_within,
    format_atom,
    nearest_atom,
    parse_pdb,
    plane_normal,
    primary_altloc,
)

# Two conformations of one Asp side chain, plus a backbone CA, in fixed-column PDB.
PDB = """\
ATOM      1  CA  ASP A 127      10.000  10.000  10.000  1.00 10.00           C
ATOM      2  OD1AASP A 127       1.000   0.000   0.000  0.30 10.00           O
ATOM      3  OD1BASP A 127       2.000   0.000   0.000  0.70 10.00           O
HETATM    4  N3  6NT A 402       0.000   0.000   0.000  1.00 10.00           N
ENDMDL
ATOM      5  CA  ASP A 999      99.000  99.000  99.000  1.00 10.00           C
"""


def hexagon(radius: float = 1.4) -> list[tuple[float, float, float]]:
    """A flat six-ring in the xy-plane, centred on the origin."""
    return [(radius * math.cos(i * math.pi / 3), radius * math.sin(i * math.pi / 3), 0.0) for i in range(6)]


def test_parse_reads_fields_and_stops_at_the_first_model():
    atoms = parse_pdb(PDB)
    assert len(atoms) == 4, "records after ENDMDL belong to model 2 and must be ignored"
    assert atoms[0].name == "CA" and atoms[0].res_name == "ASP" and atoms[0].res_seq == 127
    assert atoms[3].record == "HETATM" and atoms[3].element == "N"


def test_altloc_keeps_the_better_occupancy_only():
    kept = {(a.name, a.res_seq): a for a in primary_altloc(parse_pdb(PDB))}
    assert len(kept) == 3, "the two OD1 conformations collapse to one"
    assert kept[("OD1", 127)].x == 2.0, "the 0.70-occupancy conformation wins"


def test_format_atom_round_trips():
    original = parse_pdb(PDB)[1]
    reparsed = parse_pdb(format_atom(original, serial=7, res_seq=1))[0]
    assert (reparsed.name, reparsed.element, reparsed.res_name) == ("OD1", "O", "ASP")
    assert (reparsed.x, reparsed.y, reparsed.z) == (original.x, original.y, original.z)
    assert reparsed.res_seq == 1 and reparsed.serial == 7


def test_a_partner_in_the_ring_plane_reads_as_in_plane():
    ring = hexagon()
    # Straight out from ring[0], along its own radius: the ideal head-on approach.
    partner = (ring[0][0] * 3, ring[0][1] * 3, 0.0)
    g = contact_geometry(ring[0], [ring[1], ring[5]], plane_normal(ring), partner, (0.0, 0.0, 0.0))
    assert g["out_of_plane_deg"] == 0.0
    assert g["in_plane_deg"] == 0.0


def test_a_partner_above_the_ring_face_reads_as_out_of_plane():
    ring = hexagon()
    partner = (ring[0][0], ring[0][1], 3.0)  # straight up off the ring atom
    g = contact_geometry(ring[0], [ring[1], ring[5]], plane_normal(ring), partner, (0.0, 0.0, 0.0))
    assert g["out_of_plane_deg"] == 90.0
    assert g["distance_a"] == 3.0


def test_the_two_angular_terms_are_independent():
    """A partner can be perfectly in-plane and badly angled, which is why neither term is averaged."""
    ring = hexagon()
    sideways = (ring[1][0] * 3, ring[1][1] * 3, 0.0)  # in the plane, but swung round the ring
    g = contact_geometry(ring[0], [ring[1], ring[5]], plane_normal(ring), sideways, (0.0, 0.0, 0.0))
    assert g["out_of_plane_deg"] == 0.0
    assert g["in_plane_deg"] > 30.0


def test_plane_normal_is_unit_length_and_perpendicular():
    normal = plane_normal(hexagon())
    assert math.isclose(math.sqrt(sum(c * c for c in normal)), 1.0, abs_tol=1e-9)
    assert math.isclose(abs(normal[2]), 1.0, abs_tol=1e-9), "an xy-plane ring has a z normal"


def test_angle_at_the_vertex():
    assert math.isclose(angle((1, 0, 0), (0, 0, 0), (0, 1, 0)), 90.0, abs_tol=1e-9)
    assert math.isclose(angle((1, 0, 0), (0, 0, 0), (-1, 0, 0)), 180.0, abs_tol=1e-9)


def test_burial_counts_only_ca_within_the_radius():
    atoms = primary_altloc(parse_pdb(PDB))
    assert count_ca_within(atoms, (10.0, 10.0, 10.0), radius=12.0) == 1
    assert count_ca_within(atoms, (0.0, 0.0, 0.0), radius=1.0) == 0, "OD1 is close but is not a CA"


def test_nearest_atom_respects_the_allowed_residue_and_atom_names():
    from kemp.geometry import group_by_residue

    residues = group_by_residue(primary_altloc(parse_pdb(PDB)))
    hit = nearest_atom((0.0, 0.0, 0.0), residues, {"ASP": ("OD1", "OD2")})
    assert hit is not None
    dist, key, atom = hit
    assert atom.name == "OD1" and key[3] == "ASP" and math.isclose(dist, 2.0)
    assert nearest_atom((0.0, 0.0, 0.0), residues, {"GLU": ("OE1",)}) is None
