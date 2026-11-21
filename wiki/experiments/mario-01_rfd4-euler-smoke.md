# mario-01: RFD4-Proteina smoke test on Euler

- **Owner:** mario
- **Date:** 2026-11-21
- **Status:** done: supported
- **Question:** Can one RFD4-Proteina design be generated on Euler end to end, and refolded by the OpenFold3 oracle: `sbatch` → RFD4 venv → `rfd4-generate` → a design file → OpenFold3 refold (pLDDT, scRMSD) → a run directory with a summary?
- **Why it matters:** Nothing else in the campaign works until this does. A failure shows which stage breaks (GPU request and driver, `eth_proxy` and the weight download, the venv, the output path, the oracle container and weights).
- **Script + config:** `scripts/10_generate_smoke_design.py` + `configs/mario-01.json`
- **Runs:** seven run directories under `$SCRATCH/kemp/runs/` on Euler (table under Result); the successful oracle runs are `20261121-181403_mario-01` and `20261121-181418_mario-01`, both at commit `bcda7ea`.

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
Read from the run directories' `meta.json`, `summary.json` and job logs (2026-11-21):

| Run (`runs/…_mario-01`) | Commit | GPU | Outcome |
|---|---|---|---|
| `161421` | `2a3b7af` | RTX 2080 Ti | bf16 failed in the first forward pass: `RuntimeError: Invalid backend` (`F.scaled_dot_product_attention`) |
| `174521` | `1ba1129` | TITAN RTX | the same error |
| `175756` | `1ba1129` | none: "No devices were found" | stopped by the script's GPU check; cause not found |
| `175810` | `1ba1129` | RTX PRO 6000 Blackwell (97887 MiB) | generation OK (progress bar 0:20), no oracle |
| `181403` | `bcda7ea` | A100 80GB PCIe | generation and OpenFold3 refold OK: pLDDT 73.62, scRMSD 9.03 |
| `181418` | `bcda7ea` | RTX PRO 6000 Blackwell | generation and OpenFold3 refold OK: pLDDT 78.98, scRMSD 2.06 |

The two Turing cards (2080 Ti, TITAN RTX) failed in bf16; the Ampere and Blackwell cards worked. A design file exists
in every successful run, and the OpenFold3 oracle ran with the defaults of `envs/euler.sh` (no preflight warning), so
`apptainer`, the image and the weights are in place on Euler. Every run's `summary.json` still says `ok: false` and
`n_design_files: 0`: the script looked for the design directly in `inference_samples/`, but RFD4 writes it to
`inference_samples/<example>/<example>_generated.cif`; fixed in `find_designs` (commit after `4182845`).

Same seed, different GPUs: the designs agree (CA RMSD 0.00–0.10 Å between the A100, Blackwell and 2080 Ti fp32 designs, see
[mario-02](mario-02_rfd4-rtx2080ti-fp32.md)), but the two refolds of that design differ a lot (scRMSD 9.03 vs 2.06, pLDDT
73.6 vs 79.0), so one refold of one design says little. The design is 61–62 % Glu (the first 30 residues are all E).
RFD4's pass criterion for unconditional designs is scRMSD ≤ 1.5 ([metrics reference](https://github.com/RosettaCommons/RFD4-Proteina)); neither refold meets it.

## Verdict and next step
Supported: one design is generated on Euler, refolded by OpenFold3, and the metrics come back, on GPUs with at least
35 GB (A100, RTX PRO 6000). Not covered: Kemp conditioning (`results/theozymes/`), the Kemp scoring, a second refold
seed. Next: [theozyme-inputs.md](../theozyme-inputs.md) on Euler, and more than one refold per design.
