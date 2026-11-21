# Glossary

Domain and project terms, in alphabetical order. Add a term the first time it shows up in the wiki.

- **Kemp elimination**: a model reaction widely used to benchmark computationally designed enzymes.
- **kcat/KM**: catalytic efficiency (M⁻¹ s⁻¹), the usual headline metric for designed enzymes.
- **Raw source**: an immutable input document in `raw/`.
- **Run**: one execution of a script. Its output lives in `runs/<timestamp>_<name>/`.
- **Kemp elimination**: the model reaction we design for; the base deprotonates C3 of a benzisoxazole (ligand **6NT**).
- **base= / oxy=**: the catalytic base (D/E) and oxyanion-hole donor (Q/N/S/T/Y/K/R) declared per design, as **1-based** indices.
- **iPDE**: interface predicted distance error from Boltz-2 over the protein-ligand interface; lower is better.
- **TM-score**: structural similarity to a published structure; **> 0.7 disqualifies** a design.
- **Slurm**: the cluster job queue. `run.sh`/`sbatch` submits a job, `squeue` shows its status.
- **Head node vs worker**: the machine SSH lands on (no GPU, for editing and submitting) vs the GPU machine Slurm assigns.
- **MSA**: multiple sequence alignment, built by MMseqs2; needs the big node (~28 GB RAM).
