# Kemp eliminase theozyme candidates

16,650 sterically valid theozymes built from observed components, scored, ranked and checked for stability. Open `report/index.html` for the recommendations with images; this file is the index.

## Rules used
1. **Centre:** 6-nitrobenzotriazole (6NT, from 7K4Q chain A) is the TSA and stands in for the substrate.
2. **Catalytic base:** an Asp/Glu carboxylate, or a His–Asp dyad.
3. **π stacker:** a Trp/Phe/Tyr ring on a face of the TSA.
4. **Optional nitro stabiliser:** residue, distance and angles taken from `nitro_enzymes/motif_table.csv`.

All components are real residues from published structures, in the common TSA frame of `kemp_eliminase/structures/aligned_on_substrate/`. The stabiliser is placed by superposing the nitro group it was observed against onto the TSA nitro group (both O assignments, since the group is symmetric); the contact distance, angle and elevation are then re-measured and match the nitro data to within 0.2 Å (checked on T00003: 2.86 Å vs 2.82 Å in the source).

## What you get
| Path | Contents |
|---|---|
| `report/index.html` | Recommendations with images, score bars, Pareto plot, class table, retrospective check, limitations |
| `selected_variants.csv` | The chosen variants (design-relevant slots + the Pareto front), with scores, ranks under each weighting and geometry |
| `candidates_scored.csv` | All 16,650 candidates with component scores, five total scores, five ranks, stability counts |
| `candidates/` | 44 theozyme PDBs (top 20 + every selected variant). Chain A = 6NT, B = base (C = dyad Asp), D = stacker, E = stabiliser; REMARKs carry scores, geometry and fix-atom hints |
| `templates/` | The libraries: 15 base, 17 stacker and 88 nitro-stabiliser templates, with `nitro_stats.csv` (empirical distributions) |
| `report/img/`, `report/theozymes.pse` | PNGs per recommended variant; a PyMOL session with them overlaid |
| `0N_*.py`, `common.py` | The pipeline. Run in order with `/usr/bin/python3` (numpy only); step 6 needs `pymol -cq 06_render.py` |

## Recommendations
Because the ranking depends on the weighting (see below), these come from the Pareto front of geometric quality against published evidence plus design-relevant slots. Rank = position of 16,650 under the default weighting.

| # | ID | Base | Stacker | Nitro anchor | Rank | Role |
|---|---|---|---|---|---|---|
| 1 | T00001 | Glu231 (KE59, 3UZJ) | Trp110 (3UZJ) | none | 1 | Recommended first; best compromise, only candidate in the top 25 under 4 of 5 weightings |
| 2 | T00003 | Glu231 | Trp110 | Met backbone NH (6SRY) | 3 | Same with a data-derived nitro anchor (2.86 Å, 102°, 52°) |
| 3 | T00015 | Asp162 (Des27.7 model) | Phe113 | none | 15 | Computational-only reference (12,700 M⁻¹s⁻¹; 9HVB) |
| 4 | T00031 | Asp162 | Trp110 | Met backbone NH | 31 | Geometry-optimised hybrid on the Pareto front |
| 5 | T01327 | Asp127 (HG, 6SRY) | Trp44 (6SRY) | Met237 NH (6SRY) | 1,327 | Native set of the most active lineage; loose stack, reference |
| 6 | T00094 | His16–Asp45 (KE70-core) | Phe49 | none | 94 | Alternative base chemistry (one template only) |
| 7 | T00072 | Asp162 | Phe49 (3Q2D) | none | 72 | Optional; rank 2 on geometry |
| 8 | T00089 | Asp127 | Phe49 | none | 89 | Optional; tests HG base with a tight stacker |

Alternate binding modes (carboxylate on the N1 side: KempTIM1 Asp24, 1A53-2 Glu178) are included but not recommended: best rank 631, and a base on that side could not reach the substrate C3–H if the substrate binds like the TSA.

## How scoring works
Components (0–1): **base** 0.35, **π** 0.25, **nitro** 0.10 (only if present), **fit** 0.10, **evidence** 0.20; total = weighted mean of the components present, so a stabiliser helps only if it scores above the rest.
- *base*: approach geometry vs the Listov 2025 Rosetta constraint (`theozime.cst`: 127.6°, 120°, in-plane) with 2× tolerances, distance 2.6 Å (observed median), syn and anti carboxylate both accepted. Dyad: His N···N3 3.0 Å and Asp O···His N 2.75 Å. N1-side bases ×0.75.
- *π*: centroid distance 3.8 Å, tilt ≤10°, lateral offset ≤1.5 Å (the tight stackers in the crystals).
- *nitro*: typicality of d, angle and elevation within its residue/contact class in the nitro data, class frequency, Kemp-entry support, aromatic-nitro source.
- *fit*: clashes below 2.2 Å rejected (4,901 combinations), overlaps penalised.
- *evidence*: best published kcat/KM of the lineages (`kemp_eliminase/theozyme/THEOZYME_ORIGIN.md` §3b) and whether components were seen together; modelled structures ×0.85.

Five weightings test sensitivity: default, geometry-only, evidence-heavy, base-first, ignore-nitro.

## Things to know before using the ranking
- **The weights are my choices, not fitted.** Only 1 of 16,650 candidates stays in the top 25 under four of five weightings.
- **The score does not predict activity.** Scoring each lineage's native pair on geometry alone gives Spearman ρ = −0.10 against its best kcat/KM (n = 5; `05_retrospective.py`). The most active lineage (HG) has the loosest stack. It measures closeness to clean, observed contacts.
- **Partly circular for Des27.** The Des27/Des27.7 substrate poses are Rosetta models built with the constraint file the base score uses. The crystal structure 9HVB confirms Asp162's position, but it has no ligand.
- **Most pairings are hypotheses.** Components usually come from different proteins and were never seen together; only T00001, T00015 and T01327 are built from co-observed parts (T00003 adds a stabiliser from another protein).
- **HG3.17 activity (≈2.3×10⁵)** is from a web summary, not the paper text. One His–Asp dyad template only.
- Theozymes are static; the HG lineage's activity depends on conformational ensembles (Otten 2020).

## Reproduce
```bash
cd kemp_theozymes
/usr/bin/python3 01_extract_templates.py && /usr/bin/python3 02_extract_nitro_templates.py
/usr/bin/python3 03_generate_and_score.py && /usr/bin/python3 04_select_and_export.py
/usr/bin/python3 05_retrospective.py && pymol -cq 06_render.py && /usr/bin/python3 07_report.py
```
Inputs: `kemp_eliminase/structures/aligned_on_substrate/`, `kemp_eliminase/metadata/entries.csv`, `nitro_enzymes/{motif_table.csv,curated.csv,structures/}`.
