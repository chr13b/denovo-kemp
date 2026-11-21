"""Filters: verified against real structures and an independent reference where possible."""

from __future__ import annotations

import json

import pytest

from kemp.filters import (
    all_passed,
    check_boltz_confidence,
    check_catalytic_residues,
    check_gravy,
    check_mpnn_score,
    check_no_reactive_in_pocket,
    gravy,
    isoelectric_point,
    parse_ligandmpnn_fasta,
    split_residue_id,
    unevaluated,
)
from kemp.paths import RESULTS

THEOZYME = RESULTS / "theozyme" / "theozyme_7k4u_core.pdb"
HG3_FASTA = RESULTS / "affinity" / "hg3.fasta"


def _hg3() -> str:
    lines = HG3_FASTA.read_text(encoding="utf-8-sig").splitlines()
    return "".join(ln.strip() for ln in lines if ln.strip() and not ln.startswith(">"))


# ------------------------------------------------------------------ the None state


def test_unevaluated_is_not_a_pass():
    """The whole point: 'not measured' must never read as 'passed'."""
    r = unevaluated("x", "file missing")
    assert r.passed is None
    assert not all_passed([r])


def test_all_passed_requires_every_filter():
    good = check_gravy("AAAA", -5, 5)
    assert good.passed is True
    assert all_passed([good])
    assert not all_passed([good, unevaluated("y", "nope")])
    assert not all_passed([])


# ------------------------------------------------------------------ sequence maths


def test_gravy_matches_hand_computation():
    # Kyte-Doolittle: I=4.5, V=4.2 -> mean 4.35
    assert gravy("IV") == pytest.approx(4.35)
    # all-Arg is the hydrophilic extreme
    assert gravy("RRRR") == pytest.approx(-4.5)


def test_gravy_rejects_non_standard_residues():
    with pytest.raises(ValueError, match="non-standard"):
        gravy("AAXA")


def test_isoelectric_point_ordering_is_physical():
    """Acidic sequences must have a lower pI than basic ones."""
    acidic = isoelectric_point("DDDDEEEE")
    neutral = isoelectric_point("AAAAGGGG")
    basic = isoelectric_point("KKKKRRRR")
    assert acidic < neutral < basic
    assert acidic < 5.0
    assert basic > 9.5


def test_isoelectric_point_of_a_real_protein_is_sane():
    pi = isoelectric_point(_hg3())
    assert 3.0 < pi < 10.0


def test_gravy_matches_biopython_on_real_sequences():
    """Pins the cross-check: Biopython 1.84 gave these GRAVY values exactly.

    Verified on the cluster 2026-11-21 (Biopython is not a dependency here, so the
    reference numbers are pinned rather than recomputed).
    """
    assert gravy(_hg3()) == pytest.approx(-0.0767, abs=1e-4)


def test_isoelectric_point_uses_the_emboss_convention():
    """Ours is EMBOSS; Biopython defaults to Bjellqvist and reads ~0.1-0.25 higher.

    Pinned so a future edit to the pKa table cannot silently change the convention.
    """
    assert isoelectric_point(_hg3()) == pytest.approx(5.294, abs=0.01)  # Biopython: 5.378


def test_gravy_of_a_real_soluble_protein_is_negative():
    """HG3 is a soluble globular enzyme, so GRAVY should be mildly negative."""
    assert -1.0 < gravy(_hg3()) < 0.3


# ------------------------------------------------------------- active-site checks


def test_catalytic_residues_detects_mutation():
    seq = "ACDEFG"
    assert check_catalytic_residues(seq, {3: "D"}).passed is True
    bad = check_catalytic_residues(seq, {3: "E"})
    assert bad.passed is False
    assert "3" in bad.reason


def test_catalytic_residue_out_of_range_is_unevaluated():
    assert check_catalytic_residues("ACD", {99: "D"}).passed is None


def test_reactive_residue_in_pocket_is_caught():
    seq = "AACAA"
    assert check_no_reactive_in_pocket(seq, [3]).passed is False
    assert check_no_reactive_in_pocket(seq, [1, 2]).passed is True
    assert check_no_reactive_in_pocket(seq, []).passed is None


# ------------------------------------------------------------------ score parsing


