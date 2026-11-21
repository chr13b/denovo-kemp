# [2026-11-21 15:12] ingest | Pre-analysis moved into the repo (mario)

- Moved four standalone analysis folders (published Kemp structures, nitro-enzyme contacts, theozyme generators v1 and v2) into `pre_analysis/`; layout, run order and status are in `pre_analysis/README.md`, the pointer page is `wiki/theozyme-preanalysis.md`.
- Bulk downloads and regenerable intermediates are gitignored (end of `.gitignore`); `pre_analysis/kemp_eliminase/fetch_structures.py` re-creates the downloads (dry run: 0 missing); the 21.6 MB ranking CSV is tracked as `pre_analysis/kemp_theozymes_v2/candidates_v2.csv.gz`.
- Bookkeeping: `INDEX.md` section, three rows in `wiki/data.md`, a `wiki/team.md` row, and `pyproject.toml` excludes `pre_analysis` from ruff (the scripts are not in the repo's code style).
- Checks: `make setup`, then all pre-commit hooks on all files (ruff included) and `pytest` (29 passed, 20 skipped) pass; `tools/check_index.py` reports 0 problems.
- Not done: the scripts do not use `kemp.config` / `start_run`, and there is no experiment page or run directory.
- Branch `mario` (single-branch style, as chris).
