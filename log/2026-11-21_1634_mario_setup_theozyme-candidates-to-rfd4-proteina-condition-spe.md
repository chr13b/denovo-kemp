# [2026-11-21 16:34] setup | Theozyme candidates to RFD4-Proteina condition spec and input CIFs (mario)

- Added `scripts/01_build_theozyme_inputs.py`: reads the TS-like PDBs of the 11 recommended candidates from `pre_analysis/kemp_theozymes_v2/candidates/` and writes `results/theozymes/` (one input CIF each plus `theozymes.yaml`, the RFD4-Proteina YAML condition spec). Standard library only; it re-reads each CIF and compares it with the PDB.
- Per design: 6NT and the catalytic atoms have fixed coordinates, residues with a fixed side chain have fixed identity, every motif residue is unindexed, and one expandable segment of 160–240 residues is the scaffold (limit 260). Backbone-only N–H donors keep a free identity.
- Chose the YAML spec over the Python API because `atomworks` is not installed on this laptop and the spec is readable data with a dry run (`write_condition_spec_cifs.py`).
- `tests/test_theozyme_inputs.py` (5 tests) passes. Nothing has been run through RFD4-Proteina: the hand-written CIFs, the contig and the 6NT chemistry still need the Euler check described in `wiki/theozyme-inputs.md`.
- Choices to review are listed in `wiki/theozyme-inputs.md` (side chain + CA fixed for the base, scaffold length, free identity of N–H donors, no `C_HB`/`C_PISTACK`/`C_RAS` yet).
