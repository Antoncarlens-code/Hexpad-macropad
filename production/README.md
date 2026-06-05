# Production files

Manufacturing-ready outputs for Hexpad (separate from the source/design files).

| File | What it is |
|------|------------|
| `gerbers.zip` | PCB fabrication Gerbers + drill files (2-layer, 76 × 74 mm). Upload to a fab house (e.g. JLCPCB) to make the board. |
| `hexpad_top_plate.step` | Top plate — print this part. |
| `hexpad_bottom_case.step` | Bottom case — print this part. |
| `main.py` | KMK firmware. Copy onto the XIAO's CIRCUITPY drive alongside the `kmk/` library (see `../firmware/README.md`). |

Source/design files live in `../cad`, `../pcb`, and `../firmware`.
