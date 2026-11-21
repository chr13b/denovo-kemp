# INDEX

The map of this repo, one line per file or directory: `path — what it is`.
**If you add, move or delete a file, update this file in the same commit.** `make index` enforces it:
it catches dead links, files that aren't listed, and duplicates.
This file is union-merged across branches, so append your line in the right section and don't reorder.
Files in `wiki/ raw/ src/ scripts/ tools/ results/ .claude/skills/` each need their own line
(or a subdirectory line). Elsewhere, a line for the directory is enough.

## Start here
- [onboard.sh](onboard.sh) — **one command that sets everything up.** `bash onboard.sh` — env, hooks, handle, key, cluster, checks
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
- [wiki/experiments/chris-02_seed-sweep-boltz-vs-rfd3-geometry.md](wiki/experiments/chris-02_seed-sweep-boltz-vs-rfd3-geometry.md) — seed sweep (jobs 2–5): is that drift systematic? decides where GPU time goes
- [wiki/experiments/zonghu-01_trp-stack-theozyme-vs-crystal.md](wiki/experiments/zonghu-01_trp-stack-theozyme-vs-crystal.md) — idealised Trp44 π-stack vs the crystal edge-on contact: does a custom theozyme scaffold?
- [wiki/experiments/zonghu-02_affinity-ladder-controls.md](wiki/experiments/zonghu-02_affinity-ladder-controls.md) — does the affinity ladder separate a real Kemp eliminase from a non-enzyme? (controls first)
- [wiki/affinity-ladder.md](wiki/affinity-ladder.md) — cofold substrate/TS-analogue/product and score transition-state discrimination; method, units and limits
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
- [raw/20261121_organizers_challenge-slides.pdf](raw/20261121_organizers_challenge-slides.pdf) — kickoff slides: chemistry, the 4 scoring terms, limitations (**image-only, no text layer**)

