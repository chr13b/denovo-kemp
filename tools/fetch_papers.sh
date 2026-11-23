#!/usr/bin/env bash
# Fetch the open-access literature for this project into data/papers/ (gitignored - we do not
# commit copyrighted PDFs). The annotated reading list is wiki/literature.md.
#
#   bash tools/fetch_papers.sh
#
# Idempotent. Paywalled papers are listed in wiki/literature.md with their DOI instead.
set -u

DEST="${KEMP_DATA_DIR:-data}/papers"
mkdir -p "$DEST"

fetch() {  # fetch <short-name> <url>
    local name="$1" url="$2" out="$DEST/$1.pdf"
    if [ -s "$out" ]; then echo "  have     $name"; return 0; fi
    if curl -sSL --max-time 120 -A "denovo-kemp/1.0" -o "$out" "$url" 2>/dev/null \
       && [ -s "$out" ] && head -c 4 "$out" | grep -q "%PDF"; then
        echo "  fetched  $name  ($(du -h "$out" | cut -f1))"
    else
        rm -f "$out"; echo "  MISSING  $name  (paywalled or moved: $url)"
    fi
}

# --- Methods we are actually running -------------------------------------------------------
fetch rfdiffusion2_natmethods2025 \
    "https://www.ipd.uw.edu/wp-content/uploads/2025/12/s41592-025-02975-x.pdf"
fetch rfdiffusion2_biorxiv2025 \
    "https://www.biorxiv.org/content/10.1101/2025.04.09.648075v1.full.pdf"
fetch rfdiffusion_watson2023 \
    "https://www.nature.com/articles/s41586-023-06415-8.pdf"
fetch proteinmpnn_dauparas2022 \
    "https://www.biorxiv.org/content/10.1101/2022.06.03.494563v1.full.pdf"
fetch ligandmpnn_dauparas \
    "https://www.biorxiv.org/content/10.1101/2023.12.22.573103v1.full.pdf"
fetch foldseek_vankempen2023 \
    "https://www.nature.com/articles/s41587-023-01773-0.pdf"

# --- Kemp eliminases: the actual chemistry -------------------------------------------------
fetch kemp_privett2012_pnas \
    "https://www.pnas.org/doi/pdf/10.1073/pnas.1118082108"
fetch kemp_rothlisberger2008 \
    "https://www.nature.com/articles/nature06879.pdf"
fetch kemp_blomberg2013 \
    "https://www.nature.com/articles/nature12623.pdf"

# --- De novo enzyme design, recent ----------------------------------------------------------
fetch serine_hydrolases_science2025 \
    "https://www.ipd.uw.edu/publication-pdfs/358/00658c7b2ab054d306d78f892a6f98bd/science.adu2454.pdf"

echo
echo "in $DEST:"
ls -1sh "$DEST" 2>/dev/null | sed 's/^/  /'
