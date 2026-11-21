"""Turn a returned affinity-ladder bundle into the substrate/product-vs-TS table.

    uv run python scripts/21_report_affinity_ladder.py --out=<dir with the cluster's out/> --label=zonghu01

Reads every `affinity_*.json` under --out, groups by ligand and seed, and reports
dG(ligand) - dG(TS analogue) in kcal/mol. Positive = binds more weakly than the TS
analogue, which is the catalytically desirable direction for both the substrate (the
enzyme stabilises the TS over the ground state) and the product (it leaves instead of
inhibiting).

Writes `summary.json` and `ladder.md` into the run directory. Numbers come only from the
JSON files; nothing is filled in when a prediction is missing.
"""

from __future__ import annotations

import json
import math
import statistics
from dataclasses import dataclass
from pathlib import Path

from kemp.config import parse
from kemp.ligands import KCAL_PER_LOG10, LADDER, LIGANDS, REFERENCE, ddg_kcal, pseudo_dg_kcal
from kemp.run import start_run


@dataclass
class Config:
    name: str = "affinity-report"
    out: str = ""  # directory containing the cluster's out/ tree
    label: str = ""  # optional: only read stems starting with this label
    noise_sigmas: float = 2.0  # |ddG| must exceed this many propagated SEMs to count


def collect(out_dir: Path, label: str) -> dict[str, dict[int, dict]]:
    """-> {ligand_key: {seed: affinity_json}} parsed from the file stems."""
    found: dict[str, dict[int, dict]] = {}
    files = sorted(out_dir.rglob("affinity_*.json"))
    if not files:
        raise SystemExit(f"no affinity_*.json under {out_dir}")
    for path in files:
        stem = path.stem[len("affinity_") :]
        if label and not stem.startswith(label + "_"):
            continue
        # stem looks like <label>_<ligand>_s<seed>
        head, _, seed_part = stem.rpartition("_s")
        if not seed_part.isdigit():
            print(f"  skipping {path.name}: cannot read a seed from the name")
            continue
        seed = int(seed_part)
        lig = next((k for k in LIGANDS if head.endswith("_" + k) or head == k), None)
        if lig is None:
            print(f"  skipping {path.name}: no known ligand in {head!r}")
            continue
        # utf-8-sig reads both plain UTF-8 and a BOM-prefixed file
        found.setdefault(lig, {})[seed] = json.loads(path.read_text(encoding="utf-8-sig"))
    return found


def stats(values: list[float]) -> dict:
    n = len(values)
    sd = statistics.stdev(values) if n > 1 else 0.0
    return {
        "n": n,
        "mean": statistics.fmean(values),
        "sd": sd,
        "sem": sd / math.sqrt(n) if n else 0.0,
        "min": min(values),
        "max": max(values),
        "values": values,
    }


