# [2026-11-22 00:29] experiment | zonghu-03 novelty gate and the five-criteria scorer (zonghu)

- **A team design already fails the hard novelty gate.** `foldseek` is not in the
  organizers' image, so it is now installed at `/mnt/work/software/bin/foldseek`.
  TM-score against 7K4U over all 15 cofolded designs puts `chris_seedsweep_s3` at
  **0.705**, above the <= 0.70 gate, while it ranks 5th of 15 on contact distances -
  it could plausibly have been submitted. **chris needs to know.** A quarter of all
  designs sit between 0.63 and 0.71, so this is a routine risk of scaffolding from
  an HG3 motif, not an edge case. Method, table and limits: `wiki/novelty.md`.
- **Caveat that decides that case:** foldseek reports `alntmscore` 0.707 and
  `qtmscore`/`ttmscore` 0.705, and `challenge.md` does not say which normalization
  the organizers use. At 0.705 against 0.70 the choice flips the verdict - an open
  question for the organizers. Also, only 7K4U was used as reference, so "OK" means
  "not HG3-like", not "novel against the PDB".
- **I had been gating on the wrong confidence metric.** The funnel used pLDDT >= 80
  and ipTM >= 0.6; neither is an organizer criterion. The scored one is **iPDE**, was
  in every `summary.json` as `complex_ipde`, and went unused. They disagree
  materially: `zonghu_vA_s2` reads pLDDT 86.1 ("good") at iPDE 2.42, which is 10th of
  14. Fixed by `check_interface_error`; `check_boltz_confidence` is kept but marked
  as not scored.
- **All five criteria now have a metric, and none is redundant.** Added
  `check_approach_geometry` (K2 - angle *and* ring plane, `max` not mean, because the
  organizers say the worse of the two decides; validated against the crystal, which
  reproduces its own reference values with 0 deviation) and `check_base_burial` (K4).
  Spearman between criteria over n=15 stays between 0.21 and 0.58, so every criterion
  carries its own information. K4 correlates negatively with the distance terms -
  more burial, better contacts - which is physically the right direction.
- **Combined multiplicative score ranks `zonghu_vA_s2` first at 0.2965**, a factor of
  2.5 ahead of `chris_seedsweep_s4`, because it is the only design with no weak
  factor. **K2 is the bottleneck for all three leaders without exception**; below them
  the binding constraint switches to the donor distance. The sub-score shapes are
  ours, not the organizers' - the ranking is robust, the absolute products are not
  points and should not be quoted as such. Details: `wiki/scoring.md`.
- **There is no cheap pre-filter, and that is now measured rather than assumed.**
  Over 11 designs with known Boltz-2 outcomes, no RFD3-stage feature predicts success
  (RoG, helix/sheet/coil, clashes, and base burial on the RFD3 backbone all give
  |rho| < 0.6 at n=11). The backbones are nearly identical to each other (RoG
  16.1-17.0 A) while outcomes range 2.27-13.21 A on the base contact: what decides
  the result happens entirely inside LigandMPNN and Boltz-2. Stage-1 gating is a
  **defect filter**, not a quality filter.
- **K5 pose consistency is still unmeasured** and is deliberately not set to 1.0 in
  the product, so the score is not flattered by a missing term. Replicate runs that
  vary only the Boltz-2 seed on one fixed sequence are jobs 81/82 (`vA_s2`, `vA_s3`).
- Incidental: `tools/status.py` is not encoding-safe. A log entry containing
  characters outside cp1252 (`<=`, Greek rho, em dash) makes `test_status_runs` fail
  on Windows with `stdout` None, because the subprocess reader thread dies decoding
  it. This entry is therefore plain ASCII. Worth fixing in `status.py` itself with an
  explicit `encoding="utf-8"`, but that is a shared file - not touching it on a
  personal branch.
- New: `scripts/32_check_sequence_novelty.py`, `scripts/33_combine_criteria.py`,
  `scripts/34_score_five_criteria.py`, `scripts/35_test_cheap_prefilter.py`,
  `tests/test_criteria.py`, `wiki/novelty.md`, `wiki/scoring.md`, evidence in
  `results/criteria/`.
