# [2026-11-21 16:52] fix | 6NT needs sequence conditioning in the theozyme specs (mario)

- Euler's `check_annotated_cif.sh` on a theozyme input reported `coord_conditioned_must_be_seq_conditioned` for `B/6NT1`: the 6NT had fixed coordinates but no `C_SEQ`. `scripts/01_build_theozyme_inputs.py` now adds `sel('B')` to `C_SEQ`; `results/theozymes/theozymes.yaml` regenerated, test and `wiki/theozyme-inputs.md` updated.
- Not changed: warnings `component_ccd_atom_set_mismatch` (the `EX1` placeholder, expected), `struct_conn_ok` (informational) and `formal_charge_unknown` (89 of 91 atoms `?`; whether to write explicit charges for the Asp/Glu base and the nitro group is still open).
- Not re-checked on Euler yet: pull this commit there and run the check again.
