# [2026-11-21 11:40] experiment | chris-01 reference pipeline verified, baseline geometry measured (chris)

- Cluster job `1` finished: `VERIFIED: three independent GPU smoke tests and the Kemp pipeline passed.`
  The team's `/mnt/work/kemp_example` is now the verified reference; leave it untouched.
- Baseline from `results/reference_kemp-1_summary.json`: `complex_ipde` 1.8669, `iptm` 0.8372,
  `complex_plddt` 0.8355, min ligand-protein distance 2.1868 Å, 1 pair below 2.2 Å, CA RMSD 1.4326 Å.
- **Finding:** the catalytic base contact is 2.53 Å in RFD3's design but **5.91 Å after the Boltz-2 refold**
  (+3.38 Å), while the donor contact holds (3.09 → 2.94 Å). Scoring uses the Boltz-2 cofold, so RFD3
  geometry alone is not a safe filter. n = 1, so not yet established — next step is a seed sweep.
- Confirmed `base=`/`oxy=` indices are derivable: `rfd3.fixed[].position` are 1-based indices into
  `ligandmpnn.sequence` (177 = D, 99 = Q). `make submission` and the organizers' validator both accept it.
- Full write-up: `wiki/experiments/chris-01_reference-pipeline-baseline.md`.
