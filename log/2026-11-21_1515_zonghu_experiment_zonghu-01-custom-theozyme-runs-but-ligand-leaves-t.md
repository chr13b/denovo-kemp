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
- **RFD3 produced 6 protein–ligand pairs < 2.2 Å** (min 1.655 Å, all against the nitro group, involving the
  Trp's CB/CG/CD1/backbone and Ser99) where chris's runs had 0. **The pipeline records this number and
  never checks it** — worth adding to our own tooling as a free RFD3-stage pre-filter, since unlike the
  contact distances it is not constant by construction.
- **I first blamed my cofacial geometry for that clash, and measuring it proved me wrong.** Clearance of
  the atoms RFD3 is free to move: crystal 3.86 Å (attachment end) / 5.11 Å (backbone); my idealised pose
  3.48 / **5.81** — *more* backbone room than the crystal. The cause was **under-constraint**: pinning only
  6 of the indole's 9 atoms let RFD3 move CD1/NE1/CB by ~1 Å, which it should not be able to do at all
  since the indole is a rigid fused ring.
- **Fixed on the laptop, no GPU:** `theozyme_7k4u_core_trpopt2.pdb` reaches 3.97 Å / 6.04 Å — better than
  the crystal on both — **while keeping the cofacial stack** (perp 3.65 Å, offset 0.00 Å, 0.0°), costing
  0.20 Å of stacking distance. New configs pin the whole indole. Next GPU slot: 3 arms × 2 seeds, where
  `_trpopt` vs `_trpopt2` isolates the pinning and crystal vs `_trpopt2` isolates the geometry.
