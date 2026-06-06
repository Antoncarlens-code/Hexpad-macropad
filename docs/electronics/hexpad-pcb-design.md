# Hexpad PCB Design Package

**Date:** 2026-06-03
**Scope:** Electrical design for the existing 6-key + encoder hexpad enclosure.
**Matches:** `cad/hexpad_top_plate.py` (constants), `cad/hexpad_assembly.step`.

This is the design half the project was missing — everything needed to build the
KiCad schematic and PCB so it drops into the printed case. All coordinates are
taken directly from the CAD source so the board lines up with the plate's switch
cutouts, encoder hole, and corner posts.

---

## 1. What this board is

A **6-key** macropad (3×2 grid) plus **one EC11 rotary encoder**, driven by a
**Seeed XIAO RP2040**. Because there are fewer than 8 keys, every switch wires
**directly to its own GPIO** — no matrix, **no diodes**. The tutorial's matrix /
`1N4148` section does not apply to this build and should be skipped.

Pin budget: 6 switches + 3 encoder = **9 GPIO**. The XIAO RP2040 exposes 11
(D0–D10), so it fits with two pins (D4/D5 = SDA/SCL) left free for a future OLED.

---

## 2. Bill of materials

See `hexpad-bom.csv` for the spreadsheet version. Summary:

| Ref | Qty | Part | Footprint |
|-----|-----|------|-----------|
| U1 | 1 | Seeed XIAO RP2040 | care-package XIAO (castellated) |
| SW1–SW6 | 6 | MX keyswitch 1u | `MX_Only_1.00u` (care package) |
| ENC1 | 1 | Alps EC11 encoder + switch | `RotaryEncoder_Alps_EC11E-Switch_Vertical_H20mm` |
| — | 4 | M2 screw (~6 mm) | into plate corner posts |
| — | 6 / 1 | keycaps / encoder knob | cosmetic |

Diodes: **none.** (Listed in the BOM as qty 0 for reference only.)

---

## 3. Pin map / wiring table

Switch numbering: row by row, **front row first** (front = −Y), left to right.

| Ref | Function | XIAO pin | RP2040 GPIO | Other leg |
|-----|----------|----------|-------------|-----------|
| SW1 | key, front-left | D0 | GPIO26 | GND |
| SW2 | key, front-center | D1 | GPIO27 | GND |
| SW3 | key, front-right | D2 | GPIO28 | GND |
| SW4 | key, rear-left | D3 | GPIO29 | GND |
| SW5 | key, rear-center | D6 | GPIO0 | GND |
| SW6 | key, rear-right | D7 | GPIO1 | GND |
| ENC1.A | encoder rotation A | D8 | GPIO2 | — |
| ENC1.B | encoder rotation B | D9 | GPIO4 | — |
| ENC1.SW | encoder push | D10 | GPIO3 | — |
| ENC1.C | encoder common | — | — | GND |
| *(reserved)* | OLED SDA | D4 | GPIO6 | future |
| *(reserved)* | OLED SCL | D5 | GPIO7 | future |

Every input uses the RP2040's **internal pull-up** (firmware: `INPUT_PULLUP`),
so a press/turn pulls the pin to GND. No external resistors. See
`hexpad-schematic.svg` for the wiring diagram.

---

## 4. PCB layout coordinates

Origin = plate center (same origin as the CAD). Units mm. **Front edge = −Y**
(the case USB-C slot is cut into the −Y wall at X −15…−5).

### Switches (center of each MX footprint) — 19.05 mm pitch

| Ref | X | Y |
|-----|------|--------|
| SW1 | −19.05 | −9.525 |
| SW2 | 0.00 | −9.525 |
| SW3 | +19.05 | −9.525 |
| SW4 | −19.05 | +9.525 |
| SW5 | 0.00 | +9.525 |
| SW6 | +19.05 | +9.525 |

### Encoder

| Ref | X | Y |
|-----|---|------|
| ENC1 | 0.00 | +26.00 |

### Mounting holes (M2, must clear the plate's corner posts)

| Hole | X | Y |
|------|-------|-------|
| H1 | +32.00 | +31.00 |
| H2 | −32.00 | +31.00 |
| H3 | +32.00 | −31.00 |
| H4 | −32.00 | −31.00 |

X = ±32 (not ±31) to line up with the bottom-case screw bosses, which sit at
X ±32, Y ±31.

Drill Ø2.2 mm (M2 clearance), ~4 mm pad/annular keep-out.

### XIAO (U1)

Place on the **back** layer, USB-C connector pointing −Y, USB centered near
**X ≈ −10** so it lines up with the case slot. Body roughly centered at
**(−10, −27)** in the front margin below the bottom key row (which ends near
Y ≈ −16.5). Flip to B.Cu (press F in KiCad) before routing.

### Board outline (Edge.Cuts)

Match the plate footprint: **76 × 74 mm** rectangle (X ±38, Y ±37) with a
**3 × 3 mm notch at each corner**. Inset the edge **0.5 mm** all around if you
want clearance inside the case rim. Well within the 100 × 100 mm limit.

---

## 5. Build order in KiCad (condensed, tailored to this design)

1. New project → Schematic Editor. Place `MOUDLE-SEEEDUINO-XIAO`, 6× `SW_Push`,
   1× `RotaryEncoder_Switch`. **No diodes.**
2. Wire per the table in §3; place `GND` symbols on every switch's second leg and
   the encoder common.
3. Assign footprints per §2. (XIAO + `MX_Only_1.00u` come from the care package.)
4. PCB Editor → Update PCB from Schematic. Flip U1 to back.
5. Place SW1–SW6, ENC1, and the 4 mounting holes at the §4 coordinates (set grid
   to 19.05 mm for the switches).
6. Route on F.Cu; use B.Cu + a via only where traces cross.
7. Draw the §4 board outline on Edge.Cuts.
8. Cleanup Tracks & Vias → DRC (expect 0 errors) → 3D viewer check.
9. Fabrication Outputs → Gerbers + Drill files → zip as `gerbers.zip` → upload to
   JLCPCB for the preview/quote.

---

## 6. Integration checklist (board ↔ enclosure)

- [ ] Switch centers match plate cutouts (the 6 coords above = CAD `KEY_LOCS`). ✓ by design
- [ ] Encoder at (0, +26) = CAD `ENCODER_POS`. ✓ by design
- [ ] Mounting holes at (±31, ±31) = CAD `POST_LOCS`. ✓ by design
- [ ] USB-C exits −Y, aligned to case slot X −15…−5. (verify U1 placement)
- [ ] Board ≤ plate footprint 76×74, corner notches present.
- [ ] DRC clean before exporting Gerbers.

---

## 7. Firmware note (not built here)

KMK (CircuitPython) or QMK both run on the XIAO RP2040. Whichever you pick, the
keymap just maps each GPIO in §3 to a keycode and the encoder to A/B + push. The
pin map above is the single source of truth for the firmware's pin assignments.
