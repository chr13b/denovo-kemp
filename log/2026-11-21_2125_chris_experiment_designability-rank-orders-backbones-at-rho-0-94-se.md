# [2026-11-21 21:25] experiment | Designability rank-orders backbones at rho 0.94; sequences at r 0.12 (chris)

- TODO

- Six backbones now swept under one protocol (chris-04/05/06/07). Ranked by median CA RMSD:
  seed 4 **0.77** (median base 5.12, **2/72 in window**), 4BS0_A fresh 1.33 (6.66), seed 3 1.53
  (7.45), 8USL_B 1.99 (9.73), Trp44 2.02 (7.64), seed 5 10.67 (11.32).
- **Across backbones: median CA RMSD vs median base contact, Spearman rho = +0.943** (n=6).
  **Within seed 4 (n=72): a sequence's CA RMSD vs its own base contact, r = +0.122.**
  Not a contradiction - the distinction is the whole point. Screen *backbones* on designability;
  sample *sequences* blind, because no per-sequence filter exists and folding is 19 s.
- **Methodological catch:** ranking backbones by their *best* contact gives rho = +0.486, not +0.943,
  because best-of-72 beats best-of-32 by construction. With unequal sample sizes compare medians, not
  minima. I nearly reported the weak number as the result.
- chris-07 refuted: seed 5 is unencodable (0/48 refold under 2 Å) and seed 3, though encodable at
  1.53 Å, sits mid-table with 0/48 hits. chris-02's ~50 % loss rate stands, better stated as
  **~2 of 5 RFD3 seeds give a backbone worth sampling deeply**, judged by a sweep rather than by one
  sequence. Seed 2 cancelled (same collapse signature as seed 5, contended queue).
- The experiment still paid: it supplied two of the six points behind rho = 0.94, which is what
  justifies a ~16 min designability screen before a ~25 min deep sweep.
