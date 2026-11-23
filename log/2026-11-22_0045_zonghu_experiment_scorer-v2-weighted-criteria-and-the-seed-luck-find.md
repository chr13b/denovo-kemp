# [2026-11-22 00:45] experiment | scorer v2: weighted criteria and the seed-luck finding (zonghu)

- **Our headline number was seed luck, and that is the most important result here.**
  Jobs 81/82 refolded one fixed sequence with five Boltz-2 seeds each. `vA_s2`, the
  design we had been quoting as base 3.65 / donor 3.00 A, gives donor contacts of
  3.00, 3.37, 3.56, 4.61, 4.94 across seeds - mean 3.90, std 0.83. **The 3.00 A we
  celebrated was the best of five draws, not a property of the design**; the 3.65 A
  base was conversely the worst of its five. `vA_s3` is simply not reproducible
  (base 4.87-10.84 A, std 2.43), so its v1 lead on K2 and K3 was one lucky draw.
  Any design ranked on a single Boltz-2 prediction is ranked on noise.
- **I found a real bug in my own approach-geometry metric.** The first v2 compared
  *signed* dihedrals against the crystal's +166.8 (base) and -164.0 (donor). The
  sign only says which side of the ring plane the contact leans to, and both sides
  are the same approach, so a mirror-image contact was punished by up to 330 deg.
  That drove `s_approach` to 0.000 for 14 of 16 designs. Correct measure is
  **180 - |dihedral|**, making the reference 13.2 / 16.0 deg. After the fix `vA_s2`
  went from 70 to 58 deg worst deviation and `chris_seedsweep_s4` from 124 to 92.
  `tests/test_scoring.py::test_out_of_plane_is_sign_independent` locks it down.
- **The two contacts do not share a target distance.** Measured in 7K4U by
  `scripts/37_measure_crystal_reference.py`: base OD2...N3 = **2.535 A**, donor
  NE2...N1 = **3.197 A**. v1 used a single 2.9 A optimum for both, which was wrong
  twice over.
- **Open question for the organizers:** the brief says the crystal target and
  textbook hydrogen-bond geometry "agree". For the donor they do (3.197 vs 2.8-3.0).
  For the base they do not - 2.535 A is 0.27 A shorter than the textbook range. It
  is a plausible short, strong hydrogen bond, but the choice matters: `vA_s2`'s
  3.65 A base scores 0.42 against 2.535 and 0.68 against 2.9.
- **Weights, not a bare product.** "Geometry - items 1 and 2 together - outweighs
  everything else combined" cannot be expressed by a plain product, so v2 uses a
  weighted geometric mean with weights as exponents: distance 0.33, approach 0.22
  (geometry 0.55) against iPDE, burial and consistency at 0.15 each (0.45).
  Multiplicative collapse is preserved - a zero term costs a factor of ~900.
- **v2 ranking:** `vA_s2` 0.3090, `chris_seedsweep_s4` 0.1363, `ms_s1` 0.0053,
  everything else numerically zero. Only two designs are non-negligible and **both
  are limited by approach geometry on the donor** - the same contact zonghu-03 found
  to be the fragile one.
- **Retracted:** dropping the MSA to gain throughput is off the table. The brief
  states designs are folded *with* MSAs, so a screen without one would not measure
  what is scored. `wiki/scoring.md` previously listed it as a throughput lever.
- **Fixed a pre-existing bug in a shared tool.** `tools/status.py` wrote to stdout
  in cp1252 and crashed on the pi in zonghu-01's question line, taking
  `test_status_runs` and `make check` down on Windows. One line now forces UTF-8.
  **Team: this is a shared file, flagging it here rather than renaming anything.**
- New: `src/kemp/scoring.py` (tested reference implementation),
  `tests/test_scoring.py` (13 tests, incl. the brief's weighting claim as an
  assertion), `scripts/36_score_v2_weighted.py`,
  `scripts/37_measure_crystal_reference.py`, evidence in `results/criteria/`.
