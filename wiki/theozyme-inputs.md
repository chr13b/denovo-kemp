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
- **Chemistry of the 6NT** (bond orders, formal charges of the nitro group, aromatic bonds kekulized) is left to
  RFD4's parser, which should take it from the CCD entry `6NT`. RFD4 says aromatic bonds left unresolved are read as
  single bonds, so this is the first thing to check.

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
- That RFD4 parses the hand-written CIFs (entity blocks, `label_seq_id` for the ligand, no formal charges written).
- That `sel('A/*/1/[CA,CB,...]')` and the contig resolve as intended (contig `res_id`s refer to `label_seq_id`).
- That the Euler RFD4 checkout has the `scripts/` and `skills/` directories used above.
