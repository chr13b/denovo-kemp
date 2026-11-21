"""envs/euler.sh: the AF3/OpenFold3 settings, and the extra ones for GPUs below compute capability 8.0."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def source_env(tmp_path: Path, compute_cap: str | None, **env: str) -> dict[str, str]:
    """Source envs/euler.sh under `set -euo pipefail` with a fake nvidia-smi and HOME; return the settings."""
    home = tmp_path / "home"
    (home / "rfd4-proteina/.venv/bin").mkdir(parents=True)
    (home / "rfd4-proteina/.venv/bin/activate").write_text(": \n")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    if compute_cap is not None:
        smi = bin_dir / "nvidia-smi"
        smi.write_text(f"#!/bin/bash\necho {compute_cap}\n")
        smi.chmod(0o755)
    show = 'echo "flash=${AF3_FLASH_ATTENTION_IMPLEMENTATION:-}"; echo "xla=${XLA_FLAGS:-}"'
    script = f"set -euo pipefail; source {ROOT}/envs/euler.sh; {show}"
    out = subprocess.run(
        ["bash", "-c", script],
        capture_output=True,
        text=True,
        check=True,
        env={
            "PATH": f"{bin_dir}:/usr/bin:/bin",
            "HOME": str(home),
            "SCRATCH": str(tmp_path / "scratch"),
            **env,
        },
    )
    return dict(line.split("=", 1) for line in out.stdout.splitlines() if "=" in line)


def test_turing_gets_the_xla_settings(tmp_path):
    got = source_env(tmp_path, "7.5")
    assert got["flash"] == "xla"
    assert got["xla"] == "--xla_disable_hlo_passes=custom-kernel-fusion-rewriter"


@pytest.mark.parametrize("cap", ["8.0", "12.0", None])  # A100, Blackwell, no GPU (nvidia-smi missing)
def test_other_gpus_are_left_alone(tmp_path, cap):
    got = source_env(tmp_path, cap)
    assert got["flash"] == "" and got["xla"] == ""


def test_user_settings_win_and_are_not_duplicated(tmp_path):
    got = source_env(tmp_path, "7.5", AF3_FLASH_ATTENTION_IMPLEMENTATION="triton", XLA_FLAGS="--foo")
    assert got["flash"] == "triton"
    assert got["xla"] == "--foo --xla_disable_hlo_passes=custom-kernel-fusion-rewriter"
