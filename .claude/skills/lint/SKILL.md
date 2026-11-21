---
name: lint
description: Health-check the repo's knowledge layer (INDEX.md, LOG.md, wiki/, experiments registry) and fix drift. Use before pushing, after a burst of changes, after merging teammates' work, or when the user asks to tidy up or get an overview.
---

# Lint the knowledge layer

1. Run `python tools/check_index.py`. Fix every dead link and orphan: add a one-line entry, or remove the stale one.
2. Read the LOG entries since the last `lint` entry to see what changed (`grep "^## \[" LOG.md | tail -20`).
   Teammates may have added files or results without updating the wiki.
3. Check the wiki pages those changes touch:
   - claims superseded by newer runs
   - contradictions between pages
   - missing cross-links
   - TODOs that are now answerable

   Fix them, or mark them `> **Conflict:**` or _(unconfirmed)_.
4. In `wiki/experiments.md`, look for rows stuck in `planned` or `running` whose run directory exists. Update them from the run files.
5. Check that `INDEX.md` one-liners still describe what each file actually does.
6. Run `make test` and `make lint`.
7. Append `## [YYYY-MM-DD] lint | <one-line summary of fixes>` to `LOG.md`.
