#!/usr/bin/env python3
"""
generate.py — size a Gridfinity bin to hold an object and render it to STL.

Turns real-world object dimensions into a parametric Gridfinity bin via the
vendored `gridfinity-rebuilt` OpenSCAD library, capped by the target printer's
bed. Writes <name>.stl plus a <name>.params.json manifest (inputs, computed
grid, actual rendered dimensions, library pin) so any bin is reproducible.

The grid math uses the library's own constants (42 mm bases, 1.2 mm division
walls, ~1.2 mm perimeter inset per side, ~1.2 mm floor). After rendering, the
OpenSCAD echo output is parsed to VERIFY the object actually fits the interior
and that the outer bounding box fits the bed — the render is the source of
truth, the math is just the starting estimate.

Cross-skill contract: this driver knows nothing about the vault. The caller
(the `gridfinity` skill) gets the target printer's bed size from `tool-advisor`
and passes it as --bed-x/--bed-y.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# ---- library constants (mirrors src/core/standard.scad) --------------------
GRID_MM = 42.0        # GRID_DIMENSIONS_MM
PERIMETER_INSET = 2.4  # total infill loss across a full axis (1.2 mm per side)
DIV_WALL = 1.2        # d_div — wall between compartments
FLOOR_MM = 1.2        # bin floor below the cavity (infill_z = gridz - FLOOR_MM at gridz_define=1)
VENDOR_ENTRY = "vendor/gridfinity-rebuilt/gridfinity-rebuilt-bins.scad"
VENDOR_PIN = "910e22d8607fd7f5f51ad5e5cbc5287a76810bfd"  # kennetek/gridfinity-rebuilt-openscad


def infill_axis(grid_n: int) -> float:
    """Total interior length along one axis for `grid_n` bases."""
    return GRID_MM * grid_n - PERIMETER_INSET


def compartment_axis(grid_n: int, divs: int) -> float:
    """Usable interior of a single compartment along one axis."""
    return (infill_axis(grid_n) - (divs - 1) * DIV_WALL) / divs


def bases_for(obj_mm: float, divs: int, clearance: float) -> int:
    """Smallest base count so each of `divs` compartments fits obj+clearance."""
    need = divs * (obj_mm + clearance) + (divs - 1) * DIV_WALL + PERIMETER_INSET
    return max(1, math.ceil(need / GRID_MM - 1e-9))


def gridz_for(height_mm: float, clearance: float) -> int:
    """gridz value (gridz_define=1) giving an interior at least height+clearance."""
    return max(1, math.ceil(height_mm + clearance + FLOOR_MM - 1e-9))


def find_openscad(explicit: str | None) -> str:
    if explicit:
        return explicit
    for name in ("openscad", "OpenSCAD"):
        found = shutil.which(name)
        if found:
            return found
    # common macOS app locations (snapshot build recommended for this library)
    for app in ("/Applications/OpenSCAD.app", "/Applications/OpenSCAD-nightly.app"):
        p = Path(app) / "Contents/MacOS/OpenSCAD"
        if p.exists():
            return str(p)
    sys.exit("error: openscad not found on PATH; pass --openscad /path/to/openscad")


_VEC = re.compile(r"\[([^\]]*)\]")


def _parse_vec(line: str) -> list[float] | None:
    m = _VEC.search(line)
    if not m:
        return None
    try:
        return [float(x) for x in m.group(1).split(",")]
    except ValueError:
        return None


def render(openscad: str, scad: Path, params: dict, out_stl: Path) -> dict:
    """Run OpenSCAD headless; return parsed {infill:[x,y,z], bbox:[x,y,z]}."""
    cmd = [openscad, "-o", str(out_stl)]
    for k, v in params.items():
        if isinstance(v, bool):
            v = "true" if v else "false"
        cmd += ["-D", f"{k}={v}"]
    cmd.append(str(scad))
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0 or not out_stl.exists():
        sys.exit(f"error: OpenSCAD render failed:\n{proc.stderr.strip()}")
    info: dict = {}
    for line in proc.stderr.splitlines():
        if "Infill Dimensions" in line:
            info["infill"] = _parse_vec(line)
        elif "Bounding Box" in line:
            info["bbox"] = _parse_vec(line)
    return info


def build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Size a Gridfinity bin to an object and render it to STL.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--name", required=True, help="output basename (<name>.stl / .params.json)")
    p.add_argument("--outdir", default=".", help="directory to write outputs into")

    g = p.add_argument_group("object to hold (mm)")
    g.add_argument("--length", type=float, help="object size along X (rectangular)")
    g.add_argument("--width", type=float, help="object size along Y (rectangular)")
    g.add_argument("--diameter", type=float, help="object diameter (cylindrical cavity)")
    g.add_argument("--height", type=float, required=True, help="object height along Z")
    g.add_argument("--clearance", type=float, default=1.0, help="gap added around the object per axis")

    c = p.add_argument_group("compartments")
    c.add_argument("--divx", type=int, default=1, help="compartments along X")
    c.add_argument("--divy", type=int, default=1, help="compartments along Y")

    b = p.add_argument_group("printer bed cap (mm) — from tool-advisor")
    b.add_argument("--bed-x", type=float, required=True, help="usable bed size X")
    b.add_argument("--bed-y", type=float, required=True, help="usable bed size Y")
    b.add_argument("--bed-margin", type=float, default=2.0, help="keep-off margin from bed edges")
    b.add_argument("--printer", default="", help="printer name, recorded in the manifest")

    o = p.add_argument_group("bin options")
    o.add_argument("--no-lip", action="store_true", help="omit the stacking lip")
    o.add_argument("--magnet-holes", action="store_true", help="6mm magnet holes in the base")
    o.add_argument("--screw-holes", action="store_true", help="M3 screw holes in the base")
    o.add_argument("--openscad", help="path to the openscad binary")
    return p


def main() -> None:
    args = build_argparser().parse_args()

    cylindrical = args.diameter is not None
    if cylindrical:
        # one hole per compartment, diameter = object + clearance
        cd = args.diameter + args.clearance
        obj_x = obj_y = cd
        fit_clear = 0.0  # clearance already folded into cd / footprint
    else:
        if args.length is None or args.width is None:
            sys.exit("error: give --length and --width (rectangular) or --diameter (cylindrical)")
        obj_x, obj_y = args.length, args.width
        fit_clear = args.clearance
        cd = 0.0

    gridx = bases_for(obj_x, args.divx, fit_clear)
    gridy = bases_for(obj_y, args.divy, fit_clear)
    gridz = gridz_for(args.height, args.clearance)

    scad = (Path(__file__).resolve().parent.parent / VENDOR_ENTRY)
    if not scad.exists():
        sys.exit(f"error: vendored library not found at {scad}")
    openscad = find_openscad(args.openscad)

    outdir = Path(args.outdir).expanduser().resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    out_stl = outdir / f"{args.name}.stl"

    bed_x = args.bed_x - args.bed_margin
    bed_y = args.bed_y - args.bed_margin

    # Render, then verify against the echoed reality; bump the deficient axis and
    # re-render if the estimate fell short (rounding edge cases). Bounded loop.
    info: dict = {}
    for _ in range(4):
        params = {
            "gridx": gridx, "gridy": gridy, "gridz": gridz, "gridz_define": 1,
            "divx": args.divx, "divy": args.divy,
            "include_lip": not args.no_lip,
            "magnet_holes": args.magnet_holes, "screw_holes": args.screw_holes,
            # refined snap holes are the default, but the library forbids combining
            # them with magnet/screw holes — switch style when those are requested.
            "refined_holes": not (args.magnet_holes or args.screw_holes),
            "cut_cylinders": cylindrical, "cd": cd,
        }
        info = render(openscad, scad, params, out_stl)
        infill = info.get("infill") or [0, 0, 0]
        # per-compartment interior actually available
        comp_x = (infill[0] - (args.divx - 1) * DIV_WALL) / args.divx
        comp_y = (infill[1] - (args.divy - 1) * DIV_WALL) / args.divy
        comp_z = infill[2]
        short = False
        if comp_x < obj_x + fit_clear - 1e-6:
            gridx += 1; short = True
        if comp_y < obj_y + fit_clear - 1e-6:
            gridy += 1; short = True
        if comp_z < args.height + args.clearance - 1e-6:
            gridz += 1; short = True
        if not short:
            break

    bbox = info.get("bbox") or [0, 0, 0]
    if bbox[0] > bed_x or bbox[1] > bed_y:
        sys.exit(
            f"error: bin {bbox[0]:.1f}×{bbox[1]:.1f} mm exceeds the usable bed "
            f"{bed_x:.1f}×{bed_y:.1f} mm ({args.printer or 'printer'}, "
            f"{args.bed_margin} mm margin). Use a larger printer or split the bin.\n"
            f"       Rendered STL left at {out_stl} for inspection."
        )

    manifest = {
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "name": args.name,
        "object_mm": (
            {"diameter": args.diameter, "height": args.height} if cylindrical
            else {"length": args.length, "width": args.width, "height": args.height}
        ),
        "clearance_mm": args.clearance,
        "cavity": "cylindrical" if cylindrical else "rectangular",
        "compartments": {"divx": args.divx, "divy": args.divy},
        "grid": {"gridx": gridx, "gridy": gridy, "gridz": gridz, "gridz_define": 1},
        "options": {
            "include_lip": not args.no_lip,
            "magnet_holes": args.magnet_holes,
            "screw_holes": args.screw_holes,
        },
        "printer": args.printer,
        "bed_mm": {"x": args.bed_x, "y": args.bed_y, "margin": args.bed_margin},
        "rendered": {"infill_mm": info.get("infill"), "bounding_box_mm": info.get("bbox")},
        "library": {"name": "gridfinity-rebuilt", "commit": VENDOR_PIN},
        "openscad": openscad,
    }
    out_json = outdir / f"{args.name}.params.json"
    out_json.write_text(json.dumps(manifest, indent=2) + "\n")

    print(f"✓ {out_stl}")
    print(f"  grid {gridx}×{gridy}, gridz {gridz} (interior); bbox "
          f"{bbox[0]:.1f}×{bbox[1]:.1f}×{bbox[2]:.1f} mm — fits "
          f"{args.printer or 'bed'} {args.bed_x:.0f}×{args.bed_y:.0f}")
    print(f"  manifest {out_json}")


if __name__ == "__main__":
    main()
