"""Screen every tracked cluster `summary.json` against the stage-3 gates — no GPU.

    uv run python scripts/31_screen_summaries.py
    uv run python scripts/31_screen_summaries.py --min_plddt=80 --donor_hi=3.4

Every design the team has ever run is tracked in `results/*summary.json`. Replaying the
gates over them costs nothing and answers two questions a GPU run cannot:

  * what pass rate should we expect before committing ~23 min/design of shared node time?
  * which gate is actually binding, i.e. which one is doing the rejecting?

Threshold provenance and status: `wiki/design-filters.md`.
"""

from __future__ import annotations

import glob
import json
from dataclasses import dataclass
from pathlib import Path

from kemp.config import parse
from kemp.paths import ROOT
from kemp.run import start_run


@dataclass
class Config:
    name: str = "screen"
    pattern: str = "results/*summary.json"
    min_plddt: float = 80.0  # gate; 85 is the target, see wiki/design-filters.md
    min_iptm: float = 0.6
    base_lo: float = 2.4
    base_hi: float = 3.6
    donor_lo: float = 2.6
    donor_hi: float = 3.4
    max_ca_rmsd: float = 2.0


def screen(summary: dict, cfg: Config) -> dict | None:
    boltz = summary.get("boltz") or {}
    conf = boltz.get("confidence") or {}
    contacts = boltz.get("contacts_angstrom") or {}
    if not conf:
        return None  # not a completed cofold run
    plddt = float(conf.get("complex_plddt", 0.0))
    plddt = plddt * 100.0 if plddt <= 1.0 else plddt
    iptm = float(conf.get("iptm", 0.0))
    base = contacts.get("A127_OD2_to_6NT_N3")
    donor = contacts.get("A50_NE2_to_6NT_N1")
    ca = boltz.get("backbone_ca_rmsd_from_rfd3_angstrom")
    gates = {
        "plddt": plddt >= cfg.min_plddt,
        "iptm": iptm >= cfg.min_iptm,
        "folded": ca is not None and ca <= cfg.max_ca_rmsd,
        "base": base is not None and cfg.base_lo <= base <= cfg.base_hi,
        "donor": donor is not None and cfg.donor_lo <= donor <= cfg.donor_hi,
    }
    return {
        "plddt": round(plddt, 1),
        "iptm": round(iptm, 3),
        "base": round(base, 2) if base is not None else None,
        "donor": round(donor, 2) if donor is not None else None,
        "ca": round(ca, 2) if ca is not None else None,
        "gates": gates,
        "passed": all(gates.values()),
    }


def main(cfg: Config) -> None:
    run = start_run(cfg.name, cfg)
    rows = []
    for path in sorted(glob.glob(str(ROOT / cfg.pattern))):
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8-sig"))
        except (json.JSONDecodeError, OSError) as exc:
            print(f"  skipping {Path(path).name}: {exc}")
            continue
        res = screen(data, cfg)
        if res is None:
            continue
        res["design"] = Path(path).stem.replace("_summary", "")
        rows.append(res)

    if not rows:
        raise SystemExit(f"no completed cofold summaries matched {cfg.pattern}")

    hdr = "%-32s %6s %6s %7s %7s %6s  %s" % (
        "design",
        "pLDDT",
        "ipTM",
        "base",
        "donor",
        "CA",
        "failing gate(s)",
    )
    print(hdr)
    print("-" * len(hdr))
    binding: dict[str, int] = {}
    for r in sorted(rows, key=lambda x: x["design"]):
        bad = [k for k, ok in r["gates"].items() if not ok]
        for k in bad:
            binding[k] = binding.get(k, 0) + 1
        print(
            "%-32s %6.1f %6.3f %7s %7s %6s  %s"
            % (
                r["design"],
                r["plddt"],
                r["iptm"],
                r["base"],
                r["donor"],
                r["ca"],
                "PASS" if r["passed"] else ", ".join(bad),
            )
        )

    n_pass = sum(r["passed"] for r in rows)
    print(f"\n{n_pass}/{len(rows)} pass all gates")
    if binding:
        print(
            "most binding gate(s): "
            + ", ".join(f"{k} ({v}/{len(rows)})" for k, v in sorted(binding.items(), key=lambda kv: -kv[1]))
        )
    if n_pass:
        print(
            f"expected cost ~{len(rows) / n_pass:.0f} designs per hit "
            f"(~{23 * len(rows) / n_pass:.0f} min of serial node time)"
        )
    else:
        print(
            f"no hits in {len(rows)} designs: expected cost is > {23 * len(rows)} min "
            f"per hit, and may be unbounded at these thresholds"
        )
    run.finish(ok=True, n=len(rows), passed=n_pass, binding=binding, rows=rows)


if __name__ == "__main__":
    main(parse(Config))
