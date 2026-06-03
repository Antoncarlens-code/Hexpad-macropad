"""Parametric hexpad top plate (build123d).

Regenerates hexpad_top_plate.step and hexpad_assembly.step.
Spec: docs/superpowers/specs/2026-06-03-top-plate-rebuild-design.md
Run with the project venv:
    cad\.venv\Scripts\python.exe cad\hexpad_top_plate.py
"""
from pathlib import Path
from build123d import (
    BuildPart, BuildSketch, Plane, Locations, Rectangle, Circle,
    extrude, Mode, Compound, export_step, import_step,
)

CAD = Path(__file__).parent

# ---- Parameters (mm) ----
PLATE_W, PLATE_D = 76.0, 74.0
PLATE_T = 3.0
SEAT_Z = -1.5                       # plate bottom seats on case rim
TOP_Z = SEAT_Z + PLATE_T            # +1.5
CORNER_NOTCH = 3.0
LEDGE_T = 1.5
SWITCH_CUT = 14.0                   # top ledge opening
SWITCH_RELIEF = 16.0               # bottom relief opening
KEY_SPACING = 19.05
COL_X = (-KEY_SPACING, 0.0, KEY_SPACING)
ROW_Y = (-KEY_SPACING / 2, KEY_SPACING / 2)   # -9.525, +9.525
ENCODER_D = 7.0
ENCODER_POS = (0.0, 26.0)
POST_X, POST_Y = 31.0, 31.0
POST_D = 5.0
POST_PILOT_D = 1.7
POST_BOTTOM_Z = -5.0
POST_LEN = SEAT_Z - POST_BOTTOM_Z   # 3.5
PILOT_DEPTH = 5.0                   # from -5 up to 0

KEY_LOCS = [(x, y) for y in ROW_Y for x in COL_X]
POST_LOCS = [(POST_X, POST_Y), (-POST_X, POST_Y),
             (POST_X, -POST_Y), (-POST_X, -POST_Y)]
_cx = PLATE_W / 2 - CORNER_NOTCH / 2
_cy = PLATE_D / 2 - CORNER_NOTCH / 2
NOTCH_LOCS = [(_cx, _cy), (-_cx, _cy), (_cx, -_cy), (-_cx, -_cy)]


def build_top_plate():
    with BuildPart() as part:
        # base body with corner notches: SEAT_Z -> TOP_Z
        with BuildSketch(Plane.XY.offset(SEAT_Z)):
            Rectangle(PLATE_W, PLATE_D)
            with Locations(*NOTCH_LOCS):
                Rectangle(CORNER_NOTCH, CORNER_NOTCH, mode=Mode.SUBTRACT)
        extrude(amount=PLATE_T)

        # corner posts under the plate: POST_BOTTOM_Z -> SEAT_Z
        with BuildSketch(Plane.XY.offset(POST_BOTTOM_Z)):
            with Locations(*POST_LOCS):
                Circle(POST_D / 2)
        extrude(amount=POST_LEN)

        # stepped MX cutouts -- 14mm snap ledge: 0 -> TOP_Z
        with BuildSketch(Plane.XY):
            with Locations(*KEY_LOCS):
                Rectangle(SWITCH_CUT, SWITCH_CUT)
        extrude(amount=TOP_Z, mode=Mode.SUBTRACT)
        # stepped MX cutouts -- 16mm relief: 0 -> SEAT_Z
        with BuildSketch(Plane.XY):
            with Locations(*KEY_LOCS):
                Rectangle(SWITCH_RELIEF, SWITCH_RELIEF)
        extrude(amount=SEAT_Z, mode=Mode.SUBTRACT)

        # EC11 encoder hole, through plate body: SEAT_Z -> TOP_Z
        with BuildSketch(Plane.XY.offset(SEAT_Z)):
            with Locations(ENCODER_POS):
                Circle(ENCODER_D / 2)
        extrude(amount=PLATE_T, mode=Mode.SUBTRACT)

        # post pilot holes (M2): POST_BOTTOM_Z -> 0
        with BuildSketch(Plane.XY.offset(POST_BOTTOM_Z)):
            with Locations(*POST_LOCS):
                Circle(POST_PILOT_D / 2)
        extrude(amount=PILOT_DEPTH, mode=Mode.SUBTRACT)
    return part.part


def build_assembly():
    case = import_step(str(CAD / "hexpad_bottom_case.step"))
    plate = import_step(str(CAD / "hexpad_top_plate.step"))
    return Compound(label="hexpad_assembly", children=[case, plate])


def main():
    plate = build_top_plate()
    export_step(plate, str(CAD / "hexpad_top_plate.step"))
    asm = build_assembly()
    export_step(asm, str(CAD / "hexpad_assembly.step"))
    print("exported hexpad_top_plate.step and hexpad_assembly.step")


if __name__ == "__main__":
    main()
