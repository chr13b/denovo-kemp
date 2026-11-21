# Kemp eliminase design campaign: published structures and theozyme components

Collected 2026-11-21 from RCSB PDB, the Fleishman-lab `denovoKemp` GitHub repo, and Europe PMC.
Everything below was checked against RCSB entry metadata or the papers' open-access text, except where marked **(unverified)**.

## Layout

| Path | Contents |
|---|---|
| `structures/core/` | 29 curated entries (.cif + .pdb): original designs, TS-analog (TSA) complexes, 2025 computational designs, de novo Kemp TIMs |
| `structures/scaffolds/` | Parent scaffolds and source folds (.cif + .pdb): 1THF, 1JCL, 1A53, 1GOR, 1LBF, 1I4A, 1JCM, 1VC4, 4FB7 |
| `structures/extended/` | 71 further Kemp eliminase entries (.cif only): KE07 evolution series, KE70/KE59 variants, HG3.x, HG-series, KABLE |
| `ligands/` | CCD definitions + ideal SDF for 6NT, 3NY, 0CU, 0CT, VWF, H5J (5-nitro-1,2-benzoxazole = substrate core), 6VP (product) |
| `theozyme/rosetta_denovoKemp/` | Rosetta theozyme + matcher/design files from the Listov 2025 repo (see below) |
| `theozyme/extracted/` | Per-TSA-complex active-site shells, contact tables, and `aligned/` (all shells superposed on one TSA frame) |
| `theozyme/theozyme_ensemble.pse` | PyMOL session of all 33 superposed sites |
| `structures/aligned_on_substrate/` | **Full structures aligned on the substrate/TSA frame**: `direct/` (19 core, ligand-fitted), `extended/` (19 extended-tier, ligand-fitted), `transferred/` (8 ligand-free), `alignment_summary.csv`, `aligned_on_substrate.pse`. Script: `theozyme/align_full_structures.py` |
| `theozyme/THEOZYME_ORIGIN.md` | How the theozymes were derived (QM, motifs, scaffolds), design lineage, lessons, evidence labels |
| `theozyme/extract_theozyme.py`, `superpose_theozyme.py` | Scripts that produced the above (re-runnable) |
| `code/denovoKemp/` | Full Fleishman-lab pipeline repo (commit `c2a7421`, 2025-09-18; see `code/denovoKemp_COMMIT.txt`): backbone assembly, PROSS, matching/design, filtering, FuncLib/stabilisation, `working_pdbs/` |
| `code/zenodo_14563437/` | Zenodo package (CC-BY-4.0): Amber MD and Q6 EVB inputs, substrate parameters, Des27/Des27.7 starting structures with and without substrate |
| `figures/` | **Design-vs-activity charts**: `kemp_design_vs_activity.html` (interactive, with table views, light/dark), `svg/` (4 standalone charts), `data/` (`data.json`, `designs.csv`, `geometry.csv`). Rebuild: `python3 figures/make_geometry.py && python3 figures/make_data.py && node figures/build.js` |
| `metadata/entries.csv` | All 100 Kemp-relevant PDB entries (tier, title, protein, resolution, ligands, DOI) |
| `metadata/rcsb_details.json` | Raw RCSB GraphQL details used to build the table |

**Origin, design history, best published kcat/KM per theozyme, and caveats: see [`theozyme/THEOZYME_ORIGIN.md`](theozyme/THEOZYME_ORIGIN.md) (section 3b for performance).**

## Full structures aligned on the substrate

`structures/aligned_on_substrate/`, reference frame 7K4Q chain A (HG3 + 6NT). Each file holds the ligand-binding chain plus its ligand, in the common frame.

