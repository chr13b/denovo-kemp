#!/usr/bin/env bash
# Install foldseek + the PDB structure database on the cluster, for the novelty gate
# (TM-score <= 0.7 to published structures).
#
# Run ON THE HEAD NODE (download only, no compute):
#   ssh pdh-team 'bash -s' < envs/foldseek.sh
#
# Idempotent: skips anything already present. Everything lands in /mnt/work/tools, which is
# shared by the team, so this is run once for everyone. /mnt/ref is read-only and not ours.
set -e -o pipefail

VERSION="10-941cd33"          # pinned foldseek release
ROOT=/mnt/work/tools
BIN="$ROOT/foldseek/bin/foldseek"
DB="$ROOT/foldseek_db/pdb"

mkdir -p "$ROOT"

if [ -x "$BIN" ]; then
    echo "foldseek already installed: $("$BIN" version 2>/dev/null || echo unknown)"
else
    echo "=== downloading foldseek $VERSION ==="
    cd "$ROOT"
    curl -sSL -o foldseek.tar.gz \
        "https://github.com/steineggerlab/foldseek/releases/download/${VERSION}/foldseek-linux-avx2.tar.gz"
    tar xzf foldseek.tar.gz
    rm -f foldseek.tar.gz
    echo "installed: $("$BIN" version)"
fi

if [ -f "${DB}.dbtype" ]; then
    echo "PDB database already present at $DB"
else
    echo "=== downloading the PDB structure database (several GB, one time) ==="
    mkdir -p "$ROOT/foldseek_db"
    "$BIN" databases PDB "$DB" "$ROOT/foldseek_db/tmp" --threads 4
    rm -rf "$ROOT/foldseek_db/tmp"
fi

echo
echo "foldseek: $BIN"
echo "PDB db:   $DB"
echo "Use it:   \"$BIN\" easy-search <query.pdb|cif> \"$DB\" <out.tsv> <tmpdir> --alignment-type 1 ..."
