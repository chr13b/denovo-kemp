"""Tests for the scored criteria. The plane term had a real bug, so it gets several."""

import math

import pytest

from kemp.scoring import (
    CRYSTAL,
    SIGMA_LONG,
    SIGMA_SHORT,
    TEXTBOOK_HBOND,
    WEIGHTS,
    approach_deviation,
    dihedral,
    out_of_plane,
    score_burial,
    score_consistency,
    score_distance,
    score_ipde,
    weighted_total,
)

RING = [(1, 0, 0), (0.31, 0.95, 0), (-0.81, 0.59, 0), (-0.81, -0.59, 0), (0.31, -0.95, 0)]


def test_geometry_outweighs_everything_else_combined():
    """The brief's central weighting claim, as an assertion."""
    geometry = WEIGHTS["dist"] + WEIGHTS["approach"]
    rest = sum(v for k, v in WEIGHTS.items() if k not in ("dist", "approach"))
    assert geometry > rest
    assert WEIGHTS["dist"] > WEIGHTS["approach"]  # "carries the most weight of anything here"
    assert sum(WEIGHTS.values()) == pytest.approx(1.0)


def test_too_short_is_punished_harder_than_too_long():
    t = CRYSTAL["base"]["dist"]
    for err in (0.3, 0.6, 1.0):
        assert score_distance(t - err, t) < score_distance(t + err, t), err
    assert SIGMA_SHORT < SIGMA_LONG


def test_distance_optimum_is_at_the_crystal_value_not_a_direction():
    """ "There is an optimum, not a direction" - closer is not always better."""
    t = CRYSTAL["donor"]["dist"]
    assert score_distance(t, t) == pytest.approx(1.0)
    assert score_distance(t - 1.0, t) < 0.5  # much too short scores badly
    assert score_distance(2.0, t) < score_distance(3.2, t)


def test_the_two_contacts_have_different_targets():
    """v1's single 2.9 A optimum was wrong; the crystal gives two values."""
    assert CRYSTAL["base"]["dist"] != CRYSTAL["donor"]["dist"]
    assert abs(CRYSTAL["base"]["dist"] - CRYSTAL["donor"]["dist"]) > 0.6


def test_base_target_is_outside_textbook_range_open_question():
    """Documents the disagreement with the brief rather than hiding it."""
    assert CRYSTAL["base"]["dist"] < TEXTBOOK_HBOND[0]  # 2.535 < 2.8
    assert TEXTBOOK_HBOND[0] <= CRYSTAL["donor"]["dist"] <= TEXTBOOK_HBOND[1] + 0.25


def test_out_of_plane_is_sign_independent():
    """The bug that zeroed 14 of 16 designs: mirrored contacts must score alike."""
    above, below = (0.5, 0.0, 0.4), (0.5, 0.0, -0.4)
    d_above = dihedral(above, RING[0], RING[1], RING[2])
    d_below = dihedral(below, RING[0], RING[1], RING[2])
    assert d_above * d_below < 0, "the two really are opposite in sign"
    assert out_of_plane(above, RING[0], RING[1], RING[2]) == pytest.approx(
        out_of_plane(below, RING[0], RING[1], RING[2]), abs=1e-6
    )


def test_in_plane_contact_has_near_zero_deviation():
    in_plane = (2.5, 0.0, 0.0)
    assert out_of_plane(in_plane, RING[0], RING[1], RING[2]) == pytest.approx(0.0, abs=1e-6)


def test_dihedral_matches_a_known_value():
    """Textbook case: a +90 degree torsion."""
    assert dihedral((1, 0, 0), (0, 0, 0), (0, 1, 0), (0, 1, 1)) == pytest.approx(-90.0, abs=1e-6)


def test_worse_of_angle_and_plane_decides_never_the_mean():
    m = {"base": {"angle": CRYSTAL["base"]["angle"], "oop": CRYSTAL["base"]["oop"] + 60.0}}
    worst, what = approach_deviation(m)
    assert worst == pytest.approx(60.0)  # not 30.0, which a mean would give
    assert "ring plane" in what


def test_weighted_total_collapses_on_a_zero_term():
    """ "Strength in one term does not compensate for failure in another."

    Because the weights are exponents, a zero term does not give exactly zero but
    1e-9 ** weight - about 1.1e-3 for the distance term. That is a ~900x penalty,
    so the design is dead in any ranking, but the number is not literally 0.
    """
    good = dict(dist=1.0, approach=1.0, ipde=1.0, burial=1.0, consistency=1.0)
    assert weighted_total(good) == pytest.approx(1.0)
    for term in good:
        collapsed = weighted_total({**good, term: 0.0})
        assert collapsed < 0.05, term
        assert weighted_total(good) / collapsed > 20, term
    # geometry collapses hardest, because it carries the largest exponent
    assert weighted_total({**good, "dist": 0.0}) < weighted_total({**good, "ipde": 0.0})


def test_missing_term_is_dropped_not_treated_as_perfect():
    partial = dict(dist=0.5, approach=0.5, ipde=0.5, burial=0.5, consistency=None)
    full_bad = dict(dist=0.5, approach=0.5, ipde=0.5, burial=0.5, consistency=0.0)
    assert weighted_total(partial) == pytest.approx(0.5, abs=1e-6)
    assert weighted_total(full_bad) < weighted_total(partial)


def test_consistency_rewards_reproducibility():
    """Measured values: vA_s2 scattered 0.55/0.83 A, vA_s3 2.43/2.86 A."""
    assert score_consistency([0.55, 0.83]) > score_consistency([2.43, 2.86])
    assert score_consistency([2.43, 2.86]) < 0.001
    assert score_consistency([0.0, 0.0]) == pytest.approx(1.0)
    assert score_consistency([]) is None


def test_ipde_and_burial_are_monotone():
    assert score_ipde(1.0) > score_ipde(2.42) > score_ipde(5.0)
    assert score_burial(55) == pytest.approx(1.0)
    assert score_burial(20) == pytest.approx(0.0)
    assert math.isclose(score_burial(35), 0.5)
