# [2026-11-21 13:56] experiment | chris-02 verdict: RFD3 contacts are constant, refolding is binary, half of designs fail (chris)

All four sweep jobs (2–5) finished with no validation warnings. Summaries pulled into
`results/sweep_kemp-<job>_summary.json`; regenerate the table with
`uv run python scripts/30_compare_rfd3_vs_boltz.py`. Full write-up:
[../wiki/experiments/chris-02_seed-sweep-boltz-vs-rfd3-geometry.md](../wiki/experiments/chris-02_seed-sweep-boltz-vs-rfd3-geometry.md).

- **Pre-registered rule returns "systematic": 3 of 4 runs had base drift > +1.5 Å** (+19.39, +5.80, +0.79,
  +12.35). Judge candidates on Boltz-2 geometry.
- **Stronger than that: RFD3 contact distances are constant by construction.** The base contact is
  `2.527 Å` and the donor `3.09 Å` in *every* run, because `select_fixed_atoms` pins the motif atoms and
  the ligand. They are an input, not a measurement, and carry zero information about a design. An RFD3
  contact-distance filter was never possible — not merely unwise. Stop considering it.
- **Refolding is near-binary.** CA RMSD is {0.70, 1.36} or {13.67, 14.63} — nothing between 1.4 and 13.7.
  A design either refolds as designed or collapses with the ligand leaving the site (contacts 15–22 Å,
  iPDE 5.5–6.7). The first gate is "did it fold at all", which is one number.
- **2 of 4 new designs survived (3 of 5 with the baseline).** At 260 AA with default settings, plan on
  throwing away ~half of everything generated. This is the key number for how many designs we can afford.
- **The base contact is the fragile one.** Among designs that folded, the donor barely moves
  (−0.15, −0.02, +0.66 Å) while the base moves +3.38, +5.80, +0.79 Å. Geometry dominates scoring, so base
  placement is where points are lost.
- **Seed 4 beats the reference on everything measured:** iPDE 1.5184 vs 1.8669, CA RMSD 0.704 vs 1.433,
  base 3.32 Å, donor 3.75 Å — and it is not the shared example, so it is submittable in principle.
  **Novelty is unchecked**; that must happen before it takes one of our 20 slots.
- Next: novelty-check seed 4; test whether base burial (CA count within 12 Å) computed on the RFD3
  backbone predicts which designs survive refolding, using these 5 runs as the first labelled examples;
  then a fixed-design / Boltz-seed-only run of 5 replicates on seed 4 to measure the consistency term the
  way the organizers do.
