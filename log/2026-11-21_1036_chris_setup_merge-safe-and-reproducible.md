# [2026-11-21 10:36] setup | Merge-safe branches + reproducibility hardening (chris)

- Removed merge hotspots:
  - `LOG.md` → one file per entry in `log/`
  - the experiments table → one page per experiment in `wiki/experiments/`
  - global counters → per-person IDs (`<handle>-NN`)
  - shared line lists (INDEX, decisions, glossary, data) get `merge=union`
  - `uv.lock` is never text-merged; regenerate it with `uv lock`
- Safety nets:
  - pre-commit hooks: conflict markers, large files, private keys, ruff, nbstripout, index lint
  - CI on every branch with `uv sync --locked`
  - `check_index` flags duplicate INDEX entries and badly named log/experiment files
- Reproducibility:
  - committed `uv.lock`
  - `kemp.data.fetch` with sha256 checks
  - run dirs now also store the git diff, a script snapshot, the uv.lock hash, host and GPU
  - `envs/` for external tool environments
  - `make reproduce`
- New: `CONTRIBUTING.md` (branch and merge playbook), `tools/new.py`, `tools/status.py`, `/sync` skill, `wiki/data.md`, `wiki/pitch.md`.
- Next: everyone installs uv and runs `make setup`, picks a handle in `wiki/team.md`, and branches as `<handle>/<topic>`. The repo owner turns on branch protection for `main`.
