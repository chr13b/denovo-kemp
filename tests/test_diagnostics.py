"""Tests for the informational metrics, including that they stay out of the score."""

import math

import numpy as np
import pytest

from kemp.diagnostics import (
    DIAGNOSTIC_KEYS,
    DONOR_HEAVY_ATOMS,
    charge_environment,
    interplanar_angle,
    nearest_pi_system,
    nitro_hbonds,
    ring_plane,
)
from kemp.scoring import WEIGHTS

# A hexagon in the z=0 plane, centred on the origin.
HEX = [(1.4, 0, 0), (0.7, 1.21, 0), (-0.7, 1.21, 0), (-1.4, 0, 0), (-0.7, -1.21, 0), (0.7, -1.21, 0)]


def res(name, rid, **atoms):
    return (name, rid, atoms)


def test_diagnostics_never_enter_the_score():
    """The whole point of this module: it informs, it does not rank."""
    assert DIAGNOSTIC_KEYS.isdisjoint(WEIGHTS.keys())


def test_charges_are_counted_per_residue_not_per_atom():
    """One aspartate is one negative charge, although it has two carboxylate oxygens."""
    residues = [res("ASP", 10, OD1=(1.0, 0, 0), OD2=(2.0, 0, 0))]
    env = charge_environment(residues, [(0.0, 0, 0)])
    assert env["negative"] == 1
    assert env["net"] == -1


def test_net_charge_sums_both_signs_and_keeps_his_apart():
    residues = [
        res("ARG", 1, NE=(1.0, 0, 0)),
        res("LYS", 2, NZ=(1.5, 0, 0)),
        res("ASP", 3, OD1=(2.0, 0, 0)),
        res("HIS", 4, ND1=(2.5, 0, 0)),
    ]
    env = charge_environment(residues, [(0.0, 0, 0)])
    assert (env["positive"], env["negative"], env["histidine"]) == (2, 1, 1)
    assert env["net"] == 1  # His does not count either way


def test_charges_outside_the_radius_are_ignored():
    far = [res("ARG", 1, NE=(50.0, 0, 0))]
    assert charge_environment(far, [(0.0, 0, 0)])["net"] == 0


def test_charge_environment_returns_a_number_not_a_verdict():
    """A net of -3 must be reported as -3, with no pass/fail key anywhere."""
    residues = [res("ASP", i, OD1=(1.0 + 0.1 * i, 0, 0)) for i in range(3)]
    env = charge_environment(residues, [(0.0, 0, 0)])
    assert env["net"] == -3
    assert not {"passed", "ok", "risk", "verdict"} & set(env)


def test_nearest_pi_system_is_not_limited_to_tryptophan():
    """Designs without a Trp must still report their closest aromatic."""
    names = ("CG", "CD1", "CD2", "CE1", "CE2", "CZ")
    phe = res("PHE", 7, **{n: (x + 4.0, y, z) for n, (x, y, z) in zip(names, HEX, strict=True)})
    out = nearest_pi_system([phe], HEX)
    assert out is not None and out["residue"] == "PHE7"
    assert out["distance"] == pytest.approx(4.0, abs=0.01)


def test_nearest_pi_system_picks_the_closest_of_several():
    names = ("CG", "CD1", "CD2", "CE1", "CE2", "CZ")
    near = res("TYR", 1, **{n: (x + 4.0, y, z) for n, (x, y, z) in zip(names, HEX, strict=True)})
    far = res("PHE", 2, **{n: (x + 12.0, y, z) for n, (x, y, z) in zip(names, HEX, strict=True)})
    assert nearest_pi_system([far, near], HEX)["residue"] == "TYR1"


def test_no_aromatic_returns_none():
    assert nearest_pi_system([res("ALA", 1, CB=(0, 0, 0))], HEX) is None


def test_interplanar_angle_is_direction_agnostic():
    """A plane normal and its negation describe the same plane."""
    up, down = np.array([0.0, 0.0, 1.0]), np.array([0.0, 0.0, -1.0])
    assert interplanar_angle(up, down) == pytest.approx(0.0, abs=1e-6)
    assert interplanar_angle(up, np.array([1.0, 0.0, 0.0])) == pytest.approx(90.0, abs=1e-6)


def test_parallel_rings_have_zero_interplanar_angle():
    normal_a, _ = ring_plane(HEX)
    normal_b, _ = ring_plane([(x, y, z + 3.5) for x, y, z in HEX])
    assert interplanar_angle(normal_a, normal_b) == pytest.approx(0.0, abs=1e-6)


def test_nitro_hbonds_finds_donors_and_sorts_by_distance():
    residues = [
        res("SER", 20, OG=(3.0, 0, 0)),
        res("ARG", 21, NH1=(2.8, 0, 0)),
        res("ALA", 22, CB=(2.9, 0, 0)),  # carbon: not a donor
        res("LYS", 23, NZ=(9.0, 0, 0)),  # too far
    ]
    hits = nitro_hbonds(residues, [(0.0, 0, 0)])
    assert [h["residue"] for h in hits] == ["ARG21", "SER20"]
    assert all(h["atom"] in DONOR_HEAVY_ATOMS for h in hits)


def test_unphysically_short_contact_is_reported_not_filtered():
    """hb_s3 really has LYS:NZ at 1.90 A to a nitro oxygen - a clash, reported as is."""
    hits = nitro_hbonds([res("LYS", 229, NZ=(1.90, 0, 0))], [(0.0, 0, 0)])
    assert len(hits) == 1
    assert hits[0]["distance"] == pytest.approx(1.90)


def test_backbone_nitrogen_counts_as_a_donor():
    assert "N" in DONOR_HEAVY_ATOMS
    assert nitro_hbonds([res("GLY", 31, N=(2.83, 0, 0))], [(0.0, 0, 0)])


def test_no_donor_gives_an_empty_list_not_an_error():
    assert nitro_hbonds([res("ALA", 1, CB=(2.0, 0, 0))], [(0.0, 0, 0)]) == []
    assert math.isfinite(1.0)  # sanity
