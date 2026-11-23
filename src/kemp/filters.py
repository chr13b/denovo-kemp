"""Filters for the RFdiffusion -> LigandMPNN -> Boltz-2 design funnel.

Every filter returns a `FilterResult`, which has three states, not two:

    passed=True   the design met the threshold
    passed=False  the design failed it
    passed=None   the filter COULD NOT BE EVALUATED (missing file, missing atom,
                  tool output absent). This is deliberately not False: "we did not
                  measure it" must never be recorded as "it failed", and a design
                  must never be reported as passing a filter that never ran.

Two halves, split by dependency so the sequence half runs anywhere:

  * sequence / score filters  - standard library only
  * structure filters         - numpy + biotite

Honest substitutions, because the cluster has neither tool:
  * **DSSP/stride are not installed anywhere.** `secondary_structure()` uses biotite's
    `annotate_sse` (the P-SEA algorithm, CA-geometry based). It agrees with DSSP on
    most helices and sheets but is not DSSP; do not report it as DSSP.
  * **Rosetta is not available.** `packing_density()` is a neighbour-count proxy for
    core packing, NOT PackStat, and is labelled as such everywhere it appears.
  * `ramachandran_outliers()` uses coarse favoured regions, not MolProbity contours.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

# --------------------------------------------------------------------------- result


@dataclass
class FilterResult:
    """One filter applied to one design."""

    name: str
    passed: bool | None  # None = could not evaluate (see module docstring)
    value: Any = None
    threshold: Any = None
    reason: str = ""
    extra: dict = field(default_factory=dict)

    def as_dict(self) -> dict:
        return asdict(self)


def _ok(name, value, threshold, passed, reason="", **extra) -> FilterResult:
    return FilterResult(name, passed, value, threshold, reason, extra)


def unevaluated(name: str, reason: str, threshold: Any = None) -> FilterResult:
    """A filter that could not run. Never counts as a pass."""
    return FilterResult(name, None, None, threshold, reason)


def all_passed(results: list[FilterResult]) -> bool:
    """True only if every filter was evaluated AND passed. None blocks the gate."""
    return bool(results) and all(r.passed is True for r in results)


def failures(results: list[FilterResult]) -> list[str]:
    out = []
    for r in results:
        if r.passed is False:
            out.append(f"{r.name}: {r.reason or r.value}")
        elif r.passed is None:
            out.append(f"{r.name}: NOT EVALUATED ({r.reason})")
    return out


# ------------------------------------------------------------------- sequence tables

# Kyte & Doolittle, J Mol Biol 157:105-132 (1982), table 2.
KD_HYDROPATHY = {
    "A": 1.8,
    "R": -4.5,
    "N": -3.5,
    "D": -3.5,
    "C": 2.5,
    "Q": -3.5,
    "E": -3.5,
    "G": -0.4,
    "H": -3.2,
    "I": 4.5,
    "L": 3.8,
    "K": -3.9,
    "M": 1.9,
    "F": 2.8,
    "P": -1.6,
    "S": -0.8,
    "T": -0.7,
    "W": -0.9,
    "Y": -1.3,
    "V": 4.2,
}

# EMBOSS/pepstats pKa set.
#
# Cross-checked against Biopython 1.84 on four real sequences (2026-11-21):
#   GRAVY  - EXACT agreement to 4 decimal places on all four.
#   pI     - ours reads 0.08-0.24 units LOWER, systematically.
# That is not a bug in either: Biopython's IsoelectricPoint defaults to the
# **Bjellqvist** set (Nterm 7.5, K 10.0, R 12.0, H 5.98, Cterm 3.55, D 4.05,
# E 4.45, C 9.0, Y 10.0), which is a different published convention from EMBOSS.
# Both are standard; quote which one you used. The offset is far smaller than the
# pI window this module gates on, so it does not change any verdict.
PKA_SIDECHAIN_POS = {"K": 10.8, "R": 12.5, "H": 6.5}
PKA_SIDECHAIN_NEG = {"D": 3.9, "E": 4.1, "C": 8.5, "Y": 10.1}
PKA_N_TERM = 8.6
PKA_C_TERM = 3.6

# residues we never want introduced into a catalytic pocket
REACTIVE_IN_POCKET = ("C",)


def gravy(sequence: str) -> float:
    """Grand average of hydropathy (Kyte-Doolittle mean over all residues)."""
    seq = sequence.strip().upper()
    if not seq:
        raise ValueError("empty sequence")
    unknown = sorted(set(seq) - set(KD_HYDROPATHY))
    if unknown:
        raise ValueError(f"non-standard residues in sequence: {unknown}")
    return sum(KD_HYDROPATHY[a] for a in seq) / len(seq)


def _net_charge(seq: str, ph: float) -> float:
    """Net charge at a given pH (Henderson-Hasselbalch over ionisable groups)."""
    charge = 1.0 / (1.0 + 10 ** (ph - PKA_N_TERM))
    charge -= 1.0 / (1.0 + 10 ** (PKA_C_TERM - ph))
    for aa, pka in PKA_SIDECHAIN_POS.items():
        charge += seq.count(aa) / (1.0 + 10 ** (ph - pka))
    for aa, pka in PKA_SIDECHAIN_NEG.items():
        charge -= seq.count(aa) / (1.0 + 10 ** (pka - ph))
    return charge


def isoelectric_point(sequence: str, tol: float = 1e-4) -> float:
    """pH at which net charge is zero, by bisection on [0, 14]."""
    seq = sequence.strip().upper()
    if not seq:
        raise ValueError("empty sequence")
    lo, hi = 0.0, 14.0
    for _ in range(200):
        mid = (lo + hi) / 2
        c = _net_charge(seq, mid)
        if abs(c) < tol or (hi - lo) < tol:
            return mid
        if c > 0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


# --------------------------------------------------------------- sequence filters


def check_gravy(sequence: str, lo: float = -1.0, hi: float = 0.3) -> FilterResult:
    """Reject extreme hydrophobicity/hydrophilicity.

    Soluble globular proteins sit around -0.5 to 0.0. A strongly positive GRAVY
    usually means an aggregation-prone or membrane-like design.
    """
    try:
        g = gravy(sequence)
    except ValueError as exc:
        return unevaluated("gravy", str(exc), (lo, hi))
    passed = lo <= g <= hi
    return _ok(
        "gravy", round(g, 4), (lo, hi), passed, "" if passed else f"GRAVY {g:.3f} outside [{lo}, {hi}]"
    )


def check_isoelectric_point(sequence: str, lo: float = 4.0, hi: float = 9.5) -> FilterResult:
    """Flag designs whose pI sits near the assay pH (poor solubility there).

    The Kemp assay runs at pH 7.0, so a pI very close to 7 is worth knowing about;
    the default window is deliberately wide and is a warning band, not physics.
    """
    try:
        pi = isoelectric_point(sequence)
    except ValueError as exc:
        return unevaluated("isoelectric_point", str(exc), (lo, hi))
    passed = lo <= pi <= hi
    return _ok(
        "isoelectric_point",
        round(pi, 3),
        (lo, hi),
        passed,
        "" if passed else f"pI {pi:.2f} outside [{lo}, {hi}]",
    )


def check_catalytic_residues(sequence: str, expected: dict[int, str]) -> FilterResult:
    """Did inverse design keep the catalytic residues? `expected` is 1-based {pos: aa}."""
    if not expected:
        return unevaluated("catalytic_residues", "no expected residues given")
    wrong = {}
    for pos, aa in expected.items():
        if not 1 <= pos <= len(sequence):
            return unevaluated("catalytic_residues", f"position {pos} outside sequence")
        got = sequence[pos - 1]
        if got != aa:
            wrong[pos] = f"{aa}->{got}"
    return _ok(
        "catalytic_residues",
        wrong or "intact",
        expected,
        not wrong,
        "" if not wrong else f"catalytic residues mutated: {wrong}",
    )


def check_no_reactive_in_pocket(
    sequence: str, pocket_positions: list[int], reactive: tuple[str, ...] = REACTIVE_IN_POCKET
) -> FilterResult:
    """Reject unwanted reactive side chains (default: Cys) at pocket positions."""
    if not pocket_positions:
        return unevaluated("reactive_in_pocket", "no pocket positions given")
    found = {
        p: sequence[p - 1]
        for p in pocket_positions
        if 1 <= p <= len(sequence) and sequence[p - 1] in reactive
    }
    return _ok(
        "reactive_in_pocket",
        found or "none",
        list(reactive),
        not found,
        "" if not found else f"reactive residues in pocket: {found}",
    )


# ------------------------------------------------------------------ score parsing


def parse_ligandmpnn_fasta(path: str | Path) -> list[dict]:
    """Parse a LigandMPNN output FASTA into records.

    LigandMPNN writes `>id, T=0.1, seed=1, overall_confidence=0.42, ligand_confidence=0.44,
    seq_rec=0.30` style headers. Numeric fields are converted; unknown fields are kept
    as strings rather than dropped.
    """
    text = Path(path).read_text(encoding="utf-8-sig")
    records: list[dict] = []
    header, seq_parts = None, []

    def flush():
        if header is None:
            return
        rec: dict[str, Any] = {"header": header, "sequence": "".join(seq_parts)}
        for field_ in header.split(","):
            if "=" not in field_:
                continue
            k, _, v = field_.partition("=")
            k, v = k.strip(), v.strip()
            try:
                rec[k] = float(v)
            except ValueError:
                rec[k] = v
        records.append(rec)

    for line in text.splitlines():
        if line.startswith(">"):
            flush()
            header, seq_parts = line[1:].strip(), []
        elif line.strip():
            seq_parts.append(line.strip())
    flush()
    return records


def check_mpnn_score(record: dict, min_overall: float = 0.35, min_ligand: float = 0.35) -> FilterResult:
    """Gate on LigandMPNN confidences.

    `overall_confidence` is global; `ligand_confidence` is the ligand-aware (local,
    active-site) term and is the one that matters for a catalytic pocket. If
    LigandMPNN was not asked to emit per-residue probabilities there is no finer
    local score available - this reports unevaluated rather than inventing one.
    """
    overall = record.get("overall_confidence")
    local = record.get("ligand_confidence")
    if overall is None and local is None:
        return unevaluated("mpnn_score", "no confidence fields in the FASTA header")
    missing = [n for n, v in (("overall", overall), ("ligand", local)) if v is None]
    if missing:
        return unevaluated("mpnn_score", f"missing {missing} in header")
    passed = overall >= min_overall and local >= min_ligand
    return _ok(
        "mpnn_score",
        {"overall": overall, "ligand": local},
        {"overall": min_overall, "ligand": min_ligand},
        passed,
        "" if passed else f"overall {overall:.3f} / ligand {local:.3f} below threshold",
    )


def parse_boltz_confidence(path: str | Path) -> dict:
    """Read a Boltz-2 `confidence_*.json`."""
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def _as_plddt_percent(value: float) -> float:
    """Boltz reports pLDDT in 0-1; most thresholds are quoted on 0-100. Normalise."""
    return value * 100.0 if value <= 1.0 else value


def check_interface_error(confidence: dict, max_ipde: float = 2.0) -> FilterResult:
    """Criterion 3 of the organizers' five: **iPDE**, lower is better.

    This is THE confidence term that is actually scored:

        "Interface confidence (iPDE). The mean predicted distance error over the
         protein-ligand interface of the cofolded complex. Lower is better."

    pLDDT and ipTM are NOT on the organizers' list, and they disagree with iPDE in
    practice: zonghu-03's `vA_s2` scores pLDDT 86.1 (comfortably "good") while its
    iPDE is 2.42, which ranks 10th of 14 designs. Gate on this, not on pLDDT.

    Default 2.0 comes from the observed split: designs whose ligand stayed in the
    site cluster at 1.39-1.75, collapsed ones at 3.3-6.7.
    """
    ipde = confidence.get("complex_ipde")
    if ipde is None:
        return unevaluated("interface_error_ipde", "complex_ipde missing", max_ipde)
    ipde = float(ipde)
    passed = ipde <= max_ipde
    return _ok(
        "interface_error_ipde",
        round(ipde, 4),
        max_ipde,
        passed,
        "" if passed else f"iPDE {ipde:.3f} > {max_ipde} (interface poorly determined)",
    )


def check_boltz_confidence(confidence: dict, min_plddt: float = 85.0, min_iptm: float = 0.6) -> FilterResult:
    """Gate on mean pLDDT and ipTM. **Not a scored criterion** - see check_interface_error.

    Kept because fold quality is still worth knowing, but it must not be the gate:
    neither pLDDT nor ipTM appears in the organizers' five criteria.
    """
    plddt = confidence.get("complex_plddt")
    iptm = confidence.get("iptm", confidence.get("ligand_iptm"))
    if plddt is None:
        return unevaluated(
            "boltz_confidence", "complex_plddt missing", {"plddt": min_plddt, "iptm": min_iptm}
        )
    plddt = _as_plddt_percent(float(plddt))
    checks = {"complex_plddt": plddt}
    passed = plddt >= min_plddt
    reason = "" if passed else f"mean pLDDT {plddt:.1f} < {min_plddt}"
    if iptm is not None:
        checks["iptm"] = float(iptm)
        if float(iptm) < min_iptm:
            passed = False
            reason = (reason + "; " if reason else "") + f"ipTM {float(iptm):.3f} < {min_iptm}"
    return _ok("boltz_confidence", checks, {"plddt": min_plddt, "iptm": min_iptm}, passed, reason)


def parse_rfd3_index_map(path: str | Path) -> dict[str, str]:
    """RFD3 metadata JSON -> {original motif id: id in the generated chain}."""
    data = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    mapping = data.get("diffused_index_map", {})
    return mapping if isinstance(mapping, dict) else {}


_RESID_RE = re.compile(r"^([A-Za-z]+)(-?\d+)$")


def split_residue_id(token: str) -> tuple[str, int]:
    """'A127' -> ('A', 127). Raises ValueError on anything else."""
    m = _RESID_RE.match(token.strip())
    if not m:
        raise ValueError(f"cannot parse residue id {token!r}")
    return m.group(1), int(m.group(2))
