#!/usr/bin/env bash
# K5 (pose consistency) for a whole directory of Boltz-2 queries: refold every sequence at Boltz seeds 1..5.
#
#   sbatch scripts/41_k5_seeds.sbatch <queries_dir> <tag> [seeds]
#   e.g.   sbatch 41_k5_seeds.sbatch /mnt/work/projects/zonghu_fm_k5/A A "1 2 3 4 5"
#
# <queries_dir> holds one <id>.yaml per design (sequence + MSA path + ligand 6NT), the same inputs the
# oversample run used. Boltz's --seed is per invocation, so the model runs once per seed over the whole
# directory (model load is paid 5 times, not 5 x N). Outputs: /mnt/work/projects/zonghu_fm_k5/out_<tag>/seed<S>/.
#
# Pinned to g6.2xlarge: the l4small nodes fail to power up and requeue the job (chris_oversample_a, replicate_seeds).
# One refold costs ~20 s (oversample-35: 35 structures in 11.4 min), so budget N x 5 x 20 s.
#SBATCH --job-name=k5-seeds
#SBATCH --partition=gpu
#SBATCH --constraint=g6.2xlarge
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=14G
#SBATCH --gres=gpu:l4:1
#SBATCH --time=03:00:00
#SBATCH --output=/mnt/work/projects/zonghu_fm_k5/k5-%j.log

set -e -o pipefail
QUERIES=${1:?queries dir with <id>.yaml files}
TAG=${2:?short tag}
SEEDS=${3:-"1 2 3 4 5"}

source /mnt/work/kemp_example/env.sh
OUT=/mnt/work/projects/zonghu_fm_k5/out_$TAG
CACHE=$OUT/boltz-cache
mkdir -p "$OUT" "$CACHE"
for A in boltz2_conf.ckpt boltz2_aff.ckpt mols.tar; do
    [ -e "$CACHE/$A" ] || ln -s "$BOLTZ_ASSETS/$A" "$CACHE/$A"
done
[ -e "$CACHE/mols" ] || ln -s "$BOLTZ_ASSETS/mols" "$CACHE/mols"
export OMP_NUM_THREADS="$SLURM_CPUS_PER_TASK"

echo "### $TAG: $(ls "$QUERIES"/*.yaml | wc -l) sequences, seeds: $SEEDS"
nvidia-smi --query-gpu=name --format=csv,noheader || true
for S in $SEEDS; do
    echo "=== seed $S"
    SECONDS=0
    "$ENV_ROOT/env-boltz2/bin/boltz" predict "$QUERIES" \
        --model boltz2 --cache "$CACHE" --out_dir "$OUT/seed$S" \
        --accelerator gpu --devices 1 --no_kernels \
        --sampling_steps 200 --recycling_steps 3 --diffusion_samples 1 \
        --num_workers 0 --preprocessing-threads 1 --output_format mmcif --seed "$S" \
        > "$OUT/seed$S.log" 2>&1
    echo "seed $S done in ${SECONDS}s: $(find "$OUT/seed$S" -name '*_model_0.cif' | wc -l) structures"
done
echo "K5 SEEDS COMPLETE: $OUT"
