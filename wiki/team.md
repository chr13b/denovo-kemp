# Team

Fill this in at kickoff. "Owns" means the person who reviews and decides, not the only person allowed to touch it.
The handle goes into branch names, experiment IDs and log entries (see [CONTRIBUTING.md](../CONTRIBUTING.md)).
One row per person; add only your own row.

| Handle | GitHub | Background / strengths | Owns | Current branch |
|--------|--------|------------------------|------|----------------|
| TODO | | | | |

## Working agreements
- Every ~2–3 h: merge `origin/main` into your branch, write a log entry (`python tools/new.py log …`),
  then do a 10-minute sync around `make status`.
- Merge into `main` early and often. Small PRs, merge commits, CI green.
- Add an experiment page *before* running (`python tools/new.py exp …`), so nobody does the same work twice.
- Decisions with lasting impact go in [decisions.md](decisions.md).
