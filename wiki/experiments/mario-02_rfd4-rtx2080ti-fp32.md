# mario-02: RFD4-Proteina on an RTX 2080 Ti in full precision

- **Owner:** mario
- **Date:** 2026-11-21
- **Status:** running (part 1 done: generation works; part 2, the oracle, not run)
- **Question:** Can RFD4-Proteina generate one design on an RTX 2080 Ti (Turing, compute capability 7.5, 11 GB) if it runs in full precision (`precision="32"`) with the PyTorch attention and triangle-multiplication paths and `batch_size=1`?
- **Why it matters:** [mario-01](mario-01_rfd4-euler-smoke.md) asks for a 35 GB GPU (A100 class) after its first attempt failed with `RuntimeError: Invalid backend` in the bf16 attention. The 2080 Ti is not on RFD4's tested list (A100, H100, L40S, RTX 6000 Ada, Blackwell), but if it works it widens the pool of GPUs the campaign can use on Euler. If it fails, we stop looking at pre-Ampere cards.
- **Script + config:** `scripts/10_generate_smoke_design.py` (its `--overrides` option) + `configs/mario-02.json`; Slurm request in `scripts/euler_job_rtx2080.sbatch`
- **Runs:** `$SCRATCH/kemp/runs/20261121-182146_mario-02/` on Euler, Slurm job 21856801, commit `4182845` (branch `mario-02-rtx2080ti`).

Status values: `planned`, `running`, `done: supported`, `done: refuted`, `done: inconclusive`, `abandoned`.

## What it does

On Euler, after `git pull`:

```bash
mkdir -p "$SCRATCH/kemp/logs"
sbatch scripts/euler_job_rtx2080.sbatch python scripts/10_generate_smoke_design.py configs/mario-02.json
```

Same one unconditional 100-residue monomer as mario-01, with no oracle (`"oracle": ""`), plus these Hydra overrides on
`rfd4-generate` (from `configs/mario-02.json`, appended to the command by the script):

| Override | Why |
|---|---|
| `precision="32"` | The default `bf16-mixed` has no native support on Turing; the attention in `pair_bias_attn.py` runs in the autocast dtype. `"32"` is a documented value of RFD4's `precision` option. The inner quotes keep Hydra from reading it as the integer 32. |
| `nn.attention_type=torch`, `nn.tri_mult_backend=torch` | The cuEquivariance triangle kernels assert bf16 inputs (`triangle.py`), so they cannot run in fp32; this keeps the fused path from being picked. |
| `batch_size=1` | The card has 11 GB and fp32 roughly doubles the activations. |

`scripts/euler_job_rtx2080.sbatch` requests `--gpus=rtx_2080:1` (Euler's GPU type name; the 35 GB `gpumem` request of
`euler_job.sbatch` cannot be used here) for 2 hours, then runs `euler_job.sbatch` itself, so logs, outputs and the
environment are identical to mario-01. Check the `[euler_job] gpu:` line of the job log to see which card it got.

## Not verified yet

- That `rtx_2080` on Euler is the 2080 Ti (11 GB) and that the request is accepted (`sbatch --test-only` first).
- That `precision="32"` is accepted by `rfd4-generate` (the docs list it for training; the generation option points to that list) and that the quoted form reaches Hydra as a string.
- That the 11 GB are enough in fp32: the model's weight and activation size is unknown here.
- That `nn.attention_type` and `nn.tri_mult_backend` exist as overrides of the installed checkout (they are in RFD4's CLI reference).
- That nothing else in the model assumes bf16 or Ampere.
- Part 2, the refolding oracle on this card, is not run yet. OpenFold3/AF3 needs `XLA_FLAGS=--xla_disable_hlo_passes=custom-kernel-fusion-rewriter` and `AF3_FLASH_ATTENTION_IMPLEMENTATION=xla` below compute capability 8.0 (Euler AF3 page, RFD4 source); `envs/euler.sh` now sets both when `nvidia-smi` reports a capability below 8. Whether the container then folds on the 2080 Ti, and whether `XLA_FLAGS` reaches it through apptainer, is untested. RFD4's AF2 oracle needs 8.0 or newer.

## Result
Part 1 (generation, no oracle), read from the run directory and the job log:
- GPU `NVIDIA GeForce RTX 2080 Ti`, 11264 MiB, host `eu-lo-g2-023`. `rfd4-generate` exited with 0 after a progress bar
  of 1:23 (the Blackwell and A100 runs: 0:12 and 0:20, so about 4–7 times slower) and wrote
  `inference_samples/monomer-short/monomer-short_generated.cif`: one chain, 100 residues.
- The overrides were accepted (`precision="32"`, `nn.attention_type=torch`, `nn.tri_mult_backend=torch`, `batch_size=1`).
  Which of them removed the bf16 failure of [mario-01](mario-01_rfd4-euler-smoke.md) was not isolated.
- Same seed 0 as the other runs: the fp32 design differs from the Blackwell bf16 design by 0.09 Å CA RMSD (1 of 100
  residues differs in the sequence), and from the A100 design by 0.10 Å, so full precision on Turing reproduces the bf16
  design. CA–CA distances 3.67–3.94 Å, no CA pairs closer than 3.2 Å (own check of the CIFs, not an RFD4 metric).
- `summary.json` says `ok: false` and 0 design files: the script's glob missed the example subfolder, fixed afterwards.
- Not recorded: peak GPU memory; designs longer than 100 residues are untested.

## Verdict and next step
Part 1: supported. RFD4-Proteina generates on an RTX 2080 Ti in fp32 with these overrides. Next: part 2, the oracle on
this card (`--oracle=of3` on the same config, with the settings `envs/euler.sh` now applies), and a 250-residue example
(`monomer-long`) at `batch_size=1` to see whether 11 GB are enough.
