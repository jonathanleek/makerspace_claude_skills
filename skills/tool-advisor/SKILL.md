---
name: tool-advisor
description: Answers "what tools/machines do I have?", "can I do X on my Y?", "what bit/blade/setting for Z?", and supplies hard constraints (print-bed size, throat depth, max stock) to other skills. Backed by a per-tool inventory in the workshop vault. Use for any question about the physical shop's capabilities.
---

# Tool Advisor

Answers capability questions about the physical workshop from a structured tool
inventory, and hands hard constraints to sibling skills (notably `gridfinity`,
which needs the 3D-printer bed size).

The **tooling** (this skill) lives in the `makerspace_claude_skills` repo; the
**data** (one note per tool) lives in a workshop vault. This skill never invents
capabilities — it reads them from the inventory or says the inventory is missing
the answer.

## 1. Resolve the workshop and its inventory

1. Read `../../config/workshops.toml` (relative to this skill's own directory —
   i.e. `<repo>/config/workshops.toml`). It maps a workshop id to its `vault`
   (absolute path) and `tools_subpath` (inventory folder, relative to the vault).
2. Use the `default` workshop unless the user names another.
3. The inventory folder is `<vault>/<tools_subpath>`. Each `*.md` there is one
   tool, with the frontmatter schema in `references/inventory-format.md`.

If the folder does not exist or is empty, tell the user the inventory isn't
seeded yet and offer to create it (see §4) — do **not** guess capabilities.

## 2. Answer a capability question

1. Read the relevant tool notes (grep/glob the inventory folder; read the
   frontmatter and the note body).
2. Match the question against the tool's specs:
   - **"Can I do X on my Y?"** — find tool Y, compare X against its capacity
     fields (e.g. bed size vs. part footprint, throat depth vs. stock width,
     max cut depth, spindle taper). Give a clear yes/no **with the numbers**,
     then any caveat (e.g. "fits, but only with the part rotated 45°").
   - **"What bit/blade/setting for Z?"** — read the tool's consumables/notes and
     the material; recommend with rationale. If it's not recorded, say so.
   - **"Do I have something for…?"** — search across the inventory by capability,
     not just by name.
3. When a query spans several tools, compare them and give a recommendation with
   the reason — match the vault's "recommendation with rationale" bar.

## 3. Supply constraints to other skills

When another skill (or the user) needs a hard limit, read it straight from the
inventory and return the number plus its source note. The common ones:

- **3D printer** → build volume (X×Y×Z mm), nozzle/material. `gridfinity` uses
  the bed X×Y to cap how large a baseplate it generates.
- **Table saw / bandsaw** → max rip width (throat), max cut depth/height.
- **CNC / laser** → work area, max material thickness.
- **Lathe / mill** → swing, distance between centers, travels.

If the needed field is absent, say which note is missing it rather than assuming.

## 4. Capturing / updating a tool

Follow the vault's conventions (`CLAUDE.md` in the vault): plain-text Markdown +
frontmatter, `[[Wikilinks]]`, `YYYY-MM-DD` dates, timestamped decisions, and
record the "why-not" when a real choice is made. Create one note per tool in the
inventory folder using the frontmatter schema in
`references/inventory-format.md`. Fill capacity fields from the spec sheet (ask
the user for the model, or web-search the published specs and have the user
confirm anything measured).

Keep specs machine-legible (numbers with units in frontmatter) so capability
matching and constraint hand-off stay reliable.
