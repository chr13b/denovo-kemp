# mario-01: RFD4-Proteina smoke test on Euler

- **Owner:** mario
- **Date:** 2026-11-21
- **Status:** running (attempt 1 failed in the model, see Result)
- **Question:** Can one RFD4-Proteina design be generated on Euler end to end, and refolded by the OpenFold3 oracle: `sbatch` → RFD4 venv → `rfd4-generate` → a design file → OpenFold3 refold (pLDDT, scRMSD) → a run directory with a summary?
- **Why it matters:** Nothing else in the campaign works until this does. A failure shows which stage breaks (GPU request and driver, `eth_proxy` and the weight download, the venv, the output path, the oracle container and weights).
- **Script + config:** `scripts/10_generate_smoke_design.py` + `configs/mario-01.json`
- **Runs:** not run yet. It will be `$SCRATCH/kemp/runs/<timestamp>_mario-01/` on Euler; record the commit and Slurm job ID here.

Status values: `planned`, `running`, `done: supported`, `done: refuted`, `done: inconclusive`, `abandoned`.

## What it does

On Euler, after `git pull`:

```bash
mkdir -p "$SCRATCH/kemp/logs"
sbatch --time=02:00:00 --job-name=mario-01 scripts/euler_job.sbatch \
    python scripts/10_generate_smoke_design.py configs/mario-01.json
```

It runs `rfd4-generate inputs=data/benchmarks/monomer subset_to_examples=monomer-short num_replicates=1 seed=0
compile_lengths=null metrics/refolding_oracles=of3 'metrics_tags=[design,unconditional_refolding]'` from the
RFD4-Proteina checkout: one unconditional 100-residue monomer, no `torch.compile` warm-up, refolded by OpenFold3
([RFD4-Proteina README](https://github.com/RosettaCommons/RFD4-Proteina)). Before that it checks that `rfd4-generate`
is on the PATH, that the checkout has `.project-root`, that torch sees a GPU, and that the oracle is usable: `apptainer`
on the PATH, `AF3_IMAGE` and `AF3_MODEL_DIR` existing, `AF3_JAX_CACHE_DIR` set, and an
`of3_ported_weights.provenance.json` in the weights directory (RFD4 takes that file as the sign of OpenFold3 weights).
Afterwards it counts the design files under `inference_samples/`, reads the sequence from the first one if it is a plain
`.cif`, copies the `oracle.*` and `refolded_*` columns of `inference_metrics/per_example_metrics.csv` into `summary.json`
(the run fails if `oracle.overall_plddt` is missing), and writes `env_packages.txt` (every package version in the venv)
next to the usual `meta.json`. `--oracle=` (empty) skips refolding and scoring, which is the first version of this test.

It does not test Kemp conditioning (annotated CIF, `base=` / `oxy=`), the Kemp scoring or the submission file.

## Not verified yet

- The script's logic was tested only against a stub `rfd4-generate` (arguments, working directory, success, failure, empty and compressed output); the real model has not been run.
- That the RFD4-Proteina checkout is `~/rfd4-proteina` (inferred from the venv path; set `--rfd4_root` otherwise), that designs are written as plain `.cif` files in `inference_samples/` (from the README), and that the weights are cached or reachable through `eth_proxy`.
- Whether the driver on the GPU nodes Slurm picks suits the build: the README asks for a CUDA 13-compatible driver (CUDA 12 containers also exist).
- The oracle: `apptainer` on the compute nodes, the OpenFold3 image and weights (the paths in `envs/euler.sh` are RFD4's
  download-script defaults, not checked on Euler), and the metrics CSV location and column names (`oracle.overall_plddt`,
  `refolded_backbone_rmsd.rmsd`), which come from RFD4's docs and tutorial, not from a run.
- That `gpumem:35G` is accepted by Slurm and gives a GPU RFD4 supports (`sbatch --test-only` first).

## Result

**Attempt 1, 2026-11-21** (first version of the script: no oracle, `~metrics`, request `gpumem:24G`). The Slurm job
reached the model: the venv, Hydra, the checkpoint fetch (`Fetching 2 files`) and the input loading worked. It then
failed in the first encoder forward pass with `RuntimeError: Invalid backend` in `F.scaled_dot_product_attention`
(`pair_bias_attn.py`). The GPU the job got is not recorded here (it is in the job log's `[euler_job] gpu:` line). RFD4
lists A100, H100, L40S, RTX 6000 Ada and Blackwell GPUs as tested, so the request was raised to `gpumem:35G` to exclude
the 24 GB cards. The job also printed `CCD_MIRROR_PATH` / `PDB_MIRROR_PATH` not set warnings.

Attempt 2 (35 GB, OpenFold3 oracle): not run yet. Only numbers read from the run's `summary.json` go here.

## Verdict and next step

TODO
