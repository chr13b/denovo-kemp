"""Measure the catalytic geometry of a real Kemp eliminase, to give our designs a target.

    uv run python scripts/30_measure_theozyme_geometry.py

Writes the theozyme (ligand + catalytic base + oxyanion donor, scaffold stripped), the measured
geometry, and a standalone 3D viewer into the run directory, then copies them to results/.

Why: scoring is dominated by the geometry between the two declared catalytic residues and ligand
6NT, and the terms multiply (wiki/challenge.md). Before this we had no measured target to aim at.
PDB 7K4Z is Kemp eliminase HG3.17 bound to 6NT at 1.08 A -- the same ligand the organizers cofold
every design against, in an enzyme that actually works.

HG3.17 is a geometry reference only. It is ineligible as a design under the novelty rules
(TM <= 0.7, identity <= 70%), so we copy the arrangement and never the fold or the sequence.

Roles are assigned from contact distance, not from assumed residue numbers: the base is the
nearest Asp/Glu carboxylate to the ring nitrogen bearing the acidic hydrogen, and the donor is the
nearest allowed side-chain donor to the ring nitrogen standing in for the leaving oxygen. The
script recovers Asp127 and Gln50 on its own, which is the check that the mapping below is right.

6NT is a triazole standing in for the substrate's isoxazole, so the ring atoms correspond:

    benzisoxazole (substrate)   6NT (analogue)   role
    C3-H                        N3-H             the proton the base removes
    O1                          N1               the leaving oxygen that takes the charge
"""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path

from kemp.config import parse
from kemp.data import fetch
from kemp.geometry import (
    Atom,
    angle,
    contact_geometry,
    count_ca_within,
    distance,
    format_atom,
    group_by_residue,
    nearest_atom,
    parse_pdb,
    plane_normal,
    primary_altloc,
)
from kemp.paths import RESULTS, ROOT
from kemp.run import start_run

# The submission format accepts only these residues for each declared role (wiki/submission.md).
BASE_RESIDUES = {"ASP": ("OD1", "OD2"), "GLU": ("OE1", "OE2")}
DONOR_RESIDUES = {
    "GLN": ("NE2",),
    "ASN": ("ND2",),
    "SER": ("OG",),
    "THR": ("OG1",),
    "TYR": ("OH",),
    "LYS": ("NZ",),
    "ARG": ("NE", "NH1", "NH2"),
}
# The heavy atom each partner hangs off, for the angle at the partner itself.
PARTNER_ROOT = {
    "ASP": "CG",
    "GLU": "CD",
    "GLN": "CD",
    "ASN": "CG",
    "SER": "CB",
    "THR": "CB",
    "TYR": "CZ",
    "LYS": "CE",
    "ARG": "CZ",
}
# Ring neighbours of each catalytic nitrogen, which define "straight out from the ring".
RING_NEIGHBOURS = {"N1": ("N2", "C7A"), "N3": ("N2", "C3A")}

TEMPLATE = ROOT / "scripts" / "assets" / "theozyme_viewer.html.in"


@dataclass
class Config:
    name: str = "flavia-01"  # suffix of the run directory
    seed: int = 0
    pdb_id: str = "7K4Z"
    url: str = "https://files.rcsb.org/download/7K4Z.pdb"
    checksum: str = "ec7451e03db3b74f9a58589f61782dd94818555544eba23d4a83e40899eaca85"
    ligand: str = "6NT"
    acid_h_mimic: str = "N3"  # bears the acidic hydrogen; the base attacks here
    oxyanion_mimic: str = "N1"  # stands in for the leaving oxygen
    ring: tuple[str, ...] = ("N1", "N2", "N3", "C3A", "C4", "C5", "C6", "C7", "C7A")
    skip_residues: tuple[str, ...] = ("HOH", "1PE")  # waters and cryoprotectant
    contact_shell_a: float = 5.0  # pocket residues reported around the ligand
    hbond_range_a: tuple[float, float] = (2.5, 3.4)
    burial_radius_a: float = 12.0
    publish: bool = True  # copy the curated outputs into results/


