"""Run the three-stage design funnel and record why every design lived or died.

    uv run python scripts/30_filter_designs.py --designs=runs/my_designs --stage=1
    uv run python scripts/30_filter_designs.py --designs=... --stage=3 \
        --reference=results/theozyme/theozyme_7k4u_core.pdb

Architecture: a **funnel of independent stage gates over a flat directory of designs**,
not a workflow engine. Each design is evaluated on its own, in its own try/except, and
one record per design is appended to `verdicts.jsonl` as it finishes. That gives:

  * **isolation** - a corrupt CIF or a missing score file kills one design, never the run
  * **resumability** - rerun and already-recorded designs are skipped, so a 5000-design
    sweep survives a dropped SSH session
  * **auditability** - every filter's value, threshold and reason is kept, including for
    designs that passed, so a threshold can be re-cut later without recomputing
  * **no hidden passes** - a filter that could not be evaluated records `passed: null`
    and blocks the gate, instead of silently counting as a pass

Stages are deliberately separate invocations: stage 2 needs stage 1's survivors and a
GPU run in between, so a single long-lived process would be the wrong shape. The GPU
work stays in the cluster sbatch; this script is the cheap CPU filtering around it.
"""

from __future__ import annotations

import csv
import json
import traceback
from dataclasses import dataclass, field
from pathlib import Path

from kemp.config import parse
from kemp.filters import (
    FilterResult,
    all_passed,
    check_boltz_confidence,
    check_catalytic_residues,
    check_gravy,
    check_isoelectric_point,
    check_mpnn_score,
    check_no_reactive_in_pocket,
    failures,
    parse_boltz_confidence,
    parse_ligandmpnn_fasta,
    unevaluated,
)
from kemp.run import start_run
from kemp.structure import (
    check_active_site_plddt,
    check_backbone_rmsd,
    check_clashes,
    check_ligand_contacts,
    check_motif_rmsd,
    check_packing,
    check_radius_of_gyration,
    check_ramachandran,
    check_topology,
    load_structure,
)

# The HG3 Kemp motif, in the numbering of results/theozyme/theozyme_7k4u_core.pdb.
MOTIF_SPEC = {
    "A127": ("OD1", "CG", "OD2"),  # catalytic base
    "A50": ("OE1", "CD", "NE2"),  # oxyanion-hole donor
}
# (residue, protein atom, ligand atom, min A, max A) - windows, not minima
CATALYTIC_CONTACTS = [
    ("A127", "OD2", "N3", 2.4, 3.4),
    ("A50", "NE2", "N1", 2.6, 3.4),
]


@dataclass
class Config:
    name: str = "filter"
    designs: str = ""  # directory holding one subdirectory or file set per design
    stage: int = 1  # 1 = backbones, 2 = sequences, 3 = cofolds
    reference: str = ""  # ideal motif structure (stages 1 and 3)
    out: str = ""  # defaults to the run directory
    resume: bool = True
    # thresholds, all overridable from the command line or a config file
    max_motif_rmsd: float = 1.0
    max_backbone_rmsd: float = 2.0
    max_clashes: int = 0
    rog_tolerance: float = 1.25
    max_rama_outliers: float = 0.05
    max_coil: float = 0.6
    min_mpnn_overall: float = 0.35
    min_mpnn_ligand: float = 0.35
    gravy_range: list[float] = field(default_factory=lambda: [-1.0, 0.3])
    pi_range: list[float] = field(default_factory=lambda: [4.0, 9.5])
    min_plddt: float = 85.0
    min_iptm: float = 0.6
    catalytic: dict = field(default_factory=dict)  # {"127": "D", "50": "Q"} 1-based
    pocket_positions: list[int] = field(default_factory=list)


# ------------------------------------------------------------------ stage gates


