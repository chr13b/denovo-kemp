# zonghu-02: does the affinity ladder track measured catalytic efficiency?

> **Scope widened 2026-11-21, before any result.** The original plan was a two-control sanity
> check (a real Kemp eliminase vs lysozyme). It is now a **quantitative validation against
> published kinetics**: three enzymes from one evolutionary series whose catalytic efficiencies
> span ~1000-fold, measured in one lab with one assay. That is a far stronger test, and it can
> fail in a way the binary control could not. The original control arms are kept as arm 4/5.


- **Owner:** zonghu
- **Date:** 2026-11-21
- **Status:** planned
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

TODO: only numbers read from the run's `affinity_*.json` / `summary.json`.

## Verdict and next step

TODO
