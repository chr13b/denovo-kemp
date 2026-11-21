# LOG

Append-only and chronological, with the newest entry at the bottom. Never rewrite past entries; add a correcting entry instead.
Format: `## [YYYY-MM-DD] <type> | <title>` followed by 1–5 bullets.
Types: `setup ingest experiment decision fix lint submit`.
Write paths as `code`, not links, so the log never accumulates dead links.
Recent entries: `grep "^## \[" LOG.md | tail -10`

## [2026-11-21] setup | Repo scaffold
- Created the three-layer layout (`raw/`, `wiki/` + `INDEX.md` + `LOG.md`, code → `runs/` → `results/`); rationale in `wiki/decisions.md` D-001.
- Added `kemp.paths`, `kemp.config`, `kemp.run`, `scripts/00_smoke.py` (template), `tools/check_index.py`, tests, CI, and the skills `/ingest`, `/experiment`, `/lint`.
- Next: put the organizers' brief in `raw/` and run `/ingest`; fill in `wiki/team.md`; first `uv sync`, then commit `uv.lock`.
