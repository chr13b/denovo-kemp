# [2026-11-21 19:55] decision | add numpy and biotite for the design-funnel filters (zonghu)

- **Added `numpy` and `biotite` as the project's first runtime dependencies** (`uv add`), for
  [`src/kemp/structure.py`](../src/kemp/structure.py). Every structural filter in the funnel —
  motif RMSD, radius of gyration, clash counting, backbone dihedrals, secondary structure,
  packing, pLDDT, ligand contacts — needs array maths and a structure parser that reads
  `.pdb`, `.cif` and `.cif.gz`. The alternative was shipping filter code that only runs on the
  cluster; this way the whole sequence and structure funnel is testable locally and in CI.
  `src/kemp/filters.py` stays **standard-library only**, so sequence and score filters run
  with no dependencies at all.
- **Two tools the architecture asked for do not exist on this cluster, and I substituted
  rather than wrote code against them.** Checked all three conda envs and the PATH:
  - **No `mkdssp` / `dssp` / `stride` anywhere.** Topology uses biotite `annotate_sse`
    (P-SEA, CA-geometry). It agrees with DSSP on most regular elements but **is not DSSP**,
    and every result it produces carries `method` saying so.
  - **No Rosetta.** `packing_density()` is a neighbour-count proxy, labelled
    `"NOT Rosetta PackStat"` in its own return value so it cannot be quoted as PackStat later.
  - Ramachandran uses coarse favoured boxes, not MolProbity contours.
- **Filters have three states, not two.** `passed=None` means *could not be evaluated*
  (file missing, atom absent, score field absent) and **blocks the gate** — it never counts
  as a pass. Given how much of this session has been "the number looked fine and meant
  nothing", a design must never be recorded as passing a filter that never ran.
- **Cross-checked the biophysics against Biopython 1.84** (cluster, env-boltz2), four real
  sequences: **GRAVY agrees exactly to 4 decimal places.** pI reads 0.08–0.24 units lower,
  because ours is the **EMBOSS/pepstats** pKa set while Biopython defaults to **Bjellqvist**.
  Both are standard; the offset is far smaller than the gate window. I had written
  "verified against Biopython" in the source *before* verifying — that claim was false when
  written and is now corrected with the measured numbers and both pKa sets named.
- Structure filters are validated against a real file in the repo: the crystal contacts come
  back as 2.53 Å and 3.20 Å, matching the independent pure-Python measurement made earlier
  in [zonghu-01](../wiki/experiments/zonghu-01_trp-stack-theozyme-vs-crystal.md).
