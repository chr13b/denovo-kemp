# CLAUDE.md: Kemp Challenge (hackathon)

This file is the **schema** for the repo. It says how the repo is organized and how Claude and humans
work in it. Keep it short. Details belong in the files it points to.

@INDEX.md

## Session start

1. INDEX.md (imported above) is the map. Trust it, and keep it true.
2. Run `grep "^## \[" LOG.md | tail -10` to see what happened recently. Open full entries only if relevant.
3. Read `wiki/challenge.md` before making any scientific or design decision.

## Three layers (after Karpathy's "LLM Wiki")

| Layer | Where | Written by | Rule |
|-------|-------|------------|------|
| Sources | `raw/` | humans | **Immutable.** Add files, never edit or delete them. Name them `YYYYMMDD_short-slug.ext`. |
| Knowledge | `wiki/`, `INDEX.md`, `LOG.md` | mostly Claude | Distilled, cross-linked, current. Every claim links to a raw source or a run. |
| Code + artifacts | `src/ scripts/ configs/ tests/ tools/` → `runs/` → `results/` | everyone | Anything in `results/` can be reproduced from git + config. |

## Workflows

- **Ingest** (new brief, paper, or organizer note): save it to `raw/`, then update or create wiki pages, then INDEX, then LOG. Use `/ingest`.
- **Experiment**: write the question in `wiki/experiments.md` *before* running. Then script → run → record the result and verdict → LOG. Use `/experiment`.
- **Query**: look in INDEX → wiki → raw/code. If the answer is reusable, write it into the wiki instead of leaving it in chat.
- **Lint** (before every push): run `make check`, then fix dead links, orphan files and stale claims. Use `/lint`.

## Definition of done (every task)

- [ ] The code runs and `make check` passes
- [ ] INDEX.md has a one-line entry for each new file, and entries for moved or deleted files are gone
- [ ] LOG.md has a new entry (append at the bottom; write paths as `code`, not links, because the log is never edited)
- [ ] Findings and decisions are in `wiki/`, not only in chat

## Code style: nano-style (in the spirit of nanoGPT / nanochat)

- Choose flat and readable over clever and abstract. One file holds one idea, and a script reads top to bottom.
- Add no framework, base class or registry until the third time it's needed. Copy-paste twice before abstracting.
- Keep dependencies few. Add them to `pyproject.toml` and note the reason in LOG.
- Name scripts `scripts/NN_verb_noun.py`, where NN is the pipeline stage: `0x` setup/data, `1x` generate,
  `2x` score/filter, `3x` analyze, `9x` submit. Each script has a docstring with a usage line, a `Config`
  dataclass parsed by `kemp.config.parse`, and calls `kemp.run.start_run`. Template: `scripts/00_smoke.py`.
- Move logic into `src/kemp/` only once **two** scripts need it.
- Get paths only from `kemp.paths`. Never hardcode absolute paths.
- Set seeds explicitly. Every run writes `runs/<timestamp>_<name>/` with `config.json` and `meta.json`
  (git commit + dirty flag). **Never report a number you didn't read from a run's files.**
- Notebooks are for exploration only: `notebooks/YYYYMMDD_<initials>_<topic>.ipynb`. Nothing imports from them.
  Clear outputs before committing, and move code worth keeping into `scripts/` or `src/`.

## Data and artifacts

- `data/` (gitignored) holds bulk inputs. They must be reproducible by a `scripts/0x_fetch_*.py` script or documented in the wiki.
- `runs/` (gitignored) holds the output of every execution and is disposable. The registry lives in `wiki/experiments.md`.
- `results/` (tracked) holds curated outputs worth keeping: figures, tables, the final submission. Keep files small
  (under ~10 MB). Each INDEX entry names its source run.
- Heavy external tools with their own environment get a wrapper script whose docstring records the exact env or container.

## Git (team of new collaborators)

- `main` always passes `make check`, and CI enforces it. Work on `<name>/<topic>` branches, keep PRs small, merge when green.
- Commit messages: `type: summary`, where type is one of `feat fix exp data docs chore`.
- Never commit `.env`, secrets, large binaries or `runs/`.
- Pull before starting. On a LOG.md merge conflict, keep both entries in time order.

## Commands

`make setup` (uv sync) · `make smoke` · `make test` · `make lint` · `make fmt` · `make index` · `make check` (all checks)
Without make, each target in the Makefile is a single `uv run ...` line you can run directly.

## Don't

- Edit or delete anything in `raw/`
- Leave files out of INDEX.md
- Keep knowledge only in chat
- Add dependencies or abstractions casually
- Hardcode paths
- Claim a result without a run directory behind it
