# Cluster (team 01)

Our GPU cluster. Full detail: [raw/20261121_organizers_cluster-guide.md](../raw/20261121_organizers_cluster-guide.md)
and [raw/20261121_organizers_connect-team01.txt](../raw/20261121_organizers_connect-team01.txt).
First-time setup of the key and SSH config is in [../SETUP.md](../SETUP.md).

> **Never put the `.pem` key in this repo.** `.gitignore` blocks `*.pem`, but don't test it.
> The key belongs in `~/.ssh/`, and only inside our team.

## Connect

```bash
ssh pdh-team          # head node: ec2-user@35.181.61.66
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
