# Sourced by scripts/euler_job.sbatch on Euler: activates the RFD4-Proteina virtualenv.
# The venv lives in $HOME on Euler, outside this repo (per mario; not checked from here).
VENV_ACTIVATE="$HOME/rfd4-proteina/.venv/bin/activate"
[ -f "$VENV_ACTIVATE" ] || { echo "[envs/euler.sh] ERROR: no virtualenv at $VENV_ACTIVATE" >&2; exit 4; }
# activate scripts can read unset variables, so relax `set -u` around it and restore it afterwards
case $- in *u*) _nounset=1 ;; *) _nounset=0 ;; esac
set +u
# shellcheck disable=SC1090
source "$VENV_ACTIVATE"
[ "$_nounset" = 1 ] && set -u
unset VENV_ACTIVATE _nounset

# ---- Refolding oracle (AF3 / OpenFold3), only needed when metrics_tags enable a refolding metric --------
# NOT VERIFIED on Euler. RFD4-Proteina folds in an Apptainer container and reads these three variables (docs/installation.rst
# in its checkout). Override them from the shell; the defaults are where its download script puts the files.
# `apptainer` must be on PATH (check `which apptainer` on a compute node).
#   AF3_IMAGE          RFD4's own container (af3-open.sif, from the Hugging Face repo nvidia/RFD4-Proteina). Not the Euler
#                      one: /cluster/apps/nss/alphafold/containers/AlphaFold3/af3.sif has run_alphafold.py, while RFD4
#                      runs run_alphafold_batch.py, so they probably do not match (needs `get-access` once either way).
#   AF3_MODEL_DIR      model weights. AF3 weights are NOT provided on Euler (DeepMind terms); download them yourself, or
#                      use the converted OpenFold3 weights and pass metrics/refolding_oracles=of3. Keep them in $HOME or
#                      a project space, not $SCRATCH (15-day purge).
#   AF3_JAX_CACHE_DIR  any writable directory.
# The Euler public AF3 databases are at /cluster/project/alphafold/alphafold3 (docs.hpc.ethz.ch/software/chemistry/alphafold3).
_of3_root="${KEMP_OF3_ROOT:-$HOME/rfd4-proteina/data_path/openfold3}"
export AF3_MODEL_DIR="${AF3_MODEL_DIR:-$_of3_root/weights}"
export AF3_JAX_CACHE_DIR="${AF3_JAX_CACHE_DIR:-${SCRATCH:-$HOME}/kemp/jax_cache}"
if [ -z "${AF3_IMAGE:-}" ]; then
    # first .sif the download script left in runtime/, if any (the tutorial notebook picks it the same way)
    AF3_IMAGE="$(ls "$_of3_root"/runtime/*.sif 2>/dev/null | head -1 || true)"
    export AF3_IMAGE
fi
mkdir -p "$AF3_JAX_CACHE_DIR"
for _v in AF3_IMAGE AF3_MODEL_DIR; do
    [ -e "${!_v:-}" ] || echo "[envs/euler.sh] WARNING: $_v='${!_v:-}' does not exist; refolding metrics will fail (generation with ~metrics is fine)" >&2
done
unset _of3_root _v
