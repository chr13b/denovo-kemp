"""Two-stage "anchored" affinity ladder: cofold ONCE with the TS analogue, then score
all three ligands against that one receptor conformation and binding site.

    uv run python scripts/24_build_anchored_ladder.py --label=hg3 \
        --fasta=results/affinity/hg3.fasta --cheap=true

Why: in the plain ladder (`scripts/20_...`) each ligand gets its OWN cofold, so
ddG compares three *different* predicted pockets and ligand placements. That makes
receptor conformation a confound, and [zonghu-02](../wiki/experiments/zonghu-02_affinity-ladder-controls.md)
found the result did not track catalysis. Here:

  Stage A  protein + TS analogue -> one predicted complex
  Stage B  each ligand predicted with
             templates:   the stage-A protein  (same receptor conformation)
             constraints: pocket(binder, contacts=stage-A contact residues, force)
           so every ligand is scored in the same site of the same structure.

Boltz-2 has no "fixed ligand pose" input, so the ligand still relaxes inside the
constrained pocket - this anchors the receptor and the site, not the exact coordinates.

`--cheap=true` cuts sampling hard for a pilot. Validate the idea before paying for it.
"""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from kemp.config import parse
from kemp.ligands import LADDER, LIGANDS, REFERENCE
from kemp.paths import ROOT
from kemp.run import start_run

SBATCH = """#!/usr/bin/env bash
#SBATCH --job-name=kemp-anchored
#SBATCH --partition=gpu
#SBATCH --constraint={constraint}
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task={cpus}
#SBATCH --mem={mem}
#SBATCH --gres=gpu:l4:1
#SBATCH --time={time_limit}

set -e -o pipefail
BUNDLE="${{SLURM_SUBMIT_DIR:-$PWD}}"
[ -d "$BUNDLE/yaml_a" ] || {{ echo "STOP: no yaml_a/ under $BUNDLE" >&2; exit 1; }}
source /mnt/work/kemp_example/env.sh
OUT="$BUNDLE/out"; CACHE="$BUNDLE/boltz-cache"
mkdir -p "$OUT" "$CACHE"
for ASSET in boltz2_conf.ckpt boltz2_aff.ckpt mols.tar; do
    [ -e "$CACHE/$ASSET" ] || ln -s "$BOLTZ_ASSETS/$ASSET" "$CACHE/$ASSET"
done
[ -e "$CACHE/mols" ] || ln -s "$BOLTZ_ASSETS/mols" "$CACHE/mols"
echo "node: $(hostname)"; nvidia-smi --query-gpu=name --format=csv,noheader || true

predict () {{  # $1 = yaml, $2 = out subdir, $3 = seed
    "$ENV_ROOT/env-boltz2/bin/boltz" predict "$1" \\
        --out_dir "$2" --cache "$CACHE" \\
        --accelerator gpu --devices 1 --no_kernels \\
        --sampling_steps {sampling_steps} --recycling_steps {recycling_steps} \\
        --diffusion_samples {diffusion_samples} \\
        --sampling_steps_affinity {sampling_steps_affinity} \\
        --diffusion_samples_affinity {diffusion_samples_affinity} \\
        --output_format mmcif --num_workers 0 --preprocessing-threads 1 \\
        --seed "$3" 2>&1 | tee "$2.log"
}}

echo "######## STAGE A: cofold with the TS analogue ########"
for YAML in "$BUNDLE"/yaml_a/*.yaml; do
    NAME=$(basename "$YAML" .yaml); SECONDS=0
    predict "$YAML" "$OUT/$NAME" "${{NAME##*_s}}"
    echo "STAGE_A $NAME took ${{SECONDS}}s"
done

echo "######## deriving template + pocket from stage A ########"
# env-rfd3 is the env that carries biotite (env-boltz2 does not); the organizers'
# own prepare_ligandmpnn.py runs under env-rfd3 for the same reason.
"$ENV_ROOT/env-rfd3/bin/python" "$BUNDLE/make_stage_b.py" "$BUNDLE"

echo "######## STAGE B: all ligands, anchored to that structure ########"
for YAML in "$BUNDLE"/yaml_b/*.yaml; do
    NAME=$(basename "$YAML" .yaml); SECONDS=0
    predict "$YAML" "$OUT/$NAME" "${{NAME##*_s}}"
    echo "STAGE_B $NAME took ${{SECONDS}}s"
done

echo "ALL DONE. Affinity JSONs:"
find "$OUT" -name 'affinity_*.json' | sort
"""


