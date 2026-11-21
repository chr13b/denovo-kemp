---
name: lint
description: Health-check the repo's knowledge layer (INDEX.md, log/, wiki/, experiment pages) and fix drift. Use before pushing, after a burst of changes, after merging teammates' work, or when the user asks to tidy up or get an overview.
---

# Lint the knowledge layer

1. Run `python tools/check_index.py`. Fix every problem it reports:
   - dead link: fix or remove it
   - orphan: add a one-line entry
   - duplicate: union-merge leftover, keep the better line
   - bad name: recreate the file with `tools/new.py`
2. Run `python tools/status.py -n 20` to see what changed recently.
   After a merge, teammates may have added files or results without updating the wiki.
3. Check the wiki pages those changes touch:
   - claims superseded by newer runs
   - contradictions between pages
   - missing cross-links
   - TODOs that are now answerable
   - after a union merge, two versions of the same glossary or decision line

   Fix them, or mark them `> **Conflict:**` or _(unconfirmed)_. Don't rewrite other people's entries; add your own.
4. Experiment pages stuck in `planned` or `running` whose run dir exists: update them from the run files,
   if they're yours, or tell their owner.
5. Check that `INDEX.md` one-liners still describe what each file actually does.
6. Run `make check` (hooks + tests).
7. Run `python tools/new.py log lint "<one-line summary of fixes>"`.
