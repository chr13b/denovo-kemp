# INDEX

The map of this repo, one line per file or directory: `path — what it is`.
**If you add, move or delete a file, update this file in the same commit.** `make index` enforces it:
it catches dead links, files that aren't listed, and duplicates.
This file is union-merged across branches, so append your line in the right section and don't reorder.
Files in `wiki/ raw/ src/ scripts/ tools/ results/ .claude/skills/` each need their own line
(or a subdirectory line). Elsewhere, a line for the directory is enough.

## Start here
- [SETUP.md](SETUP.md) — **new teammate? start here.** Laptop setup, cluster access, daily rhythm, cheat sheet
- [README.md](README.md) — what this project is, in one page
- `wiki/challenge.md` — the task, hard rules, scoring and submission checklist (linked under Knowledge below)
- [CONTRIBUTING.md](CONTRIBUTING.md) — branch and merge playbook, naming scheme, reproducibility checklist

## Meta
- [CLAUDE.md](CLAUDE.md) — schema for Claude Code: rules, conventions and workflows (loads automatically)
- [AGENTS.md](AGENTS.md) — the same brief, tool-neutral, for **any** AI assistant
- [GEMINI.md](GEMINI.md) — pointer to AGENTS.md for Gemini
- [.cursor/rules/kemp-challenge.mdc](.cursor/rules/kemp-challenge.mdc) — pointer to AGENTS.md for Cursor
- [log/](log/) — the log: one file per entry, `YYYY-MM-DD_HHMM_<handle>_<type>_<slug>.md`; `make status` shows the latest
- [pyproject.toml](pyproject.toml) — package `kemp`, dependencies (add with `uv add`), ruff and pytest config
- [uv.lock](uv.lock) — exact pinned versions of every dependency; never hand-edit or hand-merge it (`uv lock`)
- [.python-version](.python-version) — Python version uv installs and uses
- [Makefile](Makefile) — `setup status smoke test lint fmt index check sync submission lock reproduce`
- [.pre-commit-config.yaml](.pre-commit-config.yaml) — commit hooks: conflict markers, large files, keys, whitespace, ruff, nbstripout, index lint
- [.env.example](.env.example) — template for `.env` (gitignored): `KEMP_HANDLE`, data/runs locations, secrets
- [.gitattributes](.gitattributes) — LF line endings; `merge=union` for shared lists; `uv.lock` never text-merged
- [.gitignore](.gitignore) · [.editorconfig](.editorconfig) — ignore rules (incl. `*.pem`); same whitespace in every editor
- [.github/](.github/) — CI (hooks + pytest on every push and PR, `uv sync --locked`), PR checklist, Copilot pointer

## Playbooks (`/name` in Claude Code; plain Markdown any assistant can follow)
- [.claude/skills/cluster/SKILL.md](.claude/skills/cluster/SKILL.md) — `/cluster`: run a design job on the GPU cluster and bring results back
- [.claude/skills/experiment/SKILL.md](.claude/skills/experiment/SKILL.md) — `/experiment`: question → run → verdict, reproducibly
- [.claude/skills/submit/SKILL.md](.claude/skills/submit/SKILL.md) — `/submit`: build, check and upload `designs.fasta`
- [.claude/skills/ingest/SKILL.md](.claude/skills/ingest/SKILL.md) — `/ingest`: turn a raw source into wiki knowledge
- [.claude/skills/sync/SKILL.md](.claude/skills/sync/SKILL.md) — `/sync`: merge `origin/main` into the current branch and resolve conflicts safely
- [.claude/skills/lint/SKILL.md](.claude/skills/lint/SKILL.md) — `/lint`: health-check INDEX, log and wiki, then fix drift

