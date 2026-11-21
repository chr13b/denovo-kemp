# [2026-11-21 16:14] setup | Euler job: GPU memory request instead of A100 (mario)

- `scripts/euler_job.sbatch` now asks for `--gpus=1` and `--gres=gpumem:24G` (a GPU with at least 24 GB, any type) instead of `--gpus=a100:1`. The ETH page lists `--gres=gpumem:<size>[units]` but gives no example, unit spelling or word on combining it with `--gpus`; check with `sbatch --test-only`.
- `wiki/euler-rfd4.md` and `wiki/experiments/mario-01_rfd4-euler-smoke.md` updated to match, with a note that the job log shows which GPU a job got. Syntax checked with `bash -n`; not run through `sbatch`.
