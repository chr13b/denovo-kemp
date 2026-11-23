"""The scored criteria as pure functions: geometry measures and sub-scores.

This is the tested reference implementation. `scripts/36_score_v2_weighted.py`
carries its own copy of the same maths on purpose, because it runs on the cluster
where this package is not installed — if you change a function here, change it
there too. The duplication is deliberate and `tests/test_scoring.py` is what keeps
this version honest.

Every constant is measured or quoted, never guessed:

* contact targets come from 7K4U via `scripts/37_measure_crystal_reference.py`
* the weights come from the brief: "Geometry — items 1 and 2 together — outweighs
  everything else combined" and "[distances] carries the most weight of anything
  here"
* the asymmetry comes from "Too short is a clash and is penalised harder than the
  same error too long"

See `wiki/scoring.md` for provenance and the open question about the base target.
"""

from __future__ import annotations

import math

import numpy as np

# Measured in 7K4U (results/theozyme/theozyme_7k4u_core.pdb). The two contacts do
# NOT share a target: they differ by 0.66 A. `oop` is 180 - |dihedral|, i.e. the
# deviation from the triazole plane in degrees.
CRYSTAL = {
    "base": {"dist": 2.535, "angle": 167.6, "oop": 13.2},
    "donor": {"dist": 3.197, "angle": 164.9, "oop": 16.0},
}
TEXTBOOK_HBOND = (2.8, 3.0)

SIGMA_SHORT = 0.50  # A; too short is a clash
SIGMA_LONG = 1.20  # A; 2.4x more forgiving than too short
SIGMA_ANGLE = 35.0  # degrees, used for both the angle and the plane term

WEIGHTS = {
    "dist": 0.33,  # }- geometry, 0.55 > 0.45 for everything else combined
    "approach": 0.22,  # }
    "ipde": 0.15,
    "burial": 0.15,
    "consistency": 0.15,
}


def angle_between(a, b, c) -> float:
    """Angle a-b-c in degrees."""
    v1, v2 = np.asarray(a) - np.asarray(b), np.asarray(c) - np.asarray(b)
    cos = float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))
    return math.degrees(math.acos(max(-1.0, min(1.0, cos))))


def dihedral(p0, p1, p2, p3) -> float:
    """Signed torsion p0-p1-p2-p3 in degrees."""
    p0, p1, p2, p3 = (np.asarray(x, dtype=float) for x in (p0, p1, p2, p3))
    b0, b1, b2 = p0 - p1, p2 - p1, p3 - p2
    b1n = b1 / np.linalg.norm(b1)
    v = b0 - np.dot(b0, b1n) * b1n
    w = b2 - np.dot(b2, b1n) * b1n
    return math.degrees(math.atan2(float(np.dot(np.cross(b1n, v), w)), float(np.dot(v, w))))


def out_of_plane(p0, p1, p2, p3) -> float:
    """Deviation from the ring plane in degrees: 0 means exactly in plane.

    This is `180 - |dihedral|`, and the absolute value is the whole point. The
    dihedral's **sign** only says which side of the plane the contact leans to,
    and both sides are chemically the same approach. Comparing signed dihedrals
    against a signed reference punishes a mirror-image contact by up to 330
    degrees — a bug that zeroed the approach term for 14 of 16 designs before it
    was caught. See wiki/scoring.md.
    """
    return 180.0 - abs(dihedral(p0, p1, p2, p3))


def score_distance(d: float, target: float) -> float:
    """Asymmetric Gaussian around the crystal target; too short decays faster."""
    sigma = SIGMA_SHORT if d < target else SIGMA_LONG
    return math.exp(-(((d - target) / sigma) ** 2))


def score_angle(deviation_deg: float) -> float:
    """Used for both the approach angle and the plane term. Deviation, not value."""
    return math.exp(-((abs(deviation_deg) / SIGMA_ANGLE) ** 2))


def score_ipde(ipde: float) -> float:
    """Lower is better; 1.0 is effectively ideal, 5 is unusable."""
    return math.exp(-((max(0.0, ipde - 1.0) / 1.8) ** 2))


def score_burial(n_ca: int) -> float:
    """CA atoms within 12 A of the base, saturating at 50."""
    return max(0.0, min(1.0, (n_ca - 20.0) / 30.0))


def score_consistency(stds: list[float]) -> float | None:
    """Spread of the contact distances over replicate seeds; the worst one decides.

    A proxy for pre-organisation: if the pocket does not hold the ligand, repeated
    predictions disagree. 0.75 A of scatter scores about a half.
    """
    return math.exp(-((max(stds) / 0.75) ** 2)) if stds else None


def approach_deviation(measured: dict) -> tuple[float, str]:
    """Worst of the angle and plane deviations over both contacts.

    The brief is explicit that these "do not average — the worse of the two
    decides", so this returns a max and never a mean.
    """
    worst, what = 0.0, ""
    for contact in ("base", "donor"):
        if contact not in measured:
            continue
        for key, label in (("angle", "angle"), ("oop", "ring plane")):
            dev = abs(measured[contact][key] - CRYSTAL[contact][key])
            if dev > worst:
                worst, what = dev, f"{contact} {label}"
    return worst, what


def weighted_total(parts: dict[str, float | None]) -> float:
    """Weighted geometric mean over the terms that could be measured.

    A plain product cannot express "geometry outweighs everything else combined",
    so the weights are exponents. Terms that are `None` are dropped and the
    remaining weights renormalised — an unmeasured term neither rewards nor
    punishes, but totals with and without K5 are not directly comparable.
    """
    known = {k: v for k, v in parts.items() if v is not None}
    if not known:
        return 0.0
    wsum = sum(WEIGHTS[k] for k in known)
    return math.exp(sum(WEIGHTS[k] * math.log(max(v, 1e-9)) for k, v in known.items()) / wsum)
