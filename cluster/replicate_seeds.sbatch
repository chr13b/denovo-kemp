#!/usr/bin/env bash
# Fold the SAME sequences at several Boltz-2 seeds, to measure the scored consistency term.
#
# Why this is necessary. The organizers score "consistency across multiple Boltz-2 seeds", 5
# replicates per sequence, and we have never measured it. We also found out the hard way that we
# have to: the 4BS0 control sequence, folded with --seed 1 in two differently sized batches, gave
# base contacts of 2.49 A and 2.07 A. A 0.42 A swing on an identical input, against a target window
# only 0.28 A wide. Any single-prediction geometry number therefore carries noise comparable to the
# whole thing we are trying to measure, and a design cannot be placed inside the window by one fold.
#
# Boltz's --seed is per invocation, so this runs the model once per seed over the same small query
# set rather than once over a big one. That pays the model-load cost N times, which is why it is
# only worth doing for a shortlist.
#
# Required environment:
#   PDH_WORKSPACE   project directory
#   RS_FASTA        FASTA of the sequences to replicate
# Optional:
#   RS_SEEDS        space-separated Boltz seeds, default "1 2 3 4 5"
#SBATCH --job-name=kemp-replicate
#SBATCH --partition=gpu
# Pinned to the working node on purpose: allowing the dead l4small nodes made Slurm allocate to
# them, fail the power-up and requeue this very job six times without it ever running.
#SBATCH --constraint=g6.2xlarge
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=14G
#SBATCH --gres=gpu:l4:1
#SBATCH --time=02:00:00

set -e -o pipefail

source "${PDH_WORKSPACE:?Submit through a launcher}/env.sh"
PROJECT="$PDH_WORKSPACE/src"
ROOT="$PDH_WORKSPACE/results/replicate-$SLURM_JOB_ID"
BOLTZ_CACHE="$ROOT/boltz-cache"
SEEDS=${RS_SEEDS:-"1 2 3 4 5"}
export OMP_NUM_THREADS="$SLURM_CPUS_PER_TASK"
mkdir -p "$ROOT" "$BOLTZ_CACHE"

echo "Job $SLURM_JOB_ID on $(hostname); outputs: $ROOT"
echo "Sequences: $RS_FASTA ($(grep -c '^>' "$RS_FASTA") records)"
echo "Boltz seeds: $SEEDS"

for ASSET in boltz2_conf.ckpt boltz2_aff.ckpt mols.tar; do
    [ -e "$BOLTZ_CACHE/$ASSET" ] || ln -s "$BOLTZ_ASSETS/$ASSET" "$BOLTZ_CACHE/$ASSET"
done
[ -e "$BOLTZ_CACHE/mols" ] || ln -s "$BOLTZ_ASSETS/mols" "$BOLTZ_CACHE/mols"

for SEED in $SEEDS; do
    RUN="$ROOT/seed$SEED"
    mkdir -p "$RUN"
    echo "=== seed $SEED"
    # build_boltz_queries.py takes a LigandMPNN root first; there is none here, so point it at a
    # path with no */seqs/*.fa and let every record come in through the plain-FASTA argument.
    "$ENV_ROOT/env-boltz2/bin/python" "$PROJECT/build_boltz_queries.py" \
        "$RUN/none" "$RUN/queries" - "$RS_FASTA" > "$RUN/build.log" 2>&1
    "$ENV_ROOT/env-boltz2/bin/boltz" predict "$RUN/queries" \
        --model boltz2 --cache "$BOLTZ_CACHE" --out_dir "$RUN/boltz" \
        --accelerator gpu --devices 1 --no_kernels \
        --sampling_steps 200 --recycling_steps 3 --diffusion_samples 1 \
        --num_workers 0 --preprocessing-threads 1 --output_format mmcif --seed "$SEED" \
        > "$RUN/boltz.log" 2>&1
    "$ENV_ROOT/env-rfd3/bin/python" "$PROJECT/measure_boltz_outputs.py" \
        "$RUN" - "$RUN/geometry.tsv" | tail -3
    "$ENV_ROOT/env-rfd3/bin/python" "$PROJECT/geometry_vs_crystal.py" /mnt/work/tools/kemp_pdb \
        "$RUN/geometry_full.tsv" "x=$RUN" | tail -1
done

echo "=================================================================="
echo "Per-sequence spread across seeds (the scored consistency term):"
"$ENV_ROOT/env-rfd3/bin/python" - "$ROOT" <<'PY'
import glob
import math
import os
import sys

root = sys.argv[1]
rows = {}
for path in sorted(glob.glob(os.path.join(root, "seed*", "geometry.tsv"))):
    seed = os.path.basename(os.path.dirname(path)).replace("seed", "")
    with open(path) as handle:
        header = handle.readline().rstrip("\n").split("\t")
        for line in handle:
            values = dict(zip(header, line.rstrip("\n").split("\t")))
            if values.get("status") != "measured":
                continue
            try:
                # Prefer the scorer's pinned measurement; fall back to the scan only for controls,
                # whose residue numbering differs per construct.
                base = float(values.get("pinned_base") or values["scan_base"])
                donor = float(values.get("pinned_donor") or values["scan_donor"])
            except (KeyError, ValueError):
                continue
            rows.setdefault(values["name"], []).append((seed, base, donor))


def spread(values):
    n = len(values)
    mean = sum(values) / n
    sd = math.sqrt(sum((v - mean) ** 2 for v in values) / n) if n > 1 else 0.0
    return mean, sd, min(values), max(values)


print(f"{'sequence':<18}{'n':>3}{'base mean':>11}{'sd':>7}{'min':>7}{'max':>7}   "
      f"{'donor mean':>11}{'sd':>7}   in-window seeds")
print("-" * 100)
for name, items in sorted(rows.items()):
    bases = [b for _, b, _ in items]
    donors = [d for _, _, d in items]
    bm, bsd, bmin, bmax = spread(bases)
    dm, dsd, _, _ = spread(donors)
    inside = sum(1 for b, d in zip(bases, donors) if 2.41 <= b <= 2.69 and 2.92 <= d <= 3.60)
    print(f"{name:<18}{len(items):>3}{bm:>11.2f}{bsd:>7.2f}{bmin:>7.2f}{bmax:>7.2f}   "
          f"{dm:>11.2f}{dsd:>7.2f}   {inside}/{len(items)}")
print()
print("A design is only a real candidate if it stays in the window across seeds.")
print("Target window: base 2.41-2.69, donor 2.92-3.60 (26 engaged copies, 23 crystal structures).")
PY
echo "REPLICATION COMPLETE: $ROOT"
