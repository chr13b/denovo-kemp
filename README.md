# kemp-challenge

Our hackathon repo.

- **What we're solving:** [wiki/challenge.md](wiki/challenge.md)
- **Where everything is:** [INDEX.md](INDEX.md), the map of every file
- **Where we are:** run `make status` (experiments table and recent log entries)
- **How we work together:** [CONTRIBUTING.md](CONTRIBUTING.md) (branches, merging, reproducibility)

## Quickstart

Requires git and [uv](https://docs.astral.sh/uv/getting-started/installation/). uv installs the right Python itself.

```bash
git clone git@github.com:chr13b/kemp-challenge.git
cd kemp-challenge
make setup   # exact env from uv.lock + git hooks + merge helpers
make smoke   # creates runs/<timestamp>_smoke/, which proves the setup works
make check   # all hooks + tests; must pass before you push (CI runs the same)
```

No `make` (plain Windows)? Every Makefile target is one or more `uv run …` lines, so copy them from the [Makefile](Makefile).
Then pick a handle, add it to [wiki/team.md](wiki/team.md), and branch: `git switch -c <handle>/<topic>`.

## How the repo is organized

There are three layers, after Andrej Karpathy's "LLM Wiki" pattern:

| Layer | Where | What |
|-------|-------|------|
| Sources | `raw/` | Challenge brief, papers, organizer notes. **Never edited.** |
| Knowledge | `wiki/` + `INDEX.md` + `log/` | Distilled understanding, decisions and one page per experiment, kept current (mostly by Claude). |
| Code + artifacts | `src/`, `scripts/`, `configs/`, `envs/` → `runs/` → `results/` | Reproducible code. Every run records its config, commit, diff and environment. |

The code is **nano-style** (think nanoGPT): flat, readable scripts, no premature abstraction, few dependencies.
Scripts are numbered by pipeline stage (`scripts/NN_verb_noun.py`). Copy `scripts/00_smoke.py` to start a new one.

## Working with Claude Code

`CLAUDE.md` loads automatically and imports `INDEX.md`, so Claude starts every session with the full map.
Project skills:

- `/ingest`: turn a source into wiki knowledge
- `/experiment`: run an experiment reproducibly and record the verdict
- `/lint`: fix drift between the repo, the index and the wiki
- `/sync`: merge `main` into your branch and resolve conflicts the safe way
