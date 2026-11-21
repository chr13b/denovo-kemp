# [2026-11-21 16:59] decision | Neutral base carboxylate is the default in the theozyme inputs (mario)

- `scripts/01_build_theozyme_inputs.py`: `--base_charge` now defaults to 0 (was -1). The base and dyad carboxylate are written as the neutral acid, the CCD form of ASP/GLU; `--base_charge=-1` still writes -1 on one carboxylate oxygen. The 6NT keeps its CCD charges (NO1 +1, O21 -1). `results/theozymes/` regenerated; `wiki/theozyme-inputs.md` updated.
- Why: RFD4 documents no training definition for charges, the CCD form of Asp/Glu is neutral, and an explicit -1 on a canonical residue may be off-distribution. Whether a charged base helps is untested; compare `--base_charge=0` and `-1` if it matters.
