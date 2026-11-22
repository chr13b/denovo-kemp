# [2026-11-22 08:37] experiment | Pipeline finished: 48 designs replicated, one passes the rule, a steadier candidate (s010) needs a decision (chris)

- TODO

- **The driver finished cleanly at 07:25:51 UTC**, stages repl1, arms, repl2 and final all done, its candidate file
  accepted by the validator (s024 only, not uploaded). The arms stage was cut short on purpose (aromatic and
  checkpoint-005 arms and the main sweep not run) after the close-variants arm won decisively.
- **Job 100 (25 designs x 5 seeds, 42 min, faster than the 52 min estimate).** 48 designs fully replicated in total;
  **only s024 passes the pre-registered rule.** None of the 45 newly replicated designs does. Single-fold winners mostly
  fail replication.
- **But several close variants of s024 have a better replicated mean geometry than s024:** s010 mean D 3.8 (worst
  seed 5.5, base in window 5/5, iPDE 1.13), s057 5.0, polar s008 6.2, s060 7.5, against 9.4 for s024 (worst seed
  29.6). They fail the rule only on "both distances in window in >= 3/5 seeds": s010 narrowly misses the donor window
  (by 0.06, 0.16, 0.18 A) in three seeds.
- **Not changed unilaterally.** Amending a rule written before the data is the team lead's call. Prepared three
  validated, novelty-checked files (strict s024; B = s024 + s010, recommended; C = s024 + four). The finalizer gained
  `--also LABEL...` to add named designs explicitly, flagged as outside the rule, and `--out`.
- **Cost of the amendment, stated plainly:** the criterion would be chosen after seeing the data, all candidates are
  one fold, and s010 is weaker than s024 on the binary count (2/5 vs 3/5). In its favour: lower mean D, no catastrophic
  seed, base in window in every seed, lower iPDE, and the scorer penalises variance.
- Queue empty, driver finished, nothing else running. Deadline believed 09:00 UTC; it is about 07:40.
