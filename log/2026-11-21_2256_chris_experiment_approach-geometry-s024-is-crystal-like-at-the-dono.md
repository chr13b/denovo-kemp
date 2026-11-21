# [2026-11-21 22:56] experiment | Approach geometry: s024 is crystal-like at the donor, not the base; 0 of 352 designs match fully (chris)

- TODO

- The organizers' brief says the geometry term also judges **approach angle at the ring and in-plane
  geometry** ("the worse of the two decides"), and that geometry outweighs everything else combined. We had
  only ever measured the two contact distances. Measured now (`cluster/geometry_vs_crystal.py`), against the
  span of 25 engaged crystal copies. Atom definitions are our stand-ins; the scorer's are unpublished.
- **0 of 352 designs** have all four approach/in-plane quantities inside the crystal range; best is 4 of 6
  including distances. s024 (5 seeds): donor approach/in-plane crystal-like in four seeds, **base approach
  129-144 deg vs crystal 167-176 and 15-25 deg out of plane vs <= 12**. s059 is the mirror image (base
  right, donor end-on at 71-93 deg approach and 51-72 deg out of plane).
- Continuous proxy D (ours): s024 = 4.8 / 3.5 / 29.6 / 5.3 / 3.5 over five seeds vs median 53.7 across all
  352 single-fold designs, so in four of five seeds it sits in the extreme tail. Pipeline's sequence
  averages 24.3, s059 17.6.
- Burial (CA within 12 A) is 48 for s024 and 45-48 for natural enzymes and other designs: no signal.
  iPDE: s024 1.20, lowest of everything measured (pipeline 1.62, s059 1.80, natural 1.53-3.00).
- **Open question for the organizers: OD2 only, or the nearer carboxylate oxygen?** s042 (job 27) has its
  nearest oxygen at 2.45 A but OD2 at 3.73 A. s024 is safe under both (OD2 nearest in all five seeds).
- 15 of the 20 best designs by D are on seed 4's backbone; the existing data hold unreplicated candidates
  (s042, s004, s006, s019) that the distance-only filter never flagged.
- Deadline believed to be 2026-11-22 10:00 (timezone presumably Paris/Basel = 09:00 UTC), unconfirmed.
  The organizers' docs: re-upload allowed, **the file present at the deadline is the one scored**, no grace.