## Knowledge: wiki/ (maintained mostly by Claude)
- [wiki/challenge.md](wiki/challenge.md) — the task, rules, scoring, timeline, submission checklist and open questions. **Start here.**
- [wiki/cluster.md](wiki/cluster.md) — cluster layout, connect, Slurm jobs, project folders, getting results back
- [wiki/submission.md](wiki/submission.md) — `designs.fasta` format, catalytic annotation, upload, deadline rules, status
- [wiki/experiments/](wiki/experiments/) — one page per experiment, `<handle>-NN_<slug>.md` (`tools/new.py exp`); table: `make status`
- [wiki/experiments/_template.md](wiki/experiments/_template.md) — template for experiment pages
- [wiki/experiments/chris-01_reference-pipeline-baseline.md](wiki/experiments/chris-01_reference-pipeline-baseline.md) — baseline: pipeline verified, RFD3 → Boltz-2 contact drift
- [wiki/data.md](wiki/data.md) — dataset registry: source, version, sha256, how to fetch
- [wiki/decisions.md](wiki/decisions.md) — decision records (append-only, dated): what we chose, why, alternatives
- [wiki/pitch.md](wiki/pitch.md) — the story for the final presentation, kept current
- [wiki/team.md](wiki/team.md) — handles, owners, branches, working agreements, division of labour
- [wiki/glossary.md](wiki/glossary.md) — domain and project terms

## Sources: raw/ (immutable, added by humans)
- [raw/20261121_organizers_start-here.md](raw/20261121_organizers_start-here.md) — organizers' one-page start (2 GPUs, novelty rule)
- [raw/20261121_organizers_cluster-guide.md](raw/20261121_organizers_cluster-guide.md) — the full cluster guide (authoritative)
- [raw/20261121_organizers_cluster-guide.html](raw/20261121_organizers_cluster-guide.html) — same guide as delivered (HTML)
- [raw/20261121_organizers_submission.md](raw/20261121_organizers_submission.md) — submission format, eligibility, scoring criteria
- [raw/20261121_organizers_connect-team01.txt](raw/20261121_organizers_connect-team01.txt) — our cluster address, fingerprint and S3 folder (**no key**)

## Code
- [src/kemp/paths.py](src/kemp/paths.py) — every project path, defined once (data/runs can be overridden by env var)
- [src/kemp/config.py](src/kemp/config.py) — `parse(Config)`: dataclass config with JSON/TOML file and `--key=value` overrides
- [src/kemp/run.py](src/kemp/run.py) — `start_run()`: run directory plus provenance (config, commit, diff, script, lock hash, host, GPU, seed)
- [src/kemp/data.py](src/kemp/data.py) — `fetch(url, dest, checksum)` and `sha256(path)` for reproducible data
- [src/kemp/submission.py](src/kemp/submission.py) — `designs.fasta` building and offline rule checking (indices, residue types, limits)
- [scripts/00_smoke.py](scripts/00_smoke.py) — smoke test for env and run bookkeeping; **template for new scripts**
- [scripts/90_build_submission.py](scripts/90_build_submission.py) — `results/designs.jsonl` → `results/designs.fasta` (`make submission`)
- [tools/check_index.py](tools/check_index.py) — lint: dead links, unindexed files, duplicate entries, bad log/experiment names
- [tools/new.py](tools/new.py) — create collision-free log entries and experiment pages (`log <type> "<title>"`, `exp <slug>`)
- [tools/status.py](tools/status.py) — overview: experiments table and recent log entries (`make status`)
- [configs/](configs/) — reusable run configs, `<handle>-NN.json`, referenced from experiment pages
- [envs/](envs/) — pinned environments for external tools with their own deps (`<tool>.yml` / `<tool>.Dockerfile`)
- [tests/](tests/) — pytest suite (config, runs, data, submission rules, cross-check vs the organizers' validator, tools, index)

## Artifacts
- [data/](data/) — bulk inputs, gitignored; registry in `wiki/data.md`
- [runs/](runs/) — one directory per execution, gitignored; linked from the experiment pages
- [results/](results/) — curated tracked outputs (figures, tables, the submission); each entry names its run
- [results/designs.jsonl.template](results/designs.jsonl.template) — copy to `results/designs.jsonl`: our submission candidates
- [results/reference_kemp-1_summary.json](results/reference_kemp-1_summary.json) — verified reference run (cluster job 1); the baseline we must beat
- [notebooks/](notebooks/) — exploration only, one folder per person (`notebooks/<handle>/`); outputs stripped on commit
