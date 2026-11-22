# One ranking for everyone's designs: ours, Zonghu's, JJ's and Mario's

Written 2026-11-22. Experiment page: `wiki/experiments/chris-08_combined-candidates-refold.md`. Every number below was
read from a result file named under each table; none is typed from memory. Every row says WHO made the design.

## 1. Who made what, and how we know

| Source | What we received | What we know about how it was made | Where it is |
|---|---|---|---|
| **Chris** (team 01) | our own designs | RFD3 backbone (motif HG3_17: Asp A127, Gln A50, ligand 6NT), LigandMPNN with the two catalytic residues fixed, Boltz-2; all on seed 4's backbone (260 residues, base Asp86, donor Gln52). Details: `wiki/approach.md` | `results/rescored_replicated_48.tsv` |
| **Zonghu** | four sequences on the same backbone (`ns4_s018`, `s122`, `s007`, `s087`) | his own LigandMPNN draws on seed 4's backbone; 59-70 % identical to our s024, so independent lineages of the same fold | `results/candidates/candidates.csv` on `origin/zonghu` |
| **JJ** (Janis Jackel) | `Hackathon_Kemp_JJ_Final`: 10 designs JJ1-JJ10 with structures, Boltz models, a design log | RFD4-Proteina backbones (160-240 residues), theozymes B (Asp + Gln + Trp44) and B2; 2554 distinct designs scored by Boltz-2 (5 diffusion samples each); 59 had the ligand placed, 22 had the base in a 2.1-3.1 A window, 9 were taken, plus JJ9 added by hand (base 3.21 A) and JJ10 from a pilot. His own log lists what that selection did NOT use: donor geometry, angles, real seeds, and a novelty check beyond the five HG3 structures | `All_hits/hits_JJ.csv` (1-based indices) |
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

<<RESULTS>>
