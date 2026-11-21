# chris-07: can oversampling rescue the backbones we wrote off?

- **Owner:** chris
- **Date:** 2026-11-21
- **Status:** done: refuted (the backbones were genuinely weak)
- **Question:** chris-02 declared seeds 2 and 5 failures (CA RMSD 14.6 and 13.7 Å) and seed 3 a
  partial failure (base contact 8.33 Å). Each verdict rests on **one sequence**. Now that chris-04 has
  shown the sequence is what fails, **were those backbones ever bad?**
- **Why it matters:** two things at once. We concluded "budget for a ~50 % loss rate" from a sample
  where the loss may have been sequence-level, and chris-04 (g3) showed sequence sampling gives no
  fold diversity — so **backbones are the scarce resource**, and we may have thrown away three of
  five. If they can be rescued, our usable backbone count doubles for 16 min each instead of 12 min
  of RFD3 plus a fresh gamble.
- **Script + config:** `cluster/oversample.sbatch` via `cluster/launch_oversample.sh`
- **Runs:** cluster jobs **38** (seed 2), **39** (seed 3), **40** (seed 5), niced behind teammates

## What this run does

The identical protocol to chris-04, on the three discarded backbones, read-only from their existing
`bridge/` directories. **No RFD3 is re-run** — all three already satisfy the motif to 0.0129 Å with
RFD3 contacts 2.53 / 3.09 Å, exactly like seed 4. Geometrically the backbones are indistinguishable
at the motif; only their single sampled sequences differed.

48 sequences each at **T = 0.2 and 0.3** only, since chris-04 measured T = 0.1 as the worst of the
three (0 winners from 24, against 2 at T = 0.2 and 1 at T = 0.3). The three natural-enzyme controls
ride along in every batch.

## Pre-registered decision rule

| Observation | Reading | Next step |
|---|---|---|
| ≥1 rescued backbone yields a base contact in 2.41–2.69 Å | the 50 % "loss rate" was a **sampling artefact** | retract that figure; oversample every backbone before discarding it, and submit across folds |
| rescued backbones refold well (CA RMSD < 2 Å) but miss the window | backbone-level geometric floors are real and differ between seeds | use the window as the backbone-selection criterion, after sampling not before |
| all 48 sequences still collapse on seeds 2 and 5 | those backbones really are unfoldable | chris-02's verdict stands; keep the 50 % budget |

The discriminating comparison is **against seed 4's 2/72 hit rate**, not against zero. A backbone that
yields 0/48 where seed 4 yielded 2/72 is weak evidence; one that yields ≥2/48 is as good as seed 4.

## Result — both discarded backbones were genuinely weak, but the sweep found something better

### Seed 5: **not rescuable.** chris-02's verdict stands.

48 sequences at T = 0.2 / 0.3. `results/oversample_rescue_s5_job40.tsv`.

| | seed 4 | **seed 5** |
|---|---|---|
| median CA RMSD | 0.77 Å | **10.67 Å** |
| refolded < 2 Å | 70/72 (97 %) | **0/48 (0 %)** |
| best base contact | 2.38 Å | 3.33 Å |
| inside both windows | 2/72 | **0/48** |

Not a single sequence out of 48 could encode this backbone. Seed 5's RFD3 geometry is identical to
seed 4's at the motif (2.53 / 3.09 Å, deviation 0.0129 Å), yet **no sequence stabilises it**. So
designability really is a per-backbone property, invisible in the motif report — the point chris-05
made from the other direction.

### A finding that outranks the rescue question: single predictions are noisy

The natural-enzyme controls ride along in every sweep, same sequences, same `--seed 1`. They agreed
**exactly** between jobs 27 and 31 (both 75-structure batches) and then disagreed in job 40:

| batch | rows | 4BS0 base | 4BS0 donor | nearest donor found |
|---|---|---|---|---|
| job 27 | 75 | 2.4925 | 6.0775 | TYR176:OH |
| job 31 | 75 | 2.4925 | 6.0775 | TYR176:OH |
| **job 40** | **51** | **2.0722** | **4.8453** | GLN209:NE2 ✓ |

