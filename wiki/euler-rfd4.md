# Running on Euler with RFD4-Proteina

Our stack, as of 2026-11-21: design campaigns run on **Euler** (ETH Zurich's HPC cluster, Slurm) with
**RFD4-Proteina**. We do not use the AWS cluster the organizers provided, nor RFD3 or LigandMPNN. The decision is
recorded in [decisions.md](decisions.md). Scoring is unchanged: the organizers cofold each submitted sequence
with 6NT in Boltz-2 ([challenge.md](challenge.md)).

## Compute rule: check before relying on Euler
The organizers ask teams to use **only the provided computing resources** "for fairness reasons"
([raw/20261121_organizers_cluster-guide.md](../raw/20261121_organizers_cluster-guide.md), and the Compute row in
[challenge.md](challenge.md)). Euler is not the provided cluster. Whether designs generated on Euler are eligible
is an open question in [challenge.md](challenge.md); get an answer from the organizers before building the
submission on Euler output.

## How we work
1. Edit and test small things locally; the heavy work never runs on a laptop.
2. Commit and push the branch (`make check` first).
3. On Euler, pull that branch.
4. Run the scripts through Slurm (`sbatch`). Outputs go to `runs/` on Euler (gitignored); small curated results come
   back into `results/` through git.

## Submitting a job
From the repo root on Euler, after `git pull`:

```bash
mkdir -p "$SCRATCH/kemp/logs"    # must exist before you submit, or the job leaves no log
sbatch scripts/euler_job.sbatch <command> [args...]    # e.g. python scripts/NN_verb_noun.py --seed=0
```

The template ([../scripts/euler_job.sbatch](../scripts/euler_job.sbatch)) asks for one GPU with at least 35 GB of memory (`--gpus=1` and `--gres=gpumem:35G`, which keeps out the 24 GB cards RFD4-Proteina does not list as supported) for
24 hours, loads the `eth_proxy` module on startup, and writes everything under `$SCRATCH/kemp`: `runs/` and `data/`
through `KEMP_RUNS_DIR` / `KEMP_DATA_DIR`, and the job log in `logs/`. It prints the commit and GPU into the log, sources
[../envs/euler.sh](../envs/euler.sh) (which activates the RFD4-Proteina venv, `$HOME/rfd4-proteina/.venv`) and puts
`src/` on `PYTHONPATH` so `import kemp` works there. Run scripts with plain `python`, not `uv run`, which would use the
repo's own environment instead of that venv. Record the job ID and run directory on the experiment page.

## First test
[experiments/mario-01_rfd4-euler-smoke.md](experiments/mario-01_rfd4-euler-smoke.md): one unconditional monomer through
the whole path, with the exact command and what is still unverified. Run it before anything larger.
[experiments/mario-02_rfd4-rtx2080ti-fp32.md](experiments/mario-02_rfd4-rtx2080ti-fp32.md) tries the same on an RTX 2080 Ti
(not a GPU RFD4 lists as supported) in full precision, through [../scripts/euler_job_rtx2080.sbatch](../scripts/euler_job_rtx2080.sbatch).

## Euler facts the template relies on
From the ETH HPC docs, read 2026-11-21: [Slurm](https://docs.hpc.ethz.ch/batchsystem/slurm/),
[GPU nodes](https://docs.hpc.ethz.ch/hardware/gpu_nodes/), [storage](https://docs.hpc.ethz.ch/hardware/storage/),
[conda](https://docs.hpc.ethz.ch/software/package-managers/conda/).
- GPUs: `--gpus=[type:]<n>`, GPU memory with `--gres=gpumem:<size>`. Types: `rtx_6000`, `nvidia_titan_rtx`, `a100`,
  `a100_80gb`, `rtx_2080`, `rtx_3090`, `rtx_4090`, `pro_6000`. The docs say the RTX Pro 6000 must be requested
  explicitly and CUDA-12-compiled programs will not run on it.
- GPU nodes are only available to shareholders; the docs do not say how anyone else gets access.
- `--time` defaults to 1 hour, `--mem-per-cpu` is per core, and the job log is `slurm-%j.out` unless set.
- `$SCRATCH` (`/cluster/scratch/<user>`): 2.5 TB, no backup, files older than 15 days are deleted. `$HOME`: 50 GB and
  500,000 files, backed up. `$TMPDIR` is node-local and deleted when the job ends.
- Conda: avoid the Lustre work directory; the docs suggest an Apptainer container with conda inside to stay under file-count limits.

## Refolding oracle (AF3 / OpenFold3)
Only needed when `metrics_tags` switch on a refolding metric; generation with `~metrics` does not touch it
([experiments/mario-01_rfd4-euler-smoke.md](experiments/mario-01_rfd4-euler-smoke.md) uses that). How RFD4-Proteina
defines it, read from its checkout on 2026-11-21:
- **Choice:** the config group `metrics/refolding_oracles` (`af3` default, `of3`, `af2`; `of3` is `af3` renamed).
  Each oracle is a Hydra `_target_` (`AF3Oracle`, `AF2Oracle`); `required_tags_any` decides which one a run uses. Only one
  oracle at a time. Boltz-2, which the organizers score with, is not among them.
- **Runtime:** `AF3Oracle` folds in an Apptainer container (a per-rank daemon, or a direct `apptainer run`) and reads
  `AF3_IMAGE`, `AF3_MODEL_DIR` and `AF3_JAX_CACHE_DIR`, plus `APPTAINER_BIND_PATHS` for data mounts. AF3 or OpenFold3 is
  chosen by the weights: an `of3_ported_weights.provenance.json` in `AF3_MODEL_DIR` selects OpenFold3.
- **Euler's own AF3** ([ETH docs](https://docs.hpc.ethz.ch/software/chemistry/alphafold3/), read 2026-11-21): container
  `/cluster/apps/nss/alphafold/containers/AlphaFold3/af3.sif` (run `get-access` once), public databases
  `/cluster/project/alphafold/alphafold3`. The **weights are not provided** (DeepMind's terms): each user downloads them
  (about 1 GB) from [google-deepmind/alphafold3](https://github.com/google-deepmind/alphafold3), and should keep them out of
  `$SCRATCH` (15-day purge). GPUs below compute capability 8.0 need extra XLA/flash-attention flags (see that page).
- **Mismatch to check:** RFD4 runs `run_alphafold_batch.py` inside its own `af3-open.sif`, while the Euler image ships
  `run_alphafold.py`, so the Euler image is probably not a drop-in for `AF3_IMAGE`. Unverified.
- [../envs/euler.sh](../envs/euler.sh) sets the three variables (defaults under
  `$HOME/rfd4-proteina/data_path/openfold3/`, the place RFD4's download script uses; override from the shell) and warns,
  without failing, when the image or weights are missing.

## What the repo already gives us
- `kemp.run.start_run` writes config, commit, diff, script snapshot, host, GPU and seed into each run directory, so a
  job on Euler is as traceable as a local one ([../INDEX.md](../INDEX.md) lists the modules).
- `make submission` builds and checks `results/designs.fasta` offline; `kemp.paths` keeps paths out of the scripts.
- Theozyme candidates from the pre-analysis, as PDB files in the common TSA frame, are the natural input for a
  motif-based design: [theozyme-preanalysis.md](theozyme-preanalysis.md). The recommended ones are already turned
  into RFD4-Proteina condition specs in `results/theozymes/` ([theozyme-inputs.md](theozyme-inputs.md)); not yet run on Euler.

## Open (nobody has filled these in yet)
- Euler access from the repo checkout: how Euler pulls from GitHub, and where the checkout lives.
- Pinning the RFD4-Proteina environment: it is the venv at `$HOME/rfd4-proteina/.venv`, outside this repo, so a run's
  `meta.json` records the repo's `uv.lock` hash but not that venv's package versions. Save them (for example
  `pip freeze`) into the run or the experiment page when a campaign starts.
- Verify [`scripts/euler_job.sbatch`](../scripts/euler_job.sbatch) on a real job. So far it was only run locally, with
  faked `SLURM_*` variables, to check the paths, the guards and that `KEMP_RUNS_DIR` redirects the run directory.
- Not stated on the ETH pages read so far: the maximum run time (the template asks for 24 h, so check Slurm accepts it)
  and the module names beyond `eth_proxy`.
- A memory-only GPU request (`gpumem`) does not pin a type. The first mario-01 attempt (2026-11-21, with `gpumem:24G`)
  failed in the model with `RuntimeError: Invalid backend` in `F.scaled_dot_product_attention`; the GPU it got is not
  recorded here yet. RFD4-Proteina lists only A100, H100, L40S, RTX 6000 Ada and Blackwell GPUs as tested, so the request
  is now `gpumem:35G`. The docs say the RTX Pro 6000 (96 GB) must be requested explicitly and cannot run
  CUDA-12-compiled programs; the job log prints the GPU name, so check which card a job got.
- `eth_proxy` comes from third-party Euler guides, which say it gives compute nodes internet access; confirm that on a real job.
- Refolding oracle on Euler: is `apptainer` available on compute nodes, who has the AF3 (or OpenFold3) weights, can the
  RFD4 image and weights be downloaded (the `eth_proxy` question), and does `APPTAINER_BIND_PATHS` need anything.
- Whether `kemp.run` should record `SLURM_JOB_ID` in each run's `meta.json` (it does not today).
- Annotated-CIF inputs: the check of `results/theozymes/` on Euler ([theozyme-inputs.md](theozyme-inputs.md)) is still to
  do, and so is deriving the `base=` / `oxy=` indices from RFD4-Proteina output. [submission.md](submission.md) still describes the RFD3 + LigandMPNN summary
  (`rfd3.fixed`, `ligandmpnn.sequence`), which does not apply to this stack. Verify the residue at each index before submitting.
- A first run: create an experiment page with `uv run python tools/new.py exp <slug>` before it, and record the
  Euler job ID and run directory on it.
