#!/bin/bash
# Euler job template: run one repo command through Slurm, with provenance. Everything it writes (runs, data
# and the job log) goes under $SCRATCH/kemp.
#
#   cd <repo root on Euler>; git pull
#   mkdir -p "$SCRATCH/kemp/logs"      # the log directory must exist BEFORE you submit, or the job leaves no log
#   sbatch scripts/euler_job.sbatch <command> [args...]
#   e.g. sbatch scripts/euler_job.sbatch python scripts/10_generate_candidates.py --seed=0
#
# Override resources for one submission without editing this file:
#   sbatch --time=08:00:00 --gpus=a100_80gb:1 scripts/euler_job.sbatch <command>
#
# Euler facts used here come from docs.hpc.ethz.ch (read 2026-11-21): see wiki/euler-rfd4.md.
# NOT YET VERIFIED on a real Euler job. GPU nodes are only available to shareholders: check your group has access.

# Wall-clock limit, HH:MM:SS: 24 hours. Euler's default is 1 hour and the ETH pages I read state no maximum,
# so check that Slurm accepts 24 h for your GPU request.
#SBATCH --time=24:00:00
#SBATCH --job-name=kemp
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
# Memory is per CPU core on Euler (--mem-per-cpu), so the job gets cpus-per-task x this.
#SBATCH --mem-per-cpu=8G
# One A100. `a100` is the type name in the ETH docs; `a100_80gb` is the 80 GB card. Alternatively ask for GPU
# memory with --gres=gpumem:<size>, e.g. --gres=gpumem:40g.
#SBATCH --gpus=a100:1
# The job log (stdout and stderr) goes to $SCRATCH/kemp/logs. Slurm does not expand $SCRATCH in #SBATCH lines
# but does expand %u (your username), and the ETH docs give scratch as /cluster/scratch/<username>.
#SBATCH --output=/cluster/scratch/%u/kemp/logs/%x-%j.out

set -euo pipefail

cd "${SLURM_SUBMIT_DIR:?run this through sbatch, from the repo root}"
[ -f pyproject.toml ] && [ -d src/kemp ] || { echo "[euler_job] submit from the repo root" >&2; exit 2; }
[ $# -gt 0 ] || { echo "usage: sbatch scripts/euler_job.sbatch <command> [args...]" >&2; exit 2; }

# Startup: load the proxy module. Third-party Euler guides say eth_proxy gives compute nodes internet access;
# it is not on the ETH pages I read. `set +u` because the module system may read unset variables.
type module >/dev/null 2>&1 || { echo "[euler_job] ERROR: the 'module' command is not available in this shell" >&2; exit 3; }
set +u
module load eth_proxy
set -u

# Outputs: runs/, data/ and logs/ all live in $SCRATCH/kemp. $SCRATCH has no backup and deletes files older than
# 15 days, and $HOME has a 50 GB / 500,000-file quota: copy what matters into results/ (tracked) in time.
export KEMP_RUNS_DIR="${KEMP_RUNS_DIR:-${SCRATCH:?SCRATCH is not set}/kemp/runs}"
export KEMP_DATA_DIR="${KEMP_DATA_DIR:-$SCRATCH/kemp/data}"
mkdir -p "$KEMP_RUNS_DIR" "$KEMP_DATA_DIR"

# ---- ENVIRONMENT -------------------------------------------------------------------------------------
# envs/euler.sh activates the RFD4-Proteina virtualenv ($HOME/rfd4-proteina/.venv). Run the repo's scripts with
# plain `python`, not `uv run`: `uv run` would use the repo's own environment instead of that venv. The `kemp`
# package (standard library only) is not installed in the venv, so put src/ on the path to make `import kemp` work.
if [ -f envs/euler.sh ]; then
    # shellcheck disable=SC1091
    source envs/euler.sh
else
    echo "[euler_job] WARNING: envs/euler.sh not found, running in the default environment" >&2
fi
export PYTHONPATH="$PWD/src${PYTHONPATH:+:$PYTHONPATH}"
# -----------------------------------------------------------------------------------------------------

# Provenance goes to the log; kemp.run.start_run records the commit, diff and GPU in the run directory.
dirty=""; [ -n "$(git status --porcelain)" ] && dirty=" (DIRTY: commit before running, see CLAUDE.md)"
echo "[euler_job] job ${SLURM_JOB_ID:-?} on $(uname -n) | $(git rev-parse --abbrev-ref HEAD) @ $(git rev-parse --short HEAD)${dirty}"
echo "[euler_job] runs -> $KEMP_RUNS_DIR | data -> $KEMP_DATA_DIR | log -> $SCRATCH/kemp/logs/"
echo "[euler_job] gpu: $(nvidia-smi --query-gpu=name,memory.total --format=csv,noheader 2>/dev/null | head -1 || true)"
echo "[euler_job] command: $*"

"$@"

echo "[euler_job] finished, exit code 0"
