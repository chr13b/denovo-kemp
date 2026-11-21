"""The mario-01 smoke script: the rfd4-generate command, the oracle preflight, the metrics readout."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def mod():
    spec = importlib.util.spec_from_file_location(
        "smoke_design", ROOT / "scripts/10_generate_smoke_design.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_command_with_and_without_oracle(mod, tmp_path):
    with_oracle = mod.build_command(mod.Config(), tmp_path)
    assert "metrics/refolding_oracles=of3" in with_oracle
    assert "metrics_tags=[design,unconditional_refolding]" in with_oracle
    assert "~metrics" not in with_oracle
    without = mod.build_command(mod.Config(oracle=""), tmp_path)
    assert "~metrics" in without
    assert not any(a.startswith(("metrics/", "metrics_tags")) for a in without)


def test_overrides_are_split_like_a_shell_line(mod, tmp_path):
    cfg = mod.Config(oracle="", overrides="precision='\"32\"' nn.attention_type=torch batch_size=1")
    cmd = mod.build_command(cfg, tmp_path)
    assert cmd[-3:] == ['precision="32"', "nn.attention_type=torch", "batch_size=1"]  # quotes kept for Hydra
    assert mod.build_command(mod.Config(oracle=""), tmp_path)[-1] == "~metrics"  # no overrides, nothing added


def test_find_designs_looks_in_the_example_folder(mod, tmp_path):
    assert mod.find_designs(tmp_path / "missing") == []
    folder = tmp_path / "inference_samples" / "monomer-short"
    folder.mkdir(parents=True)
    for name in (
        "monomer-short_generated.cif",
        "monomer-short_of3_refolded.cif",
        "monomer-short_of3_confidences.json",
    ):
        (folder / name).write_text("")
    found = mod.find_designs(tmp_path / "inference_samples")
    assert [p.name for p in found] == [
        "monomer-short_generated.cif"
    ]  # the refold and its confidences do not count


@pytest.fixture
def oracle_env(tmp_path, monkeypatch):
    """A complete oracle setup: apptainer on PATH, image and weights present, cache dir set."""
    weights = tmp_path / "weights"
    weights.mkdir()
    (weights / "of3_ported_weights.provenance.json").write_text("{}")
    image = tmp_path / "of3.sif"
    image.write_text("")
    monkeypatch.setenv("AF3_IMAGE", str(image))
    monkeypatch.setenv("AF3_MODEL_DIR", str(weights))
    monkeypatch.setenv("AF3_JAX_CACHE_DIR", str(tmp_path / "cache"))
    return weights


def test_oracle_preflight(mod, oracle_env, monkeypatch):
    monkeypatch.setattr(mod.shutil, "which", lambda name: "/usr/bin/" + name)
    assert mod.check_oracle("of3") is None
    assert "must be" in mod.check_oracle("boltz")
    (oracle_env / "of3_ported_weights.provenance.json").unlink()
    assert "OpenFold3" in mod.check_oracle("of3")  # AF3 weights would be mistaken for OpenFold3 otherwise
    assert mod.check_oracle("af3") is None
    monkeypatch.setenv("AF3_IMAGE", "/does/not/exist.sif")
    assert "AF3_IMAGE" in mod.check_oracle("af3")
    monkeypatch.setattr(mod.shutil, "which", lambda name: None)
    assert "apptainer" in mod.check_oracle("af3")


def test_oracle_metrics_readout(mod, tmp_path):
    assert mod.read_oracle_metrics(tmp_path) == {}  # no CSV yet
    csv_dir = tmp_path / "inference_metrics"
    csv_dir.mkdir()
    (csv_dir / "per_example_metrics.csv").write_text(
        "example_id,oracle.overall_plddt,refolded_backbone_rmsd.rmsd,clash_metrics.x,oracle.note\n"
        "monomer-short,81.5,1.2,0.0,ok\n"
    )
    assert mod.read_oracle_metrics(tmp_path) == {
        "oracle.overall_plddt": 81.5,
        "refolded_backbone_rmsd.rmsd": 1.2,
        "oracle.note": "ok",
    }
