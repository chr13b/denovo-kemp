# zonghu-02: does the affinity ladder track measured catalytic efficiency?

> **Scope widened 2026-11-21, before any result.** The original plan was a two-control sanity
> check (a real Kemp eliminase vs lysozyme). It is now a **quantitative validation against
> published kinetics**: three enzymes from one evolutionary series whose catalytic efficiencies
> span ~1000-fold, measured in one lab with one assay. That is a far stronger test, and it can
> fail in a way the binary control could not. The original control arms are kept as arm 4/5.


- **Owner:** zonghu
- **Date:** 2026-11-21
- **Status:** done: refuted — the ladder does **not** track catalytic efficiency; do not rank designs with it
- **Question:** Boltz-2 can predict a binding affinity for a protein–ligand pair. If we run it for the
  substrate, the TS analogue and the product against the same protein, does
  **ddG(substrate − TS)** come out positive for a *real* Kemp eliminase (HG3 K50Q) and ~zero for a
  protein that is not one (lysozyme)? And does it exceed Boltz-2's own seed noise?
- **Why it matters:** Transition-state stabilisation is the physical origin of catalysis
  (`k_cat/k_uncat ≈ K_S/K_TS`), so a working ladder would be a **causal** design filter rather than a
  geometric proxy, and it is cheap: no MMseqs2, so it runs on the small GPU nodes, two at a time,
  without touching the node the RFD3 pipeline needs. If the positive control shows no TS preference,
  the method is uninformative and we drop it — which is a cheap, valuable negative result either way.
- **Script + config:** [`scripts/20_build_affinity_ladder.py`](../../scripts/20_build_affinity_ladder.py)
  → cluster → [`scripts/21_report_affinity_ladder.py`](../../scripts/21_report_affinity_ladder.py).
  Method and limits: [../affinity-ladder.md](../affinity-ladder.md). Ligands: [`src/kemp/ligands.py`](../../src/kemp/ligands.py).
- **Runs:** TODO — cluster projects `/mnt/work/projects/zonghu_aff_<label>`

Status values: `planned`, `running`, `done: supported`, `done: refuted`, `done: inconclusive`, `abandoned`.

## Validation against measured catalytic efficiency (the main test)

Three enzymes from the **HG evolutionary series**, cluster jobs `11`, `12`, `13`. Same scaffold,
same lab, same assay, so the only thing varying is the enzyme:

| variant | mutations from HG3 | **k_cat/K_M (M⁻¹s⁻¹)** | vs HG3 | residue 50 |
|---|---|---|---|---|
| **HG3** | — | **160 ± 10** | 1× | K |
| **HG3.7** | 7 | **28 000 ± 4 000** | 175× | Q |
| **HG3.17** | 17 | **170 000 ± 20 000** | 1060× | Q |

