"""Score a share_metrics_pack (Boltz-2 structures + manifest.tsv) with scorer v2, weighted K1-K5.

    uv run python scripts/40_score_metrics_pack.py --pack=<dir containing manifest.tsv>
    uv run python scripts/40_score_metrics_pack.py --pack=<dir> --target=family

Every number is measured from the .cif files and combined by `kemp.scoring.weighted_total`.
K5 (consistency) exists only for sequences replicated over several seeds (manifest column `replicate_of`,
or `group == replicated_5seeds`);
for every other structure the formula drops K5 and renormalises, so those totals are not strictly
comparable to the replicated ones.

Contact residues: structures on a backbone in `declared_backbones` are measured at the declared
`base_position` / `donor_position` (asserted against the sequence). Everything else falls back to the
nearest allowed atom, marked `inferred` - the pack's README warns that this can latch onto the wrong
residue, so read `inferred` rows as indicative only.

`--target=v2` uses the 7K4U targets of `kemp.scoring.CRYSTAL`. `--target=family` replaces the two target
distances with the medians over the engaged ligand copies in `results/kemp_family_geometry.tsv` (23 PDB
entries, `scripts/32_kemp_family_geometry.py`); the angle targets stay at 7K4U.
"""

from __future__ import annotations

import csv
import json
import math
import statistics
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from biotite.structure.io import pdbx

from kemp import scoring as S
from kemp.config import parse
from kemp.paths import RESULTS
from kemp.run import start_run

RING = ("N1", "N2", "N3", "C3A", "C7A")
BASE_ATOMS = {"ASP": ("OD1", "OD2"), "GLU": ("OE1", "OE2")}
BASE_ATOMS_OD2 = {"ASP": ("OD2",), "GLU": ("OE2",)}  # --base_atom=od2: the syn oxygen only
# carbon bonded to the contact heteroatom: angle AT the heteroatom (A1 = C-OD2...N3, A4 = C-NE2...N1)
ATTACHED = {
    ("ASP", "OD1"): "CG",
    ("ASP", "OD2"): "CG",
    ("GLU", "OE1"): "CD",
    ("GLU", "OE2"): "CD",
    ("GLN", "NE2"): "CD",
    ("ASN", "ND2"): "CG",
    ("SER", "OG"): "CB",
    ("THR", "OG1"): "CB",
    ("TYR", "OH"): "CZ",
    ("LYS", "NZ"): "CE",
    ("ARG", "NE"): "CD",
    ("ARG", "NH1"): "CZ",
    ("ARG", "NH2"): "CZ",
}
DONOR_ATOMS = {
    "GLN": ("NE2",),
    "ASN": ("ND2",),
    "SER": ("OG",),
    "THR": ("OG1",),
    "TYR": ("OH",),
    "LYS": ("NZ",),
    "ARG": ("NE", "NH1", "NH2"),
}


@dataclass
class Config:
    name: str = "metrics-pack"
    seed: int = 0
    pack: str = ""  # directory that holds manifest.tsv and structures/
    target: str = "v2"  # v2 | family
    declared_backbones: list[str] = field(default_factory=lambda: ["seed4"])
    base_position: int = 86  # 1-based, in the sequences of the declared backbones
    donor_position: int = 52
    iptm_baseline: float = 0.8372  # organizers' reference pipeline (chris-01); a design has to beat it
    iptm_sigma: float = 0.1  # below the baseline the score falls as exp(-((baseline - iptm) / sigma)^2)
    iptm_weight: float = 0.15
    base_atom: str = (
        "nearest"  # nearest | od2: which carboxylate oxygen counts as the base contact (and burial origin)
    )


def family_targets() -> dict[str, float]:
    """Median contact distances over engaged ligand copies (base < 3 A, donor < 3.7 A)."""
    with open(RESULTS / "kemp_family_geometry.tsv") as fh:
        rows = list(csv.DictReader(fh, delimiter="\t"))
    engaged = [r for r in rows if float(r["base_dist"]) < 3.0]
    both = [r for r in engaged if float(r["donor_dist"]) < 3.7]
    return {
        "base": statistics.median(float(r["base_dist"]) for r in engaged),
        "donor": statistics.median(float(r["donor_dist"]) for r in both),
    }


def read_iptm(cif: Path):
    """ipTM from the confidence json that sits beside a Boltz-2 structure (either naming scheme)."""
    for c in (
        cif.parent / f"confidence_{cif.stem}.json",
        cif.with_suffix(".confidence.json"),
        cif.parent / f"{cif.stem}_confidence.json",
    ):
        if c.exists():
            return float(json.loads(c.read_text())["iptm"])
    return None


