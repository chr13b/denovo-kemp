# [2026-11-21 15:05] experiment | chris-03: MSA stage is provably a no-op; novelty confirmed for seed 4 (chris)

- **chris-03 (job 6): dropping the MSA changes nothing.** Boltz-2 run twice on seed 4's sequence, same
  GPU, same seed, differing only `msa: <a3m>` vs `msa: empty`. Every confidence metric identical to 4 dp
  (`complex_ipde` 1.5021 both), and the predicted structures are **bit-identical** (same MD5, 1983 atoms).
- **Stage costs measured:** of ~23 min per design, RFD3 ~12 min, **MMseqs2 ~10 min**, LigandMPNN ~6 s,
  **Boltz-2 ~19 s**. The expensive half of the pipeline was computing an empty MSA.
- **Consequence is bigger than the time saved.** The 30 GB requirement exists only for MMseqs2, and that
  requirement is why we run one job at a time. Without it, design jobs fit the small nodes and two run in
  parallel: ~3–4× effective throughput.
- **This inverts chris-02's conclusion about pre-filtering.** Evaluation costs 19 s, so we should Boltz-2
  *everything* and filter on the result, rather than building a cheap filter to avoid Boltz-2. The
  expensive stage is RFD3.
- **Caveat:** valid only while MSA depth is 1. `summary.json` reports it every run — check it, and fall
  back to the full pipeline if a design ever has real homologues.
- **Novelty, seed 4 — measured.** foldseek (installed, `envs/foldseek.sh`) TM-align vs the Kemp family
  pulled from RCSB (4BS0 HG3.17, 3NYD, 2RKX, 3IIO/3IIV, 1THF, 1A53): **best TM-score 0.367** (0.361 to
  4BS0), sequence identity 2–3 %. Gate is TM ≤ 0.7. Combined with MSA depth 1 (no homologues in 183 GB),
  seed 4 passes both halves of the novelty gate. Broad PDB-representative database still building.
- **Catalytic geometry targets now measured, not guessed.** PDB 4BS0 is HG3.17 at 1.09 Å **with 6NT
  bound** — the same ligand we are scored against. `scripts/31_measure_reference_geometry.py` reads:
  Asp127 OD2 → N3 **2.53 Å**, Gln50 NE2 → N1 **3.10 Å**, Trp44 NE1 → N3 3.86 Å. These are exactly the
  numbers RFD3 is handed, confirming the motif is lifted from this structure. Seed 4 sits ~0.7 Å long on
  both contacts — loose, but in the forgiving direction.
- Literature: `tools/fetch_papers.sh` pulls 7 open-access PDFs into `data/papers/` (gitignored);
  annotated list in [../wiki/literature.md](../wiki/literature.md). The three core Kemp papers are
  paywalled, but 4BS0 gives us what we needed from them.
