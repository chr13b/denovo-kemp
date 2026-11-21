"""The Kemp reaction coordinate as three ligands, plus the affinity unit conversion.

Shared by `scripts/20_build_affinity_ladder.py` and `scripts/21_report_affinity_ladder.py`.

Catalysis by transition-state stabilisation means the enzyme binds the TS more tightly
than the substrate: k_cat/k_uncat ~ K_S / K_TS. So the quantity we want is how much
*worse* the substrate and the product bind than the TS analogue.

All three ligands were verified with RDKit (2026-11-21): identical molecular formula
mass **164.12 Da** and exactly **12 heavy atoms** each, and substrate -> product is a
true isomerisation (both C7H4N2O3). That matters: ligand size and molecular weight are
matched across the ladder, so neither Boltz-2's `--affinity_mw_correction` nor any
size-dependent bias can explain a difference between them.

`ts_analog` has the same InChIKey as the CCD component **6NT** that the organizers'
pipeline cofolds, so this ladder is comparable to our RFD3/Boltz runs.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

# kcal/mol per decade of IC50 at 298.15 K:  R * T * ln(10)
GAS_CONSTANT_KCAL = 0.0019872041  # kcal/(mol*K)
TEMPERATURE_K = 298.15
KCAL_PER_LOG10 = GAS_CONSTANT_KCAL * TEMPERATURE_K * math.log(10)  # 1.3642


@dataclass(frozen=True)
class Ligand:
    key: str
    smiles: str  # RDKit canonical
    name: str
    role: str
    inchikey: str


# Canonical SMILES as RDKit wrote them, so the strings in the YAML are reproducible.
LIGANDS: dict[str, Ligand] = {
    "substrate": Ligand(
        key="substrate",
        smiles="O=[N+]([O-])c1ccc2oncc2c1",
        name="5-nitrobenzisoxazole",
        role="substrate (the C3-H that the base abstracts)",
        inchikey="TWOYWCWKYDYTIP-UHFFFAOYSA-N",
    ),
    "ts_analog": Ligand(
        key="ts_analog",
        smiles="O=[N+]([O-])c1ccc2nn[nH]c2c1",
        name="6-nitrobenzotriazole",
        role="transition-state analogue; same InChIKey as CCD 6NT",
        inchikey="AOCDQWRMYHJTMY-UHFFFAOYSA-N",
    ),
    "product": Ligand(
        key="product",
        smiles="N#Cc1cc([N+](=O)[O-])ccc1O",
        name="2-cyano-4-nitrophenol",
        role="product (phenol form of the phenolate released)",
        inchikey="MPQNPFJBRPRBFF-UHFFFAOYSA-N",
    ),
}

REFERENCE = "ts_analog"  # everything is measured relative to the TS analogue
LADDER = ("substrate", "ts_analog", "product")


def pseudo_dg_kcal(affinity_pred_value: float) -> float:
    """Boltz-2 `affinity_pred_value` -> a pseudo binding free energy in kcal/mol.

    `affinity_pred_value` is log10(IC50) with IC50 in micromolar, so
    log10(IC50 in M) = value - 6 and dG = R*T*ln(10) * (value - 6).

    This is a *pseudo* dG: IC50 is not Kd, and Boltz-2 regresses a value trained on
    heterogeneous assay data. Use it for comparisons within one ladder, never as an
    absolute binding energy.
    """
    return KCAL_PER_LOG10 * (affinity_pred_value - 6.0)


def ddg_kcal(value: float, reference_value: float) -> float:
    """dG(ligand) - dG(reference), in kcal/mol. The micromolar offset cancels.

    Positive means the ligand binds *more weakly* than the reference. With the TS
    analogue as reference, positive is the catalytically desirable direction for both
    the substrate (TS stabilised relative to the ground state) and the product
    (product released rather than inhibiting).
    """
    return KCAL_PER_LOG10 * (value - reference_value)
