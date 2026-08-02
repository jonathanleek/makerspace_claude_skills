# Tool inventory — note format

One Markdown note per physical tool or machine, stored in the workshop's
inventory folder (`tools_subpath` in `config/workshops.toml`). Matches the
vault's Claude-first conventions: machine-legible frontmatter, `[[Wikilinks]]`,
`YYYY-MM-DD` dates. The frontmatter is the source of truth for capability
matching; the body is for context, quirks, and the "why-not" of purchase/setup
decisions.

## Frontmatter schema

```yaml
---
type: tool
class: 3d-printer        # 3d-printer | table-saw | bandsaw | miter-saw | router
                         # | drill-press | lathe | mill | cnc | laser | printer
                         # | hand-tool | soldering | measurement | other
area: 3d-printing        # woodworking | 3d-printing | electronics | metal | shop | mixed
make: Bambu Lab
model: X1 Carbon
status: active           # active | broken | loaned | wishlist | retired
acquired: 2025-03-01     # YYYY-MM-DD (omit if unknown / wishlist)
location: "Print bench"  # where it lives in the shop
# --- capacity fields: only the ones that apply to this class ---
specs:
  build_volume_mm: [256, 256, 256]   # 3d printer: X, Y, Z
  nozzle_mm: 0.4
  # table/bandsaw: max_rip_mm, max_cut_depth_mm, blade_dia_mm, throat_mm
  # cnc/laser:     work_area_mm: [x, y], max_material_mm
  # lathe:         swing_mm, between_centers_mm
  # mill:          travels_mm: [x, y, z], spindle_taper
tags: []
---
```

Rules:
- Include **only** the capacity fields relevant to the tool's `class`. Every
  numeric field carries its unit in the key name (`_mm`, `_deg`, …) so matching
  never has to guess units.
- `build_volume_mm` / `work_area_mm` / arrays are `[x, y]` or `[x, y, z]`.
- `status` gates advice: don't recommend a `broken`/`loaned`/`wishlist` tool for
  a real job without flagging it.

## Body structure

```
# <Make> <Model>
One-line what-it's-for.

## Capabilities
Prose on what it can/can't do, quirks, tolerances the specs don't capture.

## Consumables
- Blades / bits / nozzles / filament on hand and what each is good for.

## Decisions
- **YYYY-MM-DD** — why this tool (options considered, why-not the alternatives).

## Notes
Maintenance, calibration, gotchas.
```

## Consumed by

- `tool-advisor` — capability Q&A and cross-tool comparison.
- `gridfinity` — reads the active 3D printer's `build_volume_mm` (X, Y) to cap
  generated baseplate size.