def pick_ligand(residues: dict[tuple, list[Atom]], cfg: Config) -> tuple[tuple, list[Atom]]:
    """Return the ligand copy that has both catalytic ring atoms modelled, best-ordered first."""
    usable = []
    for key, atoms in residues.items():
        if key[3] != cfg.ligand:
            continue
        if {cfg.acid_h_mimic, cfg.oxyanion_mimic} <= {a.name for a in atoms}:
            usable.append((max(a.occupancy for a in atoms), key, atoms))
    if not usable:
        raise SystemExit(f"no {cfg.ligand} copy carries both {cfg.acid_h_mimic} and {cfg.oxyanion_mimic}")
    usable.sort(key=lambda item: item[0], reverse=True)
    return usable[0][1], usable[0][2]


def write_theozyme(path: Path, residues: dict, keys: list[tuple], cfg: Config, header: list[str]) -> int:
    """Write ligand + catalytic residues as a standalone PDB, renumbered 1..n."""
    lines = list(header)
    serial = 0
    for res_seq, key in enumerate(keys, start=1):
        for atom in sorted(residues[key], key=lambda a: a.serial):
            if atom.is_hydrogen() and key[3] != cfg.ligand:
                continue  # protein H is not modelled at this resolution; ligand H is informative
            serial += 1
            lines.append(format_atom(atom, serial, res_seq))
    lines.append("END")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return serial


def render_viewer(path: Path, theozyme_atoms: list[Atom], geometry: dict, cfg: Config) -> None:
    """Fill the viewer template with the measured numbers, so the page can never drift from them."""
    atoms = [
        '    {"n":"%s","r":"%s","i":%d,"e":"%s","x":%.3f,"y":%.3f,"z":%.3f}'
        % (a.name, a.res_name, a.res_seq, a.element, a.x, a.y, a.z)
        for a in theozyme_atoms
    ]
    contacts = ["    " + json.dumps({**entry, "role": role}) for role, entry in geometry["contacts"].items()]
    payload = (
        "{\n"
        '  "atoms": [\n' + ",\n".join(atoms) + "\n  ],\n"
        '  "ring": ' + json.dumps(list(cfg.ring)) + ",\n"
        '  "contacts": [\n' + ",\n".join(contacts) + "\n  ],\n"
        '  "base_burial": %d\n' % geometry["base_burial"]["ca_atoms_within_12a"] + "}"
    )
    path.write_text(TEMPLATE.read_text(encoding="utf-8").replace("__THEOZYME_DATA__", payload), "utf-8")


