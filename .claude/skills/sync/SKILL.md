---
name: sync
description: Bring the current personal branch up to date with main and resolve merge conflicts safely, per CONTRIBUTING.md. Use every 2–3 hours, before opening or merging a PR, when the user says "merge", "update my branch", "pull main", or when git reports conflicts.
---

# Sync the branch with main

1. Run `git status -sb`. If the working tree is dirty, commit the work first; don't stash it silently.
   If you are on `main`, run `git pull` and stop.
2. Run `git fetch origin && git merge origin/main`. Use a merge, not a rebase: pushed personal branches must not be rewritten.
3. If git reports conflicts, resolve them by type:
   - `log/*`, `wiki/experiments/*`: these shouldn't conflict (one file per entry). If they do, two people used the
     same name. Keep both files and rename yours with `tools/new.py`.
   - `INDEX.md`, `wiki/decisions.md`, `wiki/glossary.md`, `wiki/data.md`: union-merged, usually automatic. If not,
     keep both sides' lines.
   - `pyproject.toml`: keep both sides' dependencies, then run `uv lock`.
   - `uv.lock`: never edit it. Run `uv lock` after `pyproject.toml` is resolved, then `git add uv.lock`.
   - Code: understand both sides before choosing, and keep both behaviours if they're independent.
     If the intent is unclear, ask the user, or the owner listed in `wiki/team.md`. Never just take "ours" to make it go away.
4. Run `uv sync --locked`, then `make check`. Fix duplicates and dead links that `check_index` reports.
5. Commit the merge. Then run `python tools/new.py log merge "<what was resolved>"` if anything was non-trivial.
6. Push only if the user asked: `git push`. Report what came in from main (`git log --oneline HEAD@{1}..HEAD`)
   and what you resolved.
