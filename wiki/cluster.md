# Cluster (team 01)

> **Historical note (2026-11-23).** Written during the hackathon (2026-11-21 and 2026-11-22) for the organizers' cluster,
> which was provided for the event. Node states, job numbers and paths on this page were true on those days.

Our GPU cluster. Full detail: [raw/20261121_organizers_cluster-guide.md](../raw/20261121_organizers_cluster-guide.md)
and [raw/20261121_organizers_connect-team01.txt](../raw/20261121_organizers_connect-team01.txt).
First-time setup of the key and SSH config is in [../SETUP.md](../SETUP.md).

> **Never put the `.pem` key in this repo.** `.gitignore` blocks `*.pem`, but don't test it.
> The key belongs in `~/.ssh/`, and only inside our team.

## Connect

```bash
ssh pdh-team          # head node: ec2-user@<CLUSTER_IP>
```

Verified host fingerprint (ED25519): `SHA256:3HYAek1L/uZ+NT9YtwYhFBd9FUuz0vW06FWAurPTQWk`.
If SSH ever shows a different one, stop and tell an organiser.

## How the machines fit together

```
your laptop  --ssh-->  head node (no GPU: edit files, submit jobs)
                           |
                           +-- Slurm --> GPU worker (all heavy compute)

shared by both:  /mnt/ref  = read-only tools, weights, reference data
                 /mnt/work = our files: inputs, code, caches, results
```

- **Never run model/heavy jobs on the head node** — it has no GPU. Always go through Slurm.
- We get **8 logical CPUs of GPU worker at a time**: either 2× `g6.xlarge` (= 2 GPUs in parallel, preferred)
  or 1× `g6.2xlarge` (1 GPU, 32 GiB RAM). **Never** the `l4big` queue — a job sent there queues forever.
- Every GPU is one NVIDIA L4 with 24 GB VRAM.
- Only the **MSA step (MMseqs2)** needs the big node (~28 GB RAM). RFD3, LigandMPNN and Boltz-2 fit on `g6.xlarge`.

## One-time per team: already done ✅

`/mnt/work/kemp_example` is prepared and **verified** (job `1`, 2026-11-21 ~10:38):
`VERIFIED: three independent GPU smoke tests and the Kemp pipeline passed.`
Baseline numbers from that run: [experiments/chris-01_reference-pipeline-baseline.md](experiments/chris-01_reference-pipeline-baseline.md).

**Nobody needs to run `setup.sh` again, and nobody should modify `/mnt/work/kemp_example`.**
To re-check at any time:

```bash
bash /mnt/work/kemp_example/status.sh /mnt/work/kemp_example
```

## Each own design run

Leave `/mnt/work/kemp_example` untouched as the reference. Use your handle in the project name so
projects never collide (`chris_long_loop`, not `my_first_design`):

```bash
bash /mnt/ref/hackathon/new-project.sh /mnt/work/kemp_example /mnt/work/projects/<handle>_<topic>
bash /mnt/work/projects/<handle>_<topic>/run.sh          # prints JOB_NUMBER
squeue -j JOB_NUMBER
tail -n 50 /mnt/work/projects/<handle>_<topic>/logs/kemp-JOB_NUMBER.log
cat /mnt/work/projects/<handle>_<topic>/results/kemp-JOB_NUMBER/summary.json
```

- A project folder holds `inputs/`, `src/`, `results/`, `logs/`, `cache/`, `tmp/`, `env.sh`, `run.sh`.
- Read `inputs/Kemp.json`, `inputs/HG3_17_kemp_motif.pdb` and `src/kemp-e2e.sbatch` together before editing.
- **Length:** `contig` in the `Kemp_HG3_17_base_donor` entry of `inputs/Kemp.json`. `200-200` = exactly 200,
  `150-260` = sample in that range. Competition limit 260.
- **Sampling:** `seed` in `src/kemp-e2e.sbatch`. Same seed = same design. Change it to explore.
  Model settings (e.g. LigandMPNN temperature) live there too.
- **Don't edit a project while its job runs.** Make a new project folder instead.
- In project mode all checks are **warnings only**: see `validation_warnings` in `summary.json` and
  `validation-warnings.jsonl`. The scripts never pad, trim or repair outputs. `pipeline_completed: true`
  with status `completed_with_warnings` is normal, but read the warnings.