Read from Table 1 (p25) of Broom et al., bioRxiv [2020.03.19.999235](https://www.biorxiv.org/content/10.1101/2020.03.19.999235v1.full),
published as Nat. Commun. 11, 4808 (2020). Table 1 also gives Blomberg et al.'s values for the same
enzymes in parentheses — **1300 / 37 000 / 230 000** — which disagree with these by up to 8× for HG3.
That between-lab spread is a floor on how precisely any prediction could possibly be validated.

Sequences are **constructed, not downloaded**: built by
[`scripts/22_build_hg_series.py`](../../scripts/22_build_hg_series.py) from the 7K4U chain-A
sequence (HG3 K50Q, RCSB lists exactly 1 mutation, so reverting Q50K recovers HG3) by applying
Table 1's mutation lists. **Every mutation's wild-type residue is asserted against the base
sequence before it is applied**, and all 17 HG3.17 mutations passed — a numbering or construct
mismatch would have aborted the build rather than producing a plausible wrong sequence.

### What this can and cannot validate

**Cannot validate substrate binding.** Table 1's footnote b says K_M and k_cat "could not be
determined accurately because saturation was not possible at the maximum substrate concentration
tested (2 mM)". There is no published K_M for this series, so there is **no experimental
substrate-binding constant to compare against** — see [../affinity-ladder.md](../affinity-ladder.md).

**Can validate transition-state affinity.** k_cat/K_M is the free energy of the transition state
relative to free enzyme + free substrate, which is a transition-state affinity — the quantity the
ladder's reference leg estimates.

### Decision rule (written before the results)

A 1060-fold spread in k_cat/K_M is **ΔΔG‡ = RT·ln(1060) = 4.13 kcal/mol** at 298 K. If the ladder
measures transition-state stabilisation, the TS leg should get *tighter* along HG3 → HG3.7 → HG3.17,
and ddG(substrate − TS) should *increase*, by something approaching that 4.13 kcal/mol.

| Outcome | Reading | What we do |
|---|---|---|
| ddG(sub − TS) rank order = HG3 < HG3.7 < HG3.17, and the HG3→HG3.17 gap exceeds its propagated noise | the ladder tracks real catalysis | Use it as a design filter; report the measured slope vs 4.13 kcal/mol. |
| rank order correct but gap within noise | directionally right, not usable at n=3 | Keep, but only with many more seeds; do not rank designs on it yet. |
| rank order wrong, or all three within noise | the ladder does not track catalysis | **Drop it.** Record so nobody re-spends GPU. |

With n = 3 enzymes this is a **rank-order check, not a correlation** — three points cannot establish
one. It is nonetheless a real falsification test: a metric that cannot order 160 vs 170 000 M⁻¹s⁻¹
cannot possibly rank our designs, which differ far less.

## Secondary: does it separate an enzyme from a non-enzyme?

Three proteins × 3 ligands × 3 seeds = **27 Boltz-2 affinity predictions**. The ladder is
[the three matched ligands](../affinity-ladder.md): identical MW (164.12) and heavy-atom count (12),
with `ts_analog` carrying the same InChIKey as CCD `6NT`.

| arm | sequence | why |
|---|---|---|
| **positive control** | HG3 K50Q, 7K4U chain A, 305 aa — [`results/affinity/hg3_k50q_7k4u_chainA.fasta`](../../results/affinity/hg3_k50q_7k4u_chainA.fasta) | an evolved, experimentally active Kemp eliminase. W44/Q50/D127 verified present at the expected positions. **Must** prefer the TS analogue or the method is uninformative. |
| **negative control** | chicken lysozyme `P00698` (on the cluster in `inputs/mmseqs_control.fasta`) | not a Kemp eliminase and not evolved for this ligand class. Should show no preference. |
| **our design** | the job-7 sequence from [zonghu-01](zonghu-01_trp-stack-theozyme-vs-crystal.md), 260 aa | the first thing we would actually want to score. |

`msa: empty` (single-sequence mode) for all arms. It lowers absolute confidence but is **identical
across the three ligands within an arm**, so it cannot bias the ddG, which is the only quantity used.

### Decision rule (written before the results)

Read `affinity_pred_value` = log10(IC50/µM) from each `affinity_*.json`; 1 decade = 1.364 kcal/mol.

| Outcome | Reading | What we do |
|---|---|---|
| positive control `ddG(sub − TS) > 0` **and** exceeds 2 propagated SEM, **and** the negative control does not | the ladder discriminates | Use it as a design filter. Score zonghu-01 and every future candidate. |
| positive control ddG ≈ 0 or negative (within noise) | uninformative, or Boltz-2 affinity cannot resolve 12-heavy-atom fragments | **Drop the method.** Record it so nobody re-spends GPU on it. |
| both controls show the same large preference | we are measuring the ligands, not the protein | Drop it: a ladder that ranks the ligands identically for any protein carries no design signal. |

Secondary, no decision attached: `affinity_probability_binary` per arm (a sanity gate — if every
ligand scores < 0.5 the protein is not treated as a binder at all), `ddG(product − TS)` as the
product-inhibition read, and the seed spread per arm as a noise baseline for future runs.

**What this cannot do:** prove catalysis. It compares a stable TS *analogue*, not the real anionic
transition state, and n = 3 seeds gives a spread, not statistics. See
[../affinity-ladder.md](../affinity-ladder.md) limits 1–4.

## Result

**Status: done: refuted.** 27/27 predictions completed (cluster jobs `14`, `15`, `16`; jobs `11–13`
were a launcher bug, no results). Every number below is read from the tracked
[../../results/affinity/zonghu-02_ladder_vs_kinetics.md](../../results/affinity/zonghu-02_ladder_vs_kinetics.md);
regenerate with `uv run python scripts/23_compare_ladder_to_kinetics.py`.

| variant | measured k_cat/K_M | TS leg log10(IC50/µM) | ddG(sub−TS) kcal/mol | ddG(prod−TS) kcal/mol | mean P(binder) |
|---|---|---|---|---|---|
| HG3 | 160 | 2.062 ± 0.174 | **−1.116 ± 0.162** | −0.661 ± 0.155 | 0.42 |
| HG3.7 | 28 000 | 2.003 ± 0.202 | **−1.015 ± 0.236** | −0.704 ± 0.188 | 0.41 |
| HG3.17 | 170 000 | 2.060 ± 0.118 | **−0.703 ± 0.131** | −0.946 ± 0.141 | 0.33 |

HG3 → HG3.17 is a measured **1062-fold** change in catalytic efficiency = **+4.129 kcal/mol** of
transition-state stabilisation.

- **TS leg shift: −0.003 ± 0.166 kcal/mol — 0.06 % of expected, 0.0 σ.** Predicted transition-state
  affinity is 2.062 / 2.003 / 2.060: *flat to three significant figures* across a thousand-fold
  change in real catalytic power. This is the decisive number.
- **ddG(sub−TS) shift: +0.413 ± 0.208 kcal/mol — 10.0 % of expected, 2.0 σ.** Rank order matches
  activity (HG3 < HG3.7 < HG3.17).
- **The sign is wrong for all three.** ddG(sub−TS) is **negative** everywhere, i.e. the substrate is
  predicted to bind *more tightly* than the TS analogue — the anti-catalytic direction — including
  for HG3.17, one of the most efficient artificial enzymes ever made.
- **The product leg runs backwards:** ddG(prod−TS) becomes *more* negative along the series
  (−0.661 → −0.946), predicting the best enzyme suffers the worst product inhibition.
- **P(binder) < 0.5 for all 9 protein/ligand combinations, and it is inverted:** HG3.17 scores
  *lowest* (0.33) and HG3 highest (0.42). Boltz-2's own binder/decoy head ranks the best enzyme as
  the least likely binder.

## Verdict and next step

**The pre-registered rule's first row was technically met — and I am failing the method anyway.**
That is a judgement call and it should be visible, not buried: the rule asked for correct rank order
plus a gap exceeding its noise, and it got correct order at exactly 2.0 σ. Five reasons it should
still be rejected:

1. **The TS leg is flat (0.06 % of expected, 0.0 σ).** k_cat/K_M *is* a transition-state affinity,
   so this is the most direct comparison available, and it shows no signal whatsoever. The small
   ddG(sub−TS) trend therefore comes from the substrate leg drifting, not from the TS being bound
   better — which is not the physics the metric claims to measure.
2. **The sign is wrong in every arm**, so the metric would label a 170 000 M⁻¹s⁻¹ enzyme
   anti-catalytic.
3. **10 % of the expected magnitude.** Our designs will differ far less than 1062-fold, so the
   residual signal would be far below noise.
4. **Correct rank order of 3 items happens by chance 1 in 6 times.** With n = 3 it is weak evidence,
   and I pre-registered it without accounting for that — a flaw in my rule, not a result.
5. **P(binder) is inverted vs activity**, an independent head of the same model disagreeing with
   the ordering.

**Do not use the affinity ladder to rank designs.** The pipeline itself is correct and reusable —
the API is verified, the ligands are size- and mass-matched, the noise handling works — but
Boltz-2's affinity head does not resolve these 12-heavy-atom fragments at the ≥ mM affinities Kemp
eliminases actually have. This is limit 1 and limit 4 of [../affinity-ladder.md](../affinity-ladder.md)
turning out to bite.

**Cost of finding this out: ~35 min on two small GPU nodes**, with the big node left free. Cheap for
a result that stops us ranking 20 submission slots on a number that does not track catalysis.

Next steps:

1. **Do not re-run this on designs.** Record and move on; that is the whole value here.
2. The two original controls (HG3 K50Q vs lysozyme) are **no longer worth running** — a method that
   cannot separate 160 from 170 000 M⁻¹s⁻¹ within one scaffold will not be rescued by an
   enzyme/non-enzyme contrast.
3. If anyone wants to revisit affinity prediction: the open question is whether an MSA (instead of
   `msa: empty`) or many more seeds changes the TS leg. I would not spend GPU on it before the
   submission deadline.
4. **Keep `scripts/20–23`.** The bundle builder is a working, tested way to run any Boltz-2 affinity
   job on the small nodes without touching the RFD3 node, which is useful independently of this
   negative result.
