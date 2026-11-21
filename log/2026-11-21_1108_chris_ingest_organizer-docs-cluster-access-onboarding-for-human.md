# [2026-11-21 11:08] ingest | organizer docs, cluster access, onboarding for humans and agents (chris)

- Ingested the organizers' packet into `raw/` (start-here, cluster guide md+html, submission spec, our
  CONNECT details) and wrote it up: `wiki/challenge.md` (goal, hard rules, the 5 scoring terms),
  `wiki/cluster.md` (Slurm, 2 GPUs, project folders), `wiki/submission.md` (FASTA format, upload, deadline rules).
- **Cluster access verified** from this machine: key in `~/.ssh/pdh-team-01.pem` (0600), `Host pdh-team` in
  `~/.ssh/config`, host key pinned after the ED25519 fingerprint matched CONNECT.txt. Login works
  (head node `ip-172-31-26-233`, git 2.40, python 3.9, aws + slurm present, GitHub reachable from there).
- **`/mnt/work/kemp_example` did not exist yet** — `bash /mnt/ref/hackathon/setup.sh` still has to be run
  once for the team, then poll `status.sh` until `VERIFIED`.
- Onboarding: `SETUP.md` (zero-to-running in ~20 min, no prior Claude/cluster experience assumed),
  `wiki/team.md` with handles and a suggested division of labour.
- Agent-neutral setup: `AGENTS.md` is canonical, with `CLAUDE.md`, `GEMINI.md`,
  `.github/copilot-instructions.md` and `.cursor/rules/` pointing at it; new playbooks `/cluster` and `/submit`.
- Submission safety net: `kemp.submission` + `scripts/90_build_submission.py` + `make submission` enforce
  every documented rule offline (14 tests), because a wrong 1-based `base=`/`oxy=` index is scored
  silently wrong rather than rejected. `*.pem` and credentials added to `.gitignore`.
- Open: branch protection on `main` still needs `gh auth login` (or the GitHub web UI) — see the
  one-time settings in `CONTRIBUTING.md`. Deadline still unknown; ask an organiser.
