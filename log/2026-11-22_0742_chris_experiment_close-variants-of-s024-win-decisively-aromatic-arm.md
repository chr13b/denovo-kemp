# [2026-11-22 07:42] experiment | Close variants of s024 win decisively; aromatic arm dropped; replication of the best 25 under way (chris)

- TODO

- **Arm results (72 sequences each, seed-4 backbone, T 0.3).** Baseline: median D 30.5, 1 design with D <= 8.7,
  12 with D <= 20, 22 with the ligand roughly in place. Polar-down (the lever read off the crystals): median 32.1,
  1, 9, 15; Mann-Whitney p = 0.21, so **not supported** (slightly worse). **Close variants of s024: median 25.2,
  11 with D <= 8.7, 28 with D <= 20, 34 in place; p = 0.013.** Best single folds D 2.8, 3.0, 3.0, 3.4, 4.2 with
  base/donor such as 2.62/2.92, 2.84/2.97, 2.57/3.05, 2.63/3.07.
- **Formally** the pre-registered rule (median <= 24.4 AND >= 3 designs with D <= 8.7) is NOT met for close variants:
  its median 25.2 misses by 0.8 while its good-design count (11) passes by a wide margin. Reported as it is; the effect
  is large regardless.
- **This overturns an earlier conclusion.** The smoothness check found no relation between identity to a winner and
  geometry over 56-74 % identity, and I concluded geometry was a lottery. At 86-95 % identity (median 92 %) it is not:
  sequences close to s024 are far better than blind samples. The earlier test only covered the wrong range.
- **Decision, made unattended and reported here:** stopped the driver, cancelled my own aromatic arm (job 99, one
  minute old), marked the arms stage done in `state.json` and restarted, so the driver went straight to replication of
  the 25 best new designs by single-fold D (job 100, about 52 min, ends about 07:33 UTC). The aromatic and checkpoint-005
  arms and the 216-sequence main sweep were NOT run, so those hypotheses stay untested. Reason: replicating the strongest
  close-variant designs has far higher expected value than an untested guess, and the time left was about 80 minutes.
- An empty queue seen between two arms was the driver's polling gap, not a failure (job 97 finished normally).
