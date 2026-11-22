# [2026-11-22 03:42] setup | Endgame tooling ready while the GPU is busy: finalizer that applies the rule, novelty gate, index check, validator (chris)

- TODO

- **zonghu's queued jobs are replications of OUR designs**, not new candidates: P = best seed-4 designs (s004,
  s006, s068), A and B1 = the 4BS0_A fresh sweep (job 35), B2 = the 8USL_B sweep (job 36); those two sweeps had
  0 of 32 in window each. His chain (92 -> 93 -> 94, chained with `afterany`) takes about 73 + 79 + 79 min from
  01:50, so my first arm starts around 05:30 UTC unless he cancels B1/B2. Slurm's displayed 04:50 start ignores the
  dependency-held jobs and is too optimistic. His own seeds run 13.5 min for 40 structures, matching our 19-21 s/fold.
- **`cluster/finalize.py`** prepares the endgame and never uploads: it applies the pre-registered rule to everything
  replicated so far, runs the novelty gate (qTM <= 0.70 against the Kemp family AND the PDB representatives) on a
  predicted structure, checks that base= is D/E and oxy= is Q/N/S/T/Y/K/R (a silent off-by-one otherwise), writes
  `designs_final.fasta`, and runs the organizers' validator. Tested on today's data: 23 replicated, 1 passes (s024),
  novelty family 0.30 / PDB 0.561, index ok, validator ACCEPTED. It does not write to the driver's log.
- One slip of mine while editing it: a docstring replacement keyed on the first triple quote hit the shebang line
  and corrupted the file; restored from the cluster copy and redone. No effect on anything running.
