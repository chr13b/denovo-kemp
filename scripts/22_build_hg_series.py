"""Build the HG-series Kemp eliminase sequences from published mutation lists, for
validating the affinity ladder against real measured catalytic efficiencies.

    uv run python scripts/22_build_hg_series.py
    uv run python scripts/22_build_hg_series.py --variants=['HG3','HG3.7','HG3.17']

Writes one FASTA per variant into results/affinity/ plus `hg_series_kinetics.json`.

Every variant is built from the 7K4U chain-A sequence (HG3 K50Q) by applying the
mutations in Table 1 of Broom et al. The "from" residue of EVERY mutation is asserted
against the base sequence first, so a numbering or construct mismatch fails loudly
instead of silently producing a wrong sequence.

Source of the kinetics and the mutation lists, read from the PDF (not from memory):
  Broom, Rakotoharisoa, Thompson, Zarifi, Nguyen, Mukhametzhanov, Liu, Fraser & Chica,
  "Evolution of an enzyme conformational ensemble guides design of an efficient
  biocatalyst", bioRxiv 2020.03.19.999235, Table 1 (page 25).
  Published as Nat. Commun. 11, 4808 (2020), doi 10.1038/s41467-020-18619-x.

Table 1 footnote b, verbatim: "Individual parameters KM and kcat could not be determined
accurately because saturation was not possible at the maximum substrate concentration
tested (2 mM)." So for this series **only kcat/KM exists** - there is no published KM,
i.e. no experimental substrate-binding constant to validate against. See
`wiki/affinity-ladder.md`.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from kemp.config import parse
from kemp.paths import RESULTS
from kemp.run import start_run

# 7K4U chain A = "Kemp Eliminase HG3 K50Q in complex with 6NT"; RCSB lists Mutation(s): 1,
# so reverting Q50K recovers HG3 itself. First residue in the PDB is numbered -2.
BASE_FASTA = RESULTS / "affinity" / "hg3_k50q_7k4u_chainA.fasta"
FIRST_RESI = -2

# Table 1, column "Mutations from HG3". Italics in the paper marked design positions;
# that formatting carries no sequence meaning and is not reproduced here.
MUTATIONS: dict[str, str] = {
    "HG3": "",
    "HG3.3b": "V6I K50H M84C S89R Q90D A125N",
    "HG3.7": "V6I Q37K K50Q M84C S89R Q90H A125N",
    "HG3.14": "V6I Q37K K50Q G82A M84C Q90H T105I A125T T142N T208M T279S D300N",
    "HG3.17": (
        "V6I Q37K N47E K50Q G82A M84C S89N Q90F T105I A125T T142N T208M F267M W275A R276F T279S D300N"
    ),
    "HG4": "K50Q G82A M84C Q90F A125T F267M W275A R276F",
}

# Table 1, column "kcat/KM (M^-1 s^-1)". `blomberg` = the value in parentheses, which the
# footnote attributes to Blomberg et al. (ref 15) - a DIFFERENT lab's measurement of the
# same enzyme, kept because the disagreement is itself informative.
KCAT_OVER_KM: dict[str, dict] = {
    "HG3": {"value": 160, "sd": 10, "blomberg": 1300},
    "HG3.3b": {"value": 2300, "sd": 800, "blomberg": 5400},
    "HG3.7": {"value": 28000, "sd": 4000, "blomberg": 37000},
    "HG3.14": {"value": 55000, "sd": 4000, "blomberg": 70000},
    "HG3.17": {"value": 170000, "sd": 20000, "blomberg": 230000},
    "HG4": {"value": 120000, "sd": 10000, "blomberg": None},
}

ASSAY = {
    "substrate": "5-nitrobenzisoxazole",
    "note_km_kcat": (
        "Table 1 footnote b: individual KM and kcat could not be determined accurately "
        "because saturation was not possible at the maximum substrate concentration "
        "tested (2 mM). Only kcat/KM is reported for this series."
    ),
    "replicates": "triplicate, enzymes from at least two independent preparations (mean +- s.d.)",
    "citation": (
        "Broom et al., bioRxiv 2020.03.19.999235, Table 1 (p25); "
        "published Nat. Commun. 11, 4808 (2020), doi 10.1038/s41467-020-18619-x"
    ),
    "related_structures": {
        "HG2": "3NYD",
        "HG3.17-E47N/N300D": "4BS0",
        "HG3 K50Q + 6NT (base sequence used here)": "7K4U",
        "Thermoascus aurantiacus xylanase 10A (parent scaffold)": "1GOR",
    },
}


@dataclass
class Config:
    name: str = "hg-series"
    variants: list[str] = field(default_factory=lambda: ["HG3", "HG3.7", "HG3.17"])
    out_dir: str = str(RESULTS / "affinity")


def read_base() -> str:
    lines = BASE_FASTA.read_text(encoding="utf-8-sig").splitlines()
    return "".join(ln.strip() for ln in lines if ln.strip() and not ln.startswith(">"))


def apply_mutations(base: str, spec: str, label: str) -> tuple[str, list[str]]:
    """Apply "V6I Q37K ..." to `base`, asserting each wild-type residue first."""
    seq = list(base)
    applied = []
    for token in spec.split():
        frm, to = token[0], token[-1]
        resi = int(token[1:-1])
        idx = resi - FIRST_RESI
        if not 0 <= idx < len(seq):
            raise SystemExit(f"{label}: residue {resi} is outside the sequence")
        if seq[idx] != frm:
            raise SystemExit(
                f"{label}: expected {frm} at residue {resi} (index {idx}) but found "
                f"{seq[idx]!r}. The base sequence does not match the published "
                f"numbering - refusing to build a sequence that may be wrong."
            )
        seq[idx] = to
        applied.append(token)
    return "".join(seq), applied


def main(cfg: Config) -> None:
    unknown = [v for v in cfg.variants if v not in MUTATIONS]
    if unknown:
        raise SystemExit(f"unknown variant(s) {unknown}; valid: {list(MUTATIONS)}")
    run = start_run(cfg.name, cfg)
    out = Path(cfg.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    base_k50q = read_base()
    # 7K4U is HG3 K50Q, so revert that single mutation to recover HG3.
    hg3, _ = apply_mutations(base_k50q, "Q50K", "HG3 (reverting 7K4U K50Q)")
    print(f"base 7K4U chain A: {len(base_k50q)} aa; HG3 recovered by Q50K revert")

    record = {}
    for variant in cfg.variants:
        seq, applied = apply_mutations(hg3, MUTATIONS[variant], variant)
        # every variant must keep the catalytic base and the pi-stacking Trp
        for resi, expect, what in ((44, "W", "pi-stack Trp"), (127, "D", "catalytic base")):
            got = seq[resi - FIRST_RESI]
            if got != expect:
                raise SystemExit(f"{variant}: residue {resi} is {got}, expected {expect} ({what})")
        donor = seq[50 - FIRST_RESI]
        path = out / f"{variant.replace('.', '_').lower()}.fasta"
        header = (
            f">{variant} length={len(seq)} kcat_over_KM={KCAT_OVER_KM[variant]['value']}"
            f" M-1s-1 donor50={donor} (Broom et al. bioRxiv 2020.03.19.999235 Table 1)"
        )
        path.write_text(f"{header}\n{seq}\n", encoding="utf-8", newline="\n")
        record[variant] = {
            "fasta": str(path.relative_to(RESULTS.parent)),
            "length": len(seq),
            "mutations_from_hg3": applied,
            "n_mutations": len(applied),
            "residue50": donor,
            "kcat_over_KM_M1s1": KCAT_OVER_KM[variant],
        }
        print(
            f"  {variant:8s} {len(seq)} aa, {len(applied):2d} mutations, res50={donor}, "
            f"kcat/KM={KCAT_OVER_KM[variant]['value']:,} M-1s-1 -> {path.name}"
        )

    meta = {"assay": ASSAY, "base_structure": "7K4U chain A", "variants": record}
    (out / "hg_series_kinetics.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    print(f"\nwrote {out / 'hg_series_kinetics.json'}")
    run.finish(ok=True, variants=list(record), **{"kinetics": meta})


if __name__ == "__main__":
    main(parse(Config))
