"""Smoke test: generate ONE design with RFD4-Proteina on Euler and check that the pipeline holds together.

    sbatch --time=02:00:00 --job-name=mario-01 scripts/euler_job.sbatch \\
        python scripts/10_generate_smoke_design.py configs/mario-01.json

Checks: `rfd4-generate` is on the PATH and a GPU is visible; one unconditional 100-residue monomer is
generated (`num_replicates=1`, no torch.compile warm-up); a design file exists and can be read; and the design
is refolded by the OpenFold3 oracle (`--oracle=of3`, the default), which needs apptainer, the oracle image
and the converted weights (`envs/euler.sh` sets AF3_IMAGE, AF3_MODEL_DIR, AF3_JAX_CACHE_DIR). The oracle's
pLDDT and the self-consistency RMSD are read from the metrics CSV into summary.json. `--oracle=` (empty)
skips refolding.
Does NOT check: Kemp conditioning (annotated CIF, base=/oxy=), the Kemp scoring, or the submission file.
Run it from the repo root inside the RFD4-Proteina venv (`envs/euler.sh` does that under Slurm).
"""

from __future__ import annotations

import csv
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from importlib import metadata
from pathlib import Path

from kemp.config import parse
from kemp.run import Run, start_run

THREE = "ALA ARG ASN ASP CYS GLN GLU GLY HIS ILE LEU LYS MET PHE PRO SER THR TRP TYR VAL".split()
THREE_TO_ONE = dict(zip(THREE, "ARNDCQEGHILKMFPSTWYV", strict=True))


@dataclass
class Config:
    name: str = "smoke-design"  # run directory suffix; use the experiment ID (configs/mario-01.json)
    seed: int = 0
    rfd4_root: str = "~/rfd4-proteina"  # RFD4-Proteina checkout: the directory that contains `.project-root`
    inputs: str = "data/benchmarks/monomer"  # relative to rfd4_root
    example: str = "monomer-short"  # one key of `inputs`: a 100-residue monomer
    num_replicates: int = 1
    oracle: str = "of3"  # refolding oracle: "of3" (OpenFold3), "af3", or "" to skip refolding and scoring
    metrics_tags: str = "design,unconditional_refolding"  # comma-separated; only used with an oracle


def check_oracle(oracle: str) -> str | None:
    """What is missing for the refolding oracle (an apptainer container, see wiki/euler-rfd4.md), or None."""
    if oracle not in ("of3", "af3"):
        return f"--oracle must be 'of3', 'af3' or empty (got {oracle!r})"
    if shutil.which("apptainer") is None:
        return "apptainer is not on PATH: the refolding oracle runs in a container"
    for var in ("AF3_IMAGE", "AF3_MODEL_DIR"):
        value = os.environ.get(var, "")
        if not value or not Path(value).exists():
            return f"{var}={value!r} does not exist (envs/euler.sh sets it; see wiki/euler-rfd4.md)"
    if not os.environ.get("AF3_JAX_CACHE_DIR"):
        return "AF3_JAX_CACHE_DIR is not set (envs/euler.sh sets it)"
    stamp = Path(os.environ["AF3_MODEL_DIR"]) / "of3_ported_weights.provenance.json"
    if (
        oracle == "of3" and not stamp.exists()
    ):  # RFD4 picks OpenFold3 from this file, otherwise it assumes AF3 weights
        return f"{stamp} is missing: AF3_MODEL_DIR does not hold converted OpenFold3 weights"
    return None


def check_environment(root: Path, oracle: str = "") -> str | None:
    """Return a description of what is wrong, or None if the environment looks usable."""
    if shutil.which("rfd4-generate") is None:
        return "rfd4-generate is not on PATH (is the RFD4-Proteina venv active? see envs/euler.sh)"
    if not (root / ".project-root").exists():
        return f"{root} has no .project-root: pass --rfd4_root=<the RFD4-Proteina checkout>"
    if oracle and (problem := check_oracle(oracle)):
        return problem
    try:
        import torch
    except ImportError:
        return None  # cannot look for a GPU from here; rfd4-generate fails loudly if there is none
    if not torch.cuda.is_available():
        return "torch cannot see a GPU (did the job request one, and does the driver match?)"
    return None


def write_packages(run: Run) -> int:
    """Record every installed package version (the RFD4 venv is outside this repo, so uv.lock misses it)."""
    pkgs = sorted(f"{d.metadata.get('Name', '?')}=={d.version}" for d in metadata.distributions())
    (run.dir / "env_packages.txt").write_text("\n".join(pkgs) + "\n", encoding="utf-8")
    return len(pkgs)


def git_commit(root: Path) -> str | None:
    if shutil.which("git") is None:
        return None
    out = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True, text=True)
    return out.stdout.strip() or None


