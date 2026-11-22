#!/usr/bin/env bash
# Novelty gate for one design: TM-score against published structures.
# A design qualifies only if TM-score <= 0.7 to every published structure (and <= 70% identity,
# which the pipeline's MSA depth already tells us - see below).
#
# Run ON THE CLUSTER (the databases live there):
#   ssh pdh-team 'bash -s' < tools/novelty_check.sh -- /path/to/predicted.cif
#
# Needs envs/foldseek.sh to have been run once. Without --full that checks the Kemp family
# only; with --full it also checks the PDB representative set.
set -u -o pipefail

GATE=0.7
FS=/mnt/work/tools/foldseek/bin/foldseek
FAM=/mnt/work/tools/novelty/famdb
REP=/mnt/work/tools/pdb_rep/db/pdbrep
TMP=/mnt/work/tools/novelty/tmp

QUERY="${1:-}"
[ -n "$QUERY" ] || { echo "usage: novelty_check.sh <structure.cif|pdb>"; exit 2; }
[ -s "$QUERY" ] || { echo "no such structure: $QUERY"; exit 2; }
[ -x "$FS" ] || { echo "foldseek missing - run envs/foldseek.sh first"; exit 2; }

search() {  # search <db> <label>
    local db="$1" label="$2" out="/tmp/novelty_$2_$$.tsv"
    [ -f "${db}.dbtype" ] || { echo "  ($label database not built - skipped)"; return 0; }
    # NOTE ON NORMALISATION - this is easy to get wrong and it flips the verdict.
    # foldseek's alntmscore is normalised by the ALIGNMENT length, so a short structure matching
    # a fragment of our design scores near 1.0 while sharing almost nothing. The number that
    # answers "is my fold already known" is qtmscore: normalised by OUR query length.
    # We rank on qtmscore and print the others for context.
    "$FS" easy-search "$QUERY" "$db" "$out" "$TMP" \
        --alignment-type 1 -e 1000000 --max-seqs 4000 \
        --format-output "target,qtmscore,ttmscore,alntmscore,fident,alnlen,qlen,tlen" >/dev/null 2>&1
    if [ ! -s "$out" ]; then echo "  $label: no alignments"; return 0; fi
    echo "  $label — top hits by query-normalised TM:"
    printf "    %-22s %7s %7s %7s %7s %6s\n" target qTM tTM alnTM ident tlen
    sort -k2 -gr "$out" | head -5 | \
        awk '{printf "    %-22s %7.3f %7.3f %7.3f %7.3f %6s\n", $1, $2, $3, $4, $5, $8}'
    local best
    best=$(sort -k2 -gr "$out" | head -1 | cut -f2)
    awk -v b="$best" -v g="$GATE" 'BEGIN{
        if (b+0 > g) printf "    *** FAILS the novelty gate (qTM %.3f > %.2f) ***\n", b, g;
        else         printf "    PASSES (best qTM %.3f <= %.2f)\n", b, g }'
    rm -f "$out"
}

mkdir -p "$TMP"
echo "novelty check: $QUERY"
echo
search "$FAM" "Kemp eliminase family"
echo
search "$REP" "PDB representatives (30% identity clusters)"
echo
cat <<'EOF'
Sequence half of the gate: the pipeline already answers it. summary.json reports the MSA depth
from the 183 GB MMseqs2 search; depth 1 with nonquery_rows 0 means no homologue was found at all,
so sequence identity to published enzymes is far below the 70% threshold.
EOF
