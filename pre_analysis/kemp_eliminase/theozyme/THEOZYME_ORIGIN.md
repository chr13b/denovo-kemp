# Origin of the Kemp eliminase theozymes and design context

Evidence labels: **[paper]** = read in open-access full text (Listov 2025 PMC12310539, Otten 2020 PMC9616100);
**[abstract]** = from the Europe PMC abstract only; **[summary]** = from a web-page summary of the paper, not read directly;
**[file]** = read directly from a file in this folder; **[memory]** = from my background knowledge, not checked against a source.
Röthlisberger 2008, Privett 2012 and Khersonsky 2011/2012 are paywalled from here, so their full methods and SI were not read.

## 1. The reaction and what a "theozyme" is

- Kemp elimination: base-promoted ring opening of 5-nitrobenzisoxazole to 2-cyano-4-nitrophenolate. The base removes the C3-H proton while the N–O bond breaks. No natural enzyme is known to have evolved for it, which is why it became the standard test for de novo enzyme design **[paper, Listov intro]**.
- Theozyme = a quantum-mechanical (QM) model of the transition state plus the minimal set of catalytic groups placed ideally around it, to be then fitted into a protein scaffold. The concept is from Tantillo, Chen and Houk (Curr Opin Chem Biol 1998, doi 10.1016/S1367-5931(98)80112-9) **[paper: ref 48 in Listov]**.
- Origin of the Kemp theozyme chemistry: Na, Houk and Hilvert, *J Am Chem Soc* 1996, 118, 6462, "Transition state of the base-promoted ring-opening of isoxazoles. Theoretical prediction of catalytic functionalities and design of haptens for antibody production" (doi 10.1021/ja953550j). Listov 2025 states its theozyme "builds on a catalytic constellation derived from quantum-mechanical calculations" and cites this paper and the 1998 theozyme review **[paper]**. The benzotriazole TS analogs (6NT, 3NY) used in the crystal structures come from this hapten/TSA tradition **[memory]**.

## 2. First-generation theozymes (Röthlisberger 2008, Baker/Tawfik/Houk labs)

- Eight enzymes were designed with **two different catalytic motifs**, with rate enhancements up to 10⁵; a crystal structure (KE07, 2RKX) showed close to atomic accuracy; evolution of KE07 gave >200-fold more kcat/KM (2,600 M⁻¹s⁻¹) **[abstract]**.
- Motif with a carboxylate base: KE07 uses a Glu side chain as base plus an apolar binding site **[web-search summary]**. KE59 (IGPS/1A53): designed E230 as base (design numbering; Glu231 in the PDB files, n+1), W109 added for π-stacking/charge delocalisation, and S179 and S210 to H-bond the nitro group, inside a tightly packed hydrophobic pocket **[paper, Khersonsky 2012 PMC3387081]**.
- Motif with a His–Asp dyad: KE70 uses His17–Asp45 as base, Tyr48 for π-stacking and Ser138 as H-bond donor to the phenolic oxygen. Residue positions relative to the transition state were optimised by QM. Scaffold is *E. coli* DERA (1JCL). RosettaMatch searched natural scaffolds for backbones that place the catalytic groups, replacing 12–20 residues **[summary of Khersonsky 2011, PMC3889864]**.
  - Numbering note: KE70 PDB variants carry insertions (263–272 residues), so Phe48/49 and Ser102 in 3Q2D/8FOR are likely the same positions as the design's Tyr48/Ser138 after mutation and renumbering, but I did not map them **[memory-level inference]**.
- Common features across designs: base to the reactive C–H, π-stacking aromatic on the benzo ring, and (in the original designs) a polar contact to the isoxazole/phenolate oxygen **[paper, Listov: "typical design studies also introduced a polar interaction with the isoxazole oxygen"]**.
- Pipeline: scan natural TIM-barrel and other scaffolds with RosettaMatch, then Rosetta design of the surrounding pocket; the best designs were then improved by library screening **[abstract + summary]**.

## 3. Lessons from the design-and-test cycles

| Series | Scaffold | Outcome |
|---|---|---|
| KE07 | HisF (1THF) | design 12 M⁻¹s⁻¹; best evolved variant 2.6×10³ **[paper, Khersonsky 2012]** |
| KE70 | DERA (1JCL) | design 126 ± 4 M⁻¹s⁻¹ (Table 1 of Khersonsky 2011; the text of that paper says ≈80); best evolved ≈5.5×10⁴ (R6 4/8B: 57,300 ± 6,140) **[paper]** |
| KE59 | IGPS (1A53) | design ≈160 M⁻¹s⁻¹ (most efficient of the series but unstable); consensus-stabilised, best variant R13-3/11H 60,430 ± 2,000 with 5-nitrobenzisoxazole (≈380-fold) and 573,090 ± 19,160 with the more reactive 5,7-dichlorobenzisoxazole **[paper, Khersonsky 2012 Table 1]** |
| HG-1 → HG-3 | *T. aurantiacus* xylanase (**1GOR**, confirmed) | HG-1 inactive; MD and crystallography blamed bound waters and flexible active-site residues; the design was moved deeper into the protein (HG-2). In the HG-2/TSA co-crystal the TSA bound to the intended base but was **flipped relative to the design model**; one more point mutation gave HG-3 (3× better) **[abstract, Privett 2012]** |
| HG3 → HG3.17 | xylanase | 17 rounds of evolution gave ~6×10⁸-fold rate acceleration, 1.09 Å structure (4BS0) **[abstract, Blomberg 2013]**; kcat/KM ≈ 2.3×10⁵ M⁻¹s⁻¹ **[web-search summary]** |

