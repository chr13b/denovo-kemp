# Pitch decks

Source for the three pitch decks. Each folder is one deck: `deck.json` is the index
(title, slide order, sections, fonts), `deck.css` the shared styling, and one file per
slide under `slides/`. Slides are plain HTML on a fixed 1920×1080 canvas.

| Folder | Deck | Content |
|---|---|---|
| `three-routes/` | **Three Routes Pitch** | The combined deck: all three approaches, a comparison table and a flow diagram |
| `theozyme-route/` | Theozyme Route Pitch | Janis's campaign only, from `Kemp eliminase design process and design choices.pdf` |
| `replication-route/` | Replication Route Pitch | Chris's campaign only, from `approach.md` |

## Editing

**For live, simultaneous editing, use the hosted deck, not this folder.** The hosted
version renders the slides, lets several people edit at once and exports to PowerPoint
and PDF. Ask Flavia for the link and for edit access; the links are not in the
repository because they grant access.

This folder is the version-controlled copy: it gives history, review and a record of
what was presented. Git merges text, it does not synchronise edits as they happen, so
two people editing the same slide file here will conflict in the normal way.

## Conventions

- One `<section id="…">` per slide file; the file name is the section id.
- The id must also appear in `order` in `deck.json`, which sets the sequence.
- Speaker notes are a single `<aside>` as the last child of the section.
- Colours come from the palette in `deck.css`, sampled from our own render of the
  enzyme: the chain runs blue at the N-terminus to red at the C-terminus, and the deck
  steps through the same spectrum, one slide at a time.
- Images are referenced as `/_blob/<id>` and live with the hosted deck, not here.