- **`direct/` (19)**: fitted on the benzotriazole core (+ nitro N where present) of the bound TSA, 0.01–0.06 Å RMSD. Includes the two modelled substrate complexes `Des27_sub` and `Des27.7_sub` (Zenodo, real 5-nitrobenzisoxazole, mapped by bond topology: substrate C3-H ↔ TSA N3, ring O ↔ N1).
- **`extended/` (19)**: every extended-tier entry that contains a TSA, same fit (0.01–0.06 Å): HG3.x/HG4 variants (5RGB–5RGF, 7K4U, 7K4X, 8USH/J/L), the HG3.17 Q50 series (6SRW, 6SRY, 6SRZ, 6SS1, 6SS3, 6TU6), KE59 R13 (3UZ5, 0CU), HG3.17 with the cyano analog (8KH3, 5-cyanobenzotriazole; nitrile C stands in for the nitro N) and the KABLE2.5 NMR structure (29SB, model 1). Chain/ligand copy used is listed in `alignment_summary.csv`; 6TU6 has 16 copies and the first one meeting the ≥8-residue test (chain P) was used.
- **`transferred/` (8)**: ligand-free structures superposed on a fitted homolog, so they inherit the frame: 3NPV→3Q2D, 3UXA→3UXD, 3NYZ→3NZ1, 3O2L→3NYD, 9U01→9TZD (protein CA RMSD 0.27–0.44 Å, good); 9HVB, 9HVG, 9HVH→Des27.7 by structural alignment (2.2, 2.8, 3.4 Å, **low confidence**, especially 9HVG/9HVH).
- **Not aligned**: KE07 (2RKX, 4Z08) has no ligand complex and its HisF fold is too different to transfer reliably.
- Skipped ligands: 9N0J sites A201/A202 (crystal-contact-like), extra copies in multi-chain entries (first chain only). The remaining extended entries have no TSA (apo, product 6VP, other ligands) and were not aligned.

What the aligned frame shows (`its_O_to_N3_A` column in `alignment_summary.csv`):
- The base carboxylate sits at the **N3 side** (the site mimicking the substrate C3-H) in HG-series (Asp127, 2.2–2.6 Å), 9N0J (Asp49, 2.47 Å), Des27/Des27.7 models (Asp162, 2.7 Å) and the 9HVB crystal structure (Asp162, 2.5 Å).
- In **3NZ1, 8FOQ, 6NW4 (Glu178) and 9TZD (Asp24)** the carboxylate sits ≈4.5–4.7 Å from N3 because it contacts **N1** (≈2.6 Å) instead: the TSA binds with its ring on the opposite side of the base compared with HG3, with the nitro group overlaid. This means a single base position does not fit all TSA complexes; treat these as a distinct binding mode.
- For 3UXD (0CU) and 3UZJ (0CT) the N1/N3 labelling is a choice, made so the base-contacting N is N3 (symmetric ring), so their 2.5–2.7 Å values are by construction, not a finding.
- The 19 extended entries all agree with the N3-side picture: Asp127 2.4–2.8 Å from N3 in all HG-family entries (including every Q50 variant and the cyano-analog complex 8KH3), Glu231 in KE59 R13 (3UZ5, by construction), and Asp49 at 2.65 Å in the KABLE2.5 NMR structure (consistent with 9N0J). No further N1-side complexes appeared.
- KE70 complexes use a His base, so the Asp/Glu column does not apply (8FOR His16 ND1 to N3 is 3.0 Å from the extraction table).
- Correction made along the way: the earlier shell superposition (`theozyme/extracted/aligned/`) mapped 0CT with the opposite flip; it is fixed and re-run.

## Theozyme definition (source files)

`theozyme/rosetta_denovoKemp/2.MatchDesign/1.Match/`
- `theozime.cst`: Rosetta enzdes constraints, two blocks:
  1. **Base**: Asp/Glu carboxylate (`OOC`, residue types `DE`) to ligand atoms `C7 C1 N1`, d = 2.93 Å, angle_A 127.6°, angle_B 120°.
  2. **π-stack**: Trp/Phe/Tyr aromatic C to the ligand virtual ring-centre atom `X1` (`X1 C5 C6`), d = 4.5 Å, both angles 90°.
