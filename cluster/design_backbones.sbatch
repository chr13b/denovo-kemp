#!/usr/bin/env bash
# Stage 1 of the two-stage pipeline: RFD3 backbones only, no MMseqs2, no Boltz-2.
#
# Idea C. One run per motif, each producing a backbone plus the LigandMPNN hand-off
# (bridge/kemp.pdb, bridge/fixed_residues.txt, bridge/sequence-less motif.json) that
# cluster/launch_oversample.sh then consumes. Splitting the pipeline here is the point:
# RFD3 is the 12-minute step and its geometry is already exact (primer finding d2), so it
# should be run once per design problem and never re-run to re-roll a sequence.
#
# Required environment:
#   PDH_WORKSPACE   project directory (set by the launcher)
#   DS_MOTIFS       space-separated motif directories, each holding Kemp.json +
#                   HG3_17_kemp_motif.pdb (see cluster/build_family_motifs.py)
# Optional:
#   DS_SEEDS        space-separated RFD3 seeds, default "1"
#SBATCH --job-name=kemp-design
#SBATCH --partition=gpu
#SBATCH --constraint=g6.2xlarge
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=30G
#SBATCH --gres=gpu:l4:1
#SBATCH --time=04:00:00

set -u -o pipefail

source "${PDH_WORKSPACE:?Submit through the launcher}/env.sh"
export PDH_RUN_MODE=project
PROJECT="$PDH_WORKSPACE/src"
ROOT="$PDH_WORKSPACE/results/design-$SLURM_JOB_ID"
SEEDS=${DS_SEEDS:-1}
export OMP_NUM_THREADS="$SLURM_CPUS_PER_TASK"
mkdir -p "$ROOT"

echo "Job $SLURM_JOB_ID on $(hostname); outputs: $ROOT"
echo "Motifs: $DS_MOTIFS"
echo "Seeds:  $SEEDS"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader

FAILED=0
for MOTIF in $DS_MOTIFS; do
    TAG=$(basename "$MOTIF")
    for SEED in $SEEDS; do
        RUN="$ROOT/${TAG}_s${SEED}"
        echo "=================================================================="
        echo "=== $TAG seed $SEED -> $RUN"
        mkdir -p "$RUN"
        # prepare_rfd3_input.py resolves the motif path relative to the motif directory and
        # copies the spec into $RUN/Kemp.json, which prepare_ligandmpnn.py reads back.
        if ! "$ENV_ROOT/env-rfd3/bin/python" "$PROJECT/prepare_rfd3_input.py" "$RUN" "$MOTIF"; then
            echo "  SKIP: input preparation failed for $TAG seed $SEED"
            FAILED=$((FAILED + 1)); continue
        fi
        if ! "$ENV_ROOT/env-rfd3/bin/rfd3" \
            inputs="$RUN/Kemp.json" \
            'json_keys_subset=[Kemp_HG3_17_base_donor]' \
            ckpt_path="$RFD3_CHECKPOINT" \
            out_dir="$RUN/rfd3" \
            diffusion_batch_size=1 n_batches=1 seed="$SEED" \
            skip_existing=False prevalidate_inputs=True \
            cleanup_guideposts=True output_full_json=True dump_prediction_metadata_json=True \
            > "$RUN/rfd3.log" 2>&1; then
            echo "  SKIP: RFD3 failed for $TAG seed $SEED (see $RUN/rfd3.log)"
            tail -5 "$RUN/rfd3.log"
            FAILED=$((FAILED + 1)); continue
        fi
        if ! "$ENV_ROOT/env-rfd3/bin/python" "$PROJECT/prepare_ligandmpnn.py" "$RUN" "$MOTIF"; then
            echo "  SKIP: hand-off failed for $TAG seed $SEED"
            FAILED=$((FAILED + 1)); continue
        fi
        echo "  READY: $RUN/bridge"
    done
done

echo "=================================================================="
echo "DESIGN STAGE COMPLETE: $FAILED failures"
echo "Backbones ready for oversampling:"
for d in "$ROOT"/*/bridge/kemp.pdb; do [ -s "$d" ] && echo "  $(dirname "$(dirname "$d")")"; done

# ---------------------------------------------------------------- chain into stage 2
# Submitting from inside the job means the sequence sweeps start the moment a backbone exists,
# with no human in the loop. Each sweep gets its own results/oversample-<jobid>/ inside this
# same workspace, so they cannot collide. DS_CHAIN=0 disables it for a design-only run.
if [ "${DS_CHAIN:-1}" = "1" ] && [ -s "$PROJECT/oversample.sbatch" ]; then
    echo "=================================================================="
    echo "Chaining stage 2: one sequence sweep per backbone"
    for BRIDGE in "$ROOT"/*/bridge/kemp.pdb; do
        [ -s "$BRIDGE" ] || continue
        RUN=$(dirname "$(dirname "$BRIDGE")")
        TAG=$(basename "$RUN")
        [ -s "$RUN/bridge/fixed_residues.txt" ] || { echo "  skip $TAG: no fixed_residues.txt"; continue; }
        # The pinned base/donor positions live in sequence.json after a full pipeline run, but
        # a design-only run has not reached LigandMPNN yet - motif.json carries the same
        # "fixed" array, so use whichever exists.
        POSITIONS="$RUN/bridge/sequence.json"
        [ -s "$POSITIONS" ] || POSITIONS="$RUN/bridge/motif.json"
        [ -s "$POSITIONS" ] || { echo "  skip $TAG: no pinned-position file"; continue; }
        JOB=$(OS_BACKBONE="$RUN/bridge/kemp.pdb" \
              OS_FIXED="$(cat "$RUN/bridge/fixed_residues.txt")" \
              OS_SEQUENCE="$POSITIONS" \
              OS_TEMPERATURES="${DS_CHAIN_TEMPERATURES:-0.1 0.2 0.3}" \
              OS_BATCH="${DS_CHAIN_BATCH:-8}" \
              OS_NBATCHES="${DS_CHAIN_NBATCHES:-3}" \
              OS_CONTROLS="${DS_CHAIN_CONTROLS:-}" \
              sbatch --parsable --chdir="$PDH_WORKSPACE" \
                     --output="$PDH_WORKSPACE/logs/oversample-%j.log" \
                     --export=ALL,OS_BACKBONE,OS_FIXED,OS_SEQUENCE,OS_TEMPERATURES,OS_BATCH,OS_NBATCHES,OS_CONTROLS \
                     --job-name="os-$TAG" \
                     "$PROJECT/oversample.sbatch" 2>&1)
        echo "  $TAG -> job $JOB"
    done
fi
