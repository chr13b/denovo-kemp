# [2026-11-21 20:10] experiment | Three anchors lose: designability is the hidden cost of motif constraints (chris)

- TODO

- **chris-05 (job 31) is refuted**, and I had predicted the opposite. 72 sequences on zonghu's
  three-anchor Trp44 backbone: **0/72 inside either window**, best base 3.26 Å, median donor
  **18.92 Å** (the ligand leaves the pocket), median CA RMSD 2.02 Å, only 35/72 refolding under 2 Å.
  Seed 4's two-anchor backbone, same protocol: best base 2.38 Å, median donor 4.68 Å, median CA RMSD
  0.77 Å, 70/72 refolding, **2/72 inside both windows**.
- The mechanism: both motifs are satisfied in design space (RFD3 deviation 0.0129 vs 0.0167 Å), so
  `fixed_pair_distance_max_deviation` cannot see the cost. Pinning four things at once (base, donor,
  indole plane, whole ligand) yields a backbone **LigandMPNN cannot write a stabilising sequence for**.
- New usable concept: **backbone designability = median CA RMSD over a sequence sweep.** It is a
  per-backbone property, it tracks the in-window hit rate, and it needs a sweep to measure - which is
  why chris-02's single-sequence verdicts were unreliable in both directions.
- zonghu's job 7 was therefore not unlucky: CA RMSD 4.26 Å is the tail of a distribution whose median
  is 2.02 Å. Note added to `wiki/team.md` correcting my earlier note to them.
- Free reproducibility check: the three natural-enzyme controls returned numbers identical to job 27
  (4BS0 2.49/6.08, 3NYD 3.49/2.80, 7K4U 2.11/5.34), so the two sweeps are directly comparable.
- Consequence: keep the minimal two-anchor motif; get backbone diversity from different crystal
  *arrangements* of those two anchors (chris-06, jobs 35/36), not from more anchors.
