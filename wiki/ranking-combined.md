# One ranking for everyone's designs: ours, Zonghu's, JJ's and Mario's

Written 2026-11-22. Experiment page: `wiki/experiments/chris-08_combined-candidates-refold.md`. Every number below was
read from a result file named under each table; none is typed from memory. Every row says WHO made the design.

## 1. Who made what, and how we know

| Source | What we received | What we know about how it was made | Where it is |
|---|---|---|---|
| **Chris** | our own designs | RFD3 backbone (motif HG3_17: Asp A127, Gln A50, ligand 6NT), LigandMPNN with the two catalytic residues fixed, Boltz-2; all on seed 4's backbone (260 residues, base Asp86, donor Gln52). Details: `wiki/approach.md` | `results/rescored_replicated_48.tsv` |
| **Zonghu** | four sequences on the same backbone (`ns4_s018`, `s122`, `s007`, `s087`) | his own LigandMPNN draws on seed 4's backbone; 59-70 % identical to our s024, so independent lineages of the same fold | `results/candidates/candidates.csv` on `origin/zonghu` |
| **JJ** (Janis) | `Kemp_JJ_Final`: 10 designs JJ1-JJ10 with structures, Boltz models, a design log | RFD4-Proteina backbones (160-240 residues), theozymes B (Asp + Gln + Trp44) and B2; 2554 distinct designs scored by Boltz-2 (5 diffusion samples each); 59 had the ligand placed, 22 had the base in a 2.1-3.1 A window, 9 were taken, plus JJ9 added by hand (base 3.21 A) and JJ10 from a pilot. His own log lists what that selection did NOT use: donor geometry, angles, real seeds, and a novelty check beyond the five HG3 structures | `All_hits/hits_JJ.csv` (1-based indices) |
| **Mario** | `mario_top20`: 20 sequences with base/oxy, 20 structures and a CSV | the CSV names theozyme batches `theo4` and `theo5`, a "consensus" rank and Zonghu-scorer columns; the structures are Boltz-2 models, one per design, from refold runs with a recorded model seed. We received no description of how the backbones and sequences were made | `top_designs.fasta`, `top_designs.csv` |

A design's name in the combined file is `<source>_<design>` (`jj_JJ1`, `mario_s105_553`, `chris_arms_98_s010`,
`zonghu_ns4_s018`), so the submitted file itself shows who made what. The organizers' rule for names is letters, digits,
`_` and `-`, at most 64 characters, unique; no free text may follow the name in the header.

## 2. Do they meet the requirements? (checked offline, then by the organizers' validator)