def test_parse_ligandmpnn_fasta(tmp_path):
    fa = tmp_path / "seqs.fa"
    fa.write_text(
        ">id=1, T=0.1, seed=4, overall_confidence=0.4197, ligand_confidence=0.4447, seq_rec=0.3023\n"
        "MKVLA\nAGIVG\n"
        ">id=2, T=0.1, seed=5, overall_confidence=0.51, ligand_confidence=0.55, seq_rec=0.40\n"
        "MKVLW\n",
        encoding="utf-8",
    )
    recs = parse_ligandmpnn_fasta(fa)
    assert len(recs) == 2
    assert recs[0]["sequence"] == "MKVLAAGIVG"  # multi-line sequence joined
    assert recs[0]["overall_confidence"] == pytest.approx(0.4197)
    assert recs[1]["seed"] == pytest.approx(5)


def test_mpnn_score_gate():
    rec = {"overall_confidence": 0.42, "ligand_confidence": 0.44}
    assert check_mpnn_score(rec, 0.35, 0.35).passed is True
    assert check_mpnn_score(rec, 0.50, 0.35).passed is False
    assert check_mpnn_score({"sequence": "A"}, 0.3, 0.3).passed is None


def test_boltz_confidence_normalises_the_plddt_scale():
    """Boltz writes pLDDT in 0-1; thresholds are quoted on 0-100."""
    r = check_boltz_confidence({"complex_plddt": 0.90, "iptm": 0.8}, min_plddt=85.0)
    assert r.passed is True
    assert r.value["complex_plddt"] == pytest.approx(90.0)
    low = check_boltz_confidence({"complex_plddt": 0.77, "iptm": 0.8}, min_plddt=85.0)
    assert low.passed is False
    assert check_boltz_confidence({}, 85.0).passed is None


def test_boltz_confidence_fails_on_low_iptm():
    r = check_boltz_confidence({"complex_plddt": 0.95, "iptm": 0.35}, 85.0, 0.6)
    assert r.passed is False
    assert "ipTM" in r.reason


def test_split_residue_id():
    assert split_residue_id("A127") == ("A", 127)
    with pytest.raises(ValueError):
        split_residue_id("oops")


# ------------------------------------------------------- structure filters (real file)

pytest.importorskip("biotite")


def test_structure_filters_on_the_real_theozyme():
    """Exercises the biotite API against a file actually in the repo."""
    from kemp.structure import (
        check_ligand_contacts,
        check_motif_rmsd,
        load_structure,
        radius_of_gyration,
    )

    atoms = load_structure(THEOZYME)
    assert len(atoms) > 0

    # the theozyme is 3 residues + ligand, so RoG is small but must be computable
    assert radius_of_gyration(atoms) > 0

    # a structure compared with itself must give exactly zero motif RMSD
    spec = {"A127": ("OD1", "CG", "OD2"), "A50": ("OE1", "CD", "NE2")}
    same = check_motif_rmsd(atoms, atoms, spec, max_rmsd=1.0)
    assert same.passed is True
    assert same.value == pytest.approx(0.0, abs=1e-6)

    # the crystal contacts: OD2->N3 is 2.53 A, NE2->N1 is 3.20 A
    contacts = check_ligand_contacts(atoms, [("A127", "OD2", "N3", 2.4, 3.4), ("A50", "NE2", "N1", 2.6, 3.4)])
    assert contacts.passed is True
    assert contacts.value["A127_OD2_to_N3"] == pytest.approx(2.53, abs=0.01)
    assert contacts.value["A50_NE2_to_N1"] == pytest.approx(3.20, abs=0.01)


def test_missing_motif_atom_is_unevaluated_not_failed():
    from kemp.structure import check_motif_rmsd, load_structure

    atoms = load_structure(THEOZYME)
    r = check_motif_rmsd(atoms, atoms, {"A999": ("CA",)}, max_rmsd=1.0)
    assert r.passed is None


def test_contacts_out_of_window_fail():
    from kemp.structure import check_ligand_contacts, load_structure

    atoms = load_structure(THEOZYME)
    # demand an impossibly short contact: 2.53 A must fall outside [1.0, 1.5]
    r = check_ligand_contacts(atoms, [("A127", "OD2", "N3", 1.0, 1.5)])
    assert r.passed is False
    assert "outside" in r.reason


def test_verdict_record_is_json_serialisable():
    """The driver writes FilterResult.as_dict() to JSONL - it must survive json.dumps."""
    r = check_gravy("AAAA")
    assert json.loads(json.dumps(r.as_dict()))["name"] == "gravy"
