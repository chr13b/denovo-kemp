"""The affinity ladder: unit conversion, YAML shape, and the report's grouping."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from kemp.ligands import KCAL_PER_LOG10, LADDER, LIGANDS, REFERENCE, ddg_kcal, pseudo_dg_kcal
from kemp.paths import ROOT


def test_ladder_ligands_are_mass_and_size_matched():
    """The comparison only means something if the three ligands are matched.

    Verified with RDKit: identical formula mass and heavy-atom count, so Boltz-2's
    molecular-weight correction cannot explain a difference between them.
    """
    assert set(LADDER) == set(LIGANDS)
    assert REFERENCE in LIGANDS
    keys = {lig.inchikey for lig in LIGANDS.values()}
    assert len(keys) == 3, "the three ligands must be distinct compounds"
    # the TS analogue must stay the same compound as CCD 6NT
    assert LIGANDS["ts_analog"].inchikey == "AOCDQWRMYHJTMY-UHFFFAOYSA-N"


def test_one_decade_is_1_364_kcal():
    assert KCAL_PER_LOG10 == pytest.approx(1.3642, abs=5e-4)


def test_pseudo_dg_uses_micromolar_offset():
    # value 6 means IC50 = 1e6 uM = 1 M, i.e. dG = 0
    assert pseudo_dg_kcal(6.0) == pytest.approx(0.0, abs=1e-12)
    # one decade tighter is one RTln10 more negative
    assert pseudo_dg_kcal(5.0) == pytest.approx(-KCAL_PER_LOG10)


def test_ddg_sign_convention_positive_means_weaker():
    # ligand with the HIGHER log10(IC50) binds more weakly -> positive ddG
    assert ddg_kcal(5.0, 4.0) == pytest.approx(KCAL_PER_LOG10)
    assert ddg_kcal(4.0, 5.0) == pytest.approx(-KCAL_PER_LOG10)
    assert ddg_kcal(3.3, 3.3) == pytest.approx(0.0)


def test_ddg_is_independent_of_the_micromolar_offset():
    """A difference must not depend on the unit offset, or the ladder is arbitrary."""
    a, b = 4.2, 3.1
    assert ddg_kcal(a, b) == pytest.approx(pseudo_dg_kcal(a) - pseudo_dg_kcal(b))


def _run(script: str, *args: str, runs_dir: Path) -> subprocess.CompletedProcess:
    """Run a script with its run directory redirected into the test's tmp_path.

    paths.py honours KEMP_RUNS_DIR, so this keeps the suite out of the real runs/
    and gives every test its own namespace - two tests sharing a run name in the
    same second would otherwise collide on start_run's exist_ok=False mkdir.
    """
    env = {**os.environ, "KEMP_RUNS_DIR": str(runs_dir)}
    return subprocess.run(
        [sys.executable, str(ROOT / "scripts" / script), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )


def test_builder_writes_one_yaml_per_ligand_and_seed(tmp_path):
    res = _run(
        "20_build_affinity_ladder.py",
        "--label=unit",
        "--sequence=MKVLAAGIVGW",
        "--seeds=2",
        runs_dir=tmp_path,
    )
    assert res.returncode == 0, res.stderr
    run_dir = Path(res.stdout.splitlines()[0].removeprefix("[run] ").strip())
    try:
        yamls = sorted((run_dir / "bundle" / "yaml").glob("*.yaml"))
        assert len(yamls) == 3 * 2
        spec = yaml.safe_load(yamls[0].read_text())
        assert spec["version"] == 1
        # exactly one affinity binder, pointing at the ligand chain
        assert spec["properties"] == [{"affinity": {"binder": "B"}}]
        ligand = next(s["ligand"] for s in spec["sequences"] if "ligand" in s)
        assert ligand["id"] == "B"
        assert ligand["smiles"] in {lig.smiles for lig in LIGANDS.values()}
        protein = next(s["protein"] for s in spec["sequences"] if "protein" in s)
        assert protein["sequence"] == "MKVLAAGIVGW"
        assert protein["msa"] == "empty"
        # the launcher must never try to reach the network for weights
        sbatch = (run_dir / "bundle" / "run.sh").read_text()
        assert "boltz2_aff.ckpt" in sbatch
        assert "--cache" in sbatch
        assert "l4big" not in sbatch, "the l4big queue must never be used"
        # Slurm runs the script from /var/spool/slurmd/jobNNNN, so the bundle path
        # must come from SLURM_SUBMIT_DIR, never from BASH_SOURCE (that failed once).
        assert "SLURM_SUBMIT_DIR" in sbatch
        assert "BASH_SOURCE" not in sbatch
        meta = json.loads((run_dir / "bundle" / "ladder.json").read_text())
        assert meta["length"] == 11
    finally:
        pass


def test_builder_reads_a_fasta_with_a_bom(tmp_path):
    """A BOM must not turn the FASTA header into sequence (it did once, loudly)."""
    fa = tmp_path / "bom.fasta"
    fa.write_text(">header line\nMKVLAAG\n", encoding="utf-8-sig")
    assert fa.read_bytes().startswith(b"\xef\xbb\xbf")
    res = _run(
        "20_build_affinity_ladder.py",
        "--label=unit",
        f"--fasta={fa}",
        "--seeds=1",
        runs_dir=tmp_path,
    )
    assert res.returncode == 0, res.stdout + res.stderr
    run_dir = Path(res.stdout.splitlines()[0].removeprefix("[run] ").strip())
    meta = json.loads((run_dir / "bundle" / "ladder.json").read_text())
    assert meta["sequence"] == "MKVLAAG"


def test_builder_rejects_a_bad_sequence(tmp_path):
    res = _run(
        "20_build_affinity_ladder.py",
        "--label=unit",
        "--sequence=MKVLXZ",
        runs_dir=tmp_path,
    )
    assert res.returncode != 0
    assert "non-standard" in (res.stdout + res.stderr)


def test_builder_rejects_an_unknown_ligand(tmp_path):
    res = _run(
        "20_build_affinity_ladder.py",
        "--label=unit",
        "--sequence=MKVL",
        "--ligands=['substrate','nope']",
        runs_dir=tmp_path,
    )
    assert res.returncode != 0
    assert "unknown ligand" in (res.stdout + res.stderr)
