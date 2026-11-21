# Nitro-group-stabilizing enzymes (PDB)

Search date: 2026-11-21. Source: RCSB PDB (search + data APIs).

## Files
- `curated.csv` – 57 hand-picked entries (pdb_id, category, title, resolution, bound ligands). Metadata pulled live from RCSB by `build_curated.py`.
- `build_curated.py` – regenerates `curated.csv` (edit the `CURATED` dict to add entries).
- `raw/comps.json` – 60 ligand component IDs matching aliphatic nitro substructure (`C[N+](=O)[O-]`).
- `raw/comps2.json` – 762 ligand component IDs (aliphatic + aromatic nitro, <=3-char IDs).
- `raw/ids.json` – 1409 PDB entries containing any of those ligands (includes many drug-like inhibitors; not curated).
- `raw/titles.json` – `{pdb_id: [title, resolution, [polymer descriptions]]}` for those 1409 entries; grep this to filter further.

## Nitro-contact analysis
- `nitro_contacts.py` – downloads each curated entry's mmCIF into `structures/`, finds nitro/nitronate groups (N bonded to 2 O + 1 heavy atom) in hetero residues, and lists everything with an atom within 4.0 A of a nitro atom. Crystal-symmetry mates excluded. Needs `gemmi` (`pip install gemmi`); run from this folder.
- `nitro_contacts.csv` – one row per (nitro group, contacting residue/ligand/water): closest distance + atom pair, and the closest N/O contact to a nitro oxygen if <= 3.5 A.
- `nitro_summary.csv` – one row per entry: number of nitro groups, protein residues within 3.5 A polar contact of a nitro O (`xN` = how many nitro groups, i.e. ligand copies in the ASU, see it), and all protein residues within 4.0 A.
- Residue numbers are the author numbering from each entry (not aligned across entries).
- "Polar contact" = any protein N/O within 3.5 A of a nitro O; donor/acceptor geometry and angles are NOT checked, so some listed pairs are not true H-bonds. Waters and cofactors are in `nitro_contacts.csv` (`contact_kind`) but not in the summary.
- Entries with no nitro group in the structure (1DS7, 9GJX, 2C12, 4Q4K, 2BMO) are reported as such in the summary.

## Contact geometry and figures
Run in order (from this folder, needs `gemmi numpy pandas matplotlib`): `nitro_geometry.py` -> `nitro_plots.py`.
- `nitro_polar_geometry.csv` – one row per N/O atom (protein, water, cofactor) within 3.5 A of a nitro O (closest O only): distance `d_O_X`, `ang_N_O_X` (angle at the nitro O), `ang_X` (angle at the partner atom X = max over its bonded heavy neighbours of Y-X...O; empty for water), `elev_deg` (elevation of the O->X vector above the nitro plane; 0 = in plane).
- `nitro_local_frame.csv` – every heavy atom within 5 A of each nitro N, in the nitro's own frame (origin N, x = substituent->N, z = plane normal).
- `figures/`: `fig1_distance_by_partner`, `fig2_angles`, `fig3a/3b_distance_vs_angle_*` (one panel per partner type), `fig4_local_frame` (all nitro groups superposed), `fig5_by_family`.
- Only deposited coordinates are used (no symmetry mates). Contacts < 2.4 A (clash / covalent / disordered) are dropped from the figures but kept in the CSV.
- Hydrogens are not modelled, so `ang_X` is a heavy-atom proxy for donor directionality, not a true D-H...A angle. Donor vs acceptor identity of His N and of waters is not resolved.
- Entries are redundant (many Kemp eliminase / PETN reductase variants and multiple copies per ASU); counts are not independent observations.

## Motif table (input for annotated CIFs)
`nitro_motifs.py` (run after `nitro_geometry.py`) -> `motif_table.csv`, `motif_sites.csv`.
- One *site* per entry = the nitro-bearing ligand copy with the most motif residues (48 sites; 9 entries have no protein contact to the nitro).
- Motif residue = protein residue with an N/O within 3.5 A of a nitro O (`hbond`, 2.4-3.5 A) and/or an F/Y/W/H ring stacked on the nitro group (`pi`: ring centroid 3.0-4.6 A off the nitro plane, <= 2.5 A lateral, normals within 40 deg).
- `motif_table.csv`: one row per motif residue (author numbering): role, `contact_type` (sidechain / bb_NH / bb_O / bb+sidechain), contact atoms, d_O_X, angles, elevation, `pi_z_lat_ang`, `suggested_fix_atoms` (atom names to fix if you motif-scaffold this residue: backbone only for backbone contacts, side chain + CA otherwise, all heavy atoms for both), `representative` flag.
- `motif_sites.csv`: one row per site with `residues` and a compact `selection` string (chain+resnum list); `representative` = per family, most motif residues among entries <= 2.2 A.
- `bb_O` contacts are backbone carbonyl O near a nitro O (acceptor-acceptor): check before treating them as stabilising.
- Not yet done: building the annotated CIFs. AtomWorks is not installed here and the skill's reference docs (annotation names, condition levels) were not available, so `suggested_fix_atoms` is generic atom names, not annotation values.

## Caveats
- Curated entries were picked from title/ligand keyword filtering plus prior knowledge; I did not inspect the structures for actual nitro-contacting residues.
- Some curated entries are apo or lack a nitro ligand but belong to the same enzyme family as the nitro-bound ones (e.g. 1DS7, 2C12, 2BMO, 3BW3, 4Q4K, 9GJX, 1Z44 has p-nitrophenol only). Check the `ligands` column.
- Kemp eliminase "nitro" ligands are transition-state analogs (nitrobenzotriazoles); PETN/OYE/nitroreductase entries carry real substrates/inhibitors.