Relevant findings from the HG3 lineage (Otten 2020, **[paper]**):
- HG3.17 improved alignment of substrate and catalytic base (**Asp127**) and gained a new H-bond donor for oxyanion stabilisation (**Gln50**; the 6SRx structures are Q50 variants).
- The original xylanase scaffold 1GOR has only an inactive backbone conformation near the active site (Leu236 carbonyl clashes with the TSA nitro group). Evolution populated the active state. In your structures this is the Leu236/Met237 region.
- Directed evolution reshaped the conformational ensemble, which a fixed-backbone theozyme match cannot see.

## 3b. Best published catalytic performance per theozyme

kcat/KM in M⁻¹s⁻¹ for 5-nitrobenzisoxazole unless stated. "Computational only" = no library screening; "evolved" = directed evolution in the loop. Numbers are as reported in the cited abstract or full text; I did not re-derive any from raw data. Conditions (pH, temperature, buffer) differ between papers, so compare orders of magnitude, not small differences.

| Theozyme (base / π-stack / scaffold) | Original design | Best computational only | Best evolved | Source |
|---|---|---|---|---|
| **KE07**: Glu base, apolar pocket / HisF (1THF) | **12** (text elsewhere says ≤10; Khersonsky 2011 says ≈10) | n/a | **2.6×10³** | **[paper]** Khersonsky 2012 PMC3387081 (design and evolved values in one sentence) |
| **KE70**: His17–Asp45 dyad, Tyr48 π, Ser138 H-bond / DERA (1JCL) | **126 ± 4** (Khersonsky 2011 Table 1; text ≈80; 57 in the 2024 ensemble study under different conditions) | ensemble-based redesign: 100–250-fold gain, i.e. up to ≈1.4×10⁴ (derived from 57 × 250, not stated) | **≈5.5×10⁴** (best listed variant 57,300 ± 6,140, 6 rounds) | **[paper]** Khersonsky 2011 PMC3889864 and 2012 PMC3387081; JACS 2024 **[abstract]** |
| **KE59**: E230/E231 base, W109/W110 π, S179 + S210 nitro H-bonds / IGPS (1A53) | **≈160** (stated as ≥160 in the text) | n/a | **6.0×10⁴** with 5-nitrobenzisoxazole (R13-3/11H, 13 rounds); 5.7×10⁵ with 5,7-dichlorobenzisoxazole, a more reactive substrate | **[paper]** Khersonsky 2012 Table 1 |
| **HG series**: Asp127 base, Trp44 π, later Gln50 / *T. aurantiacus* xylanase (1GOR) | HG-2 = 123 (substrate saturation not reached); HG-3 = 425 ± 37 (kcat 0.68 s⁻¹, KM 1.6 mM) in Privett 2012, and HG3 = 125 in the 2024 study (conditions differ) | ensemble-based redesign from HG3: 100–250-fold, i.e. up to ≈3×10⁴ (derived from 125 × 250) | HG3.17 ≈2.3×10⁵ (**~6×10⁸-fold** over uncatalysed reaction); HG3.R5 (5 rounds) >10⁸-fold, similar to HG3.17 | **[abstract]** Blomberg 2013, Nat Chem Biol 2024, JACS 2024; 2.3×10⁵ **[web-search summary]** |
| **1A53-2 (Privett 2012 redesign on IGPS; Glu178 base, Trp110 + Trp210 π in 3NZ1)** | **64.2 ± 11.6** (kcat 0.09 ± 0.01 s⁻¹, KM 1.4 ± 0.2 mM); sister designs 1A53-3 = 20.6, 1THF-2 = 7.9, 1A53-1 and 1THF-1 inactive | n/a | not evolved in that paper. The 6NW4 lineage reports ~4 orders of magnitude gain over 9 rounds, absolute value not in its abstract, and I did not confirm 6NW4 derives from 1A53-2 | **[paper]** Privett 2012 Table 1 (pH 7.25, 25 °C); 6NW4 **[abstract]** JACS 2019 |
| **Listov 2025 IGPS theozyme**: Asp162 base, Phe113 π, no polar contact / chimeric IGPS | Des27 = 130; Des61 = 210 | **Des27.7 = 12,700, kcat 2.85 s⁻¹**; with one further engineered residue >10⁵ and kcat ≈30 s⁻¹ | none (no library screening) | **[paper]** Listov 2025 |
| **KempTIM (CANVAS)**: Asp24 base / de novo minimal TIM barrel with designed lid | n/a | up to 21,000 from design; 32,000 after ensemble-based design | none | **[abstract]** 10.1038/s41589-026-02250-w |
| **KABLE**: Asp49 / de novo 127-residue protein | n/a | no kinetics found | no kinetics found | n/a |

