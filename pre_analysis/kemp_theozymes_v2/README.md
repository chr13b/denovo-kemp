# Kemp theozymes v2

Extends `../kemp_theozymes/` with three ideas, plus a cross-check against the real substrate (5-nitro-1,2-benzisoxazole, CCD H5J). Open `report/index.html` for the recommendations with images.

## What was added
| Idea | Implemented as | Where |
|---|---|---|
| 1. Leaving-group donor | Optional N–H/O–H donor within 3.6 Å of the TSA N1 (the ring-oxygen side). 12 templates: Gln50 NE2 (HG3.x, 4 clusters), His NE2, Cys84/Met N–H, Trp NE1, Asn ND2. Backbone C=O and carboxylate acceptors excluded. | `12_lg_templates.py`, `templates/lg_templates.csv` |
| 4. Nitro stacker | An aromatic stacked on the nitro group (14 observations in `nitro_enzymes/motif_table.csv` → 18 placed templates), used as the primary stacker or as a second one (sandwich). | `13_nitro_pi_and_real_templates.py` |
| 7. Continuous sampling | Carboxylate bases on a parameter grid and ring stackers on a height/offset/tilt/face grid, each built by superposing observed rotamers (clustered from every project structure); donors and nitro stackers perturbed ≤12°/≤0.25 Å. | `14_build_components.py` |
| 9. Real-substrate cross-check | The real substrate is superposed on the TSA (0.045 Å RMSD) and every candidate is tested for proton transfer, ground-state fit and clashes; three real-substrate crystal complexes are analysed in the same frame. | `10_substrate.py`, `11_real_substrate_complexes.py`, `lib2.py:substrate_check` |

Search: all base × primary-stacker pairs are scored (29,620 valid), then optional contacts are added in stages (second stacker, nitro donor, leaving-group donor) with per-class retention. 84,271 candidates; 29,340 contain no grid-sampled component; 3,402 distinct observed combinations.

## The real-substrate cross-check
- **Model check (every candidate):** with the real substrate in place of the TSA, observed N3-side bases give C3–H···O 1.2–2.0 Å at 111–179°, need 0.4–0.8 Å of retraction for a ground-state fit, and score 0.56–0.98. Every N1-side base gives H···O 5.4–5.7 Å at 22–31° (score 0.50, proton-transfer 0.00): the C–H points away from the base. Best: Glu231/3UZJ (0.98) and Des27.7 Asp162 (0.98).
- **Crystal complexes with the real substrate (6DNJ, 7EPO, 7Y9J):** none shows a productive arrangement (no base near C3 in 6DNJ and 7Y9J; Glu127 sits on the O1 side in 7EPO). They cannot validate a theozyme, but supply real donors (KSI Trp48 NE1 at O1, His123 NE2 and Lys439 NZ at the nitro). `real_substrate_contacts.csv`.
- **Limits:** a model check, not a validation; the base is retracted rigidly and the protein's response is not modelled.

## Findings
- Trp44 (HG) is a **nitro stacker**: as a ring stacker its π score was 0.39, as a nitro stacker 0.99, and the HG set rises from rank 1,327 (v1) to rank 1. But only the HG-2 crystal (3NYD) places Trp44 that way; in HG3.17-lineage crystals (6SRY) it sits 3.7 Å off the nitro (score 0.10). The top candidate is therefore a lineage composite.
- Ring stackers suit the KE59 base (0.918 vs 0.845 with a nitro stacker); nitro stackers suit the HG base (0.899 vs 0.795).
- A leaving-group donor raised the total in 66% of 430 matched pairs, median +0.008. Gln50 and His donors score 0.92–0.98; backbone N–H donors ≈0.3.
- Sandwiches (a stacker on both sites) never reach the top 25 distinct combinations.
- Grid-sampled components score ≈1.0 because they are built from the scoring targets, and carry no evidence.

## Recommended (details and risks in the report)
| # | ID | Components | Distinct rank (default) |
|---|---|---|---|
| 1 | V00001 | Asp127 + Trp44 (nitro stack) + Met237 N–H + Gln50 | 1 |
| 2 | V00009 | Asp127 + Trp44 (nitro stack) + Gln50 | 3 |
| 3 | V00023 | Glu231 + Trp110 (ring), KE59-type minimal | 7 |
| 4 | V00128 | Glu231 + Trp110 + Gln50 | 21 |
| 5 | V00236 | Asp127 + Trp44 (nitro stack), rules only | 39 |
| 6–11 | V00367, V10561, V13877, V00189, V00552, V64285 | sandwich; Des27.7 base; His–Asp dyad; real-substrate donor; sampled base; N1-side control | see report |

`candidates/` holds 75 PDBs (TS-like with the TSA, and `__michaelis` with the real substrate and the base retracted). `*` = grid-sampled, `~` = perturbed.

## Caveats
Weights are my choices; observed candidates are ranked within their own pool (grid-sampled ones are scored against the targets they were built from). Des27 poses are Rosetta models built with the constraint file used for scoring. The HG3.17 activity (≈2.3×10⁵) is from a web summary. One His–Asp dyad template. Perturbed donors are mildly selected (median score change +0.001). Geometry scores did not predict lineage activity in v1 (ρ = −0.10, n = 5).

## Reproduce (from `kemp_theozymes_v2/`, `/usr/bin/python3`; `pymol -cq` for step 18)
```bash
python3 10_substrate.py && python3 11_real_substrate_complexes.py && python3 12_lg_templates.py && python3 13_nitro_pi_and_real_templates.py
python3 14_build_components.py && python3 15_generate_v2.py && python3 16_select_export_v2.py
python3 17_summaries.py && pymol -cq 18_render_v2.py && python3 19_report_v2.py
```
Needs `../kemp_theozymes/` (v1 templates), `../kemp_eliminase/` (aligned structures) and `../nitro_enzymes/`. Step 10 downloads 7EPO and 7Y9J from RCSB.
