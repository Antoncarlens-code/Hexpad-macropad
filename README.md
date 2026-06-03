# Hexpad — 3D Printed Macropad

A hex-shaped 3D-printed macropad. CAD blueprints created 2026-06-02.

## Project layout

| Folder | Contents |
|--------|----------|
| `cad/` | Source CAD blueprints (STEP / ISO-10303-21) |
| `print/` | Slicer projects & exports (Bambu Studio `.3mf`, `.gcode` — gcode gitignored) |
| `docs/` | Notes, wiring, BOM, photos |

## CAD files

| File | Part |
|------|------|
| `cad/hexpad_assembly.step` | Full assembled macropad |
| `cad/hexpad_top_plate.step` | Top plate (key switch mounting) |
| `cad/hexpad_bottom_case.step` | Bottom case / housing |

## Toolchain

- **Slicer:** Bambu Studio (v2.07.01.57)
- **Format:** STEP — import into the slicer or any CAD tool (Fusion, FreeCAD, etc.)

## TODO

- [ ] Slice top plate + bottom case in Bambu Studio
- [ ] Bill of materials (switches, keycaps, microcontroller, diodes)
- [ ] Firmware (QMK / KMK / custom)
- [ ] Wiring diagram
