# Experiments

The registry of every experiment. Write the question first and fill in the result and verdict afterwards.
Details live in the run directory (`runs/<timestamp>_<name>/`) and in LOG.md.

Status: `planned` → `running` → `done: supported | refuted | inconclusive`, or `abandoned`.
IDs: `E-NNN`, incremented and never reused. A reusable config goes in `configs/E-NNN.json`.

| ID | Date | Owner | Question / hypothesis | Script + config | Run dir(s) | Result | Status |
|----|------|-------|-----------------------|-----------------|------------|--------|--------|
| E-000 | 2026-11-21 | setup | Do the env and the run bookkeeping work end to end? | `scripts/00_smoke.py` | `runs/*_smoke` | n/a | planned |
