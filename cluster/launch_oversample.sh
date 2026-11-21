#!/usr/bin/env bash
# Deploy and launch an Idea A sequence-oversampling job on the cluster.
#
#   bash cluster/launch_oversample.sh <project-name> <parent-run-dir> [temperatures]
#
# <parent-run-dir> is a completed pipeline run, e.g.
#   /mnt/work/projects/chris_seedsweep_s4/results/kemp-4
# We reuse its bridge/ directory: the RFD3 backbone (kemp.pdb), the fixed residue ids and the
# pinned base/donor positions. RFD3 is NOT re-run - its geometry is already exact.
#
# Idempotent: re-running refreshes src/ and submits another job. Nothing in the parent run is
# modified, and nothing is written outside /mnt/work/projects/<project-name>.
set -u -o pipefail

HOST=${KEMP_CLUSTER_HOST:-pdh-team}
NAME="${1:?usage: launch_oversample.sh <project-name> <parent-run-dir> [temperatures]}"
PARENT="${2:?need the parent run directory on the cluster}"
TEMPERATURES="${3:-0.1 0.2 0.3}"
HERE=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
REMOTE="/mnt/work/projects/$NAME"

echo "=== 1. preparing $REMOTE on $HOST"
ssh "$HOST" "bash -s" <<REMOTE_SETUP || exit 1
set -e -o pipefail
PARENT="$PARENT"
REMOTE="$REMOTE"
for f in bridge/kemp.pdb bridge/fixed_residues.txt bridge/sequence.json; do
    [ -s "\$PARENT/\$f" ] || { echo "STOP: missing \$PARENT/\$f"; exit 1; }
done
mkdir -p "\$REMOTE"/{src,inputs,logs,results,tmp,cache}
cp "\$PARENT/bridge/kemp.pdb"           "\$REMOTE/inputs/backbone.pdb"
cp "\$PARENT/bridge/fixed_residues.txt" "\$REMOTE/inputs/fixed_residues.txt"
cp "\$PARENT/bridge/sequence.json"      "\$REMOTE/inputs/sequence.json"
# env.sh is the organizers' standard preamble: reference paths plus per-project caches.
cat > "\$REMOTE/env.sh" <<'ENVEOF'
#!/usr/bin/env bash
export PDH_WORKSPACE=\$(cd -- "\$(dirname -- "\${BASH_SOURCE[0]}")" && pwd -P)
source /mnt/ref/hackathon/scripts/reference-paths.sh
export XDG_CACHE_HOME="\$PDH_WORKSPACE/cache"
export HF_HOME="\$PDH_WORKSPACE/cache/huggingface"
export TORCH_HOME="\$PDH_WORKSPACE/cache/torch"
export TORCH_EXTENSIONS_DIR="\$PDH_WORKSPACE/cache/torch-extensions"
export TRITON_CACHE_DIR="\$PDH_WORKSPACE/cache/triton"
export CUDA_CACHE_PATH="\$PDH_WORKSPACE/cache/cuda"
export PIP_CACHE_DIR="\$PDH_WORKSPACE/cache/pip"
export CONDA_PKGS_DIRS="\$PDH_WORKSPACE/cache/conda"
export TMPDIR="\$PDH_WORKSPACE/tmp"
export PYTHONDONTWRITEBYTECODE=1
export PATH="\$(dirname -- "\$MMSEQS"):\$PATH"
source "\$CONDA_ROOT/etc/profile.d/conda.sh"
ENVEOF
echo "  backbone: \$(grep -c '^ATOM' "\$REMOTE/inputs/backbone.pdb") protein atoms"
echo "  fixed:    \$(cat "\$REMOTE/inputs/fixed_residues.txt")"
REMOTE_SETUP

echo "=== 2. copying scripts"
scp -q "$HERE/oversample.sbatch" "$HERE/build_boltz_queries.py" \
       "$HERE/measure_boltz_outputs.py" "$HERE/build_control_fasta.py" \
       "$HOST:$REMOTE/src/" || exit 1
echo "  ok"

echo "=== 3. building the natural-enzyme control FASTA"
ssh "$HOST" "bash -lc '
source $REMOTE/env.sh
\"\$ENV_ROOT/env-rfd3/bin/python\" $REMOTE/src/build_control_fasta.py \
    /mnt/work/tools/kemp_pdb $REMOTE/inputs/controls.fasta 4BS0 3NYD 7K4U
'" || echo "  (controls unavailable - the job will still run, without the instrument check)"

echo "=== 4. submitting"
ssh "$HOST" "bash -lc '
source $REMOTE/env.sh
export OS_BACKBONE=$REMOTE/inputs/backbone.pdb
export OS_FIXED=\"\$(cat $REMOTE/inputs/fixed_residues.txt)\"
export OS_SEQUENCE=$REMOTE/inputs/sequence.json
export OS_TEMPERATURES=\"$TEMPERATURES\"
[ -s $REMOTE/inputs/controls.fasta ] && export OS_CONTROLS=$REMOTE/inputs/controls.fasta
sbatch --parsable --chdir=$REMOTE \
    --output=$REMOTE/logs/oversample-%j.log \
    --export=ALL \
    $REMOTE/src/oversample.sbatch
'"