@dataclass
class Config:
    name: str = "anchored"
    label: str = "design"
    sequence: str = ""
    fasta: str = ""
    msa: str = "empty"
    seeds: int = 2  # seeds per ligand in stage B
    anchor_seeds: int = 1  # stage-A cofolds; each one anchors a full stage-B ladder
    ligands: list[str] = field(default_factory=lambda: list(LADDER))
    pocket_radius: float = 5.0  # A from any TS-analogue heavy atom
    pocket_max_distance: float = 6.0  # Boltz pocket constraint tolerance
    pocket_force: bool = True
    use_template: bool = False  # pin receptor conformation too; see make_stage_b.py for why it is off
    cheap: bool = False  # pilot settings: validate the idea before paying for it
    constraint: str = "g6.xlarge"
    cpus: int = 4
    mem: str = "14G"
    time_limit: str = "03:00:00"
    sampling_steps: int = 200
    recycling_steps: int = 3
    diffusion_samples: int = 1
    sampling_steps_affinity: int = 200
    diffusion_samples_affinity: int = 5
    project: str = "/mnt/work/projects"


CHEAP = dict(
    sampling_steps=50,
    recycling_steps=1,
    diffusion_samples=1,
    sampling_steps_affinity=50,
    diffusion_samples_affinity=2,
)


def read_sequence(cfg: Config) -> str:
    if cfg.sequence and cfg.fasta:
        raise SystemExit("give --sequence or --fasta, not both")
    if cfg.fasta:
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
    if REFERENCE not in cfg.ligands:
        raise SystemExit(f"the ladder must include {REFERENCE}; it defines the anchor")
    seq = read_sequence(cfg)
    settings = dict(
        sampling_steps=cfg.sampling_steps,
        recycling_steps=cfg.recycling_steps,
        diffusion_samples=cfg.diffusion_samples,
        sampling_steps_affinity=cfg.sampling_steps_affinity,
        diffusion_samples_affinity=cfg.diffusion_samples_affinity,
    )
    if cfg.cheap:
        settings.update(CHEAP)

    run = start_run(f"{cfg.name}-{cfg.label}", cfg)
    bundle = run.dir / "bundle"
    (bundle / "yaml_a").mkdir(parents=True)

    # Stage A: the TS analogue alone defines the receptor conformation and the pocket.
    for seed in range(1, cfg.anchor_seeds + 1):
        spec = {
            "version": 1,
            "sequences": [
                {"protein": {"id": "A", "sequence": seq, "msa": cfg.msa}},
                {"ligand": {"id": "B", "smiles": LIGANDS[REFERENCE].smiles}},
            ],
            "properties": [{"affinity": {"binder": "B"}}],
        }
        (bundle / "yaml_a" / f"{cfg.label}_anchor_s{seed}.yaml").write_text(
            yaml.safe_dump(spec, sort_keys=False), encoding="utf-8"
        )

    (bundle / "ladder.json").write_text(
        json.dumps(
            {
                "label": cfg.label,
                "sequence": seq,
                "msa": cfg.msa,
                "seeds": cfg.seeds,
                "anchor_seeds": cfg.anchor_seeds,
                "reference": REFERENCE,
                "ligands": {k: LIGANDS[k].smiles for k in cfg.ligands},
                "pocket_radius": cfg.pocket_radius,
                "pocket_max_distance": cfg.pocket_max_distance,
                "pocket_force": cfg.pocket_force,
                "use_template": cfg.use_template,
                "cheap": cfg.cheap,
                "settings": settings,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    shutil.copy2(ROOT / "scripts" / "make_stage_b.py", bundle / "make_stage_b.py")
    (bundle / "run.sh").write_text(
        SBATCH.format(
            constraint=cfg.constraint,
            cpus=cfg.cpus,
            mem=cfg.mem,
            time_limit=cfg.time_limit,
            **settings,
        ),
        encoding="utf-8",
        newline="\n",
    )

    # each stage-A anchor seeds a FULL stage-B ladder, so the counts multiply
    n_b = len(cfg.ligands) * cfg.seeds * cfg.anchor_seeds
    remote = f"{cfg.project}/zonghu_anc_{cfg.label}"
    print(
        f"\nstage A: {cfg.anchor_seeds} anchor cofold(s); stage B: {n_b} anchored "
        f"prediction(s) = {len(cfg.ligands)} ligands x {cfg.seeds} seeds x "
        f"{cfg.anchor_seeds} anchor(s); total {cfg.anchor_seeds + n_b}"
    )
    print(f"settings: {settings}{'  [CHEAP PILOT]' if cfg.cheap else ''}")
    print(f"\n  ssh pdh-team 'mkdir -p {remote}'")
    print(f"  scp -r '{bundle}'/* pdh-team:{remote}/")
    print(f"  ssh pdh-team 'cd {remote} && sbatch run.sh'")
    run.finish(ok=True, stage_a=cfg.seeds, stage_b=n_b, remote=remote, settings=settings)


if __name__ == "__main__":
    main(parse(Config))
