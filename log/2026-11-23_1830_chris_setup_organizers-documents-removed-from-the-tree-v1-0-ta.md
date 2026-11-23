# [2026-11-23 18:30] setup | Organizers' documents removed from the tree; v1.0 tag (chris)

- Deleted the five organizers' documents from `raw/` (start-here note, cluster guide in Markdown and HTML, submission rules, connection file). `raw/` now holds only `README.md`; `.gitignore` excludes anything else placed there. Links into `raw/` in `wiki/`, `src/kemp/submission.py`, `onboard.sh`, `README.md` and `INDEX.md` became plain statements that the source is not included. No test or script read those files.
- The files remain in older commits of the git history; purging them needs a history rewrite, which the owner has declined. Recorded in `wiki/decisions.md`.
- Tagged the final state `v1.0` after CI passed on it.
