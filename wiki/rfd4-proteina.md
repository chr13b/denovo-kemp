# RFD4-Proteina on the cluster

Installed and **verified running on our L4** (2026-11-21). Baker Lab (IPD) × NVIDIA; code and
weights both BSD 3-Clause. Official repo: [RosettaCommons/RFD4-Proteina](https://github.com/RosettaCommons/RFD4-Proteina)
(several same-named forks exist on GitHub — this is the RosettaCommons one).
Weights: [nvidia/RFD4-Proteina](https://huggingface.co/nvidia/RFD4-Proteina).

Nothing in `/mnt/ref` was modified — it is read-only, and the organizers' `env-rfd3`,
`env-boltz2` and `env-ligandmpnn` are untouched. Everything lives under `/mnt/work/software`
and can be deleted with one `rm -rf`.

## Use it

```bash
export HF_HOME=/mnt/work/software/hf-cache      # keeps the 1.7 GB model off the 80 GB root disk
source /mnt/work/software/rfd4-proteina/.venv/bin/activate
cd /mnt/work/software/RFD4-Proteina             # for data/ and examples/
rfd4-generate inputs=<spec>.yaml num_replicates=1 out_dir=./runs/x '~metrics'
```

In a Slurm job also set **`export HF_HUB_OFFLINE=1`** — compute nodes have no internet, so
anything not already in `HF_HOME` fails there. Working example: `/mnt/work/software/rfd4_smoke.sbatch`.

| | |
|---|---|
| package | `rfd4-proteina` **0.0.3** (PyPI), repo checkout at `6306a21` |
| torch | **2.14.1+cu126** |
| weights | 1.7 GB, revision pinned to `a06e2509c7033b010fc43614e9fd840303588502` |
| venv | 7.7 GB at `/mnt/work/software/rfd4-proteina/.venv` |
| CLI | `rfd4-generate`, `rfd4-evaluate`, `rfd4-train`, `rfd4-train-ae` |

## Two install decisions worth knowing

**The project's recommended CUDA 13 profile cannot work here.** It wants torch 2.14.1/cu132,
which needs driver ≥ 580; this cluster runs **550.127.08 (CUDA 12.4)**. We used the `all-cuda12`
profile with `--torch-backend cu126`, consistent with the organizers' own `torch 2.7.1+cu126`.

**`HF_HOME` is forced onto `/mnt/work`.** By default HuggingFace caches into `~/.cache` on the
80 GB root disk shared with the OS. Do not unset it.

## Verified, and not verified

**Verified** (job 41, `/mnt/work/software/rfd4-smoke-41.log`): runs on `NVIDIA L4`, compute
capability (8, 9); CUDA available; one short monomer generated in 120 s; output CIF and metrics
CSV written; offline weight loading works.

**Not verified:** *peak VRAM is unmeasured* — the probe ran in a separate process after generation
had exited and reported a meaningless 0.00 GiB. The L4 (24 GB) is **not** on the project's tested
GPU list, which names the L40S (48 GB) for Ada. Generation at the benchmark size works; headroom at
260 residues is unknown. Measure inside the generation process before scaling up.

## Why it suits this project

RFD4 documents our exact task. From `docs/how-to/input_prep/index.md`: *"Starting from a theozyme
(a handful of catalytic residues and a substrate with no scaffold) you can condition only the atoms
in the motif and leave the rest for your model to design"*. Its conditions map onto the RFD3 config
we already use:

| RFD4 condition | granularity | our `configs/kemp_theozyme.json` |
|---|---|---|
| `C_CRD` coordinate | per **atom** | `select_fixed_atoms` |
| `C_IDX: false` index off | per **residue** | `unindex` (free placement along the chain) |
| `C_SEQ` sequence | per **residue** | implicit in the motif |

The repo ships an enzyme-design tutorial (`docs/examples/enzyme_design_tutorial.ipynb`) and an
input-authoring skill (`skills/rfd4-proteina-annotated-cif/`).

**Not yet built:** RFD4 only emits backbones. Turning one into a scored design needs a bridge to
LigandMPNN → MMseqs2 → Boltz-2, and the organizers' `prepare_ligandmpnn.py` is hardcoded to RFD3's
`.cif.gz` plus its `diffused_index_map`. That glue does not exist yet.
