"""Build curated.csv: fetch title/resolution/ligands from RCSB for hand-picked nitro-enzyme entries."""
import csv, json, urllib.request

CURATED = {
 "Kemp eliminase (designed)": "3NYD 4BS0 7K4Z 5RGE 3NZ1 9TZD 8FOQ 8FOR 8FOS 6SRY 8RD5",
 "PETN reductase (OYE family)": "1GVR 1GVO 1GVS 1VYR 3F03 3P7Y 3P80 3P81",
 "Other ene-reductase / flavin reductase": "5K1W 5K1U 4AB4 4AEO 4JIQ 1Z44",
 "Nitroreductase": "1YKI 1IDT 1OO6 1OON 5J8G 4BN6 4BN8 1DS7 9GJX",
 "Nitroalkane oxidase": "2C0U 3FCJ 3D9D 3D9E 3D9F 2C12",
 "Nitronate monooxygenase / 2-nitropropane dioxygenase": "4Q4K 2GJN 4QIT 4QIU 3BW3",
 "Nitronate-CoA analog complexes": "6N92 6WFI 6X7L 6XBR",
 "Nitroarene dioxygenase": "2BMQ 2BMR 2BMO",
 "Glutathione S-transferase (Meisenheimer / nitroaryl)": "1AQX 18GS 2F3M",
 "Ketosteroid isomerase (nitrophenol analog)": "6C17 6C1J",
}
def get(u): return json.load(urllib.request.urlopen(u))
rows = []
for cat, ids in CURATED.items():
    for i in ids.split():
        e = get(f"https://data.rcsb.org/rest/v1/core/entry/{i}")
        lig = []
        for n in e["rcsb_entry_container_identifiers"].get("non_polymer_entity_ids", []):
            d = get(f"https://data.rcsb.org/rest/v1/core/nonpolymer_entity/{i}/{n}")["pdbx_entity_nonpoly"]
            lig.append(f"{d['comp_id']}:{d['name']}")
        res = (e["rcsb_entry_info"].get("resolution_combined") or [None])[0]
        rows.append([i, cat, e["struct"]["title"], res, "; ".join(lig)])
with open("curated.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["pdb_id", "category", "title", "resolution_A", "ligands"]); w.writerows(rows)
print(len(rows), "rows")
