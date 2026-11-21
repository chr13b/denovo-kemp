# Data

Every dataset we use, with enough detail to get the exact same bytes again. The files live in `data/` (gitignored).
Download with `kemp.data.fetch(url, dest, checksum=...)`. For files obtained another way (USB stick, shared drive),
record `kemp.data.sha256(path)`. Add one row per dataset and never edit other people's rows; add a new row instead.

| Dataset | Path in data/ | Source (URL or who provided it) | Version / date | sha256 | Fetched by | Added by |
|---------|---------------|---------------------------------|----------------|--------|------------|----------|
| PDB 7K4Z — Kemp eliminase HG3.17 + ligand 6NT, 1.08 Å (geometry reference; ineligible as a design) | `reference/7K4Z.pdb` | https://files.rcsb.org/download/7K4Z.pdb | RCSB, downloaded 2026-11-21 | `ec7451e03db3b74f9a58589f61782dd94818555544eba23d4a83e40899eaca85` | `scripts/30_measure_theozyme_geometry.py` | flavia |