## Code
- [src/kemp/paths.py](src/kemp/paths.py) — every project path, defined once (data/runs can be overridden by env var)
- [src/kemp/config.py](src/kemp/config.py) — `parse(Config)`: dataclass config with JSON/TOML file and `--key=value` overrides
- [src/kemp/run.py](src/kemp/run.py) — `start_run()`: run directory plus provenance (config, commit, diff, script, lock hash, host, GPU, seed)
- [src/kemp/data.py](src/kemp/data.py) — `fetch(url, dest, checksum)` and `sha256(path)` for reproducible data
- [src/kemp/submission.py](src/kemp/submission.py) — `designs.fasta` building and offline rule checking (indices, residue types, limits)
- [src/kemp/ligands.py](src/kemp/ligands.py) — the Kemp ladder (substrate / TS analogue / product) and the log10(IC50) → kcal/mol conversion
- [scripts/00_smoke.py](scripts/00_smoke.py) — smoke test for env and run bookkeeping; **template for new scripts**
- [scripts/30_compare_rfd3_vs_boltz.py](scripts/30_compare_rfd3_vs_boltz.py) — chris-02 table: RFD3 vs Boltz-2 contact drift + the pre-registered decision rule
- [scripts/20_build_affinity_ladder.py](scripts/20_build_affinity_ladder.py) — build the cluster bundle that cofolds a sequence with all three ligands and predicts affinity
- [scripts/21_report_affinity_ladder.py](scripts/21_report_affinity_ladder.py) — parse the returned affinity JSONs → ddG(substrate/product − TS analogue) with a noise check
- [scripts/22_build_hg_series.py](scripts/22_build_hg_series.py) — build HG3/HG3.7/HG3.17 sequences from published mutation lists, asserting every wild-type residue
- [scripts/23_compare_ladder_to_kinetics.py](scripts/23_compare_ladder_to_kinetics.py) — predicted ladder vs measured k_cat/K_M: expected vs observed ddG, rank order, sign
- [scripts/24_build_anchored_ladder.py](scripts/24_build_anchored_ladder.py) — two-stage ladder: cofold once with the TS analogue, then score every ligand in that same pocket
- [scripts/make_stage_b.py](scripts/make_stage_b.py) — cluster-side helper for the above: reads the stage-A complex, finds the pocket residues, writes the anchored stage-B inputs
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
- [results/affinity/hg3_k50q_7k4u_chainA.fasta](results/affinity/hg3_k50q_7k4u_chainA.fasta) — zonghu-02 positive control: HG3 K50Q sequence from 7K4U chain A, 305 aa, W44/Q50/D127 verified
- [results/affinity/lysozyme_P00698.fasta](results/affinity/lysozyme_P00698.fasta) — zonghu-02 negative control: chicken lysozyme C, 147 aa, not a Kemp eliminase
- [results/affinity/hg3.fasta](results/affinity/hg3.fasta) — zonghu-02 validation arm: HG3, measured k_cat/K_M 160 M-1 s-1
- [results/affinity/hg3_7.fasta](results/affinity/hg3_7.fasta) — zonghu-02 validation arm: HG3.7, 7 mutations, k_cat/K_M 28 000 M-1 s-1
- [results/affinity/hg3_17.fasta](results/affinity/hg3_17.fasta) — zonghu-02 validation arm: HG3.17, 17 mutations, k_cat/K_M 170 000 M-1 s-1
- [results/affinity/hg_series_kinetics.json](results/affinity/hg_series_kinetics.json) — the published HG-series kinetics (Broom et al. Table 1) with mutation lists and assay conditions
- [results/affinity/zonghu-02_ladder_vs_kinetics.md](results/affinity/zonghu-02_ladder_vs_kinetics.md) — zonghu-02 verdict table: predicted TS affinity is flat across a 1062-fold activity range
- [results/affinity/zonghu-02_ladder_vs_kinetics_summary.json](results/affinity/zonghu-02_ladder_vs_kinetics_summary.json) — the same comparison as machine-readable numbers
- [results/affinity/runs/](results/affinity/runs/) — the 27 returned Boltz-2 affinity JSONs (9 per HG variant), the raw evidence for zonghu-02
- [results/affinity/zonghu01_kemp7_design.fasta](results/affinity/zonghu01_kemp7_design.fasta) — zonghu-02 test case: the zonghu-01 job-7 LigandMPNN design, 260 aa
- [results/theozyme/theozyme_7k4u_core.pdb](results/theozyme/theozyme_7k4u_core.pdb) — zonghu-01 input: HG3 K50Q motif from 7K4U (TRP44+GLN50+ASP127+6NT), crystal geometry
- [results/theozyme/theozyme_7k4u_core_trpopt.pdb](results/theozyme/theozyme_7k4u_core_trpopt.pdb) — zonghu-01 input: same motif, TRP44 repositioned to an idealised π-stack; base/donor/ligand unchanged
- [results/theozyme/theozyme_7k4u_core_trpopt2.pdb](results/theozyme/theozyme_7k4u_core_trpopt2.pdb) — zonghu-01 repaired input: idealised π-stack with crystal-calibrated clearance for the TRP44 attachment end
- [results/reference_kemp-1_summary.json](results/reference_kemp-1_summary.json) — verified reference run (cluster job 1); the baseline we must beat
- [results/zonghu-01_trpopt_kemp-7_summary.json](results/zonghu-01_trpopt_kemp-7_summary.json) — zonghu-01 job 7: custom theozyme runs end-to-end, but Boltz-2 put the ligand 12 Å from the base; not a candidate
- [results/zonghu-01_trpopt_kemp-7_validation-warnings.jsonl](results/zonghu-01_trpopt_kemp-7_validation-warnings.jsonl) — zonghu-01 job 7: the 2 expected launcher warnings from the extended motif
- [results/sweep_kemp-2_summary.json](results/sweep_kemp-2_summary.json) — chris-02 seed 2: collapsed refold (CA RMSD 14.6 Å)
- [results/sweep_kemp-3_summary.json](results/sweep_kemp-3_summary.json) — chris-02 seed 3: folded, base contact drifted to 8.33 Å
- [results/sweep_kemp-4_summary.json](results/sweep_kemp-4_summary.json) — chris-02 seed 4: **best design so far**, beats the baseline; novelty unchecked
- [results/sweep_kemp-5_summary.json](results/sweep_kemp-5_summary.json) — chris-02 seed 5: collapsed refold (CA RMSD 13.7 Å)
- [notebooks/](notebooks/) — exploration only, one folder per person (`notebooks/<handle>/`); outputs stripped on commit
