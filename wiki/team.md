# Team

Add **your own row** (don't edit other people's). Your handle is a short lowercase nickname; it goes into
your branch names, experiment IDs and log entries. Setup: [../SETUP.md](../SETUP.md).
"Owns" = who reviews and decides, not the only person allowed to touch it.

| Handle | GitHub | Background / strengths | Owns | Current branch |
|--------|--------|------------------------|------|----------------|
| chris | chr13b | — | repo, cluster access | main |
| TODO | | | | |

## Working agreements

- Every ~2–3 h: `make sync`, write a log entry (`uv run python tools/new.py log …`), then a 10-minute
  stand-up around `make status`.
- Merge into `main` early and often: small pull requests, merge commits, CI green.
- Add an experiment page *before* running (`uv run python tools/new.py exp …`) so nobody duplicates work.
- Decisions with lasting impact go in [decisions.md](decisions.md).
- Cluster etiquette: 2 GPU workers for the whole team, so say in the chat when you start a long job.
  Name your project folders `<handle>_<topic>` and never touch `/mnt/work/kemp_example`.

## Division of labour (suggestion for the first hours)

Discuss and overwrite. The point is that nobody waits on anybody.

| Track | What | Why it is independent |
|---|---|---|
| Pipeline | get the example verified, then run the first own design end to end | needs the cluster, not our analysis code |
| Scoring | reimplement the published scoring terms (contact distances, angles, in-plane) as a local filter | pure geometry on predicted structures |
| Novelty | TM-score and sequence-identity checks against published structures | gate every candidate before it takes a submission slot |
| Strategy | read the scoring section closely, decide what to optimize, keep `wiki/pitch.md` current | reading and writing, no compute |
