#!/usr/bin/env bash
# Idea A: sequence oversampling on an EXISTING RFD3 backbone.
#
# Why this job exists (primer finding d2): summary.json reports the catalytic contacts twice,
# once on the RFD3 backbone and once on the Boltz-2 refold. RFD3 hits the crystal window on
# every run we have ever done (base 2.53 A, donor 3.09 A, deviation 0.013 A). All of the
# geometric loss happens in the refold - and the refold is decided by the SEQUENCE, which the
# organizers' pipeline samples exactly once per backbone (id=1, T=0.1).
#
# So: hold the backbone fixed, sample the sequence many times, keep the refolds that land in
# the window measured from 23 crystal structures (base 2.41-2.69 A, donor 2.92-3.60 A).
#
# Costs that make this worth doing: RFD3 12 min, LigandMPNN 6 s, Boltz-2 19 s. We skip RFD3
# entirely (the backbone already exists) and skip MMseqs2 (chris-03: no-op, bit-identical).
#
# Required environment:
#   PDH_WORKSPACE   project directory (set by run.sh)
#   OS_BACKBONE     LigandMPNN input PDB: backbone + 6NT (a run's bridge/kemp.pdb)
#   OS_FIXED        fixed residue ids, e.g. "A52 A86" (a run's bridge/fixed_residues.txt)
#   OS_SEQUENCE     the parent run's bridge/sequence.json, for the pinned positions
# Optional:
#   OS_TEMPERATURES space-separated LigandMPNN temperatures  (default "0.1 0.2 0.3")
#   OS_BATCH        sequences per batch                       (default 8)
#   OS_NBATCHES     batches per temperature                   (default 3)
#   OS_CONTROLS     FASTA of natural-enzyme controls to fold under identical conditions
#   OS_CKPT         LigandMPNN checkpoint to use instead of the default (an experiment arm)
#   OS_EXTRA_ARGS   extra LigandMPNN arguments, e.g. "--bias_AA_per_residue <json>" (an experiment arm)
#   OS_SEED_OFFSET  added to the per-temperature seed, so two sweeps at the same T do not repeat sequences
# Node sizing: this job does not run MMseqs2 (chris-03: the stage is a no-op), so it needs only
# 4 CPUs / 14 GB and would fit the small l4small nodes. BUT those nodes are currently dead
# (idle~, "Scheduler health check failed"), and a constraint that ALLOWS them is a trap: Slurm
# allocates the job to a dead node, the power-up fails, and the job is requeued to the back of the
# line. Measured: job 47 was requeued 6 times and never ran. Pin to the one working node until
# `sinfo` shows an l4small node healthy again. l4big is never used: the organizers reserved it.
#SBATCH --job-name=kemp-oversample
#SBATCH --partition=gpu
#SBATCH --constraint=g6.2xlarge
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=14G
#SBATCH --gres=gpu:l4:1
#SBATCH --time=03:00:00

set -e -o pipefail

source "${PDH_WORKSPACE:?Submit through run.sh}/env.sh"
PROJECT="$PDH_WORKSPACE/src"
RUN_ROOT="$PDH_WORKSPACE/results/oversample-$SLURM_JOB_ID"
BOLTZ_CACHE="$RUN_ROOT/boltz-cache"
TEMPERATURES=${OS_TEMPERATURES:-"0.1 0.2 0.3"}
BATCH=${OS_BATCH:-8}
NBATCHES=${OS_NBATCHES:-3}
export OMP_NUM_THREADS="$SLURM_CPUS_PER_TASK"
mkdir -p "$RUN_ROOT" "$BOLTZ_CACHE"

echo "Job $SLURM_JOB_ID on $(hostname); outputs: $RUN_ROOT"
echo "Backbone: $OS_BACKBONE"
echo "Fixed residues: $OS_FIXED"
echo "Temperatures: $TEMPERATURES; $BATCH x $NBATCHES sequences each"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader

