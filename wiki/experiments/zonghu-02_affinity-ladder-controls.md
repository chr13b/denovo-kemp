# zonghu-02: does the affinity ladder separate a real Kemp eliminase from a non-enzyme?

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

## Design

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
