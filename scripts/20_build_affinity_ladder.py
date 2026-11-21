"""Build a cluster bundle that cofolds one sequence with substrate / TS analogue / product
and predicts the binding affinity of each, so we can score transition-state discrimination.

    uv run python scripts/20_build_affinity_ladder.py --label=zonghu01 --sequence=MVDAD...
    uv run python scripts/20_build_affinity_ladder.py --label=hg3 --fasta=results/hg3.fasta --seeds=3

Writes `runs/<stamp>_affinity-<label>/bundle/` containing one Boltz-2 YAML per
(ligand x seed) plus `run.sh`, then prints the two commands that ship and launch it.
Nothing here touches the GPU; `scripts/21_report_affinity_ladder.py` reads the results back.

Why this measures something real: catalysis by transition-state stabilisation means the
enzyme binds the TS more tightly than the substrate. See `kemp.ligands` for the ladder and
the unit conversion, and `wiki/affinity-ladder.md` for the method and its limits.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from kemp.config import parse
from kemp.ligands import LADDER, LIGANDS
from kemp.run import start_run

SBATCH = """#!/usr/bin/env bash
#SBATCH --job-name=kemp-affinity
#SBATCH --partition=gpu
#SBATCH --constraint={constraint}
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task={cpus}
#SBATCH --mem={mem}
#SBATCH --gres=gpu:l4:1
#SBATCH --time={time_limit}

# Boltz-2 affinity ladder. No MMseqs2 here, so this does NOT need the big g6.2xlarge
# node: it fits on g6.xlarge, which means two can run at once and the team's RFD3
# pipeline keeps the big node.
set -e -o pipefail

BUNDLE=$(cd -- "$(dirname -- "${{BASH_SOURCE[0]}}")" && pwd -P)
source /mnt/work/kemp_example/env.sh
OUT="$BUNDLE/out"
CACHE="$BUNDLE/boltz-cache"
mkdir -p "$OUT" "$CACHE"

# The compute nodes have no internet. Boltz resolves the affinity checkpoint as
# <cache>/boltz2_aff.ckpt, so symlink the staged weights in and it never downloads.
for ASSET in boltz2_conf.ckpt boltz2_aff.ckpt mols.tar; do
    [ -e "$CACHE/$ASSET" ] || ln -s "$BOLTZ_ASSETS/$ASSET" "$CACHE/$ASSET"
done
[ -e "$CACHE/mols" ] || ln -s "$BOLTZ_ASSETS/mols" "$CACHE/mols"

echo "node: $(hostname)"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader || true

