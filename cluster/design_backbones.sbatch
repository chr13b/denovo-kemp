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
