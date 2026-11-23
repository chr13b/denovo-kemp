"""Die fuenf Kriterien der Organisatoren als Tests - gegen den Kristall geprueft."""

import pytest

from kemp.filters import check_interface_error
from kemp.paths import RESULTS
from kemp.structure import (
    angle_between,
    base_burial,
    check_approach_geometry,
    check_base_burial,
    load_structure,
    out_of_plane_angle,
)

THEO = RESULTS / "theozyme" / "theozyme_7k4u_core.pdb"
CONTACTS = [("base", "A127", "CG", "OD2"), ("donor", "A50", "CD", "NE2")]


def test_ipde_is_the_scored_confidence_not_plddt():
    """iPDE ist Kriterium 3; pLDDT steht nicht auf der Liste."""
    assert check_interface_error({"complex_ipde": 1.5}, 2.0).passed is True
    assert check_interface_error({"complex_ipde": 3.3}, 2.0).passed is False
    # fehlendes iPDE darf NICHT als bestanden gelten
    assert check_interface_error({"complex_plddt": 0.95}, 2.0).passed is None


def test_angle_between_is_sane():
    assert angle_between((1, 0, 0), (0, 0, 0), (0, 1, 0)) == pytest.approx(90.0)
    assert angle_between((1, 0, 0), (0, 0, 0), (-1, 0, 0)) == pytest.approx(180.0)


def test_out_of_plane_is_zero_in_the_plane():
    ring = [(1, 0, 0), (0, 1, 0), (-1, 0, 0), (0, -1, 0)]
    assert out_of_plane_angle((2, 0, 0), ring) == pytest.approx(0.0, abs=1e-6)
    assert abs(out_of_plane_angle((0, 0, 5), ring)) == pytest.approx(90.0, abs=1e-6)


def test_crystal_reproduces_its_own_reference_geometry():
    """Der Kristall muss gegen seine eigenen Referenzwerte 0 Abweichung geben."""
    atoms = load_structure(THEO)
    r = check_approach_geometry(atoms, CONTACTS, max_deviation=1.0)
    assert r.passed is True, r.reason
    assert r.extra["worst_deviation"] < 1.0
    assert r.value["base"]["angle"] == pytest.approx(133.1, abs=0.2)
    assert r.value["donor"]["out_of_plane"] == pytest.approx(-10.4, abs=0.2)


def test_worse_of_the_two_decides_not_the_mean():
    """Ein guter Winkel darf eine schlechte Ebene NICHT ausgleichen."""
    atoms = load_structure(THEO)
    r = check_approach_geometry(atoms, CONTACTS, max_deviation=0.01)
    assert r.passed is False  # selbst winzige Abweichung faellt durch, kein Mitteln


def test_missing_atom_is_unevaluated():
    atoms = load_structure(THEO)
    r = check_approach_geometry(atoms, [("base", "A999", "CG", "OD2")])
    assert r.passed is None


def test_burial_counts_ca_within_12A():
    """Das Theozym hat nur 3 Reste, also fast kein Burial - Gate muss anschlagen."""
    atoms = load_structure(THEO)
    n = base_burial(atoms, "A127")
    assert 0 <= n <= 5
    assert check_base_burial(atoms, "A127", min_ca=45).passed is False
    assert check_base_burial(atoms, "A999").passed is None
