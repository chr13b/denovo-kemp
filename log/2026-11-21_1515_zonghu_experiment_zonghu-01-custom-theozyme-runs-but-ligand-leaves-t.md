# [2026-11-21 15:15] experiment | zonghu-01 custom theozyme runs, but ligand leaves the site (zonghu)

- **A custom theozyme does run through the stock pipeline.** [zonghu-01](../wiki/experiments/zonghu-01_trp-stack-theozyme-vs-crystal.md)
  job 7: `pipeline_completed: true`, RFD3 held a 3-residue motif to 0.0167 Å, and `seq[98] = W`. Two gotchas
  for anyone doing the same: `prepare_rfd3_input.py` **overwrites** `specification["input"]`, so you must
  replace `inputs/HG3_17_kemp_motif.pdb` itself rather than edit the `input` field; and
  `prepare_ligandmpnn.py` fixes only A50/A127, so a third motif residue gets designed away unless you add
  it to the mapping loop.
- **The design failed anyway:** Boltz-2 base contact **11.99 Å**, donor **26.49 Å**. Not a candidate, not
  added to `results/designs.jsonl`. This is *not* evidence against the theozyme — 11.99 Å is inside the
  3.32–21.92 Å range [chris-02](../wiki/experiments/chris-02_seed-sweep-boltz-vs-rfd3-geometry.md) measured
  with the stock motif, and my two control arms were cancelled, so n = 1 with no baseline.
- **`complex_ipde` did not catch it: 1.665, better than chris-01's 1.867, while the ligand sat 12 Å away.**
  Before building a cheap refold filter on iPDE, treat this as a counter-example — filter on the base and
  donor contact distances themselves.
- **A refold that is neither outcome in chris-02:** CA RMSD **4.26 Å**, inside the 1.4–13.7 Å gap that
  sweep found empty, with folded-range iPDE and no clashes, yet the ligand bound at a different site. The
  binary picture is a good rule of thumb but not exhaustive.
- **My idealised Trp theozyme is flawed and I would not reuse it as-is.** RFD3 produced 6 protein–ligand
  pairs < 2.2 Å (min 1.655 Å, all against the nitro group, involving the Trp's CB/CG/CD1/backbone and
  Ser99). Pinning only the indole six-ring left the attachment end free, and a cofacial stack leaves it
  nowhere to go but into the nitro substituent. The crystal's offset pose may be what keeps the Trp
  attachable. Fix the builder and pin `CG` before re-running; the pipeline never checks this number.
