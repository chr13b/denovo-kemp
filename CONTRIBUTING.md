# Contributing: branches, merging, reproducibility

Everyone starts out on their own branch. These rules make the later merges boring.

## 1. Pick a handle (once)

Choose a short lowercase handle (e.g. `chris`) and add it to [wiki/team.md](wiki/team.md).
Put `KEMP_HANDLE=<handle>` in your `.env`, or rely on the first word of `git config user.name`.
The handle goes into every name below, so parallel work can't collide.

| Thing | Pattern | Create with |
|-------|---------|-------------|
| Branch | `<handle>/<topic>` | `git switch -c chris/scoring` |
| Experiment | `wiki/experiments/<handle>-NN_<slug>.md` | `python tools/new.py exp baseline-scoring` |
| Config | `configs/<handle>-NN.json` | by hand |
| Run dir | `runs/<timestamp>_<handle>-NN/` | `start_run("<handle>-NN", cfg)` |
| Log entry | `log/YYYY-MM-DD_HHMM_<handle>_<type>_<slug>.md` | `python tools/new.py log experiment "chris-01 baseline"` |
| Notebook | `notebooks/<handle>/YYYYMMDD_<topic>.ipynb` | by hand |
| New script | `scripts/NN_<specific_verb_noun>.py` (`10_generate_candidates.py`, not `10_generate.py`) | copy `scripts/00_smoke.py` |

**No global counters.** "E-007, the next free number" collides as soon as two branches take it at the same time.

## 2. Why merges stay painless

| Hotspot | How it's defused |
|---------|------------------|
| Log | One file per entry in `log/`, so there is nothing to merge |
| Experiment registry | One page per experiment; the table is computed by `make status` |
| `INDEX.md`, `wiki/decisions.md`, `wiki/glossary.md`, `wiki/data.md` | `merge=union` in `.gitattributes`: git keeps both sides' lines. `make index` flags duplicates |
| `uv.lock` | Never text-merged. Regenerate it with `uv lock` |
| Notebooks | One folder per person; outputs stripped on commit (nbstripout hook) |
| Whitespace and line endings | `.editorconfig` + `.gitattributes` (LF) + whitespace hooks |
| Leftover `<<<<<<<` markers, big files, keys | pre-commit hooks locally, and CI on every push |

The rule behind all of it: **edit your own files, append to shared lists, and never rewrite other people's entries.**
To correct someone else's log entry or experiment page, add your own entry that references it.

## 3. Daily loop

```bash
git switch main && git pull                  # start of day
git switch -c chris/topic                    # or: git switch chris/topic && git merge main
# ... work; commit small and often (hooks run automatically) ...
git fetch origin && git merge origin/main    # at least every 2–3 h, and ALWAYS before a PR
make check
git push -u origin HEAD                      # then open a PR on GitHub
```

## 4. Merging into main (the important part)

1. **Merge main into your branch locally first:** `git fetch origin && git merge origin/main`.
   The union merges and `rerere` only run locally. GitHub's web conflict editor doesn't apply them.
2. Resolve whatever is left:
   - **`pyproject.toml`**: keep both sides' dependencies, then run `uv lock` and `git add pyproject.toml uv.lock`
   - **`uv.lock` only**: run `uv lock` and `git add uv.lock`. Never hand-edit it.
   - **`INDEX.md` and the union files**: already merged. Run `make index` to catch duplicates and dead links.
   - **Code**: resolve as usual, then run `make check`. If unsure, ask the file's owner (see `wiki/team.md`).
3. Commit the merge, push, and wait for CI to go green. The PR run tests the merge result.
4. On GitHub, merge with **"Create a merge commit"**, not squash or rebase. With a merge commit your branch
   keeps working after the merge, and the next `git merge origin/main` stays clean. (After a squash merge,
   start a fresh branch from `main` instead.)
5. If you resolved something non-trivial, add a log entry: `python tools/new.py log merge "<what>"`.

**Never:** force-push `main`, push to someone else's branch without asking, rebase a branch others have
pulled, or commit with `--no-verify` to skip the hooks.

## 5. Reproducibility checklist

- **Environment:** `uv.lock` and `.python-version` are committed. CI installs with `uv sync --locked`.
  Pin external tools that need their own environment in `envs/<tool>.yml` or `envs/<tool>.Dockerfile`, and
  name that file in the docstring of the wrapping script.
- **Code:** commit before running. Each run dir records the commit, branch, `git_diff.patch` (if dirty),
  a script snapshot, config, seed, uv.lock hash, host and GPUs.
- **Data:** fetch with `kemp.data.fetch(url, dest, checksum=...)` and register the data in `wiki/data.md`.
- **Claims:** quote only numbers read from a run's `summary.json` or `metrics.jsonl`, and link the experiment page.
- **Final:** `make reproduce` on a fresh clone must rebuild the submission. Tag what you submit:
  `git tag -a submission-v1 -m "…" && git push origin submission-v1`.

## 6. Protecting `main`

**Already active for everyone, no setup needed:** after `make setup`, a git hook refuses a direct
*commit* on `main` and tells you to use a branch. Merges are allowed, so integrating a finished branch
still works. This is the protection that matters day to day, and it costs nothing.

**Additionally, on GitHub (repo owner, optional):** require a pull request and a green CI run before
anything lands on `main`.

**With the GitHub CLI** (`gh auth login` once, then copy-paste):

```bash
gh api -X PUT repos/chr13b/kemp-challenge/branches/main/protection \
  -H "Accept: application/vnd.github+json" \
  -F required_status_checks[strict]=true \
  -F 'required_status_checks[contexts][]=check' \
  -F enforce_admins=false \
  -F required_pull_request_reviews[required_approving_review_count]=0 \
  -F restrictions=null \
  -F allow_force_pushes=false \
  -F allow_deletions=false
```

**Or in the browser:** Settings → Branches → *Add branch ruleset* / *Add rule* for `main` →
tick "Require a pull request before merging" (0 approvals is fine for a hackathon),
"Require status checks to pass" → select `check`, and leave force pushes blocked.

Also under Settings → General → Pull Requests: allow **merge commits**. If people keep long-lived
personal branches, leave "Automatically delete head branches" **off**.

> On a **private** repo, branch protection needs a paid plan (Pro/Team). If GitHub refuses, it is not
> worth paying for during a hackathon: CI still runs on every push and PR, and the team rule
> "never commit to `main` directly, always open a PR" does the rest.
