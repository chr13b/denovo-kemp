# Theozyme inputs for RFD4-Proteina

How the recommended theozyme candidates ([theozyme-preanalysis.md](theozyme-preanalysis.md)) become design inputs for
RFD4-Proteina ([euler-rfd4.md](euler-rfd4.md)). Status 2026-11-21: **authored and checked locally, not yet run through
RFD4-Proteina.** The RFD4 libraries (`atomworks`) are not installed on the laptop, so nobody has seen RFD4 accept
these files yet.

## What was built
[`scripts/01_build_theozyme_inputs.py`](../scripts/01_build_theozyme_inputs.py) writes to
[`results/theozymes/`](../results/theozymes/): one plain mmCIF per candidate and one `theozymes.yaml` with one design
per candidate (11: the slots recommended in the pre-analysis). The spec is RFD4's YAML condition spec
([docs](https://github.com/RosettaCommons/RFD4-Proteina), `docs/how-to/input_prep/yaml-json.md`): `rfd4-generate`
builds the annotated CIF from it in memory, and the RFD4 helper `scripts/write_condition_spec_cifs.py` writes the
annotated CIFs out for inspection. The spec route was chosen over the Python API because it is readable data that
diffs in git and has a built-in dry run.

Per design:
| Part | In the spec |
|---|---|
| Input CIF | motif residues renumbered 1..n in chain A (polymer), the 6NT as chain B residue 1; coordinates unchanged from the candidate PDB (checked by the script) |
| Scaffold | `contig: "EX1:160-240, A1-n, /0, B1"`: one expandable segment of 160–240 residues, so designs are 160+n … 240+n long (organizers' limit: 260) |
| `C_CRD` (fixed coordinates) | all 6NT atoms; for each motif residue CA + side chain, or N,CA,C,O for the N–H donors |
| `C_SEQ` (fixed identity) | residues whose side chain is fixed, and the 6NT (RFD4 rejects fixed non-backbone coordinates without a known identity); backbone-only donors (Met237, Gly97 N–H) stay free |
| `C_IDX: false` (unindexed) | every motif residue, one index group each: the model chooses where in the chain it sits |

Which atoms are fixed follows each candidate's own `fix atoms for motif scaffolding` remark: side chain + CA by
default (also for the base and the dyad), backbone N,CA,C,O for the backbone donors. Fixing a side-chain coordinate
fixes that residue's identity as well ([conditioning concepts](https://github.com/RosettaCommons/RFD4-Proteina),
`docs/concepts/conditioning.md`).

## Choices to review
- **Side chain + CA fixed for the base** (not only the carboxylate): this pins CB and CG too, which is stricter than
  the scored contact. A tips-only variant would leave the scaffold more room; not built.
- **Scaffold length 160–240** is my guess (HG3.17 and the KE series are about 250 residues; M-CSA benchmark inputs use
  180). Change it with `--seg_min` / `--seg_max`.
- **Backbone-donor identity left free**: the model may place Pro there, which has no N–H. Check the N–H donor
  residue in every design.
- **Not conditioned**: `C_HB` (donor/acceptor roles on 6NT), `C_PISTACK` on the stacker rings, `C_RAS` (burial of the
  6NT). They would reinforce the contacts but are extra levers; add them once the plain inputs run.
- **Formal charges are written explicitly** (`pdbx_formal_charge`, no `?`): 6NT as in its CCD entry (nitro N +1, O21 −1,
  the rest 0), −1 on one carboxylate oxygen of the base (Asp OD2 / Glu OE2) and of the dyad Asp, 0 elsewhere. RFD4
  embeds the charge of atomized tokens (the 6NT); for a canonical residue the benefit is unclear, and the CCD form of
  Asp/Glu is the neutral acid, so `--base_charge=0` writes that instead. See "How RFD4 uses charges" below.
- **Bond orders and aromaticity of the 6NT** are left to RFD4's parser, which should take them from the CCD entry `6NT`.
  RFD4 reads a bond left as aromatic as a single bond, so check the kekulized bonds on Euler.

## How RFD4 uses charges
Read from its code and docs on 2026-11-21:
- The model embeds formal charge per atom in 11 classes (−4 … +6, out-of-range clamped), initialised from sin/cos of the
  charge. `AtomChargeSeqFeat` applies it only to **atomized tokens** (ligands, non-canonical residues): the 6NT, not the
  protein residues. A second feature, `Atom37ElementChargeEmbeddingSeqFeat`, combines element and charge at every occupied
  atom37 slot; I did not find where it is switched on, so I do not know if protein charges reach the model.
- An unknown charge (`?`) is read as 0 or the CCD value, not as "unknown"; RFD4's checker warns about it (and about a
  mix of known and unknown) because that hides the difference from neutral. The benchmark CIFs leave most atoms `?`
  and write only Lys NZ and Arg NH2 (+1), the CCD values.
- No training definition for charges is documented, and the CCD form of Asp/Glu is the neutral acid. A −1 carboxylate
  may therefore lie outside what the model saw for a canonical residue. Whether the explicit charge helps is untested;
  compare designs with `--base_charge=-1` and `0` if it matters.

## Check it on Euler before spending GPU time
From the RFD4-Proteina checkout, with its venv active (a CPU job is enough; not on a login node for anything long):

```bash
python scripts/write_condition_spec_cifs.py <repo>/results/theozymes/theozymes.yaml --out-dir $SCRATCH/kemp/theozyme_cifs
bash skills/rfd4-proteina-annotated-cif/scripts/check_annotated_cif.sh $SCRATCH/kemp/theozyme_cifs/<design>.cif
```

The first prints a summary of what RFD4 understood (fixed atoms, unindexed residues, length) and stops if a safeguard
fails; the second checks the file's chemistry and conditions. Compare the printed counts with the table above. Then a
first design: `rfd4-generate inputs=<repo>/results/theozymes/theozymes.yaml subset_to_examples=A_top_observed__V00001 ...`.

## Not verified
- That RFD4 parses the hand-written CIFs (entity blocks, `label_seq_id` for the ligand, the `pdbx_formal_charge` column).
- That `sel('A/*/1/[CA,CB,...]')` and the contig resolve as intended (contig `res_id`s refer to `label_seq_id`).
- That the Euler RFD4 checkout has the `scripts/` and `skills/` directories used above.