Checked offline for each of the 30 designs (alphabet, length, residue types at the indices, names, duplicates, agreement of every sender's FASTA with his own CSV), then with the organizers' validator:

| Requirement (`raw/20261121_organizers_submission.md`) | JJ (10) | Mario (20) |
|---|---|---|
| length 50-260 | all pass (160-238) | all pass (159-240) |
| alphabet: the 20 standard amino acids, uppercase | all pass | all pass |
| `base=` points at D or E, `oxy=` at Q N S T Y K R, and they differ | all pass: every base is Asp, every donor is Gln | all pass: every base is Asp, every donor is Gln |
| indices 1-based and inside the sequence | pass; JJ's 0-based file agrees with his 1-based file | pass; header indices equal the CSV's |
| the sequence in his FASTA equals the sequence in his CSV and per-design folder | pass for all 10 | pass for all 20 |
| unique sequences, unique names | pass, 30 distinct sequences | pass |
| organizers' validator (`validate-submission.py`, run on the cluster) | ACCEPTED as a file of 10 | ACCEPTED as a file of 20 |

Not a requirement but relevant: every one of the 30 has Asp at `base=` and Gln at `oxy=`, which is exactly what our
pinned measurement (OD2 of the Asp, NE2 of the Gln) needs, so the same instrument applies to all of them.

## 3. Novelty and diversity

Identity between any two designs in the pool, global alignment over the shorter sequence: JJ and Mario against everything
else at most 0.43, among themselves at most 0.40. A shuffled sequence scores 0.29 on average and 0.37 at most against another
sequence with this scoring (30 pairs), so 0.43 is composition (helical, Glu/Leu/Ala-rich), not relatedness. Our own ten
(six of ours, four of Zonghu's) run 0.53-0.94. So the JJ and Mario designs are not variants of anything we have, and not of
each other.

The structural novelty gate (TM-score <= 0.70) is in the ranking table, measured by foldseek on OUR refold of each design
against the Kemp-eliminase family database and against the PDB representatives (30 % identity clusters), with `novelty_check.sh`. Structural identity of the best
hit is 2-6 % for every design checked so far. What was NOT done: a sequence search against UniRef for the 70 % identity rule
(the 183 GB database is not usable on the head node) and an MSA search of the new sequences. The organizers fold with MSAs;
for de novo sequences the search is empty (chris-03), but that was measured for our LigandMPNN sequences, not for JJ's or
Mario's. Low-complexity sequences such as JJ9 (mostly E/D/K) are the ones where it could differ.

## 4. Result

All numbers are in `results/ranking_combined_all_seeds.tsv` (our measurement) and `results/zonghu_k1_k5_on_our_refolds.tsv`
(Zonghu's scorer, his code unmodified, on the same refolds). **D** is the summed overshoot beyond the crystal windows, lower is
better; **D2** lets the worse of the approach and in-plane angle decide per contact; **angle over** is how far the angle at
the heteroatom lies outside the crystal range (Zonghu's definition). Seeds 1-5 are job 104 for the new designs; the fresh
seeds 6, 7, 8, 9, 0 are job 106 (nobody selected on them).

### 4.1 The instrument: our own designs, folded three times

| Source | Design | first run (seeds 1-5) | same seeds, new batch (job 104) | fresh seeds (job 106) |
|---|---|---|---|---|
| **Chris** | s010 | 3.8 | 5.8 | 4.2 |
| **Chris** | s057 | 5.0 | 17.1 | 10.4 |
| **Chris** | s024 | 9.4 | 23.8 | 16.1 |
| **Zonghu** | ns4_s018 | not folded here | 6.5 | 7.1 |

Mean D over five seeds. The same seed number in a different batch gives a different fold (s024, seed 2: 3.5 then 55.9), so a
five-seed mean of a design picked for its five-seed mean is optimistic. That is the reason for the fresh seeds.

### Table 1. Re-folded on fresh seeds (6, 7, 8, 9, 0): selection result next to fresh result

| # | Source | Design | seeds 1-5: mean D | **fresh: mean D** | fresh: D2 | fresh: angle over (deg) | fresh: both in window | fresh: OD2 nearest | fresh: iPDE | fresh: worst-seed D | pooled mean D (n) | Zonghu K1-K5 (fresh) | novelty qTM |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **Mario** | s200_62 | 0.9 | **1.4** | 1.4 | 2 | 1/5 | 5/5 | 0.51 | 2.4 | 1.2 (10) | 0.831 | 0.60 |
| 2 | **Mario** | s105_553 | 1.8 | **1.5** | 1.5 | 26 | 2/5 | 5/5 | 0.43 | 2.1 | 1.6 (10) | 0.842 | 0.49 |
| 3 | **Mario** | s201_38 | 2.1 | **2.1** | 2.1 | 2 | 0/5 | 5/5 | 0.67 | 2.8 | 2.1 (10) | 0.739 | 0.51 |
| 4 | **Chris** | arms_98_s010 | 5.8 | **4.2** | 4.1 | 32 | 1/5 | 5/5 | 1.14 | 6.9 | 4.6 (15) | 0.575 | 0.57 |
| 5 | **JJ** | JJ10 | 3.8 | **4.3** | 4.3 | 30 | 0/5 | 5/5 | 0.63 | 5.1 | 4.1 (10) | 0.548 | 0.61 |
| 6 | **Mario** | s200_93 | 5.6 | **4.8** | 4.1 | 18 | 0/5 | 5/5 | 0.35 | 5.6 | 5.2 (10) | 0.674 | 0.50 |
| 7 | **Zonghu** | ns4_s018 | 6.5 | **7.1** | 5.7 | 46 | 1/5 | 5/5 | 1.25 | 11.8 | 6.8 (10) | 0.597 | 0.55 |
| 8 | **Mario** | s100_446 | - (first fold) | **7.7** | 7.4 | 26 | 0/5 | 5/5 | 0.99 | 9.8 | 7.7 (5) | 0.442 | 0.47 |
| 9 | **JJ** | JJ7 | 2.0 | **8.8** | 8.6 | 4 | 0/5 | 5/5 | 1.11 | 33.6 | 5.4 (10) | 0.356 | 0.51 |
| 10 | **Chris** | arms_98_s057 | 17.1 | **10.4** | 9.8 | 45 | 0/5 | 5/5 | 0.99 | 33.8 | 10.8 (15) | 0.464 | 0.56 |
| 11 | **JJ** | JJ1 | 4.3 | **15.4** | 13.7 | 19 | 3/5 | 5/5 | 0.90 | 33.2 | 9.8 (10) | 0.265 | 0.49 |
| 12 | **JJ** | JJ3 | 3.1 | **15.4** | 15.4 | 13 | 0/5 | 5/5 | 0.89 | 35.2 | 9.3 (10) | 0.274 | 0.44 |
| 13 | **Chris** | seed4_s024 | 23.8 | **16.1** | 15.2 | 55 | 1/5 | 5/5 | 1.28 | 53.8 | 16.4 (15) | 0.127 | 0.56 |
| 14 | **Mario** | s201_130 | - (first fold) | **20.4** | 19.3 | 26 | 0/5 | 5/5 | 0.89 | 35.9 | 20.4 (5) | 0.032 | - |
| 15 | **Mario** | s102_539 | - (first fold) | **21.6** | 21.6 | 16 | 1/5 | 5/5 | 1.28 | 33.8 | 21.6 (5) | 0.177 | 0.59 |
| 16 | **Mario** | s200_40 | - (first fold) | **24.6** | 18.3 | 26 | 0/5 | 5/5 | 1.33 | 33.1 | 24.6 (5) | 0.149 | 0.58 |
| 17 | **Mario** | s107_375 | - (first fold) | **24.6** | 22.0 | 24 | 0/5 | 5/5 | 0.83 | 37.2 | 24.6 (5) | 0.043 | 0.57 |
| 18 | **Mario** | s203_29 | - (first fold) | **31.4** | 29.1 | 24 | 0/5 | 5/5 | 1.36 | 58.9 | 31.4 (5) | 0.053 | - |
| 19 | **Mario** | s103_480 | - (first fold) | **33.2** | 32.0 | 22 | 0/5 | 5/5 | 0.79 | 35.5 | 33.2 (5) | 0.000 | - |
| 20 | **Mario** | s105_97 | - (first fold) | **38.4** | 38.4 | 66 | 0/5 | 5/5 | 0.90 | 42.6 | 38.4 (5) | 0.001 | 0.58 |

### Table 2. Every design on seeds 1-5 (the selection evidence), best mean D first

| # | Source | Design | Len | both in window | OD2 nearest | mean D | mean D2 | angle over (deg) | burial | iPDE | Zonghu K1-K5 | novelty qTM | re-folded fresh |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **Mario** | s200_62 | 166 | 1/5 | 5/5 | 0.9 | 0.9 | 0 | 46 | 0.50 | 0.877 | 0.60 | yes |
| 2 | **Mario** | s105_553 | 219 | 0/5 | 5/5 | 1.8 | 1.8 | 27 | 45 | 0.44 | 0.800 | 0.49 | yes |
| 3 | **JJ** | JJ7 | 227 | 0/5 | 5/5 | 2.0 | 1.7 | 5 | 33 | 1.04 | 0.717 | 0.51 | yes |
| 4 | **Mario** | s201_38 | 229 | 0/5 | 5/5 | 2.1 | 2.1 | 1 | 45 | 0.66 | 0.733 | 0.51 | yes |
| 5 | **JJ** | JJ3 | 199 | 0/5 | 5/5 | 3.1 | 2.9 | 20 | 39 | 0.94 | 0.820 | 0.44 | yes |
| 6 | **JJ** | JJ10 | 171 | 0/5 | 5/5 | 3.8 | 3.8 | 31 | 43 | 0.66 | 0.630 | 0.61 | yes |
| 7 | **JJ** | JJ1 | 210 | 4/5 | 5/5 | 4.3 | 2.7 | 26 | 47 | 0.96 | 0.780 | 0.49 | yes |
| 8 | **JJ** | JJ9 | 197 | 0/5 | 5/5 | 5.4 | 4.1 | 19 | 37 | 0.62 | 0.693 | 0.67 | no |
| 9 | **Mario** | s200_93 | 239 | 0/5 | 5/5 | 5.6 | 4.7 | 13 | 43 | 0.35 | 0.624 | 0.50 | yes |
| 10 | **Chris** | arms_98_s010 (control, newest batch) | 260 | 0/5 | 5/5 | 5.8 | 5.2 | 33 | 48 | 1.15 | 0.517 | 0.57 | yes |
| 11 | **Chris** | arms_97_s008 | 260 | 1/5 | 5/5 | 6.2 | 5.1 | 35 | 46 | 0.91 | 0.522 | 0.55 | no |
| 12 | **Zonghu** | ns4_s018 (control, newest batch) | 260 | 1/5 | 5/5 | 6.5 | 5.2 | 54 | 48 | 1.22 | 0.697 | 0.55 | yes |
| 13 | **Mario** | s106_586 | 175 | 0/5 | 5/5 | 6.5 | 5.9 | 47 | 38 | 0.58 | 0.641 | 0.55 | no |
| 14 | **JJ** | JJ6 | 160 | 0/5 | 1/5 | 7.5 | 6.7 | 50 | 45 | 0.89 | 0.449 | 0.68 | no |
| 15 | **Chris** | arms_98_s060 | 260 | 0/5 | 5/5 | 7.5 | 7.2 | 54 | 46 | 0.94 | 0.551 | 0.57 | no |
| 16 | **Chris** | seed4_s068 | 260 | 0/5 | 0/5 | 10.6 | 7.1 | 66 | 47 | 0.79 | 0.673 | 0.55 | no |
| 17 | **Chris** | arms_96_s004 | 260 | 0/5 | 4/5 | 11.0 | 9.5 | 45 | 45 | 1.05 | 0.422 | - | no |
| 18 | **Chris** | seed4_s042 | 260 | 0/5 | 1/5 | 11.9 | 10.3 | 63 | 47 | 1.28 | 0.342 | - | no |
| 19 | **Chris** | seed12_s001 | 260 | 1/5 | 5/5 | 11.9 | 7.7 | 32 | 49 | 1.31 | 0.275 | - | no |
| 20 | **Mario** | s108_355 | 240 | 0/5 | 4/5 | 12.0 | 11.2 | 22 | 44 | 0.71 | 0.375 | 0.49 | no |
| 21 | **Chris** | arms_96_s069 | 260 | 0/5 | 2/5 | 12.3 | 10.0 | 58 | 49 | 1.39 | 0.447 | - | no |
| 22 | **Chris** | seed4_s069 | 260 | 0/5 | 5/5 | 12.4 | 9.7 | 76 | 47 | 1.43 | 0.398 | - | no |
| 23 | **Chris** | arms_98_s018 | 260 | 2/5 | 5/5 | 12.7 | 9.3 | 39 | 45 | 1.45 | 0.247 | - | no |
| 24 | **JJ** | JJ4 | 192 | 0/5 | 5/5 | 12.7 | 8.9 | 10 | 41 | 0.94 | 0.345 | 0.51 | no |
| 25 | **Chris** | seed4_s004 | 260 | 0/5 | 5/5 | 12.9 | 12.7 | 40 | 48 | 0.96 | 0.252 | - | no |
| 26 | **Mario** | s102_113 | 229 | 1/5 | 5/5 | 13.0 | 10.9 | 9 | 42 | 0.97 | 0.310 | 0.53 | no |
| 27 | **JJ** | JJ5 | 219 | 0/5 | 5/5 | 13.8 | 13.2 | 44 | 39 | 1.16 | 0.235 | 0.66 | no |
| 28 | **Chris** | arms_98_s020 | 260 | 0/5 | 5/5 | 13.8 | 13.0 | 45 | 47 | 1.31 | 0.106 | - | no |
| 29 | **Chris** | arms_98_s038 | 260 | 1/5 | 5/5 | 14.7 | 11.3 | 31 | 49 | 2.14 | 0.195 | - | no |
| 30 | **Chris** | arms_98_s024 | 260 | 2/5 | 5/5 | 15.2 | 14.4 | 28 | 45 | 1.09 | 0.156 | - | no |
| 31 | **Chris** | arms_98_s023 | 260 | 0/5 | 5/5 | 15.4 | 12.5 | 49 | 48 | 1.12 | 0.249 | - | no |
| 32 | **JJ** | JJ8 | 238 | 0/5 | 5/5 | 15.9 | 14.0 | 50 | 45 | 1.15 | 0.135 | 0.59 | no |
| 33 | **Chris** | arms_98_s057 (control, newest batch) | 260 | 1/5 | 5/5 | 17.1 | 17.0 | 60 | 47 | 1.11 | 0.094 | 0.56 | yes |
| 34 | **Chris** | arms_98_s031 | 260 | 0/5 | 5/5 | 17.2 | 17.0 | 38 | 49 | 0.75 | 0.198 | - | no |
| 35 | **Chris** | seed4_s056 | 260 | 0/5 | 5/5 | 17.4 | 16.9 | 26 | 46 | 0.75 | 0.131 | - | no |
| 36 | **Chris** | arms_98_s022 | 260 | 1/5 | 5/5 | 17.5 | 15.9 | 42 | 48 | 0.89 | 0.097 | - | no |
| 37 | **Chris** | c_s059 | 260 | 0/5 | 5/5 | 17.6 | 14.8 | 28 | 46 | 1.80 | 0.088 | - | no |
| 38 | **Chris** | seed4_s006 | 260 | 0/5 | 5/5 | 18.4 | 15.2 | 40 | 47 | 1.48 | 0.216 | - | no |
| 39 | **Chris** | arms_98_s037 | 260 | 0/5 | 2/5 | 18.8 | 16.2 | 73 | 48 | 1.65 | 0.093 | - | no |
| 40 | **Mario** | s108_120 | 159 | 0/5 | 5/5 | 18.9 | 17.4 | 44 | 47 | 1.04 | 0.288 | 0.62 | no |
| 41 | **Chris** | seed12_s004 | 260 | 0/5 | 5/5 | 19.6 | 16.2 | 66 | 46 | 1.94 | 0.151 | - | no |
| 42 | **Chris** | seed4_s041 | 260 | 0/5 | 5/5 | 20.5 | 18.1 | 36 | 47 | 1.39 | 0.042 | - | no |
| 43 | **JJ** | JJ2 | 232 | 0/5 | 0/5 | 20.7 | 20.1 | 64 | 38 | 0.94 | 0.008 | 0.68 | no |
| 44 | **Chris** | arms_96_s063 | 260 | 0/5 | 5/5 | 20.9 | 19.4 | 79 | 49 | 1.02 | 0.203 | - | no |
| 45 | **Chris** | arms_98_s003 | 260 | 1/5 | 5/5 | 21.4 | 20.3 | 32 | 47 | 1.40 | 0.090 | - | no |


### 4.2 What the tables say

1. **Mario's s200_62, s105_553 and s201_38 hold up on fresh seeds** (D 1.4, 1.5, 2.1; the worst single seed is 2.4, 2.1,
   2.8) and they lead Zonghu's K1-K5 too (0.83, 0.84, 0.74). They are the most consistent designs in the pool.
2. **JJ's JJ7, JJ1 and JJ3 do not hold** (2.0 to 8.8, 4.3 to 15.4, 3.1 to 15.4; each has a fresh seed with D above 33), in
   line with Zonghu's own finding that JJ3 collapses on some seeds. **JJ10 holds** (3.8 to 4.3).
3. **Our s010 holds** (fresh 4.2; 4.6 pooled over 15 seeds), s057 and s024 are worse than the first run said.
4. **Mario's lower eight**: only s100_446 is usable (7.7); the other seven are at 20-38 or worse.
5. **Nobody passes the pre-registered rule on fresh seeds** (both contacts in window in >= 3 of 5 seeds AND mean D <= 15):
   JJ1 has 3 of 5 but D 15.4. The window box is narrower than what D tolerates, so D is the measure that separates designs;
   the file below is chosen on D and says so.
6. **Angle at the heteroatom:** Mario's s200_62 and s201_38 (within 3 degrees of the crystal range) and JJ7 (4 degrees) are
   the only designs near it. The other fresh-folded designs are 13-66 degrees outside, ours 32-55.
7. **Novelty** (foldseek on our own refold, qTM against the Kemp family and the PDB representatives): every design checked is
   under the 0.70 gate (highest 0.68, JJ6 in job 104); the eight designs in 4.3 are at or below 0.61. Not run for s201_130,
   s203_29, s103_480 (not candidates).
8. **Not done:** UniRef search for the 70 % identity rule, MSA search of the new sequences (the organizers fold with MSAs).

### 4.3 The file this supports (8 designs, not uploaded by us)

Rule used: only designs folded on fresh seeds are candidates; keep those with fresh mean D <= 8.7 (the 95th percentile of the
unbiased baseline, fixed in chris-08 before the fresh seeds existed); OD2 the nearest oxygen in >= 4 of 5 seeds; index check;
novelty on our own refold; the organizers' validator ACCEPTS. `results/designs_combined_recommended.fasta`:

| # | Name in the file | Source | fresh mean D | worst seed D | Zonghu K1-K5 |
|---|---|---|---|---|---|
| 1 | `mario_s200_62` | **Mario** | 1.4 | 2.4 | 0.831 |
| 2 | `mario_s105_553` | **Mario** | 1.5 | 2.1 | 0.842 |
| 3 | `mario_s201_38` | **Mario** | 2.1 | 2.8 | 0.739 |
| 4 | `chris_arms_98_s010` | **Chris** | 4.2 | 6.9 | 0.575 |
| 5 | `jj_JJ10` | **JJ** | 4.3 | 5.1 | 0.548 |
| 6 | `mario_s200_93` | **Mario** | 4.8 | 5.6 | 0.674 |
| 7 | `zonghu_ns4_s018` | **Zonghu** | 7.1 | 11.8 | 0.597 |
| 8 | `mario_s100_446` | **Mario** | 7.7 | 9.8 | 0.442 |

Next in line, outside the threshold: JJ7 (fresh 8.8, pooled over 10 seeds 5.4, one fresh seed at 33.6), s057 (10.4).

### 4.4 The file that is in the team's S3 slot (uploaded 2026-11-22 12:16 UTC by a teammate, 20 designs, 5162 bytes)

Read back from the bucket, read-only. Our rows for each of its designs:

| Name in the uploaded file | Real source | D seeds 1-5 | D fresh seeds | Note |
|---|---|---|---|---|
| `mario_s105_553`, `mario_s200_62`, `mario_s201_38`, `mario_s200_93` | **Mario** | 1.8, 0.9, 2.1, 5.6 | 1.5, 1.4, 2.1, 4.8 | all in the recommended file |
| `zonghu_arms_98_s010` | **Chris** (labelled zonghu) | 5.8 | 4.2 | in the recommended file |
| `zonghu_ns4_s018` | **Zonghu** | 6.5 | 7.1 | in the recommended file |
| `janis_JJ7`, `janis_JJ1`, `janis_JJ3` | **JJ** | 2.0, 4.3, 3.1 | 8.8, 15.4, 15.4 | regress on fresh seeds |
| `janis_JJ9` | **JJ** | 5.4 | not re-folded | |
| `zonghu_arms_98_s057`, `zonghu_seed4_s024`, `zonghu_arms_97_s008` | **Chris** (labelled zonghu) | 17.1, 23.8, 6.2 | 10.4, 16.1, not re-folded | |
| `mario_s204_170`, `mario_s203_28`, `mario_s107_319` | **Mario** | 26.6, 32.3, 24.7 | not re-folded | poor on seeds 1-5 already |
| `janis_JJ6` | **JJ** | 7.5 | not re-folded | **fails the OD2 gate** (1 of 5 seeds) |
| `zonghu_ns4_s122`, `zonghu_ns4_s087`, `zonghu_ns4_s007` | **Zonghu** | not folded here | not folded here | Zonghu's own K1-K5: 0.551, 0.507, 0.529 |

Missing from it although they hold up on fresh seeds: `jj_JJ10` (4.3) and `mario_s100_446` (7.7). Four designs in it were
already poor on seeds 1-5 (s204_170, s203_28, s107_319, JJ6). Three of our own designs carry the name prefix `zonghu_`; the
prefix does not affect scoring, but the source is wrong.