def main(cfg: Config) -> None:
    run = start_run(cfg.name, cfg, seed=cfg.seed)
    structure = fetch(cfg.url, f"reference/{cfg.pdb_id}.pdb", checksum=cfg.checksum)

    atoms = primary_altloc(parse_pdb(structure.read_text(encoding="utf-8")))
    atoms = [a for a in atoms if a.res_name not in cfg.skip_residues]
    residues = group_by_residue(atoms)

    lig_key, lig_atoms = pick_ligand(residues, cfg)
    lig_by_name = {a.name: a for a in lig_atoms}
    ring_xyz = [lig_by_name[n].xyz for n in cfg.ring if n in lig_by_name]
    if len(ring_xyz) < 6:
        raise SystemExit("ligand ring is incomplete")
    normal = plane_normal(ring_xyz)

    roles = {
        "base": (cfg.acid_h_mimic, BASE_RESIDUES, "deprotonates the acidic position"),
        "donor": (cfg.oxyanion_mimic, DONOR_RESIDUES, "stabilises the developing oxyanion"),
    }
    found, contacts = {}, {}
    for role, (mimic, allowed, description) in roles.items():
        hit = nearest_atom(lig_by_name[mimic].xyz, residues, allowed)
        if hit is None:
            raise SystemExit(f"no candidate {role} found near {mimic}")
        dist, res_key, partner = hit
        lo, hi = cfg.hbond_range_a
        if not lo - 0.1 <= dist <= hi + 0.2:
            # Not a hydrogen bond means the role assignment is wrong, and a wrong target is
            # worse than no target at all.
            raise SystemExit(f"{role} contact is {dist:.2f} A, outside hydrogen-bonding range")
        found[role] = (res_key, partner)

        res_atoms = {a.name: a for a in residues[res_key]}
        entry = contact_geometry(
            ring_atom=lig_by_name[mimic].xyz,
            ring_neighbours=[lig_by_name[n].xyz for n in RING_NEIGHBOURS[mimic]],
            ring_normal=normal,
            partner=partner.xyz,
            partner_root=res_atoms[PARTNER_ROOT[res_key[3]]].xyz,
        )
        entry.update(
            residue=f"{res_key[3]}{res_key[1]}",
            atom=partner.name,
            ligand_atom=mimic,
            role_text=description,
        )
        # The crystal models a hydrogen on the acidic nitrogen, which gives the true hydrogen-bond
        # angle. Heavy atoms alone cannot show it, and Boltz-2 will not give us one.
        if role == "base" and "H3" in lig_by_name:
            h = lig_by_name["H3"]
            entry["h_bond_angle_deg"] = round(angle(lig_by_name[mimic].xyz, h.xyz, partner.xyz), 1)
            entry["h_to_partner_a"] = round(distance(h.xyz, partner.xyz), 2)
        contacts[role] = entry
        run.log(role=role, **{k: v for k, v in entry.items() if isinstance(v, (int, float))})

    base_key, _ = found["base"]
    base_atoms = {a.name: a for a in residues[base_key]}
    burial = count_ca_within(atoms, base_atoms[PARTNER_ROOT[base_key[3]]].xyz, cfg.burial_radius_a)

    lig_heavy = [a.xyz for a in lig_atoms if not a.is_hydrogen()]
    catalytic = {res_key for res_key, _ in found.values()}
    nearby = sorted(
        (min(distance(a.xyz, p) for a in res if not a.is_hydrogen() for p in lig_heavy), key)
        for key, res in residues.items()
        if key != lig_key and key not in catalytic
    )
    pocket = [f"{key[3]}{key[1]}" for d, key in nearby if d <= cfg.contact_shell_a]

    geometry = {
        "source": f"PDB {cfg.pdb_id}, Kemp eliminase HG3.17 with 6-nitrobenzotriazole (6NT), 1.08 A",
        "note": "Geometry reference only. HG3.17 is ineligible as a design under the novelty rules.",
        "ligand": f"{lig_key[3]} {lig_key[0]}{lig_key[1]}",
        "contacts": contacts,
        "base_burial": {
            "ca_atoms_within_12a": burial,
            "measured_from": f"{base_key[3]}{base_key[1]} {PARTNER_ROOT[base_key[3]]}",
        },
        "pocket_residues": pocket,
    }

    header = [
        "REMARK   1 THEOZYME: Kemp eliminase catalytic arrangement",
        f"REMARK   1 SOURCE  : PDB {cfg.pdb_id} (HG3.17 + {cfg.ligand}), geometry reference only",
        f"REMARK   1 BASE    : {contacts['base']['residue']} -> {cfg.ligand} {cfg.acid_h_mimic}",
        f"REMARK   1 DONOR   : {contacts['donor']['residue']} -> {cfg.ligand} {cfg.oxyanion_mimic}",
        "REMARK   1 HG3.17 is ineligible as a design (novelty rules). Geometry only.",
    ]
    pdb_out = run.dir / "theozyme_6nt.pdb"
    keys = [found["base"][0], found["donor"][0], lig_key]
    n_atoms = write_theozyme(pdb_out, residues, keys, cfg, header)
    (run.dir / "geometry.json").write_text(json.dumps(geometry, indent=2) + "\n", encoding="utf-8")
    render_viewer(run.dir / "theozyme_viewer.html", parse_pdb(pdb_out.read_text()), geometry, cfg)

    published: list[str] = []
    if cfg.publish:
        RESULTS.mkdir(parents=True, exist_ok=True)
        for name, dest in (
            ("theozyme_6nt.pdb", "theozyme_7k4z.pdb"),
            ("geometry.json", "theozyme_7k4z_geometry.json"),
            ("theozyme_viewer.html", "theozyme_viewer.html"),
        ):
            shutil.copy2(run.dir / name, RESULTS / dest)
            published.append(f"results/{dest}")

    for role, entry in contacts.items():
        print(
            f"{role:6} {entry['residue']:>7} {entry['atom']:<4} -> {entry['ligand_atom']:<3} "
            f"{entry['distance_a']:.2f} A | in-plane {entry['in_plane_deg']:5.1f} "
            f"| out-of-plane {entry['out_of_plane_deg']:5.1f}"
        )
    print(f"burial {burial} CA within {cfg.burial_radius_a:.0f} A | theozyme {n_atoms} atoms")

    run.finish(
        ok=True,
        source_pdb=cfg.pdb_id,
        base=contacts["base"],
        donor=contacts["donor"],
        base_burial_ca_within_12a=burial,
        theozyme_atoms=n_atoms,
        pocket_residues=pocket,
        published=published,
    )


if __name__ == "__main__":
    main(parse(Config))
