# Data

Every dataset we use, with enough detail to get the exact same bytes again. The files live in `data/` (gitignored).
Download with `kemp.data.fetch(url, dest, checksum=...)`. For files obtained another way (USB stick, shared drive),
record `kemp.data.sha256(path)`. Add one row per dataset and never edit other people's rows; add a new row instead.

| Dataset | Path in data/ | Source (URL or who provided it) | Version / date | sha256 | Fetched by | Added by |
|---------|---------------|---------------------------------|----------------|--------|------------|----------|
| HG3 K50Q + 6NT theozyme, crystal geometry | tracked in repo: `results/theozyme/theozyme_7k4u_core.pdb` | PDB **7K4U** chain A (Otten et al., Science 2020, doi 10.1126/science.abd3623), reduced to TRP44+GLN50+ASP127+6NT by `kemp_rfd3_workflow/scripts/extract_theozyme_7k4u.pml` | 7K4U; extracted 2026-11-21 | `cf942a2440605b2fed7f9675020b227bb9c65abca82f3b300575a3dedca149c2` | zonghu | zonghu |
| Same theozyme, TRP44 idealised π-stack | tracked in repo: `results/theozyme/theozyme_7k4u_core_trpopt.pdb` | derived from the row above by `kemp_rfd3_workflow/scripts/optimize.py` (rigid-body TRP44 placement; 6NT/ASP127/GLN50 byte-for-byte unchanged) | 2026-11-21 | `e8023fe75c90f564c230f693f46172cd2b6273f8385a87d19f7aa3800dccb69c` | zonghu | zonghu |
