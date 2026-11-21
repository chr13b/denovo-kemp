# pre_analysis: published Kemp structures and theozyme building

Standalone analysis done before the design runs: what the published Kemp eliminase structures say about a catalytic
site (base, π stacker, nitro and leaving-group donors around the 6NT transition-state analog), and a generator that
builds and ranks theozyme candidates from those observations. It moved here from four loose folders; they are kept
as siblings so their cross-folder relative paths still work. Paths in the sub-READMEs are relative to this folder.

## Where to start
- [kemp_theozymes_v2/report/index.html](kemp_theozymes_v2/report/index.html) — the current recommendations (open in a browser), with methods and caveats
- [kemp_theozymes_v2/README.md](kemp_theozymes_v2/README.md) — what v2 added and how to rerun it
- [kemp_eliminase/theozyme/THEOZYME_ORIGIN.md](kemp_eliminase/theozyme/THEOZYME_ORIGIN.md) — where the published theozymes came from and the best kcat/KM per family
- [kemp_eliminase/figures/kemp_design_vs_activity.html](kemp_eliminase/figures/kemp_design_vs_activity.html) — design vs activity charts

## The four folders
| Folder | What it holds | Reads from |
|---|---|---|
| [kemp_eliminase/](kemp_eliminase/README.md) | 100 published Kemp eliminase entries and 9 scaffolds, all structures aligned on the substrate, the theozyme extraction, the origin write-up, charts | RCSB, GitHub, Zenodo |
| [nitro_enzymes/](nitro_enzymes/README.md) | Nitro-group contacts in 57 enzyme structures; the motif table of donor and stacker geometries | RCSB |
| [kemp_theozymes/](kemp_theozymes/README.md) | v1 generator: 16,650 theozymes, scoring, ranking, report | the two folders above |
| [kemp_theozymes_v2/](kemp_theozymes_v2/README.md) | v2 generator: adds leaving-group donors, nitro stackers, sampling and a real-substrate check; 84,271 candidates | all three above |

## What is not in git (re-create it)
Bulk downloads and regenerable intermediates are gitignored (see the end of the repo `.gitignore`).

| Ignored | How to get it back |
|---|---|
| `kemp_eliminase/structures/**/*.cif, *.pdb` (RCSB downloads), `kemp_eliminase/code/`, `kemp_eliminase/theozyme/rosetta_denovoKemp/` | `python3 kemp_eliminase/fetch_structures.py` |
| `kemp_eliminase/structures/aligned_on_substrate/` (aligned copies) | `pymol -cq kemp_eliminase/theozyme/align_full_structures.py`, run from `kemp_eliminase/` |
| `nitro_enzymes/structures/` | `nitro_enzymes/nitro_contacts.py` downloads them |
| `kemp_theozymes_v2/structures/` (7EPO, 7Y9J, aligned real-substrate complexes) | `10_substrate.py`, `11_real_substrate_complexes.py` |
| `*.pkl`, `*.pse` (intermediates and PyMOL sessions) | rerun the stage that writes them (`03_generate_and_score.py` in v1, `15_generate_v2.py` in v2; PyMOL steps for sessions) |
| `kemp_theozymes_v2/candidates_v2.csv` | tracked as `candidates_v2.csv.gz`; step 15 rewrites the plain CSV |

The Fleishman-lab repo (`denovoKemp`) has no licence file, so it is fetched, not committed.

## Run order and requirements
1. `kemp_eliminase/`: `fetch_structures.py` → `theozyme/extract_theozyme.py` → `pymol -cq theozyme/superpose_theozyme.py` → `pymol -cq theozyme/align_full_structures.py` → `figures/make_geometry.py`, `make_data.py`, `build.js`
2. `nitro_enzymes/`: `nitro_contacts.py` → `nitro_geometry.py` → `nitro_plots.py` and `nitro_motifs.py`
3. `kemp_theozymes/`: `01`–`07` in order (`06_render.py` runs under PyMOL)
4. `kemp_theozymes_v2/`: `10`–`19` in order (`18_render_v2.py` under PyMOL)

Needs Python 3 with numpy (scoring), `gemmi pandas matplotlib` (nitro_enzymes only), PyMOL, and node (charts). This is
**not** part of the repo's `uv` environment, and the scripts are not in the repo's nano-style (no `Config`, no
`start_run`); ruff excludes this folder (`pyproject.toml`).

## Provenance and status
No numbers here come from a `runs/` directory: they are the output of these scripts, committed as written. Known
weak spots are listed in the reports (weights are the author's choices; geometry scores did not predict lineage
activity; the HG3.17 activity is from a web summary and not verified in the paper text).
