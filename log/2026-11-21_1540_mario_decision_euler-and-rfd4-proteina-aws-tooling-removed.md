# [2026-11-21 15:40] decision | Euler and RFD4-Proteina, AWS tooling removed (mario)

- Decision: campaigns run on Euler with RFD4-Proteina, not the AWS cluster with RFD3 and LigandMPNN. Loop: edit locally, push, pull on Euler, run through `sbatch`. Recorded in `wiki/decisions.md` and `wiki/euler-rfd4.md`.
- Removed on this branch (all still on `main`): `.claude/skills/cluster/`, `wiki/cluster.md`, the key and connection steps of `onboard.sh` (now 4 steps), `tests/test_submission_vs_organizer.py`, the chris-01 and chris-02 experiment pages and log entries, `results/reference_kemp-1_summary.json`.
- Rewritten for Euler: Part 2 of `SETUP.md`, the cluster lines of `CLAUDE.md` and `AGENTS.md` (kept in sync), `README.md`, `INDEX.md`; dead links in `wiki/challenge.md` fixed.
- Raised, not resolved: the organizers ask teams to use only the provided computing resources (`raw/20261121_organizers_cluster-guide.md`), and Euler is not that cluster. Added as the first open question in `wiki/challenge.md`.
- Left alone: `raw/`, `wiki/submission.md` (still describes the RFD3 + LigandMPNN `base=` mapping), the cluster-etiquette lines in `wiki/team.md`, and numbers in `wiki/challenge.md` that came from the AWS pipeline. `tools/check_index.py` 0 problems, `pytest` 29 passed; not committed.
