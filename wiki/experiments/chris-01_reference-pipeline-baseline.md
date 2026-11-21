# chris-01: reference pipeline baseline

- **Owner:** chris
- **Date:** 2026-11-21
- **Status:** done: supported
- **Question:** Does the provided pipeline run end to end on our cluster, and what baseline numbers does
  its reference design give us?
- **Why it matters:** Sets the number to beat, and shows how a design's `base=`/`oxy=` header indices come
  out of the pipeline.
- **Script + config:** organizers' `bash /mnt/ref/hackathon/setup.sh` (verification mode, strict, exactly 260 residues)
- **Runs:** cluster job `1`, `/mnt/work/kemp_example/results/kemp-1/`, finished 2026-11-21 ~10:38,
  ~23 min wall clock on one NVIDIA L4. Summary copied to `results/reference_kemp-1_summary.json`.

## Result

`status: passed`, `pipeline_completed: true`, `validation_warnings: []`.
A 260-residue design, ligand 6NT. All numbers below are read from that `summary.json`.

**Catalytic contacts — RFD3's design vs the Boltz-2 refold (the refold is what gets scored):**

| Contact | RFD3 design | Boltz-2 | change |
|---|---|---|---|
| `A127_OD2 → 6NT_N3` (catalytic base, D177) | 2.53 Å | **5.91 Å** | **+3.38 Å** |
| `A50_NE2 → 6NT_N1` (donor, Q99) | 3.09 Å | 2.94 Å | −0.15 Å |

**Boltz-2 confidence and geometry:**

| Metric | Value | Note |
|---|---|---|
| `complex_ipde` | **1.8669** | the iPDE scoring term; lower is better |
| `confidence_score` | 0.8359 | |
| `iptm` / `ligand_iptm` | 0.8372 | |
| `complex_plddt` / `complex_iplddt` | 0.8355 / 0.7009 | |
| `minimum_ligand_protein_distance` | 2.1868 Å | |
| `ligand_protein_pairs_below_2_2_angstrom` | **1** | one borderline-close contact |
| `backbone_ca_rmsd_from_rfd3` | 1.4326 Å | the fold moves during refolding |

**MSA:** the design got `depth: 1` (query only, no homologues — expected and allowed for a novel design);
the natural-protein control P00698 got depth 301, which is what the strict setup check requires.

**Header indices are derivable from the pipeline output:** `summary.json → rfd3.fixed[]` gives
`position` and `amino_acid`, and those positions are 1-based indices into `ligandmpnn.sequence`.
Verified: position 177 is `D`, position 99 is `Q`, so this design would be declared `base=177 oxy=99`.
Both our `make submission` and the organizers' `validate-submission.py` accept that file.

## Verdict and next step

The pipeline works and the toolchain is verified. The useful finding is the **first row of the table**:
the base contact is well placed in RFD3's output (2.53 Å) but **falls apart to 5.91 Å after Boltz-2
refolds the complex** — far outside hydrogen-bonding range — while the donor contact survives.
Scoring is done on the Boltz-2 cofold, and catalytic contact distance carries the most weight, so a
design that only looks good in RFD3's output can still score badly.

Caveats, stated plainly: this is **n = 1**, from an example built to exercise the code rather than to
score well, and the single borderline contact (2.19 Å) plus 1.43 Å backbone drift suggest this particular
design is not tightly packed. Whether the base contact generally degrades is **not established** by one run.

**Next steps**
1. Measure the RFD3 → Boltz-2 contact change across several seeds (cheap: only `seed` in
   `src/kemp-e2e.sbatch` changes). If it is systematic, we must filter candidates on **Boltz-2** geometry,
   not RFD3 geometry — that changes how we spend GPU time.
2. Do not submit this sequence: it is the shared example, so every team has it, and its novelty is unverified.
3. Build the local geometry filter (distance + angle + in-plane, worse-of-the-two) against these numbers
   as a known reference point.
