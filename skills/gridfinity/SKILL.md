---
name: gridfinity
description: Designs a Gridfinity storage bin sized to hold a specific object and renders it to a printable STL. Researches the object's dimensions (by name via web search, from calipered measurements, or from a photo you confirm), sizes a parametric bin to the Gridfinity grid, caps it to the printer bed via tool-advisor, and writes STL + a params manifest. Use for "make a gridfinity bin/holder/tray for X".
---

# Gridfinity Designer

Turns "I want a Gridfinity bin to hold X" into a printable STL. Pipeline:
**research dimensions → size a parametric bin → render headless STL + manifest**,
capped by the target printer's bed. The generator is the vendored
`gridfinity-rebuilt` OpenSCAD library driven by `scripts/generate.py`.

Requires the OpenSCAD **snapshot/nightly** build (the library uses syntax the
2021.01 stable can't parse). `scripts/generate.py` finds `openscad` on PATH.

## 1. Get the object's dimensions (mm)

Establish the L×W×H (rectangular) or diameter×height (cylindrical) of the thing
to hold, in millimeters:

- **By name** — web-search the product's spec / datasheet dimensions. Show the
  user the numbers and source before generating.
- **From measurements** — the user calipers it and gives you numbers. Preferred;
  most accurate.
- **From a photo** — estimate, then **confirm with the user** (ideally against a
  caliper). Never generate off an unconfirmed photo estimate.

Add a fit **clearance** (default 1.0 mm per axis; use 1.5–2 mm for a hand-grab or
loose fit, ~0.5 mm for a snug nest). This is a gap, not tolerance for print
shrinkage.

## 2. Get the printer bed cap (from tool-advisor)

The bin must fit the printer bed. Use the `tool-advisor` skill to read the target
printer's `build_volume_mm` (X, Y). If the user hasn't named a printer, pick the
one that fits and mention it (at WW the **H2S** has the larger bed at 340×320;
the **X1-Carbon** is 256×256). Pass those as `--bed-x`/`--bed-y`. The generator
hard-fails if the bin won't fit, so this is a real constraint, not a formality.

## 3. Choose the cavity layout

- **Rectangular** — one object in a box: `--length --width --height`.
- **Cylindrical** — round object(s): `--diameter --height`. Combine with
  `--divx N` to get a row of N identical holes (e.g. battery/marker holder).
- **Multi-compartment** — a uniform grid of compartments: `--divx --divy`. Each
  compartment is sized so the object fits in one; the driver grows the grid as
  needed. (Non-uniform / custom-sized compartments are a v2 — not yet supported.)

## 4. Generate

```sh
python3 scripts/generate.py \
  --name <slug> --outdir <project-repo-or-files-dir> \
  --length 60 --width 30 --height 25 --clearance 1.5 \
  --bed-x 256 --bed-y 256 --printer "Bambu X1-Carbon"
```

Cylindrical / dividers / base holes:
```sh
python3 scripts/generate.py --name battery-holder --outdir <dir> \
  --diameter 22 --height 40 --divx 3 --magnet-holes \
  --bed-x 340 --bed-y 320 --printer "Bambu H2S"
```

Useful flags: `--divx/--divy`, `--magnet-holes`, `--screw-holes`, `--no-lip`,
`--bed-margin` (default 2 mm), `--openscad <path>`. Run with `-h` for all.

It writes `<name>.stl` and `<name>.params.json` (inputs, computed grid, actual
rendered dimensions, library commit) so the bin is reproducible. See
`references/gridfinity-spec.md` for the dimensional model and the driver contract.

## 5. Save and report

Save the STL + manifest into the **project repo** (or the vault project's
`files/` per the vault's heavy-files convention — STLs are gitignored there).
Report to the user: the grid size (e.g. "2×1, 28 mm interior"), the outer
bounding box vs. the bed, and any print notes (e.g. "magnet holes need 6×2 mm
magnets", "disable supports — base is designed support-free").

## Notes
- The library defaults to gridfinity-**refined** snap holes in the base; the
  driver switches them off automatically when `--magnet-holes`/`--screw-holes`
  is set (the library forbids combining them).
- Heights use `gridz_define=1` (interior mm), so `--height + --clearance` is the
  usable cavity depth; the driver verifies this against the render and grows the
  bin if a rounding edge case leaves it short.
