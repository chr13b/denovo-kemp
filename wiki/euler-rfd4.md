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

The template ([../scripts/euler_job.sbatch](../scripts/euler_job.sbatch)) asks for one A100 (`--gpus=a100:1`) for
24 hours, loads the `eth_proxy` module on startup, and writes everything under `$SCRATCH/kemp`: `runs/` and `data/`
through `KEMP_RUNS_DIR` / `KEMP_DATA_DIR`, and the job log in `logs/`. It prints the commit and GPU into the log, sources
[../envs/euler.sh](../envs/euler.sh) (which activates the RFD4-Proteina venv, `$HOME/rfd4-proteina/.venv`) and puts
`src/` on `PYTHONPATH` so `import kemp` works there. Run scripts with plain `python`, not `uv run`, which would use the
repo's own environment instead of that venv. Record the job ID and run directory on the experiment page.

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

## What the repo already gives us
- `kemp.run.start_run` writes config, commit, diff, script snapshot, host, GPU and seed into each run directory, so a
  job on Euler is as traceable as a local one ([../INDEX.md](../INDEX.md) lists the modules).
- `make submission` builds and checks `results/designs.fasta` offline; `kemp.paths` keeps paths out of the scripts.
- Theozyme candidates from the pre-analysis, as PDB files in the common TSA frame, are the natural input for a
  motif-based design: [theozyme-preanalysis.md](theozyme-preanalysis.md). Turning one into an annotated CIF for
  RFD4-Proteina is not done yet (see Open).

## Open (nobody has filled these in yet)
- Euler access from the repo checkout: how Euler pulls from GitHub, and where the checkout lives.
- Pinning the RFD4-Proteina environment: it is the venv at `$HOME/rfd4-proteina/.venv`, outside this repo, so a run's
  `meta.json` records the repo's `uv.lock` hash but not that venv's package versions. Save them (for example
  `pip freeze`) into the run or the experiment page when a campaign starts.
- Verify [`scripts/euler_job.sbatch`](../scripts/euler_job.sbatch) on a real job. So far it was only run locally, with
  faked `SLURM_*` variables, to check the paths, the guards and that `KEMP_RUNS_DIR` redirects the run directory.
- Not stated on the ETH pages read so far: the maximum run time (the template asks for 24 h, so check Slurm accepts it)
  and the module names beyond `eth_proxy`.
- `eth_proxy` comes from third-party Euler guides, which say it gives compute nodes internet access; confirm that on a real job.
- Whether `kemp.run` should record `SLURM_JOB_ID` in each run's `meta.json` (it does not today).
- Annotated-CIF inputs: how a theozyme candidate becomes the design input, and how `base=` / `oxy=` indices are
  derived from RFD4-Proteina output. [submission.md](submission.md) still describes the RFD3 + LigandMPNN summary
  (`rfd3.fixed`, `ligandmpnn.sequence`), which does not apply to this stack. Verify the residue at each index before submitting.
- A first run: create an experiment page with `uv run python tools/new.py exp <slug>` before it, and record the
  Euler job ID and run directory on it.
