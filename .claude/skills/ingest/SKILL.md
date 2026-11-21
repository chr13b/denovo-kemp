---
name: ingest
description: Ingest a new source (challenge brief, paper, organizer note, dataset description) into the wiki. Use when a file lands in raw/ or the user shares material that should become project knowledge.
---

# Ingest a source

1. **Store it.** If the source isn't in `raw/` yet, save it as `raw/YYYYMMDD_<short-slug>.<ext>`.
   Never edit or delete files that are already in `raw/`.
2. **Read all of it.** Extract:
   - what it claims
   - key numbers, with units
   - the methods, tools and data it names
   - constraints that bind us
   - what it implies for our plan
3. **Update the wiki.** Prefer updating an existing page (`wiki/challenge.md` first) over creating a new one.
   Create `wiki/<topic>.md` only for a genuinely new topic. Link the raw file for every claim.
   If the source is the challenge brief, fill every TODO in `wiki/challenge.md` that it answers.
   Datasets it mentions go in `wiki/data.md`.
4. **Surface conflicts.** If the source contradicts the wiki, write `> **Conflict:** …` with both sources.
   Never overwrite silently.
5. **Index it.** Give the raw file and any new wiki page a one-line entry each in `INDEX.md`. Append to the right section.
6. **Log it.** Run `python tools/new.py log ingest "<title>"` and fill in 1–3 bullets on what changed in the wiki.
7. Run `python tools/check_index.py` and fix anything it reports.
8. Tell the user the 3–5 most decision-relevant points in chat, each with a link to the wiki page.
