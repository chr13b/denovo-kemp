"""Cluster-side helper: turn the stage-A cofold into the stage-B anchored inputs.

    python make_stage_b.py <bundle>

Runs on the cluster inside env-boltz2 (needs biotite + numpy). Shipped inside the
bundle by `scripts/24_build_anchored_ladder.py`; not a standalone pipeline stage, so
it deliberately does not use kemp.config / kemp.run - the cluster has no repo checkout.

It reads the stage-A predicted complex, writes a protein-only template CIF, finds the
residues lining the TS analogue, and emits one YAML per (ligand x seed) that pins both.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import yaml
from biotite.structure.io import pdb as pdbio
from biotite.structure.io import pdbx

LIGAND_CHAIN = "B"
PROTEIN_CHAIN = "A"


def main(bundle: Path) -> None:
    meta = json.loads((bundle / "ladder.json").read_text())
    out = bundle / "out"
    yaml_b = bundle / "yaml_b"
    yaml_b.mkdir(exist_ok=True)
    templates = bundle / "templates"
    templates.mkdir(exist_ok=True)

    anchors = sorted(out.glob(f"{meta['label']}_anchor_s*/**/*_model_0.cif"))
    if not anchors:
        raise SystemExit(f"no stage-A structure under {out}")
    print(f"stage-A structures found: {[p.name for p in anchors]}")

    written = 0
    for anchor in anchors:
        seed = anchor.parent.name.rsplit("_s", 1)[-1]
        if not seed.isdigit():
            seed = anchor.parts[-4].rsplit("_s", 1)[-1]
        atoms = pdbx.get_structure(pdbx.CIFFile.read(str(anchor)), model=1, use_author_fields=True)

        lig = atoms[(atoms.hetero) & (atoms.element != "H")]
        prot = atoms[(~atoms.hetero) & (atoms.element != "H")]
        if len(lig) == 0 or len(prot) == 0:
            raise SystemExit(f"{anchor}: expected both protein and ligand atoms")

        # residues lining the TS analogue define the pocket every ligand must sit in
        d = np.linalg.norm(prot.coord[:, None] - lig.coord[None, :], axis=-1)
        near = d.min(axis=1) <= float(meta["pocket_radius"])
        contact_res = sorted({int(r) for r in prot.res_id[near]})
        if not contact_res:
            raise SystemExit(f"{anchor}: no residue within {meta['pocket_radius']} A of the ligand")
        print(f"  seed {seed}: {len(contact_res)} pocket residues {contact_res[:12]}...")

        # The template must be PROTEIN-ONLY and in a format Boltz can parse.
        # Two failures got us here, both worth keeping written down:
        #   1. Boltz's own output CIF still contains the ligand, and parse_mmcif
        #      resolves every component against the CCD -> "CCD component LIG1 not
        #      found!" (LIG1 is Boltz's placeholder name for a SMILES ligand).
        #   2. A biotite-written, atom_site-only CIF makes gemmi build zero models,
        #      so Boltz dies with IndexError at structure[0].
        # A plain protein-only PDB avoids both: Boltz accepts `pdb:` templates and
        # the format carries the records gemmi needs. Template id = file stem.
        # ... and it is OFF by default, because in this Boltz build every template
        # format failed: Boltz's own CIF -> "CCD component LIG1 not found" (it still
        # holds the ligand); a biotite atom_site-only CIF -> gemmi builds 0 models,
        # IndexError at structure[0]; a bare coordinate PDB -> parse_polymer indexes
        # past the entity sequence because there are no SEQRES records.
        # The pocket constraint alone already pins the ligand to one site, which is
        # the confound we are actually testing. See wiki/affinity-ladder.md.
        tmpl = templates / f"anchor_s{seed}.pdb"
        if meta.get("use_template"):
            pf = pdbio.PDBFile()
            pf.set_structure(prot)
            pf.write(str(tmpl))

        for lig_key, smiles in meta["ligands"].items():
            for s in range(1, int(meta["seeds"]) + 1):
                spec = {
                    "version": 1,
                    "sequences": [
                        {
                            "protein": {
                                "id": PROTEIN_CHAIN,
                                "sequence": meta["sequence"],
                                "msa": meta["msa"],
                            }
                        },
                        {"ligand": {"id": LIGAND_CHAIN, "smiles": smiles}},
                    ],
                    **({"templates": [{"pdb": str(tmpl.resolve())}]} if meta.get("use_template") else {}),
                    "constraints": [
                        {
                            "pocket": {
                                "binder": LIGAND_CHAIN,
                                "contacts": [[PROTEIN_CHAIN, r] for r in contact_res],
                                "max_distance": float(meta["pocket_max_distance"]),
                                "force": bool(meta["pocket_force"]),
                            }
                        }
                    ],
                    "properties": [{"affinity": {"binder": LIGAND_CHAIN}}],
                }
                name = f"{meta['label']}_anc{seed}_{lig_key}_s{s}"
                (yaml_b / f"{name}.yaml").write_text(yaml.safe_dump(spec, sort_keys=False), encoding="utf-8")
                written += 1

    print(f"wrote {written} stage-B YAML(s) into {yaml_b}")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
