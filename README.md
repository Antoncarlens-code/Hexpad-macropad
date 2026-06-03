# Hexpad — 3D Printed Macropad

A 6-key (3×2) + rotary-encoder macropad: 3D-printed case, custom PCB, and KMK
firmware. Driven by a Seeed XIAO RP2040 — keys wire direct to GPIO (no matrix,
no diodes).

## Project layout

| Folder | Contents |
|--------|----------|
| `cad/` | Enclosure: STEP blueprints + parametric build123d source |
| `pcb/` | KiCad 10 PCB project + fabrication Gerbers |
| `firmware/` | KMK (CircuitPython) keymap |
| `docs/electronics/` | Schematic, BOM, PCB design notes |
| `docs/superpowers/` | Design specs & implementation plans |
| `print/` | Slicer projects & exports (`.gcode` gitignored) |

## CAD (enclosure)

| File | Part |
|------|------|
| `cad/hexpad_top_plate.step` | Top plate — stepped MX cutouts + encoder hole |
| `cad/hexpad_bottom_case.step` | Bottom case / housing |
| `cad/hexpad_assembly.step` | Full assembled macropad (preview only) |
| `cad/hexpad_top_plate.py` | Parametric source — edit constants, run to regenerate |

Regenerate the plate: `cad/.venv/Scripts/python.exe cad/hexpad_top_plate.py`
(build123d in a Python 3.12 venv; the system Python 3.14 has no wheels).

## PCB

| File | Purpose |
|------|---------|
| `pcb/hexpad-gerbers.zip` | **Upload this to JLCPCB** to order boards |
| `pcb/hexpad.kicad_pcb` | KiCad 10 board (routed, DRC-clean) |
| `pcb/build_hexpad_pcb.py` | Regenerates component placement from the spec |

2-layer, 76×74 mm, matches the plate's switch/encoder/mounting coordinates.

## Firmware

KMK keymap at `firmware/code.py`. Default: front row Copy/Paste/Cut, rear row
Undo/Redo/Save, encoder = volume (press = mute). See `firmware/README.md` for
flashing and remapping. (QMK is also an option.)

## Bill of materials

`docs/electronics/hexpad-bom.csv` — XIAO RP2040, 6× Cherry MX switches, 1× EC11
encoder, 4× M2 screws, keycaps + knob. No diodes.

## Toolchain

- **CAD:** build123d (Python) → STEP
- **PCB:** KiCad 10
- **Slicer:** Bambu Studio
- **Firmware:** CircuitPython + KMK

## Build checklist

- [x] CAD: top plate + bottom case
- [x] PCB: board routed + Gerbers exported
- [x] Bill of materials
- [x] Firmware keymap
- [ ] Order PCB from JLCPCB (`pcb/hexpad-gerbers.zip`)
- [ ] Print top plate + bottom case
- [ ] Solder switches/encoder/XIAO, flash firmware, assemble
