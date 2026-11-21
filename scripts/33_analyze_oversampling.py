"""Analyse a sequence-oversampling sweep against the pre-registered decision rules.

Usage:
    uv run python scripts/33_analyze_oversampling.py results/oversample_*.tsv

Reads the `geometry.tsv` files written by `cluster/measure_boltz_outputs.py` (copy them into
results/ first) and answers the three questions chris-04/05/06 were registered to answer:

  1. The instrument check. What does Boltz-2 report for the NATURAL enzymes' own sequences?
     Everything else is uninterpretable until this number exists, because the target window was
     measured from crystal structures and the designs are measured with Boltz-2.

  2. Is the base drift sequence-level or backbone-level? One backbone, 72 sequences: if the
     spread is wide, sampling is the fix; if they all cluster, the backbone has a floor.

  3. Does CA RMSD predict base drift WITHIN one backbone, as it does across backbones?
     That is the feature a cheap filter would use.

Prints only numbers read from the files. No run directory is required because the measurement
step already did the structure reading; this script is pure analysis.
"""

import math
import sys
from pathlib import Path

# Measured across 26 engaged ligand copies from 23 crystal structures (scripts/32).
BASE_WINDOW = (2.41, 2.69)
DONOR_WINDOW = (2.92, 3.60)


def read_tsv(path):
    lines = path.read_text().splitlines()
    header = lines[0].split("\t")
    rows = []
    for line in lines[1:]:
        if not line.strip():
            continue
        values = line.split("\t")
        row = dict(zip(header, values, strict=False))
        for key, value in list(row.items()):
            if value == "":
                row[key] = None
                continue
            try:
                row[key] = float(value)
            except ValueError:
                pass
        rows.append(row)
    return rows


def number(row, key):
    value = row.get(key)
    return value if isinstance(value, float) and math.isfinite(value) else None


def contact(row, which):
    """The pinned measurement when available, else the numbering-agnostic scan."""
    return number(row, f"pinned_{which}") or number(row, f"scan_{which}")


