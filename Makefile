# Each target is a thin wrapper around uv. No make? Run the indented line(s) by hand.
.PHONY: setup status smoke test lint fmt index check lock reproduce

setup:  # exact env from uv.lock + git hooks + better merge defaults (repo-local git config)
	uv sync --locked
	uv run --frozen pre-commit install
	git config rerere.enabled true
	git config merge.conflictstyle diff3

status:  # where are we? experiments table + recent log entries
	uv run --frozen python tools/status.py

smoke:  # end-to-end check of env + run bookkeeping -> runs/<timestamp>_smoke/
	uv run --frozen python scripts/00_smoke.py

test:
	uv run --frozen pytest

lint:  # all pre-commit hooks on all files (incl. ruff and the INDEX check)
	uv run --frozen pre-commit run --all-files

fmt:  # auto-format and auto-fix
	uv run --frozen ruff format . && uv run --frozen ruff check --fix .

index:  # INDEX.md covers every file; no dead links, duplicates or bad names
	uv run --frozen python tools/check_index.py

check: lint test  # run before every push; CI runs the same

lock:  # after editing deps in pyproject.toml by hand or after a merge conflict (prefer `uv add <pkg>`)
	uv lock

reproduce:  # FULL pipeline from a fresh clone -> results/. Add every pipeline stage here, in order.
	uv run --frozen python scripts/00_smoke.py
