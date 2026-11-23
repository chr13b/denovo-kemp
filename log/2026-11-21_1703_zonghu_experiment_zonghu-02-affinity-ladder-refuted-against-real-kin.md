# [2026-11-21 17:03] experiment | zonghu-02 affinity ladder refuted against real kinetics (zonghu)

- **Boltz-2 affinity does not track Kemp catalysis. Do not rank designs with it.** Tested on
  HG3 / HG3.7 / HG3.17, measured k_cat/K_M 160 / 28,000 / 170,000 M-1 s-1 — a **1062-fold** span
  = 4.13 kcal/mol of transition-state stabilisation. Predicted **TS affinity was flat:
  2.062 / 2.003 / 2.060**, a shift of **0.06 % of expected (0.0 sigma)**. Full numbers:
  [zonghu-02](../wiki/experiments/zonghu-02_affinity-ladder-controls.md).
- **The sign was wrong in every arm:** ddG(substrate − TS) came out negative for all three
  (−1.12 / −1.02 / −0.70 kcal/mol), i.e. substrate predicted to bind tighter than the TS analogue,
  which would label HG3.17 — one of the best artificial enzymes known — anti-catalytic. `P(binder)`
  was < 0.5 for all 9 combinations and *inverted* against activity (HG3.17 lowest at 0.33).
- **My pre-registered rule said "pass" and I overrode it.** Rank order was correct at exactly
  2.0 sigma, which my rule's first row accepted. But correct order of 3 items happens 1 in 6 times
  by chance, the TS leg (the quantity k_cat/K_M actually measures) showed nothing, and the sign was
  wrong — so the rule was under-specified, not the result. Recorded as a judgement call, in the open.
- **There is no published K_M for this series to validate "substrate binding" against.** Broom et al.
  Table 1 footnote b: K_M and k_cat "could not be determined accurately because saturation was not
  possible at the maximum substrate concentration tested (2 mM)". These enzymes bind substrate at
  >= mM, far outside where Boltz-2's affinity head was trained. That is the likely root cause.
- **Cost: ~35 min on the two small GPU nodes**, big node untouched — the affinity job needs no
  MMseqs2, so `scripts/20_build_affinity_ladder.py` targets `g6.xlarge` and two run at once.
  Keep that tooling; it is a tested way to run any Boltz-2 affinity job without blocking RFD3.
- Published values disagree between labs by up to 8x for the same enzyme (HG3: 160 here vs 1300 in
  Blomberg et al., both printed in the same table). Worth remembering before trusting any single
  literature k_cat/K_M as ground truth.