- `UNK_virt.params`: the substrate-like ligand (isoxazole O1/N1/C7-H4, nitro N2/O2/O3, virtual `X1`). Reactive C7–H4 is the one the base attacks.
- `matcher_flags`, `bb1000_0001.pos` (12 matched positions), `2.Design/` (design xml + enzdes flags). The flags contain absolute paths from the authors' cluster; edit before reuse.
- Author note: the theozyme "builds on a catalytic constellation derived from quantum-mechanical calculations" (refs 47, 48 in the Nature paper): base + π-stacking aromatic, and in earlier designs an extra polar interaction with the nitro group.

## Catalytic constellations observed in TSA complexes

From `theozyme/extracted/theozyme_summary.csv` (≤3.6 Å base to ring N, π-stack ≤5.5 Å and ≤40° ring-normal angle, nitro H-bonds ≤3.5 Å):

| Family (scaffold) | PDB (TSA) | Base | π-stack | Nitro contacts |
|---|---|---|---|---|
| HG-2 / HG3 / HG3.17 / HG3.R5 / HG649 (xylanase) | 3NYD, 5RGA, 7K4Q, 7K4Z, 4BS0, 8FOS, 8USF, 8RD5 | Asp127 | Trp44 (≈5 Å; some entries beyond cutoff) | Met237 backbone NH |
| 1A53-2 / KE59-like / 6NW4 (IGPS) | 3NZ1, 8FOQ, 6NW4 | Glu178 | Trp110 + Trp210 | Arg53 NE, Ala81 O (6NW4) |
| KE59 R1 7/10H (IGPS) | 3UXD (0CU), 3UZJ (0CT) | Glu231 | Trp110 | none in analogs lacking nitro |
| KE70-core (DERA) | 8FOR (6NT) | His16 ND1 (≈3.0 Å) | Phe48 | none |
| KE70 variant | 3Q2D (3NY) | no base within 3.6 Å | Phe49, His17 | Ser102 OG |
| KempTIM1 (de novo TIM) | 9TZD | Asp24 | none | Gly97 NH, Val71 O |
| KABLE (de novo) | 9N0J | Asp49 | none | Trp20 NE1 |

Caveats:
- 9N0J has three modelled ligands. Only the A203 site (Asp49/Trp20) looks like the active site; A201 and A202 touch only 5–7 residues and are probably crystal-contact binders. **(not confirmed against the paper)**
- The KE70 row is a detector result, not a literature statement: the script found His16 (8FOR numbering) H-bonding the ring N. The literature describes a His–Asp dyad for KE70; I did not confirm the Asp partner from the structure.
- **No KE07 structure with a bound TSA exists in this set** (2RKX, 4Z08 and the 5D2x/6Cxx evolution series are all ligand-free). KE07's base (Glu) is therefore not extracted here **(unverified)**.
- Theozyme residue numbering differs between entries; use `theozyme/extracted/aligned/` for a common frame.

## Core entries (what each is)

- **Original designs**: 2RKX (KE07 on HisF/1THF, 95% id to 1THF), 3NPV and 3Q2D (KE70 on DERA/1JCL, 94% id), 3UXA/3UXD/3UZJ (KE59 on 1A53/IGPS, 93% id), 3O2L (HG-1, inactive, xylanase fold), 3NYZ/3NZ1 (1A53-2).
- **Directed-evolution endpoints with TSA**: HG3 (5RGA, 7K4Q), HG3.17 (7K4Z, 4BS0), HG3.R5 (8RD5), HG649 (8USF), 6NW4 (evolved IGPS design).
- **Core/shell dissection (2024)**: 8FOQ (1A53-core), 8FOR (KE70-core), 8FOS (HG3-shell), each with TSA.
- **Complete computational designs (Listov 2025)**: 9HVB = Des27.7 (catalytic Asp162, kcat/KM 12,700 M⁻¹s⁻¹), 9HVG = Des49, 9HVH = R2.Des39; all ligand-free. IGPS source fragments: 1LBF, 1I4A, 1JCM, 1VC4, 4FB7 (in `scaffolds/`).
- **De novo folds**: KempTIM1 (9TZD with TSA, 9U01 apo), KempTIM4 (9QKX), KABLE (9N0J).

