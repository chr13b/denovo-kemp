# Literature

Reading list for this project. **PDFs are not committed** (copyright) — they download into
`data/papers/` (gitignored) with:

```bash
bash tools/fetch_papers.sh
```

Paywalled entries are listed with their DOI so you can get them through your institution.
The chemistry and method summaries distilled from these live in [primer.md](primer.md).

## The reaction and the enzymes we are imitating

| Paper | Why it matters | Have it? |
|---|---|---|
| **Blomberg et al. 2013**, *Nature* 503:418, [10.1038/nature12623](https://doi.org/10.1038/nature12623) — "Precision is essential for efficient catalysis in an evolved Kemp eliminase" | **The single most relevant paper.** HG3.17, evolved from HG3, ~6×10⁸-fold rate enhancement. Our entire motif comes from its structure. Thesis: *precise placement*, not generic TS binding, is what buys catalysis. | paywalled — **but we have the structure, see below** |
| **PDB [4BS0](https://www.rcsb.org/structure/4BS0)** — HG3.17 at 1.09 Å with **6NT bound** | Better than the paper for our purposes: the actual coordinates, with the same ligand we are scored against. Measured targets: Asp127 OD2→N3 **2.53 Å**, Gln50 NE2→N1 **3.10 Å**, Trp44 NE1→N3 3.86 Å. | ✅ `data/pdb/4BS0.cif`, measured by `scripts/31_measure_reference_geometry.py` |
| **Privett et al. 2012**, *PNAS* 109:3790, [10.1073/pnas.1118082108](https://doi.org/10.1073/pnas.1118082108) — iterative design of HG3 | How HG3 (the parent of HG3.17) was designed, and what the design process got wrong before evolution fixed it. | paywalled |
| **Röthlisberger et al. 2008**, *Nature* 453:190, [10.1038/nature06879](https://doi.org/10.1038/nature06879) — KE07, the first designed Kemp eliminases | The origin of the whole benchmark. Shows how modest purely-computational designs were before evolution. | paywalled |
| **Kemp & Casey 1973**, *JACS* 95:6670 — the original Kemp elimination | The physical-organic chemistry: why this reaction is a clean probe of proton transfer from carbon. | paywalled |

Other Kemp structures downloaded for the novelty check (in `/mnt/work/tools/pdb_ref` on the cluster):
`3NYD` (HG3), `2RKX` (KE07), `3IIO`/`3IIV` (KE70), `1THF`/`1A53` (the TIM-barrel scaffolds).

## The methods in our pipeline

| Paper | Why it matters | Have it? |
|---|---|---|
| **RFdiffusion3** (2025), [PMID 41000976](https://pubmed.ncbi.nlm.nih.gov/41000976/) — "De novo design of all-atom biomolecular interactions" | **This is the model we are running** (RFD3). Generates structure in the context of ligands and other non-protein atoms. | see PubMed link |
| **RFdiffusion2** (2025), *Nat Methods*, [biorxiv 2025.04.09.648075](https://www.biorxiv.org/content/10.1101/2025.04.09.648075) — atom-level active-site scaffolding | Directly on our problem: scaffolds **41/41** enzyme active sites vs 16 for previous methods, with active hits from <96 sequences tested. Read its filtering strategy — that is our Idea 1. | ✅ ×2 (bioRxiv + Nat Methods) |
| **Watson et al. 2023**, *Nature*, [10.1038/s41586-023-06415-8](https://doi.org/10.1038/s41586-023-06415-8) — RFdiffusion | The original. Establishes the self-consistency idea (design → inverse-fold → re-predict → RMSD) that our CA-RMSD gate is an instance of. | ✅ |
| **Dauparas et al. 2022** — ProteinMPNN, [biorxiv 2022.06.03.494563](https://www.biorxiv.org/content/10.1101/2022.06.03.494563) | The inverse-folding method. Explains why LigandMPNN outputs a sequence and not a structure. | ✅ |
| **Dauparas et al.** — LigandMPNN, [biorxiv 2023.12.22.573103](https://www.biorxiv.org/content/10.1101/2023.12.22.573103) | The ligand-aware version we actually run. | ✅ |
| **van Kempen et al. 2023**, *Nat Biotech*, [10.1038/s41587-023-01773-0](https://doi.org/10.1038/s41587-023-01773-0) — Foldseek | The TM-score search we use for the novelty gate. | ✅ |
| **Boltz-2** (2025) | The cofolding model that produces the structure we are scored on, and `complex_ipde`. | not yet fetched |

## Our own prior work

| Paper | Why it matters here | Have it? |
|---|---|---|
| **Bertsch**, *Confidence is not competence: reading and steering protein binding with the inverse-folding mixed derivative* (preprint, ETH Zürich) | An inverse-folding model's **confidence** is a within-state scalar of the bound distribution and is blind to binding by construction; the binding signal is the **mixed derivative** — the response to ablating the partner. In our pipeline that ablation is one existing flag (`--ligand_mpnn_use_atom_context 0/1`), making **ligand leverage** a ~6 s feature. The paper's own caveat applies directly to us: the steering effect "vanishes on fully de-novo backbones", and ours are fully de novo — so use it as a **diagnostic**, not a steering knob. See [primer.md §6c](primer.md). | local, unpublished — not committed |

## Recent de novo enzyme design

| Paper | Why it matters | Have it? |
|---|---|---|
| **Lauko et al. 2025**, *Science*, computational design of serine hydrolases | State of the art for designing real catalytic machinery de novo; shows selection across the reaction coordinate rather than on one state. | ✅ |

## What to read first

1. **4BS0 geometry** (already measured) — this is our target.
2. **RFdiffusion2 bioRxiv §filtering** — how they decide which designs to test. Our Idea 1 in published form.
3. **Watson 2023 self-consistency** — the justification for using CA RMSD as a pass/fail gate.
