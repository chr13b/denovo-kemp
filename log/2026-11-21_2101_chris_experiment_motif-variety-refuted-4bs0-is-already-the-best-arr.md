# [2026-11-21 21:01] experiment | Motif variety refuted: 4BS0 is already the best arrangement (chris)

- TODO

- **chris-06 is refuted as a lever.** The most geometrically distinct family motif (8USL_B, 2.20 Å
  from 4BS0 in the pinned-atom distance matrix) gives **worse** backbones than the arrangement the
  pipeline already ships: median CA RMSD 1.99 vs 1.33 Å, 53 % vs 84 % refolding under 2 Å, best base
  contact 3.52 vs 2.90 Å, median 9.73 vs 6.66 Å.
- Predictable in hindsight: **4BS0 is the 1.09 Å structure of HG3.17**, the most optimised variant in
  the family. Farthest-point selection chose the most *different* motif, not the most *useful* one.
- Both 0/32 hit counts are uninformative: at the measured ~3 % rate, 32 sequences expect 1 hit and
  P(0) ≈ 0.38. **Use 72+ sequences per sweep** or a zero means nothing. The distributions are what
  carry the signal at n = 32.
- The design stage itself was clean (job 34, 0 failures): a motif lifted from any family member
  satisfies the launcher verbatim and RFD3 hits it to 0.013-0.016 Å. Tooling kept.
- **Net procedure across all four experiments:** many RFD3 seeds on the 4BS0 motif (12 min each) →
  short sweep to screen on **designability** (median CA RMSD, ~16 min) → deep sweep only the
  designable ones → 5-seed replication of the hits → novelty gate → submit across folds.
  Designability is the property that varies (0.77 / 1.33 / 1.99 / 10.67 Å across four backbones), it
  is cheap, and nothing the pipeline reports about a single design reveals it.
