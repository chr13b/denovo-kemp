#!/usr/bin/env bash
# Install foldseek and build the structure databases used for the novelty gate
# (TM-score <= 0.7 to published structures).
#
# Run ON THE HEAD NODE (downloads only, no compute):
#   ssh pdh-team 'bash -s' < envs/foldseek.sh            # binary + Kemp family (fast, ~1 min)
#   ssh pdh-team 'bash -s' < envs/foldseek.sh --full     # also the PDB representative set (~1 h, 10 GB)
#
# Idempotent. Everything lands in /mnt/work/tools, shared by the team, so this is run once.
#
# NOTE: foldseek's own `foldseek databases PDB` does NOT work from this cluster — the
# steineggerlab mirror returns HTTP 429 (rate limited) and foldseek silently untars the 17-byte
# error page. Verified 2026-11-21 for PDB, CATH50 and AlphaFold/Swiss-Prot. We therefore build
# the databases from RCSB directly, which has no such limit.
set -u -o pipefail

VERSION="10-941cd33"
ROOT=/mnt/work/tools
BIN="$ROOT/foldseek/bin/foldseek"
FULL=0
[ "${1:-}" = "--full" ] && FULL=1

mkdir -p "$ROOT"

# ---------------------------------------------------------------- 1. the binary
if [ -x "$BIN" ]; then
    echo "foldseek already installed ($("$BIN" version 2>/dev/null))"
else
    echo "=== downloading foldseek $VERSION ==="
    cd "$ROOT"
    curl -sSL -o foldseek.tar.gz \
        "https://github.com/steineggerlab/foldseek/releases/download/${VERSION}/foldseek-linux-avx2.tar.gz"
    tar xzf foldseek.tar.gz && rm -f foldseek.tar.gz
    echo "installed: $("$BIN" version)"
fi

# ---------------------------------------------------------------- 2. the Kemp family (always)
# The structures our designs are most likely to resemble, since our motif came from HG3.17.
REF="$ROOT/pdb_ref"
mkdir -p "$REF"
echo "=== Kemp eliminase family from RCSB ==="
for ID in 4BS0 3NYD 2RKX 3IIO 3IIV 1THF 1A53; do
    F="$REF/${ID}.cif"
    if [ ! -s "$F" ]; then
        curl -sSL --max-time 60 -o "$F" "https://files.rcsb.org/download/${ID}.cif" 2>/dev/null
        if [ ! -s "$F" ] || head -1 "$F" | grep -qi html; then rm -f "$F"; echo "  skip $ID"; continue; fi
    fi
    echo "  have $ID"
done
if [ ! -f "$ROOT/novelty/famdb.dbtype" ]; then
    mkdir -p "$ROOT/novelty"
    "$BIN" createdb "$REF"/*.cif "$ROOT/novelty/famdb" >/dev/null 2>&1 && echo "  family db built"
fi

# ---------------------------------------------------------------- 3. PDB representatives (--full)
if [ "$FULL" = "1" ]; then
    WORK="$ROOT/pdb_rep"
    mkdir -p "$WORK/cif"
    if [ ! -s "$WORK/clusters.txt" ]; then
        echo "=== RCSB 30% sequence-identity cluster list ==="
        curl -sSL --max-time 180 -o "$WORK/clusters.txt" \
            "https://cdn.rcsb.org/resources/sequence/clusters/clusters-by-entity-30.txt"
    fi
    awk '{print $1}' "$WORK/clusters.txt" | cut -d_ -f1 | tr 'a-z' 'A-Z' | sort -u > "$WORK/ids.txt"
    echo "=== downloading $(wc -l < "$WORK/ids.txt") representatives (8-way, resumable) ==="
    download() {
        F="/mnt/work/tools/pdb_rep/cif/${1}.cif.gz"
        [ -s "$F" ] && return 0
        curl -sSL --max-time 45 -o "$F" "https://files.rcsb.org/download/${1}.cif.gz" 2>/dev/null
        [ -s "$F" ] || rm -f "$F"
    }
    export -f download
    xargs -a "$WORK/ids.txt" -P 8 -I{} bash -c 'download "$@"' _ {} 2>/dev/null
    echo "  have $(ls -1 "$WORK/cif" | wc -l) structures, $(du -sh "$WORK/cif" | cut -f1)"
    echo "=== building foldseek database (takes a while; 40k structures) ==="
    rm -rf "$WORK/db"; mkdir -p "$WORK/db"   # foldseek will NOT create this directory itself
    # Pass the directory, not a glob: 40k filenames can exceed the shell's argument limit.
    "$BIN" createdb "$WORK/cif/" "$WORK/db/pdbrep" --threads 4 2>&1 | tail -2
    [ -f "$WORK/db/pdbrep.dbtype" ] || { echo "STOP: createdb produced no database"; exit 1; }
fi

echo
echo "foldseek:   $BIN"
echo "family db:  $ROOT/novelty/famdb"
[ "$FULL" = "1" ] && echo "PDB rep db: $ROOT/pdb_rep/db/pdbrep"
echo "Check a design: bash tools/novelty_check.sh <structure.cif|pdb>"