- We all share one Linux login, so folder separation is organisational, not permissions.

## Only ONE GPU actually works (checked 2026-11-21 23:28 UTC)

`gpu-dy-l4-1` (g6.2xlarge, 8 CPU, 31 GB) is the only usable node. `gpu-dy-l4small-1/-2` are stuck at
`Scheduler health check failed` (stamped 20:39 UTC). A one-job probe with `--constraint=l4small --no-requeue`
started on `l4small-1` at 23:28:08 and ended 12 s later as `NODE_FAIL / NodeDown`; the node then failed its health
check again. `l4big` is reserved and off limits. So **everything is serial on one GPU**: ~19 s per Boltz-2 fold at
260 residues. Pin jobs to `--constraint=g6.2xlarge`; a constraint that allows the small nodes makes Slurm allocate
to a dead node and requeue the job to the back of the line (one of ours was requeued 6 times and never ran).
Use `--no-requeue` on any probe.

## The unattended pipeline (`cluster/autopilot.py`)

A driver that runs on the head node under `nohup` and survives a dropped session. It only polls Slurm and parses TSV
files; all GPU work is submitted with `sbatch`. Stages: `repl1` (replicate the 20 best existing designs by geometry
D), `arms` (72-sequence arms on seed 4's backbone), `main` (216 more sequences with the winning arm's settings), `repl2` (replicate the best new
designs), `final` (aggregate, apply the selection rule, write `final_candidates.tsv` and `designs_candidate.fasta`).
The arms are five, run in this order so that cuts fall on the weakest ideas first: baseline (the comparison, always runs),
polar-down pocket (read off the crystals), close variants of s024, aromatic pocket, LigandMPNN checkpoint 005.

**Time-aware by design.** Before each arm after the first it checks that the arm plus 45 min to replicate its designs still
fits before `--stop-by`, otherwise it stops adding arms; replication is sized to the time left (about 1.75 min per design
at 5 seeds) and skipped if fewer than 3 designs fit; a stage that does not fit is skipped without blocking a later,
cheaper one. The aim is that however late the GPU arrives, the run ends with replicated candidates and not with arms
nobody had time to confirm.

- Start: `cd /mnt/work/projects/chris_autopilot && nohup setsid python3 src/autopilot.py > autopilot.out 2>&1 &`
- Rehearse without submitting: `python3 src/autopilot.py --dry-run`. Watch: `tail -f autopilot.log`.
- Resumable per JOB (`state.json` maps job names to Slurm ids, so a restart reuses running or finished jobs instead
  of resubmitting). A job that fails twice is SKIPPED and logged as `STOP:`; later stages continue, so one bad job
  cannot waste the night. A transient `squeue` error is not read as 'finished'. It logs a heartbeat every 10 min, warns
  if a job pends over 90 min, and will not start a stage that cannot finish before `--stop-by` (default 2026-11-22T08:00 UTC).
- It never uploads and never touches other users' jobs. The novelty gate and the upload stay with a human, and
  `python3 src/finalize.py` does the preparation: it applies the rule to everything replicated so far, runs the novelty
  gate and the base/oxy index check, writes `designs_final.fasta` and runs the organizers' validator. It can be run at
  any moment. The upload is then `cd /mnt/work/projects/chris_oversample_a/validator && ./submit-designs.sh <file>`.
- Selection rule (pre-registered): both distances in window in >= 3/5 seeds, mean D <= 15, the nearest carboxylate
  oxygen is OD2 in >= 4/5 seeds, qTM <= 0.70 (checked separately), the organizers' validator accepts.

## Interactive poking around (no heavy compute!)

```bash
source /mnt/work/projects/<handle>_<topic>/env.sh
conda activate /mnt/ref/software/envs/env-rfd3     # or env-ligandmpnn, env-boltz2
```

## Get results onto your laptop (and into this repo)

Run on your **laptop**, in the folder where you want the files:

```bash
mkdir <handle>_<topic>_export
scp -r pdh-team:/mnt/work/projects/<handle>_<topic>/{inputs,src,results} <handle>_<topic>_export
```

`/mnt/work` is **not backed up** by the organizers' reference snapshot. Copy anything that matters.
Put small, important artifacts (sequences, summary.json, figures) into this repo under `results/`,
and register the run on its experiment page in `wiki/experiments/`. Keep big raw outputs out of git.
