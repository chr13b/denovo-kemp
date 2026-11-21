# [2026-11-21 18:27] decision | RFD3 hits the geometry window; the loss is entirely in the refold (chris)

- TODO

- `summary.json` reports the catalytic contacts **twice** — on the RFD3 backbone and on the Boltz-2
  refold. Comparing the two columns across all 6 full-pipeline runs: **RFD3 gives base 2.53 Å / donor
  3.09 Å every single time**, dead centre in the 23-structure crystal window (2.41–2.69 / 2.92–3.60).
  `rfd3.fixed_pair_distance_max_deviation_angstrom` is 0.013 Å.
- Therefore **100 % of the geometric loss happens in the refold**, not in generation. Base drift was
  +0.79 (seed 4), +3.38 (ref), +5.80 (seed 3), +9.46 (zonghu-07), +12.35, +19.39 Å, tracking
  `backbone_ca_rmsd_from_rfd3_angstrom` almost monotonically.
- `ligandmpnn_scores` reads `id: 1, T: 0.1` on every run: **one near-deterministic sequence per
  backbone.** The sequence is the only variable between a 0.70 Å and a 14 Å refold, and we sampled it
  once. At 6 s (LigandMPNN) + 19 s (Boltz-2), 64 samples cost 27 min — less than two new backbones.
- zonghu's Trp44 theozyme (`/mnt/work/projects/zonghu_trpopt_s1/inputs/Kemp.json`) also gave an
  in-window RFD3 backbone (2.53 / 3.20 Å) and lost it at CA RMSD 4.26 Å. **The motif was never
  refuted — it was tested with one sequence.**
- Boltz-2's affinity head (zonghu's `aff_*` runs, 27 predictions) separates TS analogue from substrate
  and product with zero overlap in all 3 real enzymes, but scores HG3 and HG3.17 identically (2.06 vs
  2.06) despite a ~1000× rate difference. Usable as a negative filter, useless for ranking.
- Decision: **sequence oversampling on seed 4's existing backbone is the next job** (primer §7 Idea A),
  preceded by a 19 s instrument check — fold HG3.17's real sequence and measure the contacts with our
  own code, since we judge against crystal distances but measure with Boltz-2.
