#!/usr/bin/env bash
# Are our own candidate designs different from EACH OTHER?
#
#   ssh pdh-team 'bash -s' < tools/self_diversity.sh -- <dir-of-structures> [gate]
#
# tools/novelty_check.sh answers "is this fold already known" against 40k PDB representatives.
# This answers the other question: we get up to 20 submission slots and the organizers pick at
# least 5 designs for lab validation. Twenty near-copies of one fold is a bad hedge - if that
# fold happens not to work, every slot fails together. An all-versus-all TM-score over our own
# candidates shows how many genuinely distinct folds we are actually offering.
#
# Reuses the foldseek binary built by envs/foldseek.sh. Reads only; writes to a temp directory.
set -u -o pipefail

FS=/mnt/work/tools/foldseek/bin/foldseek
GATE=${2:-0.7}
SRC="${1:-}"
WORK=$(mktemp -d /tmp/selfdiv.XXXXXX)
trap 'rm -rf "$WORK"' EXIT

[ -n "$SRC" ] || { echo "usage: self_diversity.sh <dir-of-structures> [gate]"; exit 2; }
[ -d "$SRC" ] || { echo "no such directory: $SRC"; exit 2; }
[ -x "$FS" ] || { echo "foldseek missing - run envs/foldseek.sh first"; exit 2; }

mkdir -p "$WORK/in"
COUNT=0
# Flatten whatever layout the predictions came in; foldseek wants one directory of structures.
while IFS= read -r f; do
    [ -s "$f" ] || continue
    cp "$f" "$WORK/in/$(echo "$f" | sed 's#.*/predictions/##; s#/#_#g')"
    COUNT=$((COUNT + 1))
done < <(find "$SRC" -name "*_model_0.cif" -o -name "*.pdb" 2>/dev/null | sort)

echo "structures collected: $COUNT"
[ "$COUNT" -ge 2 ] || { echo "need at least 2 structures to compare"; exit 0; }

"$FS" createdb "$WORK/in/" "$WORK/db" >/dev/null 2>&1
[ -f "$WORK/db.dbtype" ] || { echo "STOP: createdb produced no database"; exit 1; }

# qtmscore, not alntmscore: normalised by the QUERY length. alntmscore divides by the aligned
# length, so a design matching a fragment of another scores near 1.0 while sharing almost
# nothing - the same trap that produced a false novelty FAILURE in tools/novelty_check.sh.
"$FS" easy-search "$WORK/in/" "$WORK/db" "$WORK/hits.tsv" "$WORK/tmp" \
    --alignment-type 1 -e 1000000 --max-seqs 2000 \
    --format-output "query,target,qtmscore,fident,alnlen,qlen,tlen" >/dev/null 2>&1
[ -s "$WORK/hits.tsv" ] || { echo "no alignments produced"; exit 1; }

echo
echo "Pairs above the novelty gate (qTM > $GATE) - these are effectively the same fold:"
awk -F'\t' -v g="$GATE" '$1 != $2 && $3+0 > g {printf "  %-34s %-34s qTM %.3f  id %.2f\n", $1, $2, $3, $4}' \
    "$WORK/hits.tsv" | sort -u | head -40

echo
echo "Distinct-fold clustering at qTM $GATE (single linkage):"
awk -F'\t' -v g="$GATE" '$1 != $2 && $3+0 > g {print $1"\t"$2}' "$WORK/hits.tsv" | sort -u > "$WORK/edges.tsv"
ls -1 "$WORK/in" > "$WORK/nodes.txt"
python3 - "$WORK/nodes.txt" "$WORK/edges.tsv" <<'PY'
import sys
nodes = [line.strip() for line in open(sys.argv[1]) if line.strip()]
parent = {n: n for n in nodes}

def find(x):
    while parent.get(x, x) != x:
        parent[x] = parent[parent[x]]
        x = parent[x]
    return x

for line in open(sys.argv[2]):
    parts = line.rstrip("\n").split("\t")
    if len(parts) != 2:
        continue
    a, b = (p if p in parent else p + ".cif" for p in parts)
    if a in parent and b in parent:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

clusters = {}
for n in nodes:
    clusters.setdefault(find(n), []).append(n)
print(f"  {len(nodes)} structures -> {len(clusters)} distinct folds")
for i, (_, members) in enumerate(sorted(clusters.items(), key=lambda kv: -len(kv[1])), 1):
    print(f"  fold {i}: {len(members)} member(s)  e.g. {members[0]}")
PY

echo
echo "Submission guidance: fill the 20 slots from DIFFERENT folds first. If the lab validates"
echo "at least 5, spreading them across folds hedges against one fold being inactive."
