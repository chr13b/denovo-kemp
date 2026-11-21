"""Compare predicted affinity-ladder values against measured catalytic efficiency.

    uv run python scripts/23_compare_ladder_to_kinetics.py

Reads the returned affinity JSONs for each HG variant plus the published k_cat/K_M in
`results/affinity/hg_series_kinetics.json`, and answers one question: does the ladder
move when real catalysis moves by 1060-fold?

Transition-state theory makes k_cat/K_M a transition-state affinity, so a 1060-fold
spread is ddG = R*T*ln(1060) = 4.13 kcal/mol of transition-state stabilisation. The
ladder should show that, both in the TS leg and in ddG(substrate - TS).
"""

from __future__ import annotations

import json
import math
import statistics
from dataclasses import dataclass, field
from pathlib import Path

from kemp.config import parse
from kemp.ligands import KCAL_PER_LOG10, LIGANDS, REFERENCE
from kemp.paths import RESULTS
from kemp.run import start_run


@dataclass
class Config:
    name: str = "ladder-vs-kinetics"
    runs: str = str(RESULTS / "affinity" / "runs")
    kinetics: str = str(RESULTS / "affinity" / "hg_series_kinetics.json")
    arms: list[str] = field(default_factory=lambda: ["hg3", "hg37", "hg317"])
    variants: list[str] = field(default_factory=lambda: ["HG3", "HG3.7", "HG3.17"])


def load_arm(d: Path, label: str) -> dict[str, list[float]]:
    vals: dict[str, list[float]] = {}
    for path in sorted(d.glob("affinity_*.json")):
        stem = path.stem[len("affinity_") :]
        head, _, seed = stem.rpartition("_s")
        lig = next((k for k in LIGANDS if head.endswith("_" + k) or head == k), None)
        if lig is None or not seed.isdigit():
            continue
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        vals.setdefault(lig, []).append(data["affinity_pred_value"])
    return vals


def msd(xs: list[float]) -> tuple[float, float, float]:
    sd = statistics.stdev(xs) if len(xs) > 1 else 0.0
    return statistics.fmean(xs), sd, sd / math.sqrt(len(xs))


def main(cfg: Config) -> None:
    run = start_run(cfg.name, cfg)
    kin = json.loads(Path(cfg.kinetics).read_text(encoding="utf-8-sig"))["variants"]
    rows = []
    for arm, variant in zip(cfg.arms, cfg.variants, strict=True):
        vals = load_arm(Path(cfg.runs) / arm, arm)
        missing = [lig for lig in LIGANDS if lig not in vals]
        if missing:
            raise SystemExit(f"{arm}: missing predictions for {missing}")
        ts_m, ts_sd, ts_sem = msd(vals[REFERENCE])
        sub_m, sub_sd, sub_sem = msd(vals["substrate"])
        prod_m, prod_sd, prod_sem = msd(vals["product"])
        eff = kin[variant]["kcat_over_KM_M1s1"]["value"]
        rows.append(
            {
                "variant": variant,
                "kcat_over_KM": eff,
                "log10_eff": math.log10(eff),
                "ts_mean": ts_m,
                "ts_sd": ts_sd,
                "ts_sem": ts_sem,
                "sub_mean": sub_m,
                "sub_sem": sub_sem,
                "prod_mean": prod_m,
                "prod_sem": prod_sem,
                "ddg_sub_minus_ts": KCAL_PER_LOG10 * (sub_m - ts_m),
                "ddg_sub_sem": KCAL_PER_LOG10 * math.hypot(sub_sem, ts_sem),
                "ddg_prod_minus_ts": KCAL_PER_LOG10 * (prod_m - ts_m),
                "ddg_prod_sem": KCAL_PER_LOG10 * math.hypot(prod_sem, ts_sem),
            }
        )

    lo, hi = rows[0], rows[-1]
    fold = hi["kcat_over_KM"] / lo["kcat_over_KM"]
    expected = KCAL_PER_LOG10 * (hi["log10_eff"] - lo["log10_eff"])
    obs_ddg = hi["ddg_sub_minus_ts"] - lo["ddg_sub_minus_ts"]
    obs_ddg_sem = math.hypot(hi["ddg_sub_sem"], lo["ddg_sub_sem"])
    obs_ts = KCAL_PER_LOG10 * (hi["ts_mean"] - lo["ts_mean"])
    obs_ts_sem = KCAL_PER_LOG10 * math.hypot(hi["ts_sem"], lo["ts_sem"])

    out = []
    out.append(
        "| variant | k_cat/K_M (M-1 s-1) | TS leg log10(IC50/uM) | "
        "ddG(sub-TS) kcal/mol | ddG(prod-TS) kcal/mol |"
    )
    out.append("|---|---|---|---|---|")
    for r in rows:
        out.append(
            "| %s | %s | %.3f +- %.3f | %+.3f +- %.3f | %+.3f +- %.3f |"
            % (
                r["variant"],
                f"{r['kcat_over_KM']:,}",
                r["ts_mean"],
                r["ts_sd"],
                r["ddg_sub_minus_ts"],
                r["ddg_sub_sem"],
                r["ddg_prod_minus_ts"],
                r["ddg_prod_sem"],
            )
        )
    out.append("")
    out.append(f"{lo['variant']} -> {hi['variant']}: measured {fold:,.0f}-fold in k_cat/K_M")
    out.append(f"  EXPECTED ddG shift            : {expected:+.3f} kcal/mol")
    out.append(
        f"  OBSERVED ddG(sub-TS) shift    : {obs_ddg:+.3f} +- {obs_ddg_sem:.3f} "
        f"({100 * obs_ddg / expected:.1f}% of expected, {abs(obs_ddg) / obs_ddg_sem:.1f} sigma)"
    )
    out.append(
        f"  OBSERVED TS-leg shift         : {obs_ts:+.3f} +- {obs_ts_sem:.3f} "
        f"({100 * obs_ts / -expected:.2f}% of expected, {abs(obs_ts) / obs_ts_sem:.1f} sigma)"
    )
    out.append("")
    order_ok = all(
        rows[i]["ddg_sub_minus_ts"] < rows[i + 1]["ddg_sub_minus_ts"] for i in range(len(rows) - 1)
    )
    out.append(f"  rank order of ddG(sub-TS) matches activity order : {order_ok}")
    signs = [r["ddg_sub_minus_ts"] > 0 for r in rows]
    out.append(f"  ddG(sub-TS) positive (catalytically correct sign) : {signs}")
    print("\n".join(out))
    (run.dir / "comparison.md").write_text("\n".join(out) + "\n", encoding="utf-8")

    run.finish(
        ok=True,
        rows=rows,
        fold_change=fold,
        expected_ddg_kcal=expected,
        observed_ddg_sub_minus_ts_kcal=obs_ddg,
        observed_ddg_sem=obs_ddg_sem,
        fraction_of_expected=obs_ddg / expected,
        observed_ts_leg_shift_kcal=obs_ts,
        ts_leg_fraction_of_expected=obs_ts / -expected,
        rank_order_matches=order_ok,
        ddg_sign_correct=signs,
    )


if __name__ == "__main__":
    main(parse(Config))