def main(cfg: Config) -> None:
    if not cfg.out:
        raise SystemExit("pass --out=<directory containing the returned out/ tree>")
    out_dir = Path(cfg.out)
    if not out_dir.is_dir():
        raise SystemExit(f"not a directory: {out_dir}")

    run = start_run(cfg.name + (f"-{cfg.label}" if cfg.label else ""), cfg)
    found = collect(out_dir, cfg.label)

    per_ligand: dict[str, dict] = {}
    for lig in LADDER:
        if lig not in found:
            continue
        seeds = sorted(found[lig])
        vals = [found[lig][s]["affinity_pred_value"] for s in seeds]
        probs = [found[lig][s]["affinity_probability_binary"] for s in seeds]
        per_ligand[lig] = {
            "seeds": seeds,
            "log10_ic50_uM": stats(vals),
            "probability_binary": stats(probs),
            "pseudo_dg_kcal_mean": pseudo_dg_kcal(statistics.fmean(vals)),
            "ic50_uM_from_mean": 10 ** statistics.fmean(vals),
        }

    missing = [lig for lig in LADDER if lig not in per_ligand]
    ref = per_ligand.get(REFERENCE)

    comparisons: dict[str, dict] = {}
    if ref is not None:
        for lig, data in per_ligand.items():
            if lig == REFERENCE:
                continue
            a, b = data["log10_ic50_uM"], ref["log10_ic50_uM"]
            ddg = ddg_kcal(a["mean"], b["mean"])
            noise = KCAL_PER_LOG10 * math.hypot(a["sem"], b["sem"])
            threshold = cfg.noise_sigmas * noise
            comparisons[f"{lig}_minus_{REFERENCE}"] = {
                "ddg_kcal_per_mol": ddg,
                "propagated_sem_kcal": noise,
                "threshold_kcal": threshold,
                "exceeds_noise": abs(ddg) > threshold if noise > 0 else None,
                "ranges_overlap": not (a["min"] > b["max"] or b["min"] > a["max"]),
                "direction": (
                    "binds more weakly than the TS analogue (favourable)"
                    if ddg > 0
                    else "binds more tightly than the TS analogue (unfavourable)"
                ),
            }

    weak_binder = None
    if per_ligand:
        weak_binder = all(d["probability_binary"]["mean"] < 0.5 for d in per_ligand.values())

    lines = [f"# Affinity ladder{': ' + cfg.label if cfg.label else ''}", ""]
    lines += [
        "`affinity_pred_value` is log10(IC50) with IC50 in uM, so lower = tighter. "
        f"1 decade = {KCAL_PER_LOG10:.3f} kcal/mol at 298 K.",
        "",
        "| ligand | role | n | log10(IC50/uM) mean +- sd | IC50 (uM) | P(binder) mean |",
        "|---|---|---|---|---|---|",
    ]
    for lig, d in per_ligand.items():
        s = d["log10_ic50_uM"]
        lines.append(
            "| `%s` %s | %s | %d | %.3f +- %.3f | %.3g | %.3f |"
            % (
                lig,
                "**(reference)**" if lig == REFERENCE else "",
                LIGANDS[lig].name,
                s["n"],
                s["mean"],
                s["sd"],
                d["ic50_uM_from_mean"],
                d["probability_binary"]["mean"],
            )
        )
    lines += ["", "## Relative to the TS analogue", ""]
    if ref is None:
        lines.append(f"**Cannot compare: no predictions for the reference `{REFERENCE}`.**")
    else:
        lines += [
            "| comparison | ddG (kcal/mol) | propagated SEM | exceeds %.0f sigma | ranges overlap |"
            % cfg.noise_sigmas,
            "|---|---|---|---|---|",
        ]
        for key, c in comparisons.items():
            lines.append(
                "| `%s` | **%+.3f** | %.3f | %s | %s |"
                % (
                    key,
                    c["ddg_kcal_per_mol"],
                    c["propagated_sem_kcal"],
                    {True: "yes", False: "**no**", None: "n/a"}[c["exceeds_noise"]],
                    "yes" if c["ranges_overlap"] else "no",
                )
            )
        lines += [
            "",
            "Positive ddG = that ligand binds **more weakly** than the TS analogue, which is "
            "the direction catalysis needs for both the substrate and the product.",
        ]
    if missing:
        lines += ["", f"**Missing predictions for:** {', '.join(missing)}."]
    if weak_binder:
        lines += [
            "",
            "**Caution: every ligand has P(binder) < 0.5.** Boltz-2's own binary head does not "
            "consider this protein a binder, so the `affinity_pred_value` differences are "
            "comparisons between non-binders and should not be trusted.",
        ]
    (run.dir / "ladder.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))

    run.finish(
        ok=True,
        source=str(out_dir),
        label=cfg.label or None,
        per_ligand=per_ligand,
        comparisons=comparisons,
        missing_ligands=missing,
        all_below_binder_threshold=weak_binder,
        kcal_per_log10=KCAL_PER_LOG10,
    )


if __name__ == "__main__":
    main(parse(Config))
