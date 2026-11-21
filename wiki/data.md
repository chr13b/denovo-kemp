# Data

Every dataset we use, with enough detail to get the exact same bytes again. The files live in `data/` (gitignored).
Download with `kemp.data.fetch(url, dest, checksum=...)`. For files obtained another way (USB stick, shared drive),
record `kemp.data.sha256(path)`. Add one row per dataset and never edit other people's rows; add a new row instead.

| Dataset | Path in data/ | Source (URL or who provided it) | Version / date | sha256 | Fetched by | Added by |
|---------|---------------|---------------------------------|----------------|--------|------------|----------|
| _none yet_ | | | | | | |
| RCSB Kemp eliminase entries (100) + scaffolds (9) | `pre_analysis/kemp_eliminase/structures/` (not `data/`) | https://files.rcsb.org, IDs in `pre_analysis/kemp_eliminase/metadata/entries.csv` | fetched 2026-11-21 | n/a: RCSB files, no pinned checksum | `pre_analysis/kemp_eliminase/fetch_structures.py` | Mario Kunz |
| RCSB nitro-enzyme entries (57) | `pre_analysis/nitro_enzymes/structures/` (not `data/`) | https://files.rcsb.org, IDs in `pre_analysis/nitro_enzymes/curated.csv` | fetched 2026-11-21 | n/a: RCSB files, no pinned checksum | `pre_analysis/nitro_enzymes/nitro_contacts.py` | Mario Kunz |
| denovoKemp repo (no licence file) + Zenodo 10.5281/zenodo.14563437 (CC-BY-4.0) | `pre_analysis/kemp_eliminase/code/` (not `data/`) | github.com/Fleishman-Lab/denovoKemp at `c2a7421`; zenodo.org/records/14563437 | 2025-09-18 (repo commit); 2024-12-27 (Zenodo) | n/a | `pre_analysis/kemp_eliminase/fetch_structures.py` | Mario Kunz |
