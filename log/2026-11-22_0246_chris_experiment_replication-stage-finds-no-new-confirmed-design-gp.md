# [2026-11-22 02:46] experiment | Replication stage finds no new confirmed design; GPU contention; driver made time-aware (chris)

- TODO

- **repl1 finished (job 90, 35 min, faster than the 45 min estimate): none of the 20 newly replicated designs
  passes the rule.** s024 remains the only confirmed design. Best of the new ones by mean D: s068 10.6 (iPDE
  0.79, the lowest of everything measured), s042 11.9, seed12_s001 11.9, s069 12.4, s004 12.9; all have 0 or 1
  of 5 seeds with both distances in window.
- **The OD2-versus-nearer-oxygen question matters much less than feared.** Counting both distances in window per
  seed under either convention, exactly one design (s024) reaches 3 of 5 seeds under OD2-only and under
  nearer-oxygen. The other candidates fail on the distances themselves, not on which oxygen is used.
- **GPU contention.** zonghu queued jobs 91-95 (his consistency run plus four `k5-seeds` jobs, a copy of our
  replication recipe over his own sequence sets: 40, 44, 44 and 3 sequences = about 245 min at 5 seeds) ahead of
  the arms on the single GPU. Not touched, per the rule never to touch a teammate's jobs. Asked the team lead to
  coordinate. Worst case if all his jobs run to completion: arms start about 05:45 UTC.
- **Driver made time-aware and hot-swapped** (stopped the old one, replaced the file, restarted: it logged
  `resuming arm-baseline with job 96` and submitted nothing new). Arms reordered by evidence (baseline, polar-down,
  close, aromatic, checkpoint 005); each arm after the first needs 27 min plus 45 min to replicate; replication is
  sized to the time left. Tested: failure handling, resume of the real queued job 96, and a simulated clock
  (70 min left runs 1 arm, 100 runs 2, 150 runs 3, 170 runs 4, 190+ runs all 5). Worst case now degrades to
  baseline + polar + close arms and about 19 replicated designs, ending around 07:50 UTC.
- Two test mistakes of mine, both in the test and not the driver: a fixture I had just moved, and a dry-run that does
  not advance the clock, then an arithmetic slip on the 190 min boundary.