def total_with_iptm(parts: dict, w_iptm: float) -> float:
    """Weighted geometric mean of K1-K5 plus ipTM (K6), same weights as `kemp.scoring.WEIGHTS`."""
    w = {**S.WEIGHTS, "iptm": w_iptm}
    known = {k: v for k, v in parts.items() if v is not None}
    return math.exp(sum(w[k] * math.log(max(v, 1e-9)) for k, v in known.items()) / sum(w[k] for k in known))


def atom(res, name):
    return res.coord[res.atom_name == name][0]


def nearest(prot, lig, allowed, lig_atom, res_id=None):
    """Closest allowed (residue, atom) to a ligand atom; restricted to `res_id` when it is declared."""
    best = None
    for rid in [res_id] if res_id else sorted(set(prot.res_id)):
        res = prot[prot.res_id == rid]
        if not len(res) or res.res_name[0] not in allowed:
            continue
        for name in allowed[res.res_name[0]]:
            if (res.atom_name == name).any():
                d = float(np.linalg.norm(atom(res, name) - atom(lig, lig_atom)))
                if best is None or d < best[3]:
                    best = (rid, name, res.res_name[0], d)
    return best


def measure(cif, base_id, donor_id, base_atoms=BASE_ATOMS):
    at = pdbx.get_structure(pdbx.CIFFile.read(str(cif)), model=1, use_author_fields=True)
    at = at[at.element != "H"]
    lig, prot = at[at.hetero & (at.res_name == "6NT")], at[~at.hetero]
    centre = np.mean([atom(lig, n) for n in RING], axis=0)
    out = {}
    for label, allowed, lig_atom, nb2, rid in (
        ("base", base_atoms, "N3", "C3A", base_id),
        ("donor", DONOR_ATOMS, "N1", "C7A", donor_id),
    ):
        hit = nearest(prot, lig, allowed, lig_atom, rid)
        if hit is None:
            return None
        res_id, name, resname, dist = hit
        p, t = atom(prot[prot.res_id == res_id], name), atom(lig, lig_atom)
        out[label] = {
            "res": f"{resname}{res_id}",
            "rid": res_id,
            "atom": name,
            "d": dist,
            "angle": S.angle_between(p, t, centre),
            "A": S.angle_between(atom(prot[prot.res_id == res_id], ATTACHED[(resname, name)]), p, t),
            "oop": S.out_of_plane(p, t, atom(lig, "N2"), atom(lig, nb2)),
        }
    base = prot[prot.res_id == out["base"]["rid"]]
    ca = prot[prot.atom_name == "CA"].coord
    out["burial"] = int((np.linalg.norm(ca - atom(base, out["base"]["atom"]), axis=1) <= 12).sum())
    return out