for YAML in "$BUNDLE"/yaml/*.yaml; do
    NAME=$(basename "$YAML" .yaml)
    echo "=== $NAME ==="
    SECONDS=0
    "$ENV_ROOT/env-boltz2/bin/boltz" predict "$YAML" \\
        --out_dir "$OUT/$NAME" \\
        --cache "$CACHE" \\
        --accelerator gpu --devices 1 --no_kernels \\
        --sampling_steps {sampling_steps} --recycling_steps {recycling_steps} \\
        --diffusion_samples {diffusion_samples} \\
        --sampling_steps_affinity {sampling_steps_affinity} \\
        --diffusion_samples_affinity {diffusion_samples_affinity} \\
        --output_format mmcif --num_workers 0 --preprocessing-threads 1 \\
        --seed "${{NAME##*_s}}" \\
        2>&1 | tee "$OUT/$NAME.log"
    echo "$NAME took ${{SECONDS}}s"
done

echo "ALL DONE. Affinity JSONs:"
find "$OUT" -name 'affinity_*.json' | sort
"""


@dataclass
class Config:
    name: str = "affinity"  # run-directory suffix gets "-<label>"
    label: str = "design"  # short tag for this protein, used in file names
    sequence: str = ""  # protein sequence, or use --fasta
    fasta: str = ""  # path to a 1-record FASTA instead of --sequence
    msa: str = "empty"  # "empty" = single-sequence mode, or a path to an .a3m ON THE CLUSTER
    seeds: int = 3  # replicates per ligand; needed to tell signal from noise
    ligands: list[str] = field(default_factory=lambda: list(LADDER))
    # cluster resources: the small node is the default on purpose (2 can run at once)
    constraint: str = "g6.xlarge"
    cpus: int = 4
    mem: str = "14G"
    time_limit: str = "02:00:00"
    # Boltz-2 sampling
    sampling_steps: int = 200
    recycling_steps: int = 3
    diffusion_samples: int = 1
    sampling_steps_affinity: int = 200
    diffusion_samples_affinity: int = 5
    project: str = "/mnt/work/projects"  # where the bundle lands on the cluster


def read_sequence(cfg: Config) -> str:
    if cfg.sequence and cfg.fasta:
        raise SystemExit("give --sequence or --fasta, not both")
    if cfg.fasta:
        # utf-8-sig so a BOM-prefixed FASTA does not turn its header into sequence
        lines = Path(cfg.fasta).read_text(encoding="utf-8-sig").splitlines()
        seq = "".join(ln.strip() for ln in lines if ln.strip() and not ln.startswith(">"))
    else:
        seq = cfg.sequence.strip()
    seq = seq.upper()
    if not seq:
        raise SystemExit("empty sequence: pass --sequence=... or --fasta=path")
    bad = sorted(set(seq) - set("ACDEFGHIKLMNPQRSTVWY"))
    if bad:
        raise SystemExit(f"sequence has non-standard residues: {bad}")
    return seq


def main(cfg: Config) -> None:
    unknown = [lig for lig in cfg.ligands if lig not in LIGANDS]
    if unknown:
        raise SystemExit(f"unknown ligand(s) {unknown}; valid: {sorted(LIGANDS)}")
    if cfg.seeds < 1:
        raise SystemExit("--seeds must be >= 1")
    seq = read_sequence(cfg)

    run = start_run(f"{cfg.name}-{cfg.label}", cfg)
    bundle = run.dir / "bundle"
    (bundle / "yaml").mkdir(parents=True)

    written = []
    for lig_key in cfg.ligands:
        lig = LIGANDS[lig_key]
        for seed in range(1, cfg.seeds + 1):
            stem = f"{cfg.label}_{lig_key}_s{seed}"
            protein: dict = {"id": "A", "sequence": seq}
            # "empty" is Boltz-2's single-sequence mode. Whatever we choose, it is the
            # SAME for all three ligands, so it cannot bias the difference between them.
            protein["msa"] = cfg.msa
            spec = {
                "version": 1,
                "sequences": [
                    {"protein": protein},
                    {"ligand": {"id": "B", "smiles": lig.smiles}},
                ],
                # one affinity ligand only - Boltz-2 rejects more than one
                "properties": [{"affinity": {"binder": "B"}}],
            }
            path = bundle / "yaml" / f"{stem}.yaml"
            path.write_text(yaml.safe_dump(spec, sort_keys=False), encoding="utf-8")
            written.append(stem)

    (bundle / "run.sh").write_text(
        SBATCH.format(
            constraint=cfg.constraint,
            cpus=cfg.cpus,
            mem=cfg.mem,
            time_limit=cfg.time_limit,
            sampling_steps=cfg.sampling_steps,
            recycling_steps=cfg.recycling_steps,
            diffusion_samples=cfg.diffusion_samples,
            sampling_steps_affinity=cfg.sampling_steps_affinity,
            diffusion_samples_affinity=cfg.diffusion_samples_affinity,
        ),
        encoding="utf-8",
        newline="\n",
    )
    (bundle / "ladder.json").write_text(
        json.dumps(
            {
                "label": cfg.label,
                "sequence": seq,
                "length": len(seq),
                "msa": cfg.msa,
                "seeds": cfg.seeds,
                "ligands": {k: LIGANDS[k].__dict__ for k in cfg.ligands},
                "yaml_stems": written,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    remote = f"{cfg.project}/zonghu_aff_{cfg.label}"
    print(f"\n{len(written)} prediction(s): {len(cfg.ligands)} ligand(s) x {cfg.seeds} seed(s)")
    print(f"sequence length {len(seq)}, msa={cfg.msa}\n")
    print("ship it:")
    print(f"  ssh pdh-team 'mkdir -p {remote}'")
    print(f"  scp -r '{bundle}'/* pdh-team:{remote}/")
    print("launch it:")
    print(f"  ssh pdh-team 'cd {remote} && sbatch run.sh'")
    print("bring it back:")
    print(f"  scp -r pdh-team:{remote}/out '<local dir>'")
    run.finish(ok=True, predictions=len(written), remote=remote, length=len(seq))


if __name__ == "__main__":
    main(parse(Config))
