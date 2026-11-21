"""Compare RFD3 design geometry against the Boltz-2 refold, across runs (experiment chris-02).

    uv run python scripts/30_compare_rfd3_vs_boltz.py
    uv run python scripts/30_compare_rfd3_vs_boltz.py --threshold=1.5

Reads the tracked `results/*_summary.json` files, builds the per-run table, and applies the
decision rule written down in wiki/experiments/chris-02_... *before* the runs finished:

    >= 3 of 4 new runs with base drift > threshold  -> drift is systematic
    <= 1 of 4                                       -> the baseline was an outlier
    otherwise                                       -> inconclusive

Scoring happens on the Boltz-2 cofold, so "drift" is how far the scored structure moves away from
the motif geometry RFD3 was handed.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from kemp.config import parse
from kemp.paths import RESULTS
from kemp.run import start_run

BASE_ATOM = "_6NT_N3"  # the atom the catalytic base attacks
DONOR_ATOM = "_6NT_N1"  # the atom the oxyanion-hole donor stabilises


@dataclass
class Config:
    name: str = "chris-02"
    seed: int = 0
    baseline: str = "reference_kemp-1_summary.json"  # the shared example; not one of the 4 new runs
    pattern: str = "sweep_kemp-*_summary.json"  # the new runs
    threshold: float = 1.5  # angstrom of base drift that counts as "drifted"


def _contact(contacts: dict, suffix: str) -> float | None:
    """Distance for the one contact ending in `suffix`. Keys carry the original motif numbering."""
    hits = [v for k, v in contacts.items() if k.endswith(suffix)]
    return float(hits[0]) if len(hits) == 1 else None


def read_run(path) -> dict:
    data = json.loads(path.read_text())
    rfd3, boltz = data.get("rfd3", {}), data.get("boltz", {})
    conf = boltz.get("confidence", {})
    row = {
        "run": path.name.replace("_summary.json", ""),
        "base_rfd3": _contact(rfd3.get("contacts_angstrom", {}), BASE_ATOM),
        "base_boltz": _contact(boltz.get("contacts_angstrom", {}), BASE_ATOM),
        "donor_rfd3": _contact(rfd3.get("contacts_angstrom", {}), DONOR_ATOM),
        "donor_boltz": _contact(boltz.get("contacts_angstrom", {}), DONOR_ATOM),
        "ipde": conf.get("complex_ipde"),
        "iptm": conf.get("iptm"),
        "ca_rmsd": boltz.get("backbone_ca_rmsd_from_rfd3_angstrom"),
        "warnings": len(data.get("validation_warnings", [])),
        "length": len(data.get("ligandmpnn", {}).get("sequence", "")),
    }
    for a, b, name in (("base_rfd3", "base_boltz", "d_base"), ("donor_rfd3", "donor_boltz", "d_donor")):
        row[name] = None if row[a] is None or row[b] is None else row[b] - row[a]
    return row


def fmt(value: float | None, spec: str = "7.2f") -> str:
    return "      -" if value is None else format(value, spec)


def main(cfg: Config) -> None:
    run = start_run(cfg.name, cfg, seed=cfg.seed)

    rows = [read_run(p) for p in sorted(RESULTS.glob(cfg.pattern))]
    baseline_path = RESULTS / cfg.baseline
    baseline = read_run(baseline_path) if baseline_path.exists() else None

    header = (
        f"{'run':<28}{'base_rfd3':>10}{'base_boltz':>11}{'d_base':>8}"
        f"{'donor_boltz':>12}{'d_donor':>9}{'ipde':>8}{'ca_rmsd':>9}"
    )
    print(header)
    print("-" * len(header))
    for row in ([baseline] if baseline else []) + rows:
        tag = row["run"] + (" (baseline)" if baseline and row is baseline else "")
        print(
            f"{tag:<28}{fmt(row['base_rfd3'], '10.2f')}{fmt(row['base_boltz'], '11.2f')}"
            f"{fmt(row['d_base'], '+8.2f')}{fmt(row['donor_boltz'], '12.2f')}"
            f"{fmt(row['d_donor'], '+9.2f')}{fmt(row['ipde'], '8.4f')}{fmt(row['ca_rmsd'], '9.3f')}"
        )
        run.log(**row)

    # RFD3 contacts are held fixed by select_fixed_atoms, so they should be constant across designs.
    rfd3_base = {round(r["base_rfd3"], 3) for r in rows if r["base_rfd3"] is not None}
    constant = len(rfd3_base) == 1
    print(
        f"\nRFD3 base contact across the new runs: {sorted(rfd3_base)} "
        f"-> {'CONSTANT (fixed by construction, carries no information)' if constant else 'VARIES'}"
    )

    drifted = [r for r in rows if r["d_base"] is not None and r["d_base"] > cfg.threshold]
    n, k = len(rows), len(drifted)
    if n and k >= 3:
        verdict = "systematic: filter candidates on Boltz-2 geometry, not RFD3 geometry"
    elif n and k <= 1:
        verdict = "baseline was an outlier: RFD3 geometry may work as a cheap pre-filter"
    else:
        verdict = "inconclusive: do not build a filtering strategy on this yet"
    print(f"Decision rule: {k} of {n} new runs drifted > {cfg.threshold} A  ->  {verdict}")

    usable = [r for r in rows if r["ca_rmsd"] is not None and r["ca_rmsd"] < 2.0]
    print(f"Backbone self-consistency: {len(usable)} of {n} new runs refolded within 2.0 A CA RMSD")

    run.finish(
        n_runs=n,
        n_drifted=k,
        threshold=cfg.threshold,
        verdict=verdict,
        rfd3_base_constant=constant,
        n_self_consistent=len(usable),
    )
    print(f"\nrun directory: {run.dir}")


if __name__ == "__main__":
    main(parse(Config))