Reading the table:
- Highest absolute numbers: HG3.17 (≈2.3×10⁵ with 5-nitrobenzisoxazole) and KE59 (≈6×10⁴ with 5-nitrobenzisoxazole, 5.7×10⁵ only with a more reactive substrate), both after many rounds of directed evolution. Do not compare the KE59 5.7×10⁵ figure directly with the others.
- Best **without** screening mutant libraries: Listov 2025, with Des27.7 at 12,700 and the engineered extra residue pushing it above 10⁵ (30 s⁻¹). The KempTIM paper reports 21,000 to 32,000 without library screening.
- Earlier computational-only starting points were weak (1–420 M⁻¹s⁻¹, kcat 0.006–0.7 s⁻¹ across the first-generation designs **[paper, Listov intro]**), so the gap between motif families is mostly set by scaffold and active-site optimisation, not by which carboxylate-or-dyad base was used.
- The "residue considered essential" that Listov 2025 redesigned to exceed 10⁵ is described only in the abstract; I did not read which residue it is, so check the paper before relying on it.

## 4. Latest theozyme: Listov et al., Nature 2025 (Fleishman lab)

**[paper]** unless marked **[file]**.
- Theozyme: a nucleophile (Asp or Glu) as base for proton abstraction, plus an aromatic side chain π-stacking the substrate in the transition state. In earlier designs the π-stack was "used in all previous computational Kemp eliminase design studies".
- Deliberately excluded: the polar contact to the isoxazole oxygen. Reasons given: a water can satisfy it, and a misplaced polar group could lower the pKa of the catalytic base and so reduce reactivity.
- Fold choice: IGPS TIM barrels, which can sterically accommodate 5-nitrobenzisoxazole and were used for earlier designs.
- Pipeline: (1) combinatorial assembly of backbones from five IGPS structures (1LBF, 1I4A, 1JCM, 1VC4, 4FB7), segmented at positions 44, 105, 154, 206; (2) PROSS stabilisation; (3) geometric matching of the theozyme plus Rosetta design of the whole active site, mutating all positions including the natural enzyme's vestigial catalytic residues; (4) filtering with a "fuzzy-logic" objective (energy, desolvation etc.); (5) FuncLib-style active-site optimisation (homology restrictions removed) and pSUFER. Code: `code/denovoKemp/`.
- Results: 73 designs tested, 66 soluble, 14 with cooperative melting, 3 active; Des27 and Des61 at 130 and 210 M⁻¹s⁻¹. Energy-based redesign of the active site gave Des27.7 (7 mutations) at 12,700 M⁻¹s⁻¹ and kcat 2.85 s⁻¹, >140 mutations from any natural protein. Crystal structure 9HVB matched the design within 0.7 Å all-atom RMSD over 20 active-site residues, including Asp162.
- Failure analysis: R2.Des39 (9HVH) and Des49 (9HVG) active sites were within 0.6 and 0.82 Å RMSD of the designs but several loops differed.
- Implementation of the constraint **[file: `rosetta_denovoKemp/2.MatchDesign/1.Match/theozime.cst`]**: block 1 carboxylate (OOC, residues D/E) to ligand `C7 C1 N1`, distanceAB 2.93 Å (σ 0.2), angle_A 127.6°, angle_B 120°, torsions 180°; block 2 aromatic (W/F/Y) to the ligand virtual ring-centre `X1` (`X1 C5 C6`), 4.5 Å (σ 0.2), angles 90°, torsions 90°. No polar-contact block, consistent with the paper.
- Data in this folder: Des27/Des27.7 substrate-bound models (Zenodo) and the 9HVB crystal structure.

## 5. What this means for your campaign

1. The theozyme is two components (carboxylate base + π-stack); polar stabilisation of the oxyanion is optional and was dropped in the best published design.
2. The observed TSA poses differ from design models: HG-2's TSA was flipped, and in your core set the stacking Trp44 in HG3-family complexes sits ~4.8–5.2 Å from the ring (the design value is 4.5 Å). Use the aligned shells in `extracted/aligned/` as empirical targets, not only the `.cst` values.
3. Natural scaffolds can pre-organise the wrong backbone (1GOR Leu236). Check backbone near the nitro group in any scaffold you pick.
4. Distinct base geometries are in the data: Asp127 (HG3), Glu178/Glu231 (IGPS), Asp162 (Des27), Asp24 (KempTIM1), Asp49 (KABLE), and the His dyad (KE70). Choose one and keep the matching consistent.

## 6. Not found / not verified

- Röthlisberger 2008 SI: QM level of theory, theozyme coordinates, the full scaffold list and the 59 designs.
- Privett 2012 design-procedure details beyond the abstract.
- Which numbering maps the KE70 design's Tyr48/Ser138 onto the PDB variants (see section 2).
- Whether the benzotriazole TSAs follow directly from the 1996 hapten design **[memory]**.