def build_command(cfg: Config, out_dir: Path) -> list[str]:
    """The rfd4-generate command line (Hydra key=value arguments)."""
    cmd = [
        "rfd4-generate",
        f"inputs={cfg.inputs}",
        f"subset_to_examples={cfg.example}",
        f"num_replicates={cfg.num_replicates}",
        f"out_dir={out_dir}",
        f"seed={cfg.seed}",
        "compile_lengths=null",  # skip the torch.compile warm-up
    ]
    if cfg.oracle:
        cmd += [f"metrics/refolding_oracles={cfg.oracle}", f"metrics_tags=[{cfg.metrics_tags}]"]
    else:
        cmd.append("~metrics")  # skip scoring: no refolding environment needed
    return cmd


def generate(cfg: Config, root: Path, out_dir: Path, log_path: Path) -> int:
    """Run rfd4-generate from its repo root, streaming its output to the job log and to a file."""
    cmd = build_command(cfg, out_dir)
    print("[smoke] " + " ".join(cmd), flush=True)
    with open(log_path, "w", encoding="utf-8") as log:
        proc = subprocess.Popen(cmd, cwd=root, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in proc.stdout or []:
            sys.stdout.write(line)
            log.write(line)
        return proc.wait()


def read_oracle_metrics(out_dir: Path) -> dict[str, float | str]:
    """Oracle and refolding columns of the first row of per_example_metrics.csv ({} if there is none)."""
    path = out_dir / "inference_metrics" / "per_example_metrics.csv"
    if not path.is_file():
        return {}
    with open(path, newline="", encoding="utf-8") as f:
        row = next(csv.DictReader(f), None) or {}
    out: dict[str, float | str] = {}
    for key, val in row.items():
        if key.startswith(("oracle.", "refolded_")):
            try:
                out[key] = float(val)
            except ValueError:
                out[key] = val
    return out


def read_sequences(path: Path) -> dict[str, str]:
    """One-letter sequence per chain from the CA atoms of the first model of a plain mmCIF (stdlib only)."""
    cols: list[str] = []
    seqs: dict[str, list[str]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("_atom_site."):
            cols.append(line.split(".", 1)[1].strip())
        elif cols and line.startswith(("loop_", "#", "_")):
            break  # the atom_site loop has ended
        elif cols and line.strip():
            row = dict(zip(cols, line.split(), strict=False))
            is_residue = row.get("group_PDB") == "ATOM" and row.get("label_atom_id") == "CA"
            if (
                is_residue
                and row.get("pdbx_PDB_model_num", "1") == "1"
                and row.get("label_comp_id") in THREE_TO_ONE
            ):
                seqs.setdefault(row.get("label_asym_id", "?"), []).append(THREE_TO_ONE[row["label_comp_id"]])
    return {chain: "".join(aa) for chain, aa in seqs.items()}


def main(cfg: Config) -> None:
    root = Path(cfg.rfd4_root).expanduser().resolve()
    run = start_run(cfg.name, cfg, seed=cfg.seed)
    n_packages = write_packages(run)
    problem = check_environment(root, cfg.oracle)
    if problem:
        run.finish(ok=False, problem=problem, n_env_packages=n_packages)
        raise SystemExit(f"smoke: {problem}")

    out_dir = run.dir / "rfd4"
    exit_code = generate(cfg, root, out_dir, run.dir / "rfd4_generate.log")
    samples = out_dir / "inference_samples"
    designs = sorted(p for p in samples.glob("*") if p.is_file()) if samples.is_dir() else []

    summary: dict = {
        "exit_code": exit_code,
        "n_design_files": len(designs),
        "design_files": [p.name for p in designs],
        "n_env_packages": n_packages,
        "rfd4_commit": git_commit(root),
    }
    plain = [p for p in designs if p.suffix == ".cif"]
    if plain:
        chains = read_sequences(plain[0])
        summary["first_design"] = {c: {"length": len(s), "sequence": s} for c, s in chains.items()}
    elif designs:
        summary["first_design"] = f"not parsed: {designs[0].name} is not a plain .cif"
    ok = exit_code == 0 and len(designs) >= 1
    if cfg.oracle:
        summary["oracle"] = cfg.oracle
        summary["oracle_metrics"] = read_oracle_metrics(out_dir)
        ok = ok and "oracle.overall_plddt" in summary["oracle_metrics"]  # the refold produced a score
    run.finish(ok=ok, **summary)
    if not ok:
        raise SystemExit(
            f"smoke: rfd4-generate exit code {exit_code}, {len(designs)} design file(s) in {samples}, "
            f"oracle metrics: {summary.get('oracle_metrics', 'not requested')}"
        )


if __name__ == "__main__":
    main(parse(Config))
