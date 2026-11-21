"""Bundle structures and our metrics for a teammate who wants to test other metrics against ours.

    uv run python tools/make_share_pack.py [--host pdh-team]

Writes data/share_metrics_pack/ and data/share_metrics_pack.zip (gitignored: bulk, not a result).

A metric is only useful if it SEPARATES good from bad, so the pack is a labelled spread and not just the
winners: the best designs by our geometry score, an evenly spaced sample down seed 4's ranking, its worst
designs, a few mid-range designs from other backbones, three designs replicated over five Boltz-2 seeds
(the closest thing we have to ground truth), three natural enzymes folded the same way, and the 4BS0 crystal.

Needs the committed result tables and ssh access to the cluster. Fetches structures and confidence files
with one tar stream; PAE/PDE matrices are NOT bundled (500 KB each) but their cluster paths are listed.
"""

import argparse
import csv
import json
import math
import shutil
import subprocess
import zipfile
from pathlib import Path

from kemp.paths import DATA, RESULTS

README = Path(__file__).with_name("share_pack_README.md")
SWEEPS = {  # label -> (cluster results dir, tsv holding iptm / iPDE / pLDDT / CA RMSD)
    "seed4": ("chris_oversample_a/results/oversample-27", "oversample_a_seed4_job27"),
    "Trp44": ("chris_oversample_b/results/oversample-31", "oversample_b_trp44_job31"),
    "fresh4BS0A": ("chris_family_motifs/results/oversample-35", "oversample_c_4bs0a_job35"),
    "8USL_B": ("chris_family_motifs/results/oversample-36", "oversample_c_8usl_job36"),
    "seed12": ("chris_family_motifs/results/oversample-59", "screen_4bs0a_s12_job59"),
    "seed13": ("chris_family_motifs/results/oversample-60", "screen_4bs0a_s13_job60"),
    "seed11": ("chris_family_motifs/results/oversample-58", "screen_4bs0a_s11_job58"),
    "seed3": ("chris_os_s3/results/oversample-39", "oversample_rescue_s3_job39"),
    "seed5": ("chris_os_s5/results/oversample-40", "oversample_rescue_s5_job40"),
}
REPLICATE = "chris_oversample_a/results/replicate-47"
PROJECTS = "mnt/work/projects"
# (low, high, tolerance, weight when below low): the crystal range, in tolerance units
RANGES = {
    "base_d": (2.41, 2.69, 0.25, 2.0),
    "donor_d": (2.92, 3.24, 0.25, 2.0),
    "base_approach": (167.1, 175.8, 15, 1.0),
    "base_oop": (1.0, 11.7, 15, 1.0),
    "donor_approach": (162.1, 173.0, 15, 1.0),
    "donor_oop": (0.6, 16.1, 15, 1.0),
}
GEOMETRY = list(RANGES)


def deviation(row):
    total = 0.0
    for key, (low, high, tolerance, weight) in RANGES.items():
        value = float(row[key])
        if value < low:
            total += weight * (low - value) / tolerance
        elif value > high:
            total += (value - high) / tolerance
    return total


def read(path):
    with open(path) as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def number(value):
    try:
        out = float(value)
        return out if math.isfinite(out) else ""
    except (TypeError, ValueError):
        return ""


