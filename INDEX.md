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
- [wiki/literature.md](wiki/literature.md) — annotated reading list; `tools/fetch_papers.sh` downloads the open-access PDFs
- [wiki/primer.md](wiki/primer.md) — **the project explained from scratch**: chemistry, pipeline, what we measured, and the 3 strategies we commit to (§7)
- [wiki/cluster.md](wiki/cluster.md) — cluster layout, connect, Slurm jobs, project folders, getting results back
- [wiki/submission.md](wiki/submission.md) — `designs.fasta` format, catalytic annotation, upload, deadline rules, status
- [wiki/experiments/](wiki/experiments/) — one page per experiment, `<handle>-NN_<slug>.md` (`tools/new.py exp`); table: `make status`
- [wiki/experiments/_template.md](wiki/experiments/_template.md) — template for experiment pages
- [wiki/experiments/chris-01_reference-pipeline-baseline.md](wiki/experiments/chris-01_reference-pipeline-baseline.md) — baseline: pipeline verified, RFD3 → Boltz-2 contact drift
- [wiki/experiments/chris-02_seed-sweep-boltz-vs-rfd3-geometry.md](wiki/experiments/chris-02_seed-sweep-boltz-vs-rfd3-geometry.md) — seed sweep (jobs 2–5): is that drift systematic? decides where GPU time goes
- [wiki/experiments/chris-03_msa-free-boltz-screen.md](wiki/experiments/chris-03_msa-free-boltz-screen.md) — **the MSA stage is a no-op**: bit-identical output without it, ~3–4× throughput
- [wiki/experiments/chris-04_sequence-oversampling-fixed-backbone.md](wiki/experiments/chris-04_sequence-oversampling-fixed-backbone.md) — **Idea A**: 72 sequences on one fixed backbone; is the base drift sequence-level or backbone-level?
- [wiki/experiments/chris-05_trp44-three-anchor-retested.md](wiki/experiments/chris-05_trp44-three-anchor-retested.md) — **Idea B**: zonghu's Trp44 theozyme, retested with 72 sequences instead of 1
- [wiki/experiments/chris-06_motif-library-kemp-family.md](wiki/experiments/chris-06_motif-library-kemp-family.md) — **Idea C**: four RFD3 motifs from the family's own crystal structures
- [wiki/experiments/chris-07_rescue-written-off-backbones.md](wiki/experiments/chris-07_rescue-written-off-backbones.md) — were seeds 2/3/5 ever bad, or did they just draw one bad sequence?
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
- [scripts/00_smoke.py](scripts/00_smoke.py) — smoke test for env and run bookkeeping; **template for new scripts**
- [scripts/30_compare_rfd3_vs_boltz.py](scripts/30_compare_rfd3_vs_boltz.py) — chris-02 table: RFD3 vs Boltz-2 contact drift + the pre-registered decision rule
- [scripts/31_measure_reference_geometry.py](scripts/31_measure_reference_geometry.py) — catalytic geometry targets measured from PDB 4BS0 (HG3.17 + 6NT)
- [scripts/32_kemp_family_geometry.py](scripts/32_kemp_family_geometry.py) — measures catalytic geometry across all 97 PDB 'kemp eliminase' entries
- [scripts/33_analyze_oversampling.py](scripts/33_analyze_oversampling.py) — reads a sweep's `geometry.tsv`: instrument check, sequence-vs-backbone verdict, what predicts the base contact
- [scripts/34_plot_contact_vs_rmsd.py](scripts/34_plot_contact_vs_rmsd.py) — the talk's figure: base contact vs CA RMSD per sweep, with the crystal window as a band
- [scripts/90_build_submission.py](scripts/90_build_submission.py) — `results/designs.jsonl` → `results/designs.fasta` (`make submission`)
- [scripts/91_bank_from_sweep.py](scripts/91_bank_from_sweep.py) — promote a sweep's best designs into `results/designs.jsonl`, verifying the base/donor residue at each index
- [tools/check_index.py](tools/check_index.py) — lint: dead links, unindexed files, duplicate entries, bad log/experiment names
- [tools/new.py](tools/new.py) — create collision-free log entries and experiment pages (`log <type> "<title>"`, `exp <slug>`)
- [tools/fetch_papers.sh](tools/fetch_papers.sh) — download the open-access literature into `data/papers/` (gitignored)
- [tools/novelty_check.sh](tools/novelty_check.sh) — TM-score a design against published structures; PASS/FAIL against the 0.7 gate
- [tools/self_diversity.sh](tools/self_diversity.sh) — all-vs-all TM-score over OUR OWN candidates: how many distinct folds are we actually submitting?
- [tools/status.py](tools/status.py) — overview: experiments table and recent log entries (`make status`)
- [configs/](configs/) — reusable run configs, `<handle>-NN.json`, referenced from experiment pages
- [envs/](envs/) — pinned environments for external tools with their own deps (`<tool>.yml` / `<tool>.Dockerfile`)
- [tests/](tests/) — pytest suite (config, runs, data, submission rules, cross-check vs the organizers' validator, tools, index)

- [cluster/](cluster/) — the two-stage pipeline we run on the GPU cluster (design once, sample sequences many times)
- [cluster/oversample.sbatch](cluster/oversample.sbatch) — **Idea A**: many LigandMPNN sequences on one existing backbone, folded and measured
- [cluster/design_backbones.sbatch](cluster/design_backbones.sbatch) — stage 1: RFD3 backbones only, one per motif, no MMseqs2 and no Boltz-2
- [cluster/replicate_seeds.sbatch](cluster/replicate_seeds.sbatch) — fold the same sequences at 5 Boltz-2 seeds: the scored consistency term, and the noise floor
- [cluster/launch_oversample.sh](cluster/launch_oversample.sh) — deploy + submit an oversampling job from a finished run's `bridge/`
- [cluster/launch_design.sh](cluster/launch_design.sh) — deploy + submit the RFD3 design stage over a directory of motifs
- [cluster/build_boltz_queries.py](cluster/build_boltz_queries.py) — many sequences → one Boltz-2 query directory, with query-only alignments
- [cluster/measure_boltz_outputs.py](cluster/measure_boltz_outputs.py) — catalytic geometry for a whole batch: the pinned contacts plus a numbering-agnostic scan
- [cluster/build_family_motifs.py](cluster/build_family_motifs.py) — **Idea C**: RFD3 motifs from the family's own crystal structures, farthest-point selected
- [cluster/build_control_fasta.py](cluster/build_control_fasta.py) — natural-enzyme control sequences for the instrument check, taken from the deposited structures

## Artifacts
- [data/](data/) — bulk inputs, gitignored; registry in `wiki/data.md`
- [runs/](runs/) — one directory per execution, gitignored; linked from the experiment pages
- [results/](results/) — curated tracked outputs (figures, tables, the submission); each entry names its run
- [results/designs.jsonl.template](results/designs.jsonl.template) — copy to `results/designs.jsonl`: our submission candidates
- [results/designs.jsonl](results/designs.jsonl) — **our submission candidates**; rebuild the FASTA with `make submission`
- [results/oversample_a_seed4_job27.tsv](results/oversample_a_seed4_job27.tsv) — chris-04: 72 sequences on seed 4's backbone + 3 natural controls, fully measured
- [results/oversample_b_trp44_job31.tsv](results/oversample_b_trp44_job31.tsv) — chris-05: 72 sequences on zonghu's Trp44 backbone; refutes the three-anchor motif
- [results/oversample_rescue_s5_job40.tsv](results/oversample_rescue_s5_job40.tsv) — chris-07: seed 5 is not rescuable (0/48 refolded under 2 Å)
- [results/oversample_c_4bs0a_job35.tsv](results/oversample_c_4bs0a_job35.tsv) — chris-06: a fresh 4BS0_A backbone, designable at 1.33 Å but 0/32 in window
- [results/oversample_c_8usl_job36.tsv](results/oversample_c_8usl_job36.tsv) — chris-06: the most distinct family motif gives less designable backbones
- [results/oversample_a_seed4_job27_contact_vs_rmsd.png](results/oversample_a_seed4_job27_contact_vs_rmsd.png) — **the figure**: the fold is reproduced, the catalytic contact is not
- [results/reference_kemp-1_summary.json](results/reference_kemp-1_summary.json) — verified reference run (cluster job 1); the baseline we must beat
- [results/kemp_family_geometry.tsv](results/kemp_family_geometry.tsv) — **the geometry target**: 43 ligand copies from 23 crystal structures
- [results/sweep_kemp-2_summary.json](results/sweep_kemp-2_summary.json) — chris-02 seed 2: collapsed refold (CA RMSD 14.6 Å)
- [results/sweep_kemp-3_summary.json](results/sweep_kemp-3_summary.json) — chris-02 seed 3: folded, base contact drifted to 8.33 Å
- [results/sweep_kemp-4_summary.json](results/sweep_kemp-4_summary.json) — chris-02 seed 4: **best design so far**, beats the baseline; novelty unchecked
- [results/sweep_kemp-5_summary.json](results/sweep_kemp-5_summary.json) — chris-02 seed 5: collapsed refold (CA RMSD 13.7 Å)
- [notebooks/](notebooks/) — exploration only, one folder per person (`notebooks/<handle>/`); outputs stripped on commit
