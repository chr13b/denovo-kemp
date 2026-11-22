# [2026-11-22 11:24] experiment | Arms explained and verified, burial and worse-of added to our scorer, Zonghu's newest ranking read (chris)

- TODO

- **Deadline.** The team lead says about 3 h 15 min remained at about 10:15 UTC (so roughly 13:30 UTC); not confirmed
  with the organizers. The earlier 09:00 UTC belief is retracted as unverified. Nothing was uploaded this turn.
- **Arms verified.** LigandMPNN samples softmax((logit + bias) / T); the bias worked as built (polar 4.0 to 1.7 at the
  pocket sites, identity to s024 63 % to 91 %), the pinned Asp86 and Gln52 survived in all 216 sequences. Details in
  `wiki/approach.md`, `wiki/primer.md` g16.
- **Our scorer gained burial and "worse of the two decides"** (`cluster/rescore_replicated.py`, table
  `results/rescored_replicated_48.tsv`): s010 stays first under D and D2; burial does not separate designs.
- **Found and corrected two mistakes of mine in the same sitting:** a draft sentence said every design is 31-76 deg
  outside the angle range (true range over all 48: 10.6-93.2, median 40), and a claim that no mutation stood out was
  based on the top ten of a smoothed ratio (47 residues are carried by two or more good designs; the best is I59M, raw p
  0.009, not significant after correction).
- **Zonghu's newest commit** scores all four of our new designs (s010 second of 193). His new sequences are independent
  lineages (53-69 % identical to s024). His ipTM term K6 is not an organizer criterion.
