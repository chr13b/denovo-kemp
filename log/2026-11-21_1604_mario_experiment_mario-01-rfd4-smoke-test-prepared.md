# [2026-11-21 16:04] experiment | mario-01 RFD4 smoke test prepared (mario)

- Prepared mario-01 (status `planned`): `scripts/10_generate_smoke_design.py` + `configs/mario-01.json` generate one unconditional 100-residue monomer with `rfd4-generate` on Euler and check the pipeline; page `wiki/experiments/mario-01_rfd4-euler-smoke.md` has the `sbatch` command.
- Checked locally only, against a stub `rfd4-generate`: arguments and working directory are as intended, and success, failure, empty output, compressed output, missing tool and missing checkout all behave; ruff passes. The real model was not run.
- Unverified: checkout path `~/rfd4-proteina`, plain `.cif` output in `inference_samples/`, weight availability, driver vs the CUDA 13 build on the A100 nodes.
- Not run yet; no result to record.