def stage1_backbone(design: Path, cfg: Config, reference) -> list[FilterResult]:
    """RFdiffusion backbones: motif fidelity, clashes, compactness, topology."""
    struct_file = _first(design, ("*.cif.gz", "*.cif", "*.pdb"))
    if struct_file is None:
        return [unevaluated("structure", f"no structure file in {design}")]
    atoms = load_structure(struct_file)
    results = [
        check_clashes(atoms, max_clashes=cfg.max_clashes),
        check_radius_of_gyration(atoms, tolerance=cfg.rog_tolerance),
        check_ramachandran(atoms, max_fraction=cfg.max_rama_outliers),
        check_topology(atoms, max_coil=cfg.max_coil),
    ]
    if reference is None:
        results.append(unevaluated("motif_rmsd", "no --reference given", cfg.max_motif_rmsd))
    else:
        # RFdiffusion renumbers; map the motif through its diffused_index_map if present
        design_spec = _mapped_spec(design)
        results.append(
            check_motif_rmsd(
                atoms, reference, MOTIF_SPEC, max_rmsd=cfg.max_motif_rmsd, design_spec=design_spec
            )
        )
    return results


def stage2_sequence(design: Path, cfg: Config, _reference) -> list[FilterResult]:
    """LigandMPNN sequences: score, biophysics, active-site integrity, packing."""
    fasta = _first(design, ("*.fa", "*.fasta"))
    if fasta is None:
        return [unevaluated("sequence", f"no FASTA in {design}")]
    records = parse_ligandmpnn_fasta(fasta)
    if not records:
        return [unevaluated("sequence", f"no records parsed from {fasta.name}")]
    rec = records[0]
    seq = rec["sequence"]
    catalytic = {int(k): v for k, v in cfg.catalytic.items()} if cfg.catalytic else {}
    results = [
        check_mpnn_score(rec, cfg.min_mpnn_overall, cfg.min_mpnn_ligand),
        check_gravy(seq, *cfg.gravy_range),
        check_isoelectric_point(seq, *cfg.pi_range),
        check_catalytic_residues(seq, catalytic),
        check_no_reactive_in_pocket(seq, cfg.pocket_positions),
    ]
    struct_file = _first(design, ("*.cif.gz", "*.cif", "*.pdb"))
    if struct_file is None:
        results.append(unevaluated("packing", "no structure alongside the sequence"))
    else:
        results.append(check_packing(load_structure(struct_file)))
    return results


def stage3_cofold(design: Path, cfg: Config, reference) -> list[FilterResult]:
    """Boltz-2 cofolds: RMSD to the design and the motif, confidence, contacts."""
    model = _first(design, ("*_model_0.cif", "*.cif", "*.pdb"))
    if model is None:
        return [unevaluated("model", f"no Boltz model in {design}")]
    atoms = load_structure(model)
    results: list[FilterResult] = []

    conf_file = _first(design, ("confidence_*.json",))
    if conf_file is None:
        results.append(
            unevaluated(
                "boltz_confidence", "no confidence_*.json", {"plddt": cfg.min_plddt, "iptm": cfg.min_iptm}
            )
        )
    else:
        results.append(check_boltz_confidence(parse_boltz_confidence(conf_file), cfg.min_plddt, cfg.min_iptm))

    design_bb = _first(design, ("rfd3*.cif.gz", "rfd3*.cif", "design.pdb"))
    if design_bb is None:
        results.append(
            unevaluated("backbone_rmsd", "no RFdiffusion backbone to compare against", cfg.max_backbone_rmsd)
        )
    else:
        results.append(check_backbone_rmsd(atoms, load_structure(design_bb), cfg.max_backbone_rmsd))

    if reference is None:
        results.append(unevaluated("motif_rmsd", "no --reference given", cfg.max_motif_rmsd))
    else:
        results.append(
            check_motif_rmsd(
                atoms, reference, MOTIF_SPEC, max_rmsd=cfg.max_motif_rmsd, design_spec=_mapped_spec(design)
            )
        )

    site = [(c, r) for c, r in (_split(t) for t in MOTIF_SPEC)]
    results.append(check_active_site_plddt(atoms, site, cfg.min_plddt))
    results.append(check_ligand_contacts(atoms, CATALYTIC_CONTACTS))
    return results


STAGES = {1: stage1_backbone, 2: stage2_sequence, 3: stage3_cofold}


# ---------------------------------------------------------------------- helpers


def _split(token: str) -> tuple[str, int]:
    from kemp.filters import split_residue_id

    return split_residue_id(token)


def _first(design: Path, patterns: tuple[str, ...]) -> Path | None:
    for pat in patterns:
        hits = sorted(design.glob(pat)) if design.is_dir() else []
        if hits:
            return hits[0]
    return None


