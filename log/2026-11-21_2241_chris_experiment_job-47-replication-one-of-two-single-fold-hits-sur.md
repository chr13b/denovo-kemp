# [2026-11-21 22:41] experiment | Job 47 replication: one of two single-fold hits survives (s024), measured at pinned positions (chris)

- TODO

- **Job 47 finished** (6 sequences x 5 Boltz seeds, one batch per seed). Measured at the scorer's
  declared positions (base=86, oxy=52): **s024** base 2.77 +/- 0.51 A (4/5 in window), donor 4.01 +/-
  0.77 (3/5 in), **both in window in 3/5 seeds**, with one seed losing the ligand (3.78 / 5.53 A).
  **s059** base 3.22 +/- 0.80 (2/5), donor 4.20 +/- 0.41 (**0/5**; never below 3.82 A). The pipeline's
  own sequence: base 3.72 +/- 1.29, both-in-window 0/5.
- **Pre-registered rule (written in chris-04 before the run) applied:** s024 confirmed; s059 dropped
  (mean base > 3.0 A) and commented out of `results/designs.jsonl` with the reason. The single-fold hit
  rate of 2/72 became a replicated 1/72, i.e. half of single-fold "hits" were noise.
- **Natural enzymes** land in both windows in 0/5, 0/5 and 1/5 seeds, so the rule's "instrument cannot
  hit the window" row fires. Not acted on: they fold with no MSA as 307-318 residue constructs, which
  handicaps them far more than a de novo design. Becomes a question for the organizers.
- **My measurement error, caught before reporting:** the replication first used the numbering-agnostic
  scan because the sequences had no declared positions. Base unaffected (it always picked Asp86); the
  donor scan often picked another Gln/Asn (217, 49, 119), understating the scored distance. s059's donor
  was 2.70-2.95 A by scan and 3.82-4.85 A at GLN52. `build_boltz_queries.py` now reads `base=`/`oxy=`
  from FASTA headers and `replicate_seeds.sbatch` aggregates on the pinned columns.
- `results/designs.fasta` now holds one design and the organizers' `validate-submission.py` ACCEPTS it.
