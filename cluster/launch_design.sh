#!/usr/bin/env bash
# Deploy and launch the RFD3 design stage (Idea C) on the cluster.
#
#   bash cluster/launch_design.sh <project-name> <motif-root> [seeds]
#
# <motif-root> holds one subdirectory per motif, each with Kemp.json and
# HG3_17_kemp_motif.pdb, as written by cluster/build_family_motifs.py.
#
# The organizers' helpers (prepare_rfd3_input.py, prepare_ligandmpnn.py, validation.py) are
# copied from an existing project rather than reimplemented, so the motif hand-off and the
# geometry report stay exactly the ones the scoring pipeline uses.
set -u -o pipefail

HOST=${KEMP_CLUSTER_HOST:-pdh-team}
NAME="${1:?usage: launch_design.sh <project-name> <motif-root> [seeds]}"
MOTIF_ROOT="${2:?need the motif root directory on the cluster}"
SEEDS="${3:-1}"
DONOR=${KEMP_HELPER_SOURCE:-/mnt/work/projects/chris_seedsweep_s4/src}
HERE=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
REMOTE="/mnt/work/projects/$NAME"

echo "=== 1. preparing $REMOTE on $HOST"
ssh "$HOST" "bash -s" <<REMOTE_SETUP || exit 1
set -e -o pipefail
mkdir -p "$REMOTE"/{src,inputs,logs,results,tmp,cache}
for helper in prepare_rfd3_input.py prepare_ligandmpnn.py validation.py; do
    [ -s "$DONOR/\$helper" ] || { echo "STOP: missing $DONOR/\$helper"; exit 1; }
    cp "$DONOR/\$helper" "$REMOTE/src/\$helper"
done
cat > "$REMOTE/env.sh" <<'ENVEOF'
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
MOTIFS=\$(find "$MOTIF_ROOT" -mindepth 1 -maxdepth 1 -type d -printf '%p ' | sort)
[ -n "\$MOTIFS" ] || { echo "STOP: no motif directories under $MOTIF_ROOT"; exit 1; }
echo "  motifs: \$MOTIFS"
for m in \$MOTIFS; do
    [ -s "\$m/Kemp.json" ] && [ -s "\$m/HG3_17_kemp_motif.pdb" ] || { echo "STOP: \$m is incomplete"; exit 1; }
done
echo "  helpers copied, env written"
REMOTE_SETUP

echo "=== 2. copying the design job"
scp -q "$HERE/design_backbones.sbatch" "$HOST:$REMOTE/src/" || exit 1
echo "  ok"

echo "=== 3. submitting"
ssh "$HOST" "bash -lc '
source $REMOTE/env.sh
export DS_MOTIFS=\"\$(find $MOTIF_ROOT -mindepth 1 -maxdepth 1 -type d | sort | tr \"\\n\" \" \")\"
export DS_SEEDS=\"$SEEDS\"
sbatch --parsable --chdir=$REMOTE \
    --output=$REMOTE/logs/design-%j.log \
    --export=ALL \
    $REMOTE/src/design_backbones.sbatch
'"