def spread(ranked, count, exclude):
    """`count` entries evenly spaced down a ranked list, skipping those already chosen."""
    pool = [r for r in ranked if (r["sweep"], r["name"]) not in exclude]
    if not pool:
        return []
    step = max(1, len(pool) // count)
    return pool[step // 2 :: step][:count]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="pdh-team")
    host = parser.parse_args().host

    geometry = [r for r in read(RESULTS / "geometry_full_crystal_vs_designs.tsv")]
    swept = [r for r in geometry if not r["sweep"].startswith("rep")]
    meta = {}
    for label, (_, stem) in SWEEPS.items():
        for row in read(RESULTS / f"{stem}.tsv"):
            if row.get("kind") == "design":
                meta[(label, row["name"])] = row
    for row in swept:
        row["D"] = deviation(row)
    ranked = sorted(swept, key=lambda r: r["D"])
    seed4 = [r for r in ranked if r["sweep"] == "seed4"]

    chosen = []  # (group, row)
    taken = set()

    def take(group, rows):
        for row in rows:
            key = (row["sweep"], row["name"])
            if key not in taken:
                taken.add(key)
                chosen.append((group, row))

    take("best", ranked[:12])
    take("worst_seed4", seed4[-8:])
    take("spread_seed4", spread(seed4, 12, taken))
    for label in ("Trp44", "seed3", "8USL_B"):
        take(f"midrange_{label}", spread([r for r in ranked if r["sweep"] == label], 2, taken))

    out = DATA / "share_metrics_pack"
    if out.exists():
        shutil.rmtree(out)
    (out / "structures").mkdir(parents=True)
    work = out / "_fetch"
    work.mkdir()

    wanted = {f"{PROJECTS}/{REPLICATE}/seed1/queries.json", "mnt/work/tools/kemp_pdb/4BS0.cif"}
    for path, _ in SWEEPS.values():
        wanted.add(f"{PROJECTS}/{path}/queries.json")

    def prediction(root, name):
        base = f"{PROJECTS}/{root}/boltz/boltz_results_queries/predictions/{name}"
        return f"{base}/{name}_model_0.cif", f"{base}/confidence_{name}_model_0.json", base

    plan = []  # (id, group, sweep label, name, seed, cif path, json path, directory)
    for group, row in chosen:
        root = SWEEPS[row["sweep"]][0]
        cif, conf, base = prediction(root, row["name"])
        plan.append(
            (f"{group}__{row['sweep']}__{row['name']}", group, row["sweep"], row["name"], "", cif, conf, base)
        )
    for sequence in ("c_s024", "c_s059", "c_seed4_original"):
        for seed in range(1, 6):
            cif, conf, base = prediction(f"{REPLICATE}/seed{seed}", sequence)
            plan.append(
                (
                    f"replicated__{sequence[2:]}__seed{seed}",
                    "replicated_5seeds",
                    "seed4",
                    sequence[2:],
                    seed,
                    cif,
                    conf,
                    base,
                )
            )
    for natural in ("c_4BS0", "c_3NYD", "c_7K4U"):
        cif, conf, base = prediction(f"{REPLICATE}/seed1", natural)
        plan.append(
            (f"natural__{natural[2:]}", "natural_control", "natural", natural[2:], 1, cif, conf, base)
        )
    for entry in plan:
        wanted.update((entry[5], entry[6]))

    listing = "\n".join(sorted(wanted)) + "\n"
    stream = subprocess.run(["ssh", host, "tar czf - -C / -T -"], input=listing.encode(), capture_output=True)
    if stream.returncode != 0 or not stream.stdout:
        raise SystemExit(f"fetch failed: {stream.stderr.decode()[:300]}")
    subprocess.run(["tar", "xzf", "-", "-C", str(work)], input=stream.stdout, check=True)

    sequences = {}
    for label, (path, _) in SWEEPS.items():
        for record in json.loads((work / PROJECTS / path / "queries.json").read_text()):
            sequences[(label, record["name"])] = record["sequence"]
    for record in json.loads((work / PROJECTS / REPLICATE / "seed1/queries.json").read_text()):
        # replicate records are named c_<name>; store under the bare name the plan looks up
        bare = record["name"][2:]
        sequences.setdefault(("seed4", bare), record["sequence"])
        sequences[("natural", bare)] = record["sequence"]

    replicated = {(r["sweep"], r["name"]): r for r in geometry if r["sweep"].startswith("rep")}
    scan = {(r["seed"], r["name"]): r for r in read(RESULTS / "replication_job47_pinned.tsv")}
    rows, fasta = [], []
    for ident, group, label, name, seed, cif, conf, base in plan:
        source = work / cif
        if not source.exists():
            print(f"  missing {cif}")
            continue
        shutil.copy(source, out / "structures" / f"{ident}.cif")
        shutil.copy(work / conf, out / "structures" / f"{ident}.confidence.json")
        if group == "replicated_5seeds":
            geo = replicated.get((f"rep{seed}", f"c_{name}"), {})
            info = {"iptm": "", "complex_ipde": "", "complex_plddt": "", "ca_rmsd": "", "temperature": ""}
            confidence = json.loads((out / "structures" / f"{ident}.confidence.json").read_text())
            info.update(
                iptm=number(confidence.get("iptm")),
                complex_ipde=number(confidence.get("complex_ipde")),
                complex_plddt=number(confidence.get("complex_plddt")),
            )
            positions, note = (86, 52), "declared positions, replicate Boltz seed"
        elif group == "natural_control":
            hit = scan.get((str(seed), f"c_{name}"), {})
            geo = {"base_d": hit.get("scan_base", ""), "donor_d": hit.get("scan_donor", "")}
            confidence = json.loads((out / "structures" / f"{ident}.confidence.json").read_text())
            info = {
                "iptm": number(confidence.get("iptm")),
                "complex_ipde": number(confidence.get("complex_ipde")),
                "complex_plddt": number(confidence.get("complex_plddt")),
                "ca_rmsd": "",
                "temperature": "",
            }
            positions, note = ("", ""), "natural enzyme, no MSA; distances by nearest-atom scan, no angles"
        else:
            geo = next(r for r in swept if r["sweep"] == label and r["name"] == name)
            info = meta[(label, name)]
            positions, note = (
                (info.get("base_position", ""), info.get("donor_position", "")),
                "single Boltz fold",
            )
        sequence = sequences.get((label, name), "")
        row = {
            "id": ident,
            "group": group,
            "backbone": label,
            "design": name,
            "boltz_seed": seed,
            "length": len(sequence),
            "base_position": positions[0],
            "donor_position": positions[1],
        }
        for key in GEOMETRY:
            row[key] = number(geo.get(key, ""))
        row["D"] = round(deviation(geo), 2) if all(number(geo.get(k, "")) != "" for k in GEOMETRY) else ""
        for key in ("iptm", "complex_ipde", "complex_plddt", "ca_rmsd", "temperature"):
            row[key] = number(info.get(key, ""))
        row.update(note=note, structure=f"structures/{ident}.cif", cluster_dir=f"/{base}", sequence=sequence)
        rows.append(row)
        if sequence:
            header = f"{ident}" + (f" base={positions[0]} oxy={positions[1]}" if positions[0] != "" else "")
            fasta.append(f">{header}\n{sequence}")

    shutil.copy(work / "mnt/work/tools/kemp_pdb/4BS0.cif", out / "structures" / "crystal__4BS0.cif")
    shutil.copy(RESULTS / "kemp_family_geometry.tsv", out / "crystal_contacts_43_ligand_copies.tsv")
    shutil.rmtree(work)
    columns = list(rows[0])
    with (out / "manifest.tsv").open("w") as handle:
        handle.write("\t".join(columns) + "\n")
        for row in rows:
            handle.write("\t".join(str(row[c]) for c in columns) + "\n")
    (out / "designs.fasta").write_text("\n".join(fasta) + "\n")
    (out / "README.md").write_text(README.read_text().format(count=len(rows)))
    archive = DATA / "share_metrics_pack.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as bundle:
        for path in sorted(out.rglob("*")):
            if path.is_file():
                bundle.write(path, path.relative_to(DATA))
    print(f"{len(rows)} structures -> {out}")
    print(f"zip: {archive} ({archive.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
