"""The theozyme input builder: one design per candidate, the right atoms fixed, CIFs that match the PDBs."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CANDIDATES = ROOT / "pre_analysis/kemp_theozymes_v2/candidates"


def load_script():
    path = ROOT / "scripts/01_build_theozyme_inputs.py"
    spec = importlib.util.spec_from_file_location("build_theozyme_inputs", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def mod():
    return load_script()


def test_every_recommended_slot_has_one_ts_like_pdb(mod):
    for slot in mod.RECOMMENDED.split(","):
        files = [p for p in CANDIDATES.glob(f"{slot}__V*.pdb") if not p.stem.endswith("__michaelis")]
        assert len(files) == 1, slot


def test_read_candidate_policies(mod):
    ligand, motif, _ = mod.read_candidate(CANDIDATES / "A_top_observed__V00001.pdb")
    assert [r.name for r in motif] == ["ASP", "TRP", "MET", "GLN"]
    assert [r.policy for r in motif] == ["sidechain", "sidechain", "backbone", "sidechain"]
    assert len(ligand) == 12 and ligand[3][0] == "N3"  # 6NT, the scored base target
    assert motif[0].fixed == ["CA", "CB", "CG", "OD1", "OD2"]  # carboxylate base: CA + side chain, no N, C, O
    assert motif[2].fixed == ["N", "CA", "C", "O"]  # N-H donor: backbone only, identity left free


def test_unknown_residue_in_remark_fails(mod, tmp_path):
    with pytest.raises(SystemExit, match="no entry for MET"):
        mod.policy_from_remark("TRP: side chain + CA", "MET", tmp_path / "x.pdb")


def test_build_writes_spec_and_cifs(mod, tmp_path):
    cfg = mod.Config(out_dir=str(tmp_path), slots="A_top_observed,I_dyad", seg_min=100, seg_max=120)
    # main() writes a run directory through start_run; call the pieces it uses instead
    entries = []
    for slot in cfg.slots.split(","):
        pdb = next(p for p in CANDIDATES.glob(f"{slot}__V*.pdb") if not p.stem.endswith("__michaelis"))
        ligand, motif, remarks = mod.read_candidate(pdb)
        mod.write_cif(tmp_path / f"{pdb.stem}.cif", pdb.stem, ligand, motif)
        n_atoms = len(ligand) + sum(len(r.atoms) for r in motif)
        assert mod.check(tmp_path, pdb.stem, ligand, motif)["n_atoms"] == n_atoms
        entries.append(mod.design_entry(pdb.stem, f"{pdb.stem}.cif", motif, remarks, cfg))
    spec = "\n\n".join(entries)
    assert 'contig: "EX1:100-120, A1-4, /0, B1"' in spec  # V00001: 4 motif residues
    assert 'contig: "EX1:100-120, A1-3, /0, B1"' in spec  # dyad: His, Asp, Phe
    yaml = pytest.importorskip("yaml")
    design = yaml.safe_load(entries[0])["A_top_observed__V00001"]
    # YAML 1.1 reads the keys `true:` / `false:` as booleans; the spec's own examples are written that way
    seq = [e["select"] for e in design["conditions"]["C_SEQ"][True]]
    assert seq == [
        "sel('A/*/[1,2,4]')",
        "sel('B')",
    ]  # MET (3) stays free; the fixed 6NT needs its identity too
    assert {e["group"] for e in design["conditions"]["C_IDX"][False]} == {"res1", "res2", "res3", "res4"}


def test_length_limit_is_enforced(mod, tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "start_run", lambda *a, **k: None)  # no run directory for a failing call
    cfg = mod.Config(out_dir=str(tmp_path), slots="A_top_observed", seg_min=250, seg_max=258)
    with pytest.raises(SystemExit, match="the 260 limit"):
        mod.main(cfg)
