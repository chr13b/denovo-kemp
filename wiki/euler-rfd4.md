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

## What the repo already gives us
- `kemp.run.start_run` writes config, commit, diff, script snapshot, host, GPU and seed into each run directory, so a
  job on Euler is as traceable as a local one ([../INDEX.md](../INDEX.md) lists the modules).
- `make submission` builds and checks `results/designs.fasta` offline; `kemp.paths` keeps paths out of the scripts.
- Theozyme candidates from the pre-analysis, as PDB files in the common TSA frame, are the natural input for a
  motif-based design: [theozyme-preanalysis.md](theozyme-preanalysis.md). Turning one into an annotated CIF for
  RFD4-Proteina is not done yet (see Open).

## Open (nobody has filled these in yet)
- Euler access from the repo checkout: how Euler pulls from GitHub, and where the checkout lives.
- Environment for RFD4-Proteina on Euler (modules or conda), and where to pin it (`envs/`).
- A Slurm job template: GPU request, time limit, partition. Add it as a numbered script or an `sbatch` file once it is verified.
- Annotated-CIF inputs: how a theozyme candidate becomes the design input, and how `base=` / `oxy=` indices are
  derived from RFD4-Proteina output. [submission.md](submission.md) still describes the RFD3 + LigandMPNN summary
  (`rfd3.fixed`, `ligandmpnn.sequence`), which does not apply to this stack. Verify the residue at each index before submitting.
- A first run: create an experiment page with `uv run python tools/new.py exp <slug>` before it, and record the
  Euler job ID and run directory on it.
