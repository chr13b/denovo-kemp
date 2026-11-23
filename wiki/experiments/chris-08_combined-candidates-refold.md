# chris-08: combined candidates refold

- **Owner:** chris
- **Date:** 2026-11-22
- **Status:** done: supported (the requirement check and the ranking are complete; the file choice is the team's)
- **Question:** Do the 10 designs JJ sent (`Kemp_JJ_Final`) and the 20 designs Mario sent (`mario_top20`) meet the
  submission rules, and how do they rank against ours when every one of them is folded on the SAME instrument
  (Boltz-2, ligand 6NT, 5 seeds, 200 sampling steps, 3 recycling steps, query-only MSA) and measured by the SAME code?
- **Why it matters:** the file at the deadline is the one scored and holds at most 20 designs. Our own family is one fold,
  and our top four share 88-94 % identity. JJ's and Mario's designs are on other backbones (at most 43 % identity to
  anything else in the pool), so they are the only way to add real diversity, if they hold up on seeds nobody selected on.
- **Script + config:** `cluster/rank_candidates.py` (ranking), `cluster/assemble_combined.py` (file), `cluster/zh_score_batch.py`
  (Zonghu's scorer as a second opinion), submitted with `cluster/replicate_seeds.sbatch` (`RS_FASTA`, `RS_SEEDS`)
- **Runs:** job 104 = JJ's 10 + Mario's top 12 (his own order) + 4 in-batch controls (our s024, s010, s057, Zonghu's
  `ns4_s018`), seeds 1-5; job 106 = fresh seeds 6, 7, 8, 9, 0 for 20 designs (see below). Job 105 (Mario's lower 8 on seeds
  1-5) was submitted and cancelled before it started. Results on the cluster in `results/replicate-104` and
  `results/replicate-106`.

Status values: `planned`, `running`, `done: supported`, `done: refuted`, `done: inconclusive`, `abandoned`.

## Pre-registered before any JJ or Mario design was folded

- **Gates for every design:** the validator accepts; the residue at `base=` is D/E and at `oxy=` is one of QNSTYKR;
  length 50-260; unique sequence; unique legal name; OD2 of the declared Asp is the nearest oxygen in at least 4 of 5
  seeds; novelty (qTM <= 0.70 against the Kemp family AND the PDB representatives) measured on OUR refold, not on the
  structure the sender supplied.
- **Selection rule (unchanged from the one that selected s024):** both contacts in window in >= 3 of 5 seeds and mean
  D <= 15. A design that fails it can still be added, but it is printed as "outside the rule".
- **Ranking:** mean D over the five seeds (D = summed overshoot beyond the crystal windows, in tolerance units), with
  D2 ("worse of approach and in-plane decides"), the angle at the heteroatom (Zonghu's definition) and Zonghu's K1-K5
  shown beside it. A control that is folded again contributes the row from the newest job, so every design in the table
  was folded in a comparable batch.
- **Fresh-seed re-fold (added 12:11 UTC, before the five-seed ranking of job 104 was complete).** Every design was
  picked, by its sender or by us, on a fold that is also the fold it is scored on, so its five-seed mean is optimistic
  (winner's curse). The four in-batch controls measure how large that effect is for our own designs. So: SELECT on
  seeds 1-5 (job 104), then ESTIMATE on five seeds nobody selected on (6, 7, 8, 9, 0). Inclusion in the submitted file is
  decided on the fresh-seed numbers with the thresholds above; the seed 1-5 row stays in the table as the selection evidence.
  A design with no fresh-seed fold is not a candidate for the file.
- **What was actually submitted (12:21 UTC, changed from the first plan because job 104 took longer than estimated).**
  Job 105 (Mario's lower 8 on seeds 1-5) was cancelled and replaced by job 106 = one job on seeds 6, 7, 8, 9, 0 with 20 designs:
  Mario's lower 8 (first fold, so these are fresh by construction), the 8 new designs with the best mean D over seeds 1-3 of
  job 104 (Mario: s200_62, s105_553, s201_38, s200_93; JJ: JJ7, JJ3, JJ10, JJ1), and the four controls (our s010, s024, s057,
  Zonghu's ns4_s018). The shortlist was cut on three seeds, not five, because of the clock. Designs ranked below the cut by
  job 104 (JJ9, Mario's s106_586, ...) were NOT re-folded and are not candidates unless the written result says otherwise.
- **Not done, on purpose:** MSA search for the new sequences (JJ's and Mario's are de novo; for those the search returns
  an empty alignment, chris-03), and a UniRef/BLAST identity search (the 183 GB database is not usable on the head node).
  The identity half of the novelty gate is therefore read from the structural alignments only (2-6 % identity).

## Result

Full tables, the control comparison and the comparison with the file in the S3 slot are in `wiki/ranking-combined.md`
section 4; data in `results/ranking_combined_all_seeds.tsv` and `results/zonghu_k1_k5_on_our_refolds.tsv`.

- **Requirements:** all 30 designs (JJ 10, Mario 20) pass every rule; the organizers' validator accepts JJ's file of 10 and
  Mario's file of 20; each sender's structure matches his FASTA (30 of 30); identity to anything else in the pool is at most 0.43.
- **Fresh seeds (6, 7, 8, 9, 0), mean D:** Mario s200_62 1.4, s105_553 1.5, s201_38 2.1; our s010 4.2; JJ10 4.3; Mario s200_93 4.8;
  Zonghu ns4_s018 7.1; Mario s100_446 7.7; JJ7 8.8; our s057 10.4; JJ1 15.4; JJ3 15.4; our s024 16.1; Mario's other 7 re-folded
  designs 20.4-38.4.
- **Controls (our own designs, seeds 1-5 first run, same seeds in a new batch, fresh seeds):** s010 3.8, 5.8, 4.2; s057 5.0, 17.1,
  10.4; s024 9.4, 23.8, 16.1. The batch changes the fold of a given seed, so five-seed means of selected designs are optimistic.
- **Pre-registered rule on fresh seeds:** no design passes (JJ1 has both contacts in window in 3 of 5 seeds but mean D 15.4).
- **File:** `results/designs_combined_recommended.fasta`, 8 designs (fresh mean D <= 8.7, OD2 gate, novelty on our refold),
  validator ACCEPTED. Not uploaded by us: a teammate had already uploaded a 20-design file at 12:16 UTC, which contains four
  designs that were already poor on seeds 1-5 and lacks JJ10 and s100_446.

## Verdict and next step

Supported: the JJ and Mario designs do add real diversity (unrelated sequences, other folds), but only some survive fresh
seeds, three of Mario's clearly, JJ10 and Mario s200_93 and s100_446 well enough. The one decision that remains is the team's:
whether to replace the 20-design upload by the 8-design file or by a 20-design file with the four weakest swapped out. Whether
a weak design in a slot costs anything depends on how the organizers combine a team's designs into one score, which is not
known (open question for the organizers).
