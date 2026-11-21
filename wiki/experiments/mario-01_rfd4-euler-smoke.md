# mario-01: RFD4-Proteina smoke test on Euler

- **Owner:** mario
- **Date:** 2026-11-21
- **Status:** planned
- **Question:** Can one RFD4-Proteina design be generated on Euler end to end: `sbatch` → RFD4 venv → `rfd4-generate` → a design file → a run directory with a summary?
- **Why it matters:** Nothing else in the campaign works until this does. A failure shows which stage breaks (GPU request and driver, `eth_proxy` and the weight download, the venv, the output path).
- **Script + config:** `scripts/10_generate_smoke_design.py` + `configs/mario-01.json`
- **Runs:** not run yet. It will be `$SCRATCH/kemp/runs/<timestamp>_mario-01/` on Euler; record the commit and Slurm job ID here.

Status values: `planned`, `running`, `done: supported`, `done: refuted`, `done: inconclusive`, `abandoned`.

## What it does

On Euler, after `git pull`:

```bash
mkdir -p "$SCRATCH/kemp/logs"
sbatch --time=01:00:00 --job-name=mario-01 scripts/euler_job.sbatch \
    python scripts/10_generate_smoke_design.py configs/mario-01.json
```

It runs `rfd4-generate inputs=data/benchmarks/monomer subset_to_examples=monomer-short num_replicates=1 seed=0 '~metrics'
compile_lengths=null` from the RFD4-Proteina checkout: one unconditional 100-residue monomer, no refolding, no
`torch.compile` warm-up ([RFD4-Proteina README](https://github.com/RosettaCommons/RFD4-Proteina)). Before that it checks that
`rfd4-generate` is on the PATH, that the checkout has `.project-root`, and that torch sees a GPU. Afterwards it counts the
design files under `inference_samples/`, reads the sequence from the first one if it is a plain `.cif`, and writes
`env_packages.txt` (every package version in the venv) next to the usual `meta.json` and `summary.json`.

It does not test Kemp conditioning (annotated CIF, `base=` / `oxy=`), scoring or the submission file.

## Not verified yet

- The script's logic was tested only against a stub `rfd4-generate` (arguments, working directory, success, failure, empty and compressed output); the real model has not been run.
- That the RFD4-Proteina checkout is `~/rfd4-proteina` (inferred from the venv path; set `--rfd4_root` otherwise), that designs are written as plain `.cif` files in `inference_samples/` (from the README), and that the weights are cached or reachable through `eth_proxy`.
- Whether the driver on the GPU nodes Slurm picks suits the build: the README asks for a CUDA 13-compatible driver (CUDA 12 containers also exist).

## Result

Not run yet. Only numbers read from the run's `summary.json` go here.

## Verdict and next step

TODO