def main(cfg: Config) -> None:
    pack = Path(cfg.pack)
    if not (pack / "manifest.tsv").exists():
        raise SystemExit(f"no manifest.tsv in {pack!s}: pass --pack=<dir>")
    targets = {k: dict(v) for k, v in S.CRYSTAL.items()}
    if cfg.target == "family":
        for label, dist in family_targets().items():
            targets[label]["dist"] = dist
    elif cfg.target != "v2":
        raise SystemExit("--target must be v2 or family")
    run = start_run(cfg.name, cfg, seed=cfg.seed)

    with open(pack / "manifest.tsv") as fh:
        rows = list(csv.DictReader(fh, delimiter="\t"))
    crystal = pack / "structures" / "crystal__4BS0.cif"
    if crystal.exists():  # reference crystal: Asp127 / Gln50 in its own numbering
        rows.append(
            {
                "id": "crystal__4BS0",
                "group": "crystal",
                "backbone": "",
                "structure": f"structures/{crystal.name}",
                "complex_ipde": "",
                "D": "",
            }
        )

    res = {}
    for r in rows:
        # positions: per row from the manifest (`base_position` / `donor_position`) if present,
        # else the config default for the declared backbones, else inferred
        base_pos, donor_pos = r.get("base_position"), r.get("donor_position")
        if base_pos and donor_pos:
            base_pos, donor_pos = int(base_pos), int(donor_pos)
        elif r["backbone"] in cfg.declared_backbones:
            base_pos, donor_pos = cfg.base_position, cfg.donor_position
        else:
            base_pos = donor_pos = None
        declared = base_pos is not None
        if declared:
            seq = r["sequence"]
            assert seq[base_pos - 1] in "DE" and seq[donor_pos - 1] in "QNSTYKR", r["id"]
        m = measure(
            pack / r["structure"],
            base_pos,
            donor_pos,
            BASE_ATOMS_OD2 if cfg.base_atom == "od2" else BASE_ATOMS,
        )
        if m is None:
            print("not measurable:", r["id"])
            continue
        dev = max(abs(m[c][k] - targets[c][k]) for c in ("base", "donor") for k in ("angle", "oop"))
        ipde = float(r["complex_ipde"]) if r["complex_ipde"] else None
        parts = {
            "dist": min(S.score_distance(m[c]["d"], targets[c]["dist"]) for c in ("base", "donor")),
            "approach": S.score_angle(dev),
            "ipde": S.score_ipde(ipde) if ipde is not None else None,
            "burial": S.score_burial(m["burial"]),
            "consistency": None,
        }
        iptm = read_iptm(pack / r["structure"])
        parts["iptm"] = (
            None
            if iptm is None
            else (
                1.0
                if iptm >= cfg.iptm_baseline
                else math.exp(-(((cfg.iptm_baseline - iptm) / cfg.iptm_sigma) ** 2))
            )
        )
        res[r["id"]] = {
            "row": r,
            "m": m,
            "dev": dev,
            "parts": parts,
            "mode": "declared" if declared else "inferred",
            "iptm": iptm,
        }

    # K5: spread of the two contact distances over the seeds of one replicated sequence
    reps: dict[str, list] = {}
    for key, v in res.items():
        if v["row"].get("replicate_of"):  # one design refolded at several seeds
            reps.setdefault(v["row"]["replicate_of"], []).append(v)
        elif v["row"]["group"] == "replicated_5seeds":
            reps.setdefault(key.split("__")[1], []).append(v)
    for vs in reps.values():
        stds = [float(np.std([v["m"][c]["d"] for v in vs], ddof=1)) for c in ("base", "donor")]
        for v in vs:
            v["parts"]["consistency"] = S.score_consistency(stds)
    for v in res.values():
        k15 = {k: x for k, x in v["parts"].items() if k != "iptm"}
        v["total"] = S.weighted_total(k15)
        v["total6"] = total_with_iptm(v["parts"], cfg.iptm_weight)

    def f(x, n=3):
        return "" if x is None else f"{x:.{n}f}"

    out = run.dir / "weighted_scores.tsv"
    with open(out, "w", newline="") as fh:
        w = csv.writer(fh, delimiter="\t")
        cols = "id group mode base_res base_d donor_res donor_d approach_dev burial ipde"
        cols += (
            " s_dist s_approach s_ipde s_burial K5 iptm s_iptm WEIGHTED manifest_D WEIGHTED_K6 A1 A4 dev_oop"
        )
        w.writerow(cols.split())
        for key, v in res.items():
            p, m = v["parts"], v["m"]
            w.writerow(
                [
                    key,
                    v["row"]["group"],
                    v["mode"],
                    m["base"]["res"],
                    f(m["base"]["d"], 2),
                    m["donor"]["res"],
                    f(m["donor"]["d"], 2),
                    f(v["dev"], 0),
                    m["burial"],
                    v["row"]["complex_ipde"][:5],
                    f(p["dist"], 6),
                    f(p["approach"], 6),
                    f(p["ipde"], 6),
                    f(p["burial"], 6),
                    f(p["consistency"], 6),
                    f(v["iptm"], 3),
                    f(p["iptm"], 6),
                    f(v["total"], 4),
                    v["row"]["D"],
                    f(v["total6"], 4),
                    f(m["base"]["A"], 1),
                    f(m["donor"]["A"], 1),
                    f(max(abs(m[c]["oop"] - targets[c]["oop"]) for c in ("base", "donor")), 1),
                ]
            )
    summary = {n: float(np.mean([v["total"] for v in vs])) for n, vs in reps.items()}
    run.finish(ok=True, n_scored=len(res), target=cfg.target, replicated_mean_weighted=summary)
    print(f"scored {len(res)} structures -> {out}")
    for n, mean in sorted(summary.items(), key=lambda kv: -kv[1]):
        print(f"  {n:16s} mean weighted K1-K5 over seeds: {mean:.3f}")


if __name__ == "__main__":
    main(parse(Config))
