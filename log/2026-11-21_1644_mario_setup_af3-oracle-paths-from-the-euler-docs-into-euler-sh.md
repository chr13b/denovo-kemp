# [2026-11-21 16:44] setup | AF3 oracle paths from the Euler docs into euler.sh and the wiki (mario)

- Read how RFD4-Proteina defines the refolding oracle (Hydra config group `metrics/refolding_oracles`, `AF3Oracle` runs in an Apptainer container, reads `AF3_IMAGE`, `AF3_MODEL_DIR`, `AF3_JAX_CACHE_DIR`) and the ETH AF3 page (container `/cluster/apps/nss/alphafold/containers/AlphaFold3/af3.sif`, databases `/cluster/project/alphafold/alphafold3`, weights not provided centrally).
- `envs/euler.sh` now sets the three variables (defaults under `$HOME/rfd4-proteina/data_path/openfold3/`, overridable) and only warns when they point at nothing; test-sourced locally with a fake HOME under `set -u`.
- `wiki/euler-rfd4.md` has a "Refolding oracle" section and a new open item. The Euler `af3.sif` probably does not fit RFD4 (`run_alphafold_batch.py` in `af3-open.sif` vs `run_alphafold.py`); nothing here was run on Euler.