## Scaffold parentage (checked by sequence identity against the PDB files)

KE07 → 1THF (0.95) · KE70 → 1JCL (0.94) · KE59 / 1A53-2 → 1A53 (0.93–0.95) · HG-1/HG-2/HG3 → *T. aurantiacus* xylanase 1GOR (0.977; confirmed as the design scaffold by Otten et al. 2020, Science, who cite "PDB 1gor").

## Designed substrate poses (Zenodo)

`code/zenodo_14563437/Classical_MD_Simulations/Classical_MD_Simulations/Starting_Structures/`: `Des27_liganded.pdb`, `Des27.7_liganded.pdb` (plus unliganded). Substrate is residue `MOL` (16 atoms, 5-nitrobenzisoxazole; AMBER parameters in `Parameter_SUB/SUB.frcmod`, `EVB_Simulations/.../SUB.lib`). In both, Asp162 OD1 sits 1.64 Å from the abstracted substrate H (`H1`), and the shell within 4 Å includes Phe113, Ile216, Val134, Ile160 and residue 84 (Thr in Des27, Val in Des27.7). The 1.64 Å H–O distance is a modelled pre-reaction pose, not a crystal measurement. These are the nearest thing here to a design-stage Kemp theozyme on the IGPS fold. `EVB_Simulations/.../0_starting_structures/` holds IN/OUT variants for Des27 and Des27.7.

The full `denovoKemp` repo has no licence file, so check with the authors before redistributing outside the team. `theozyme/rosetta_denovoKemp/` is a subset of the same repo, kept for convenience.

## Not downloaded

- Original Röthlisberger 2008 Rosetta theozyme/constraint files: not found in an open source during this search.
- Paper PDFs (Nature, PNAS and JMB are paywalled or login-gated from here; only the Listov paper and Otten 2020 have open full text on Europe PMC).

## Key literature

- Röthlisberger et al., Nature 2008, [10.1038/nature06879](https://doi.org/10.1038/nature06879): KE07/KE59/KE70 original designs
- Khersonsky et al., J Mol Biol 2011, [10.1016/j.jmb.2011.01.041](https://doi.org/10.1016/j.jmb.2011.01.041): KE70 optimisation
- Privett et al., PNAS 2012, [10.1073/pnas.1118082108](https://doi.org/10.1073/pnas.1118082108): iterative design, HG-1/2/3, 1A53-2
- Khersonsky et al., PNAS 2012, [10.1073/pnas.1121063109](https://doi.org/10.1073/pnas.1121063109): KE59 evolution
- Blomberg et al., Nature 2013: HG3.17 (4BS0)
- Otten et al., Science 2020, [10.1126/science.abd3623](https://doi.org/10.1126/science.abd3623) (open: PMC9616100): HG3.17 ensemble / energy landscape (7K4x)
- Listov et al., Nature 2025, [10.1038/s41586-025-09136-2](https://doi.org/10.1038/s41586-025-09136-2) (open: PMC12310539): complete computational design (9HVB/G/H)
- KempTIM / de novo TIM barrels: [10.1038/s41589-026-02250-w](https://doi.org/10.1038/s41589-026-02250-w) (9TZD, 9U01, 9QKX)
- HG3.R5 / 6NT complexes: [10.1038/s41589-024-01712-3](https://doi.org/10.1038/s41589-024-01712-3) (8RD5)
- HG649/630/198/185 series: [10.1021/jacs.4c00677](https://doi.org/10.1021/jacs.4c00677) (8USx)
- Core/shell entries (8FMC–8FOS), KABLE (9N0I/J/K, 9SMT, 29SB): RCSB lists no linked publication; find the paper before citing.