def stats(values):
    values = sorted(v for v in values if v is not None)
    if not values:
        return None
    n = len(values)
    mean = sum(values) / n
    return {
        "n": n,
        "min": values[0],
        "median": values[n // 2],
        "max": values[-1],
        "mean": mean,
        "sd": math.sqrt(sum((v - mean) ** 2 for v in values) / n) if n > 1 else 0.0,
    }


def correlation(pairs):
    pairs = [(x, y) for x, y in pairs if x is not None and y is not None]
    if len(pairs) < 3:
        return None
    n = len(pairs)
    mx = sum(x for x, _ in pairs) / n
    my = sum(y for _, y in pairs) / n
    sxy = sum((x - mx) * (y - my) for x, y in pairs)
    sxx = sum((x - mx) ** 2 for x, _ in pairs)
    syy = sum((y - my) ** 2 for _, y in pairs)
    return sxy / math.sqrt(sxx * syy) if sxx > 0 and syy > 0 else None


paths = [Path(p) for p in sys.argv[1:]]
if not paths:
    sys.exit(__doc__)

for path in paths:
    if not path.is_file():
        print(f"!! missing: {path}")
        continue
    rows = read_tsv(path)
    measured = [r for r in rows if r.get("status") == "measured"]
    designs = [r for r in measured if r.get("kind") == "design"]
    controls = [r for r in measured if r.get("kind") == "control"]

    print("=" * 96)
    print(
        f"{path.name}: {len(rows)} queries, {len(measured)} measured "
        f"({len(designs)} designs, {len(controls)} controls)"
    )
    failed = [r for r in rows if r.get("status") not in ("measured", None)]
    if failed:
        print(f"  not measured: {len(failed)}")
        for row in failed[:5]:
            print(f"    {row.get('name')}: {row.get('status')}")

    # ---------------------------------------------------------------- 1. instrument check
    if controls:
        print("\n-- INSTRUMENT CHECK: natural enzymes, folded under the same conditions")
        print(
            f"   {'structure':<12}{'base':>8}{'donor':>8}   "
            f"{'nearest base':<18}{'nearest donor':<18}{'iptm':>7}"
        )
        for row in sorted(controls, key=lambda r: str(r.get("name"))):
            base, donor = contact(row, "base"), contact(row, "donor")
            print(
                f"   {str(row.get('name')):<12}"
                f"{base if base else float('nan'):>8.2f}{donor if donor else float('nan'):>8.2f}   "
                f"{str(row.get('scan_base_residue') or ''):<18}"
                f"{str(row.get('scan_donor_residue') or ''):<18}"
                f"{number(row, 'iptm') or float('nan'):>7.3f}"
            )
        control_bases = [contact(r, "base") for r in controls]
        inside = [b for b in control_bases if b and BASE_WINDOW[0] <= b <= BASE_WINDOW[1]]
        print(
            f"   crystal window {BASE_WINDOW[0]}-{BASE_WINDOW[1]} A: "
            f"{len(inside)} of {len(controls)} natural enzymes land inside it when FOLDED"
        )
        if not inside:
            best = stats(control_bases)
            if best:
                print(
                    "   >> Boltz-2 does NOT reproduce crystal geometry even for real enzymes "
                    f"(best {best['min']:.2f} A)."
                )
                print(
                    "   >> The target window must be recalibrated to what Boltz-2 reports for "
                    "working enzymes,"
                )
                print("   >> not to what the crystals show. Judge designs against THIS number.")
        else:
            print("   >> The window is reachable through Boltz-2. Designs outside it genuinely miss.")

    if not designs:
        continue

    # ---------------------------------------------------------------- 2. sequence vs backbone
    bases = [contact(r, "base") for r in designs]
    donors = [contact(r, "donor") for r in designs]
    rmsds = [number(r, "ca_rmsd") for r in designs]
    base_stats, donor_stats, rmsd_stats = stats(bases), stats(donors), stats(rmsds)
    print("\n-- DESIGNS: is the drift sequence-level or backbone-level?")
    for label, s in (("base contact", base_stats), ("donor contact", donor_stats), ("CA RMSD", rmsd_stats)):
        if s:
            print(
                f"   {label:<14} n={s['n']:<4} min {s['min']:6.2f}  median {s['median']:6.2f}  "
                f"max {s['max']:6.2f}  sd {s['sd']:5.2f}"
            )
    if base_stats:
        spread = base_stats["max"] - base_stats["min"]
        in_base = sum(1 for b in bases if b and BASE_WINDOW[0] <= b <= BASE_WINDOW[1])
        in_both = sum(
            1
            for r in designs
            if (
                lambda b, d: (
                    b
                    and d
                    and BASE_WINDOW[0] <= b <= BASE_WINDOW[1]
                    and DONOR_WINDOW[0] <= d <= DONOR_WINDOW[1]
                )
            )(contact(r, "base"), contact(r, "donor"))
        )
        print(f"   in base window:  {in_base}/{len(designs)}")
        print(f"   in BOTH windows: {in_both}/{len(designs)}")
        if in_base:
            print("   >> VERDICT: drift is SEQUENCE-level. Oversampling is the pipeline.")
        elif spread < 0.3:
            print(
                f"   >> VERDICT: drift is BACKBONE-level (spread only {spread:.2f} A). "
                "This backbone has a floor."
            )
        else:
            print(
                f"   >> VERDICT: partial. Spread {spread:.2f} A, best {base_stats['min']:.2f} A - "
                "sampling moves it but does not close the gap."
            )

    # ---------------------------------------------------------------- 3. per-temperature
    temperatures = sorted({number(r, "temperature") for r in designs} - {None})
    if len(temperatures) > 1:
        print("\n-- BY TEMPERATURE (does diversity help, or just break the fold?)")
        print(
            f"   {'T':>5}{'n':>5}{'best base':>11}{'median base':>13}"
            f"{'median RMSD':>13}{'folded<2A':>11}{'in window':>11}"
        )
        for temperature in temperatures:
            group = [r for r in designs if number(r, "temperature") == temperature]
            gb, gr = stats([contact(r, "base") for r in group]), stats([number(r, "ca_rmsd") for r in group])
            folded = sum(1 for r in group if (number(r, "ca_rmsd") or 99) < 2.0)
            inside = sum(
                1
                for r in group
                if (lambda b: b and BASE_WINDOW[0] <= b <= BASE_WINDOW[1])(contact(r, "base"))
            )
            print(
                f"   {temperature:>5.2f}{len(group):>5}"
                f"{gb['min'] if gb else float('nan'):>11.2f}{gb['median'] if gb else float('nan'):>13.2f}"
                f"{gr['median'] if gr else float('nan'):>13.2f}{folded:>11}{inside:>11}"
            )

    # ---------------------------------------------------------------- 4. is CA RMSD the feature?
    r_rmsd = correlation([(number(r, "ca_rmsd"), contact(r, "base")) for r in designs])
    r_iptm = correlation([(number(r, "iptm"), contact(r, "base")) for r in designs])
    r_lig = correlation([(number(r, "ligand_confidence"), contact(r, "base")) for r in designs])
    print("\n-- WHAT PREDICTS THE BASE CONTACT? (Pearson r against base distance; 0 = useless)")
    for label, value in (("CA RMSD", r_rmsd), ("iptm", r_iptm), ("LigandMPNN ligand_confidence", r_lig)):
        print(f"   {label:<30}{'n/a' if value is None else f'{value:+.3f}'}")
    if r_rmsd is not None and r_iptm is not None and abs(r_rmsd) > abs(r_iptm) + 0.15:
        print("   >> CA RMSD beats confidence, as across backbones. Filter on fidelity, not confidence.")

    # ---------------------------------------------------------------- 5. the shortlist
    ranked = sorted(
        (r for r in designs if contact(r, "base")),
        key=lambda r: abs(contact(r, "base") - 2.51),  # 2.51 A is the family median
    )[:10]
    if ranked:
        print("\n-- TOP 10 by closeness to the family median base contact (2.51 A)")
        print(f"   {'name':<8}{'T':>5}{'base':>8}{'donor':>8}{'CA RMSD':>9}{'iptm':>7}{'plddt':>8}  window")
        for row in ranked:
            base, donor = contact(row, "base"), contact(row, "donor")
            mark = []
            if base and BASE_WINDOW[0] <= base <= BASE_WINDOW[1]:
                mark.append("base")
            if donor and DONOR_WINDOW[0] <= donor <= DONOR_WINDOW[1]:
                mark.append("donor")
            print(
                f"   {str(row.get('name')):<8}{number(row, 'temperature') or float('nan'):>5.2f}"
                f"{base:>8.2f}{donor if donor else float('nan'):>8.2f}"
                f"{number(row, 'ca_rmsd') or float('nan'):>9.2f}"
                f"{number(row, 'iptm') or float('nan'):>7.3f}"
                f"{number(row, 'complex_plddt') or float('nan'):>8.3f}  {'+'.join(mark)}"
            )
print("=" * 96)
