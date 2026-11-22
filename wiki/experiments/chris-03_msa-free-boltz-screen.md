# chris-03: can we drop the MSA stage?

- **Owner:** chris
- **Date:** 2026-11-21
- **Status:** done: supported
- **Question:** Every de novo design we generate reports **MSA depth 1, nonquery_rows 0** — MMseqs2 searches
  183 GB and finds no homologues. That search costs ~10 of the 23 minutes per job. If an MSA of the query
  alone is informationally identical to no MSA, we can delete the stage and roughly double throughput.
  Does Boltz-2 in single-sequence mode reproduce the MSA-based result?
- **Why it matters:** Compute is the binding constraint. Geometry dominates scoring and ~half of all
  designs fail to refold, so the number of designs we can afford to generate and screen decides how many
  good ones we find.
- **Script + config:** cluster job `6`, project `/mnt/work/projects/chris_msatest`, both arms in one job on
  one GPU so hardware and software state are identical. Inputs differ by exactly one line:
  ```diff
  -    msa: /mnt/work/projects/chris_seedsweep_s4/results/kemp-4/msa/kemp.a3m
  +    msa: empty
  ```
  Same sequence (seed 4), same `--seed 1`, same `--sampling_steps 200 --recycling_steps 3`.
- **Runs:** `/mnt/work/projects/chris_msatest/results/msatest-6/{msa,nomsa}/`

## Result

**Every confidence metric is identical to four decimal places.**

| Metric | with MSA | no MSA | diff |
|---|---|---|---|
| `confidence_score` | 0.9269 | 0.9269 | 0.0000 |
| `ptm` | 0.9555 | 0.9555 | 0.0000 |
| `iptm` / `ligand_iptm` | 0.8461 | 0.8461 | 0.0000 |
| `complex_plddt` | 0.9470 | 0.9470 | 0.0000 |
| `complex_iplddt` | 0.8707 | 0.8707 | 0.0000 |
| `complex_pde` | 0.4051 | 0.4051 | 0.0000 |
| **`complex_ipde`** | **1.5021** | **1.5021** | **0.0000** |

And the predicted structures are **bit-identical** — same MD5 (`a3f430fe0f2c…`) over all 1983 atoms.
Not "similar within noise": the same file.

### Stage costs (why this is worth so much)

From the job logs and file timestamps, of the ~23 min per design:

| Stage | Time | Note |
|---|---|---|
| RFD3 | ~12 min | the real cost of *designing* |
| LigandMPNN | ~6 s | negligible |
| **MMseqs2 (MSA)** | **~10 min** | **provably produces nothing for our designs** |
| **Boltz-2** | **~19 s** | **evaluation is essentially free** |

The expensive half of our pipeline was computing an empty file.

## Verdict

**Supported, as strongly as this can be shown.** For de novo designs that return MSA depth 1, the MSA
stage is a no-op and can be removed with *zero* loss of fidelity.

Two consequences, the second larger than the first:

1. **~1.8× throughput immediately** — 23 min → ~13 min per design.
2. **The 30 GB memory requirement disappears with MMseqs2.** That requirement is the only reason the job
   asks for `g6.2xlarge` and therefore the only reason we run **one job at a time**. Without it, design
   jobs fit the smaller nodes and **two can run in parallel** — so the practical gain is closer to **3–4×**.

Also worth noting: **evaluation is nearly free (19 s)**. Screening strategy should therefore be "generate
backbones, Boltz-2 everything, filter on the result" rather than "filter cheaply to avoid Boltz-2". The
expensive stage is RFD3, not evaluation — which inverts the assumption behind
[chris-02](chris-02_seed-sweep-boltz-vs-rfd3-geometry.md)'s proposed pre-filter.

### Caveat, stated clearly

This holds **only while MSA depth is 1**. If we ever design on a natural scaffold, or any sequence with
real homologues, the MSA will matter and this result does not transfer. The check is free — `summary.json`
reports the depth on every run. **Skip the MSA only when depth is 1.**

## Bonus: a first read on the consistency term

Seed 4's sequence scored `complex_ipde` **1.5184** with Boltz seed 4 (in chris-02) and **1.5021** here with
Boltz seed 1 — a 1.1 % change from the sampling seed alone, on a well-folded design. One pair is not a
distribution, but it suggests replicate variance is small for designs that fold, which would make the
consistency scoring term discriminate mostly between folders and non-folders rather than among good
designs. Worth the proper 5-replicate measurement before relying on it.

## Next steps

1. **Build the two-stage pipeline:** a design job (RFD3 → LigandMPNN, small node, no MSA) and an evaluate
   job (Boltz-2, 19 s). Run two design jobs in parallel.
2. Since evaluation is ~free, **evaluate everything** rather than pre-filtering, and keep the features
   (burial, Rg, secondary structure) alongside the outcome to build the labelled set a filter would need.
3. Re-check MSA depth on every new design; fall back to the full pipeline if it is ever > 1.