# ---------------------------------------------------------------- 1. many sequences, one backbone
echo "START 1/4: LigandMPNN sequence oversampling"
for T in $TEMPERATURES; do
    # A distinct seed per temperature keeps the three sweeps independent; without it the
    # same RNG stream would make the low-temperature samples near-copies of each other.
    SEED=$(awk -v t="$T" -v o="${OS_SEED_OFFSET:-0}" 'BEGIN{printf "%.0f", t*1000+o}')
    echo "  --- T=$T seed=$SEED"
    "$ENV_ROOT/env-ligandmpnn/bin/python" "$LIGANDMPNN_ROOT/run.py" \
        --model_type ligand_mpnn \
        --checkpoint_ligand_mpnn "${OS_CKPT:-$LIGANDMPNN_CHECKPOINT}" \
        --pdb_path "$OS_BACKBONE" \
        --out_folder "$RUN_ROOT/ligandmpnn/T$T" \
        --fixed_residues "$OS_FIXED" \
        --ligand_mpnn_use_atom_context 1 --ligand_mpnn_use_side_chain_context 1 \
        --temperature "$T" ${OS_EXTRA_ARGS:-} \
        --batch_size "$BATCH" --number_of_batches "$NBATCHES" \
        --pack_side_chains 0 --seed "$SEED" --verbose 0 \
        >> "$RUN_ROOT/ligandmpnn.log" 2>&1
    echo "      $(cat "$RUN_ROOT/ligandmpnn/T$T/seqs/"*.fa | grep -c '^>') records written"
done

# ---------------------------------------------------------------- 2. one Boltz query per sequence
echo "START 2/4: building Boltz-2 queries (query-only alignments, per chris-03)"
"$ENV_ROOT/env-boltz2/bin/python" "$PROJECT/build_boltz_queries.py" \
    "$RUN_ROOT/ligandmpnn" "$RUN_ROOT/queries" "$OS_SEQUENCE" ${OS_CONTROLS:-}

# ---------------------------------------------------------------- 3. fold them all in one call
# One `boltz predict <directory>` call loads the model once for the whole batch. Folding each
# sequence in its own call would pay the model-load cost ~70 times over.
echo "START 3/4: Boltz-2 batch prediction"
for ASSET in boltz2_conf.ckpt boltz2_aff.ckpt mols.tar; do
    [ -e "$BOLTZ_CACHE/$ASSET" ] || ln -s "$BOLTZ_ASSETS/$ASSET" "$BOLTZ_CACHE/$ASSET"
done
[ -e "$BOLTZ_CACHE/mols" ] || ln -s "$BOLTZ_ASSETS/mols" "$BOLTZ_CACHE/mols"
"$ENV_ROOT/env-boltz2/bin/boltz" predict "$RUN_ROOT/queries" \
    --model boltz2 --cache "$BOLTZ_CACHE" --out_dir "$RUN_ROOT/boltz" \
    --accelerator gpu --devices 1 --no_kernels \
    --sampling_steps 200 --recycling_steps 3 --diffusion_samples 1 \
    --num_workers 0 --preprocessing-threads 1 --output_format mmcif --seed 1 \
    2>&1 | tee "$RUN_ROOT/boltz.log"

# ---------------------------------------------------------------- 4. measure every structure
echo "START 4/4: measuring catalytic geometry"
"$ENV_ROOT/env-rfd3/bin/python" "$PROJECT/measure_boltz_outputs.py" \
    "$RUN_ROOT" "$OS_BACKBONE" "$RUN_ROOT/geometry.tsv"
# Full geometry (distances + approach angle + in-plane angle) against the crystal copies. Cheap, and the
# structures are kept, so this could be redone later - but doing it here means every sweep is ranked the
# same way without a separate step.
"$ENV_ROOT/env-rfd3/bin/python" "$PROJECT/geometry_vs_crystal.py" /mnt/work/tools/kemp_pdb \
    "$RUN_ROOT/geometry_full.tsv" "x=$RUN_ROOT" | tail -2

echo "OVERSAMPLE COMPLETE: $RUN_ROOT/geometry.tsv"
