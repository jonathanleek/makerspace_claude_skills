# Gridfinity dimensional model & driver contract

Reference for how `scripts/generate.py` sizes a bin. The math mirrors the
constants in the vendored library (`vendor/gridfinity-rebuilt/src/core/standard.scad`).

## The Gridfinity grid

- **Footprint unit:** 42 mm. A bin is `42 × gridx` by `42 × gridy` mm on a side
  (a small tolerance makes the printed part ~0.5 mm under, so bins drop into a
  baseplate).
- **Height unit:** 7 mm (`gridz` in 7 mm increments), plus a 7 mm base and an
  optional ~3.5 mm stacking lip on top.
- Bins sit in **baseplates**; the base has optional magnet (6 mm ⌀ × 2 mm) and/or
  M3 screw holes, or "refined" printable snap holes (the default here).

## Library constants used for sizing

| Constant | Value | Meaning |
|---|---|---|
| `GRID_MM` | 42 | footprint unit |
| `PERIMETER_INSET` | 2.4 | interior lost across a full axis (1.2 mm per side) |
| `DIV_WALL` | 1.2 | wall between compartments (`d_div`) |
| `FLOOR_MM` | 1.2 | floor below the cavity |

Derived (per axis):

```
infill(gridN)            = 42*gridN - 2.4
compartment(gridN, divs) = (infill(gridN) - (divs-1)*1.2) / divs
```

## Sizing math (the estimate)

For an object of size `obj` (+ `clearance`) that must fit in **one** of `divs`
compartments along an axis:

```
gridN = ceil( (divs*(obj+clearance) + (divs-1)*1.2 + 2.4) / 42 )
```

Height uses `gridz_define=1` (interior mm): `gridz = ceil(height + clearance + 1.2)`.

## Verify, don't trust

The math is only the starting estimate. `generate.py` renders once, parses the
OpenSCAD echo (`Infill Dimensions`, `Bounding Box`), and:

1. Recomputes each compartment's **actual** interior from the echoed infill; if
   the object doesn't fit, it grows the deficient axis and re-renders (bounded).
2. Hard-fails if the **bounding box** exceeds `bed − margin` on X or Y, telling
   the user to use a larger printer or split the bin. The over-size STL is left
   on disk for inspection.

So the rendered geometry — not the formula — is the source of truth.

## Driver contract (separation of concerns)

- `generate.py` is **vault-agnostic**: it takes object dims + `--bed-x/--bed-y`
  and produces STL + manifest. It never reads the vault.
- The **skill** does the research (dimensions) and gets the bed size from
  `tool-advisor`, then invokes the driver. This keeps tool inventory in one place
  (`tool-advisor`) and CAD generation in another.

## Cavity types (v1)

- **Rectangular:** `--length --width --height`.
- **Cylindrical:** `--diameter --height` → one chamfered cylindrical hole per
  compartment; use `--divx N` for a row of N.
- **Multi-compartment:** `--divx --divy` → uniform grid; object fits in one cell.
- **Not yet (v2):** non-uniform / custom-sized compartments (the library supports
  it via `compartment_cutter`/`cgs`, but the driver doesn't expose it yet).

## Vendored library

`vendor/gridfinity-rebuilt/` — kennetek/gridfinity-rebuilt-openscad, pinned at
commit `910e22d` (recorded in each manifest and in `generate.py:VENDOR_PIN`).
MIT licensed (see `vendor/gridfinity-rebuilt/LICENSE`). Needs the OpenSCAD
snapshot/nightly build.
