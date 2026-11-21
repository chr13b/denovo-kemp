#!/bin/bash
# euler_job.sbatch on one RTX 2080 Ti instead of a 35 GB GPU: the same job (same body, same logs and outputs under
# $SCRATCH/kemp), only the Slurm request differs. Used by mario-02, which tries RFD4-Proteina on this card; the
# card is not on RFD4's supported list (see wiki/experiments/mario-02_rfd4-rtx2080ti-fp32.md).
#
#   cd <repo root on Euler>; git pull; mkdir -p "$SCRATCH/kemp/logs"
#   sbatch scripts/euler_job_rtx2080.sbatch <command> [args...]
#
# Slurm reads the #SBATCH lines of this file, then it hands over to euler_job.sbatch (whose own #SBATCH lines are
# plain comments to bash). Submit from the repo root, as for euler_job.sbatch. Override as usual, for example
# `sbatch --time=00:30:00 scripts/euler_job_rtx2080.sbatch ...`.
# NOT YET VERIFIED on Euler: that `rtx_2080` is the 2080 Ti (check the `[euler_job] gpu:` line in the job log).

#SBATCH --time=02:00:00
#SBATCH --job-name=mario-02
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem-per-cpu=8G
# GPU by type (the 11 GB of this card is why the 35 GB request of euler_job.sbatch cannot be used here)
#SBATCH --gpus=rtx_2080:1
#SBATCH --output=/cluster/scratch/%u/kemp/logs/%x-%j.out

set -euo pipefail
exec bash "${SLURM_SUBMIT_DIR:?run this through sbatch, from the repo root}/scripts/euler_job.sbatch" "$@"