def _mapped_spec(design: Path) -> dict | None:
    """Translate MOTIF_SPEC through an RFdiffusion diffused_index_map if one is there."""
    meta = _first(design, ("*.json",))
    if meta is None:
        return None
    try:
        from kemp.filters import parse_rfd3_index_map

        mapping = parse_rfd3_index_map(meta)
    except (json.JSONDecodeError, OSError):
        return None
    if not mapping:
        return None
    out = {}
    for token, names in MOTIF_SPEC.items():
        mapped = mapping.get(token)
        if not isinstance(mapped, str):
            return None  # incomplete map: better to fail the filter than guess
        out[mapped] = names
    return out


def _designs(root: Path) -> list[Path]:
    if not root.is_dir():
        raise SystemExit(f"--designs is not a directory: {root}")
    subdirs = sorted(p for p in root.iterdir() if p.is_dir())
    return subdirs or [root]


# ------------------------------------------------------------------------- main


def main(cfg: Config) -> None:
    if not cfg.designs:
        raise SystemExit("pass --designs=<directory>")
    if cfg.stage not in STAGES:
        raise SystemExit(f"--stage must be one of {sorted(STAGES)}")

    run = start_run(f"{cfg.name}-stage{cfg.stage}", cfg)
    out_dir = Path(cfg.out) if cfg.out else run.dir
    out_dir.mkdir(parents=True, exist_ok=True)
    verdict_path = out_dir / f"verdicts_stage{cfg.stage}.jsonl"

    done: set[str] = set()
    if cfg.resume and verdict_path.exists():
        for line in verdict_path.read_text(encoding="utf-8").splitlines():
            try:
                done.add(json.loads(line)["design"])
            except (json.JSONDecodeError, KeyError):
                continue  # a truncated last line from a killed run - just redo it
        print(f"[resume] {len(done)} design(s) already recorded")

    reference = None
    if cfg.reference:
        try:
            reference = load_structure(cfg.reference)
        except (OSError, ValueError) as exc:
            raise SystemExit(f"could not read --reference {cfg.reference}: {exc}") from exc

    gate = STAGES[cfg.stage]
    designs = _designs(Path(cfg.designs))
    n_pass = n_fail = n_error = 0

    with verdict_path.open("a", encoding="utf-8") as sink:
        for design in designs:
            if design.name in done:
                continue
            try:
                results = gate(design, cfg, reference)
                passed = all_passed(results)
                record = {
                    "design": design.name,
                    "stage": cfg.stage,
                    "passed": passed,
                    "reasons": failures(results),
                    "filters": [r.as_dict() for r in results],
                }
                n_pass, n_fail = (n_pass + 1, n_fail) if passed else (n_pass, n_fail + 1)
            except Exception as exc:  # noqa: BLE001 - one bad design must not kill the run
                n_error += 1
                record = {
                    "design": design.name,
                    "stage": cfg.stage,
                    "passed": False,
                    "reasons": [f"ERROR: {type(exc).__name__}: {exc}"],
                    "traceback": traceback.format_exc(limit=6),
                    "filters": [],
                }
            sink.write(json.dumps(record) + "\n")
            sink.flush()  # survive a kill mid-sweep
            run.log(design=design.name, passed=record["passed"], reasons=record["reasons"])
            flag = "PASS" if record["passed"] else "FAIL"
            print(
                f"  [{flag}] {design.name}"
                + ("" if record["passed"] else f"  <- {'; '.join(record['reasons'])}")
            )

    _write_csv(verdict_path, out_dir / f"verdicts_stage{cfg.stage}.csv")
    print(f"\nstage {cfg.stage}: {n_pass} passed, {n_fail} failed, {n_error} errored")
    print(f"verdicts: {verdict_path}")
    run.finish(
        ok=True, stage=cfg.stage, passed=n_pass, failed=n_fail, errored=n_error, verdicts=str(verdict_path)
    )


def _write_csv(jsonl: Path, csv_path: Path) -> None:
    """Flatten the verdicts to one row per design, one column per filter value."""
    rows, columns = [], ["design", "passed", "reasons"]
    for line in jsonl.read_text(encoding="utf-8").splitlines():
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        row = {
            "design": rec["design"],
            "passed": rec["passed"],
            "reasons": " | ".join(rec.get("reasons", [])),
        }
        for f in rec.get("filters", []):
            col = f["name"]
            row[col] = f["value"]
            if col not in columns:
                columns.append(col)
        rows.append(row)
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main(parse(Config))
