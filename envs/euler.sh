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
