# CLAUDE.md: Kemp Challenge (hackathon)

This file is the **schema** for the repo. It says how the repo is organized and how Claude and humans
work in it. Keep it short. Details belong in the files it points to.

@INDEX.md

## Session start

1. INDEX.md (imported above) is the map. Trust it, and keep it true.
2. Run `python tools/status.py` for the experiments table and the last 10 log entries.
   Also run `git status -sb` to see which branch you're on and whether it's behind.
3. Read `wiki/challenge.md` before making any scientific or design decision.

## Three layers (after Karpathy's "LLM Wiki")

| Layer | Where | Written by | Rule |
|-------|-------|------------|------|
| Sources | `raw/` | humans | **Immutable.** Add files, never edit or delete them. Name them `YYYYMMDD_short-slug.ext`. |
| Knowledge | `wiki/`, `INDEX.md`, `log/` | mostly Claude | Distilled, cross-linked, current. Every claim links to a raw source or an experiment. |
| Code + artifacts | `src/ scripts/ configs/ envs/ tests/ tools/` → `runs/` → `results/` | everyone | Anything in `results/` can be reproduced from git + config. |

## Workflows

- **Ingest** (new brief, paper, or organizer note): save it to `raw/`, then update wiki pages, then INDEX, then a log entry. Use `/ingest`.
- **Experiment**: run `python tools/new.py exp <slug>` *before* running. Then script → run → record the result and verdict on that page. Use `/experiment`.
- **Query**: look in INDEX → wiki → raw/code. If the answer is reusable, write it into the wiki instead of leaving it in chat.
- **Lint** (before every push): run `make check`, then fix dead links, orphans, duplicates and stale claims. Use `/lint`.
- **Sync** (every 2–3 h and before every PR): merge `origin/main` into the branch and resolve conflicts per CONTRIBUTING.md. Use `/sync`.

## Parallel branches: merge-safe rules

Everyone works on their own `<handle>/<topic>` branch. The full playbook is in `CONTRIBUTING.md`.

- **Per-person names, no global counters.** Experiments are `<handle>-NN`, and so are their configs and run names.
  Log entries are one file each. Create both with `tools/new.py`.
- **Edit your own files, append to shared lists.** INDEX, decisions, glossary and data are union-merged lists: add lines and don't reorder.
  Never rewrite other people's log entries, experiment pages or notebooks. Add your own entry instead.
- **Lockfile:** never hand-edit or hand-merge `uv.lock`. Use `uv add <pkg>`, and run `uv lock` after a conflict.
- Don't move or rename shared files (`src/kemp/*`, `wiki/*`) on a personal branch without telling the team. Renames conflict badly.

## Definition of done (every task)

- [ ] The code runs and `make check` passes (hooks: ruff, conflict markers, large files, INDEX lint)
- [ ] INDEX.md has a one-line entry for each new file, and entries for moved or deleted files are gone
- [ ] There is a log entry: `python tools/new.py log <type> "<title>"`, then fill in 1–5 bullets. Write paths as `code`.
- [ ] Findings and decisions are in `wiki/`, not only in chat

## Code style: nano-style (in the spirit of nanoGPT / nanochat)

- Choose flat and readable over clever and abstract. One file holds one idea, and a script reads top to bottom.
- Add no framework, base class or registry until the third time it's needed. Copy-paste twice before abstracting.
- Keep dependencies few. Add them with `uv add` and give the reason in the log entry.
- Name scripts `scripts/NN_specific_verb_noun.py`, where NN is the pipeline stage: `0x` setup/data, `1x` generate,
  `2x` score/filter, `3x` analyze, `9x` submit. Each script has a docstring with a usage line, a `Config`
  dataclass parsed by `kemp.config.parse`, and calls `kemp.run.start_run`. Template: `scripts/00_smoke.py`.
  Add every final pipeline stage to `make reproduce`.
- Move logic into `src/kemp/` only once **two** scripts need it.
- Get paths only from `kemp.paths`. Never hardcode absolute paths.
- Fetch data with `kemp.data.fetch(..., checksum=...)` and register it in `wiki/data.md`.
- Set seeds explicitly. Commit before running. **Never report a number you didn't read from a run's files.**
- Notebooks are for exploration only: `notebooks/<handle>/YYYYMMDD_<topic>.ipynb`. Nothing imports from them,
  and outputs are stripped on commit.

## Data and artifacts

- `data/` (gitignored) holds bulk inputs, reproducible through `kemp.data.fetch` or documented in `wiki/data.md`.
- `runs/` (gitignored) holds the output of every execution, with config, meta, diff patch and script snapshot. It is disposable.
- `results/` (tracked) holds curated outputs (figures, tables, submission). Files over 10 MB are blocked by a hook.
- `envs/` holds pinned environments for external tools (conda yml or Dockerfile). The wrapper script names its env.

## Commands

`make setup` · `make status` · `make smoke` · `make test` · `make lint` · `make fmt` · `make index` · `make check` · `make lock` · `make reproduce`
Without make, each target is one or more `uv run ...` lines in the Makefile.

## Don't

- Edit `raw/`, or rewrite others' log entries or experiment pages
- Hand-merge `uv.lock`
- Leave files out of INDEX.md
- Keep knowledge only in chat
- Hardcode paths
- Claim a result without a run directory behind it
- Force-push `main`, or bypass the hooks with `--no-verify`
