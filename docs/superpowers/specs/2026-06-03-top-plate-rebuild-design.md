# Hexpad Top Plate Rebuild — Design

**Date:** 2026-06-03
**Status:** Approved (design), pending spec review
**Branch:** `fix/top-plate-rebuild`

## Problem

The CAD blueprints in `cad/` were generated yesterday via an Antigravity IDE
session that produced only STEP exports (no source script was saved). The
top-plate blueprint is malformed:

- `hexpad_top_plate.step` solid `#49` (the plate itself) spans **Z −74.50 → 1.50
  (76 mm tall)**. Its point cloud is a correct thin plate at Z 0 → 1.5 **fused to
  a stray slab at Z = −74.5**, welded into a single watertight body. This is what
  appears to "levitate"/sink in Bambu Studio.
- `hexpad_assembly.step` inherits the broken plate solid.
- `hexpad_bottom_case.step` is **clean** (1 solid, Z −10.1 → −1.5, 8.6 mm tall)
  and stays untouched.

Because the defect is in the main solid (not a separable floating object) and the
original generator script is unrecoverable (it lived only in the Antigravity chat,
which stores history server-side), the fix is to **rebuild the top plate from a
fresh parametric script**, reverse-engineering the real design parameters from the
existing STEP geometry and the clean bottom case.

## Reverse-engineered parameters (from STEP)

- Plate footprint: **76 × 74 mm** (X ±38, Y ±37), **3 × 3 mm notch at each corner**
  (matches the bottom-case rim outline).
- Bottom-case rim top: **Z = −1.5** → the plate seats here.
- Front edge = **−Y** (bottom-case USB-C port is cut into the −Y wall, X −15…−5).
- Recovered key grid: 14 mm square MX cutouts, **19.05 mm** spacing
  (standard MX 0.75″), columns X = −19.05 / 0 / +19.05.
- Corner mounting features at **(±31, ±31)**.

## Goals

Produce a clean, printable, parametric top plate that seats correctly on the
existing bottom case, with a maintainable source file checked into the repo.

## Non-goals

- Do not modify `hexpad_bottom_case.step` (it is correct).
- Do not reproduce the original's broken asymmetry or the stray Z = −74.5 slab.
- No firmware, BOM, or wiring changes.

## Design

### Toolchain
- **build123d** (Python, OCCT-based) — produces clean STEP, readable parametric
  source. Installed via pip. (Alternatives considered: CadQuery — heavier syntax;
  OpenSCAD — exports STL not STEP, rejected.)

### Outline & fit
- 76 × 74 mm rectangle, **3 × 3 mm notch at each of the 4 corners** to match the
  case rim.
- Bottom face seats on the case rim plane at **Z = −1.5**.
- Orientation: front edge = −Y.

### Body & switch mounting
- Body thickness: **3 mm** (seats at Z −1.5, top surface at Z +1.5).
- **Stepped cutouts** (true MX snap-fit on a thick plate): each opening is two
  stacked squares —
  - **Top 1.5 mm** (Z +1.5 → 0): **14.0 mm** square — the snap ledge the switch
    body fits and the clips latch under.
  - **Bottom 1.5 mm** (Z 0 → −1.5): **16.0 mm** square relief — wider so the MX
    side clips have room to spring out and latch beneath the 14 mm ledge.
- **6 keys**, 3 × 2 grid, **19.05 mm** spacing, **centered** on the plate:
  - Column centers X = −19.05, 0, +19.05
  - Row centers Y = −9.525, +9.525

### Encoder
- **Ø7.0 mm** through hole for an EC11 rotary encoder, centered in the top margin
  at **(0, +26)**.

### Mounting
- **4 corner posts** on the underside at **(±31, ±31)**, extending from the plate
  underside (Z −1.5) down to **Z −5** (3.5 mm long).
- Each post has a **Ø1.7 mm** pilot hole for an **M2 screw inserted from the case
  bottom**, threading up into the post. Matches the recovered posts and the case
  corner bosses.

### Parameters (constants at top of script)
| Constant | Value |
|----------|-------|
| `PLATE_W` × `PLATE_D` | 76 × 74 mm |
| `CORNER_NOTCH` | 3 mm |
| `PLATE_T` | 3 mm |
| `LEDGE_T` | 1.5 mm |
| `SWITCH_CUT` | 14.0 mm (top ledge) |
| `SWITCH_RELIEF` | 16.0 mm (bottom relief) |
| `KEY_SPACING` | 19.05 mm |
| `COLS` × `ROWS` | 3 × 2 |
| `SEAT_Z` | −1.5 mm |
| `ENCODER_D` | 7.0 mm |
| `ENCODER_POS` | (0, 26) |
| `POST_POS` | (±31, ±31) |
| `POST_LEN` | 3.5 mm |
| `POST_PILOT_D` | 1.7 mm |

## Deliverables

- `cad/hexpad_top_plate.py` — parametric build123d source (constants at top).
- Regenerated `cad/hexpad_top_plate.step` — clean, ~3 mm tall plate (Z −5 → 1.5
  including posts), no Z = −74.5 slab.
- Regenerated `cad/hexpad_assembly.step` — new plate + unchanged bottom case,
  correctly positioned.
- `cad/hexpad_bottom_case.step` — **unchanged**.

## Verification

1. **Geometry sanity** (`_analyze_step.py`): top-plate solids have sane Z extents
   (no −74.5 slab); plate body ~3 mm; assembly has plate + case at correct Z.
2. **Visual**: open regenerated STEPs in Bambu Studio — plate sits flat, no
   levitating parts, encoder + 6 cutouts present, seats on case.
3. **Fit check**: plate outline and corner posts align with the bottom case in the
   assembly view.

## Cleanup

Remove the temporary analysis scripts `cad/_analyze_step.py` and
`cad/_extract_geom.py` after verification passes (they served only the
reverse-engineering step).
