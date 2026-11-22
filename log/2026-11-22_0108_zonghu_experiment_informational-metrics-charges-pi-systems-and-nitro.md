# [2026-11-22 01:08] experiment | informational metrics: charges, pi systems, nitro H-bonds (zonghu)

- **Three measurements added that are deliberately NOT scored.** They are not
  organizer criteria, so they are reported as bare numbers with no verdict -
  turning an unscored observation into a pass/fail would invent a criterion nobody
  is ranked on. `tests/test_diagnostics.py::test_diagnostics_never_enter_the_score`
  asserts the keys are disjoint from `kemp.scoring.WEIGHTS`, so the separation is
  enforced by the suite rather than by a comment.
- **Charge environment, both sides, per residue within 6 A.** Criterion 4 counts CA
  atoms around the base; that says how enclosed it is and nothing about whether the
  carboxylate is deprotonated at pH 7. `zonghu_vA_s2`, the design the scorer ranks
  first, carries **net -3 around its base and -5 around its donor, with no positive
  charge at all near the base** - three carboxylates clustered around a catalytic
  carboxylate. That raises its pKa and could leave the base protonated and inert.
  **Maximising burial without this check can select inactive designs**; the two
  quantities pull against each other. Reported, not scored.
- Counted per RESIDUE, not per atom. An earlier atom-wise pass gave -6 for the base
  because it counted both oxygens of every carboxylate. One aspartate is one charge.
- **Nearest pi system, any aromatic, not just Trp.** Several designs carry no
  tryptophan at the motif position and LigandMPNN often puts Phe, Tyr or His there
  instead. **The pi-stack that zonghu-01 built the theozyme around is largely absent
  from the final structures**: in `vA_s2` the Trp is edge-on at 4.72 A and 59 deg,
  and `chris_seedsweep_s4` (rank 2) has no aromatic within 13 A of the ligand. In
  several designs the nearest pi system is a residue the motif never specified.
- **H-bonds to the nitro group** (6NT: O11/O21 on NO1), heavy-atom donor within
  3.5 A. The nitro group delocalises the developing negative charge, so a bond here
  is real extra stabilisation no criterion sees. **Both top-ranked designs have
  zero.** `zonghu_vA_s1` has three (ARG157 twice, THR181).
- Honest limits recorded in the module: no angle criterion and no hydrogens, because
  Boltz-2 does not output them, so a hit is a *candidate* bond. `hb_s3`'s LYS229:NZ
  at **1.90 A** is too short for a hydrogen bond and is a steric clash - reported as
  measured rather than filtered out, because dropping it would hide a defect.
- New: `src/kemp/diagnostics.py`, `tests/test_diagnostics.py` (14 tests),
  `scripts/38_report_diagnostics.py`, `results/criteria/diagnostics.json`, and a
  section in `wiki/scoring.md` that states up front these never enter the score.