Boltz's `--seed` is per invocation, so the RNG stream depends on the batch, not on the structure. The
same sequence therefore gives base contacts of **2.49 Å and 2.07 Å** — a 0.42 Å swing, against a
target window **0.28 Å wide**.

**Consequence: a single fold cannot place a design inside the window.** s024's 2.49 Å is inside, but
the measurement noise is larger than the window. This is exactly why the organizers score consistency
over 5 Boltz-2 seeds — a term we had never measured. Job **47** now replicates s024, s059 and seed 4's
original sequence at seeds 1–5 (`cluster/replicate_seeds.sbatch`); until it returns, treat the Idea A
hit as promising rather than established.

It also means my claim last round that "the instrument check is deterministic" was wrong. It was
reproducible across two identically sized batches, which is not the same thing.

### Seed 3: designable, but still no hits

`results/oversample_rescue_s3_job39.tsv`, 48 sequences at T = 0.2 / 0.3. Median CA RMSD **1.53 Å**,
32/48 refolding under 2 Å — so this backbone *is* encodable, unlike seed 5. Best base contact 3.86 Å,
**0/48 in window**. At a ~3 % rate 48 sequences expect ~1.4 hits and P(0) ≈ 0.23, so this is
suggestive rather than conclusive — but combined with the median base contact of 7.45 Å it is not a
promising backbone.

(Seed 2 was cancelled: it collapsed at CA RMSD 14.6 Å with its one sequence, the same signature as
seed 5, and the queue was contended. If it matters later it is a 16-minute screen.)

## The finding that came out of this: designability predicts backbones, not sequences

Six backbones have now been swept under one protocol. Ranked by designability:

| backbone | n | median CA RMSD | **median base** | best base | in window |
|---|---|---|---|---|---|
| **seed 4** | 72 | **0.77 Å** | **5.12 Å** | 2.38 | **2/72** |
| 4BS0_A fresh | 32 | 1.33 | 6.66 | 2.90 | 0/32 |
| seed 3 | 48 | 1.53 | 7.45 | 3.86 | 0/48 |
| 8USL_B | 32 | 1.99 | 9.73 | 3.52 | 0/32 |
| Trp44 (3 anchors) | 72 | 2.02 | 7.64 | 3.26 | 0/72 |
| seed 5 | 48 | 10.67 | 11.32 | 3.33 | 0/48 |

| relationship | statistic |
|---|---|
| **across backbones**: median CA RMSD vs **median** base contact | **Spearman ρ = +0.943** (n=6) |
| across backbones: median CA RMSD vs *best* base contact | ρ = +0.486 — **confounded, do not use** |
| **within** seed 4 (n=72): a sequence's CA RMSD vs its base contact | **r = +0.122** |

Two things worth separating carefully:

1. **The two correlations are not in conflict, and the distinction is the whole point.** How
   designable a *backbone* is almost perfectly rank-orders how close its ligand ends up (ρ = 0.94).
   How well an individual *sequence* refolds tells you essentially nothing about its own contact
   (r = 0.12). So: **screen backbones on designability, then sample sequences blind.** There is no
   useful per-sequence filter, and folding is 19 s, so that is fine.
2. **The "best base contact" column is a trap and I nearly reported it.** Best-of-72 beats best-of-32
   by construction, so ranking backbones on their best result mostly measures how many sequences we
   drew. It drags the correlation from 0.94 down to 0.49. Compare medians, not minima, whenever the
   sample sizes differ.

## Verdict and next step

**chris-07 refuted: the discarded backbones were genuinely weak.** Seed 5 is unencodable (0/48 refold
under 2 Å) and seed 3, while encodable, sits mid-table with no hits. chris-02's ~50 % loss rate stands
as a rough figure — though the right way to state it is **~2 of 5 RFD3 seeds give a backbone worth
sampling deeply**, judged by median CA RMSD rather than by one sequence's fate.

The experiment paid for itself anyway: it supplied two of the six points that establish ρ = 0.94, and
that is what justifies spending ~16 minutes screening a backbone before spending ~25 minutes sampling
it.
