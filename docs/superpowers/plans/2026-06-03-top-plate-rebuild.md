# Hexpad Top Plate Rebuild Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the malformed `hexpad_top_plate.step` with a clean, parametric build123d-generated top plate that seats correctly on the existing bottom case.

**Architecture:** A single parametric Python script (`cad/hexpad_top_plate.py`) builds the plate from named constants and exports `hexpad_top_plate.step`, then composes it with the unchanged `hexpad_bottom_case.step` into `hexpad_assembly.step`. Geometry is verified after each stage with the existing stdlib analyzer `cad/_analyze_step.py`.

**Tech Stack:** Python + build123d (OpenCASCADE). Because only Python 3.14 is installed (no build123d/OCP wheels for 3.14 yet), the build runs inside a `uv`-managed Python 3.12 venv at `cad/.venv`. The analyzer is stdlib-only and runs on system Python 3.14.

**Spec:** `docs/superpowers/specs/2026-06-03-top-plate-rebuild-design.md`
**Branch:** `fix/top-plate-rebuild`

---

## File Structure

| File | Responsibility | Status |
|------|----------------|--------|
| `cad/hexpad_top_plate.py` | Parametric source: constants + `build_top_plate()` + `build_assembly()` + `main()` | Create |
| `cad/hexpad_top_plate.step` | Generated clean plate | Overwrite |
| `cad/hexpad_assembly.step` | Generated plate + unchanged case | Overwrite |
| `cad/hexpad_bottom_case.step` | Clean case | **Untouched** |
| `cad/_analyze_step.py` | Per-solid bbox verifier (stdlib) | Use, then remove |
| `cad/_extract_geom.py` | Reverse-engineering helper | Remove at end |
| `.gitignore` | Ignore `cad/.venv/`, `__pycache__/` | Modify |
| `README.md` | Tick the "slice top plate" TODO context | Modify |

**Coordinate model (final, absolute Z):** plate body Z −1.5 → +1.5 (seats on case rim at −1.5); corner posts Z −5 → −1.5; stepped cutouts: 14 mm square Z 0 → +1.5, 16 mm relief Z −1.5 → 0; front edge = −Y.

---

## Task 1: Provision build123d environment

**Files:** none (environment only)

- [ ] **Step 1: Install uv (standalone, runs on 3.14)**

Run:
```powershell
python -m pip install uv
```
Expected: `Successfully installed uv-...`

- [ ] **Step 2: Install a managed Python 3.12 and create the venv**

Run:
```powershell
uv python install 3.12
uv venv cad\.venv --python 3.12
```
Expected: `Creating virtual environment at: cad\.venv`

- [ ] **Step 3: Install build123d into the venv**

Run:
```powershell
uv pip install --python cad\.venv\Scripts\python.exe build123d
```
Expected: resolves and installs `build123d`, `cadquery-ocp`, etc. (may take a few minutes).

- [ ] **Step 4: Verify the import works**

Run:
```powershell
cad\.venv\Scripts\python.exe -c "import build123d as b; print('build123d', b.__version__)"
```
Expected: prints a version (e.g. `build123d 0.9.x`). If this fails with an OCP/wheel error, try `uv python install 3.11` and recreate the venv with `--python 3.11`.

---

## Task 2: Base plate with corner notches

**Files:**
- Create: `cad/hexpad_top_plate.py`

- [ ] **Step 1: Create the script with constants + base body + main()**

Create `cad/hexpad_top_plate.py`:
```python
"""Parametric hexpad top plate (build123d).

Regenerates hexpad_top_plate.step and hexpad_assembly.step.
Spec: docs/superpowers/specs/2026-06-03-top-plate-rebuild-design.md
Run with the project venv:
    cad\\.venv\\Scripts\\python.exe cad\\hexpad_top_plate.py
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
    return part.part


def main():
    plate = build_top_plate()
    export_step(plate, str(CAD / "hexpad_top_plate.step"))
    print("exported hexpad_top_plate.step")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run the script (regenerates the plate STEP)**

Run:
```powershell
cad\.venv\Scripts\python.exe cad\hexpad_top_plate.py
```
Expected: `exported hexpad_top_plate.step`

- [ ] **Step 3: Verify geometry with the analyzer**

Run:
```powershell
python cad\_analyze_step.py cad\hexpad_top_plate.step
```
Expected: `1 solid(s)`, one solid with `Z[  -1.50,   1.50]`, `X[ -38.00,  38.00]`, `Y[ -37.00,  37.00]`, `size 76.0x74.0x3.0`. **No Z = −74.5.**

- [ ] **Step 4: Commit**

```powershell
git add cad\hexpad_top_plate.py cad\hexpad_top_plate.step
git commit -m "feat(cad): base top plate body with corner notches"
```

---

## Task 3: Corner posts + pilot holes

**Files:**
- Modify: `cad/hexpad_top_plate.py` (extend `build_top_plate()`)

- [ ] **Step 1: Add posts and pilot holes to `build_top_plate()`**

Replace the `build_top_plate()` function body with:
```python
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

        # post pilot holes (M2): POST_BOTTOM_Z -> 0
        with BuildSketch(Plane.XY.offset(POST_BOTTOM_Z)):
            with Locations(*POST_LOCS):
                Circle(POST_PILOT_D / 2)
        extrude(amount=PILOT_DEPTH, mode=Mode.SUBTRACT)
    return part.part
```

- [ ] **Step 2: Regenerate and verify**

Run:
```powershell
cad\.venv\Scripts\python.exe cad\hexpad_top_plate.py
python cad\_analyze_step.py cad\hexpad_top_plate.step
```
Expected: `1 solid(s)` (posts fuse to plate), Z extent now `Z[  -5.00,   1.50]`, size `76.0x74.0x6.5`. No Z = −74.5.

- [ ] **Step 3: Commit**

```powershell
git add cad\hexpad_top_plate.py cad\hexpad_top_plate.step
git commit -m "feat(cad): add corner mounting posts with M2 pilot holes"
```

---

## Task 4: Stepped MX switch cutouts

**Files:**
- Modify: `cad/hexpad_top_plate.py` (extend `build_top_plate()`)

- [ ] **Step 1: Add the stepped cutouts before the pilot-hole block**

Replace the `build_top_plate()` function body with:
```python
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

        # post pilot holes (M2): POST_BOTTOM_Z -> 0
        with BuildSketch(Plane.XY.offset(POST_BOTTOM_Z)):
            with Locations(*POST_LOCS):
                Circle(POST_PILOT_D / 2)
        extrude(amount=PILOT_DEPTH, mode=Mode.SUBTRACT)
    return part.part
```

- [ ] **Step 2: Regenerate and verify**

Run:
```powershell
cad\.venv\Scripts\python.exe cad\hexpad_top_plate.py
python cad\_analyze_step.py cad\hexpad_top_plate.step
```
Expected: still `1 solid(s)`, Z `[-5.00, 1.50]`. (Cutouts are internal, so the bbox is unchanged — confirms no stray geometry was introduced.)

- [ ] **Step 3: Sanity-check cutout count/positions**

Run:
```powershell
cad\.venv\Scripts\python.exe -c "from cad.hexpad_top_plate import KEY_LOCS; print(len(KEY_LOCS), KEY_LOCS)"
```
Expected: `6 [(-19.05, -9.525), (0.0, -9.525), (19.05, -9.525), (-19.05, 9.525), (0.0, 9.525), (19.05, 9.525)]`

- [ ] **Step 4: Commit**

```powershell
git add cad\hexpad_top_plate.py cad\hexpad_top_plate.step
git commit -m "feat(cad): add 6 stepped MX switch cutouts (14/16mm)"
```

---

## Task 5: Encoder hole

**Files:**
- Modify: `cad/hexpad_top_plate.py` (extend `build_top_plate()`)

- [ ] **Step 1: Add the encoder hole after the relief block, before pilot holes**

Insert this block immediately after the `# stepped MX cutouts -- 16mm relief` extrude and before the `# post pilot holes` block:
```python
        # EC11 encoder hole, through plate body: SEAT_Z -> TOP_Z
        with BuildSketch(Plane.XY.offset(SEAT_Z)):
            with Locations(ENCODER_POS):
                Circle(ENCODER_D / 2)
        extrude(amount=PLATE_T, mode=Mode.SUBTRACT)
```

- [ ] **Step 2: Regenerate and verify**

Run:
```powershell
cad\.venv\Scripts\python.exe cad\hexpad_top_plate.py
python cad\_analyze_step.py cad\hexpad_top_plate.step
```
Expected: `1 solid(s)`, Z `[-5.00, 1.50]`, unchanged bbox. No Z = −74.5.

- [ ] **Step 3: Commit**

```powershell
git add cad\hexpad_top_plate.py cad\hexpad_top_plate.step
git commit -m "feat(cad): add EC11 encoder hole at (0, 26)"
```

---

## Task 6: Assembly generation

**Files:**
- Modify: `cad/hexpad_top_plate.py` (add `build_assembly()`, extend `main()`)

- [ ] **Step 1: Add `build_assembly()` and update `main()`**

Add this function after `build_top_plate()`:
```python
def build_assembly():
    case = import_step(str(CAD / "hexpad_bottom_case.step"))
    plate = import_step(str(CAD / "hexpad_top_plate.step"))
    return Compound(label="hexpad_assembly", children=[case, plate])
```

Replace `main()` with:
```python
def main():
    plate = build_top_plate()
    export_step(plate, str(CAD / "hexpad_top_plate.step"))
    asm = build_assembly()
    export_step(asm, str(CAD / "hexpad_assembly.step"))
    print("exported hexpad_top_plate.step and hexpad_assembly.step")
```

- [ ] **Step 2: Regenerate and verify the assembly**

Run:
```powershell
cad\.venv\Scripts\python.exe cad\hexpad_top_plate.py
python cad\_analyze_step.py cad\hexpad_assembly.step
```
Expected: `2 solid(s)` — one `Z[ -10.10,  -1.50]` size `76.0x74.0x8.6` (case, unchanged) and one `Z[  -5.00,   1.50]` size `76.0x74.0x6.5` (plate). No Z = −74.5.

- [ ] **Step 3: Confirm the bottom case file is byte-identical (untouched)**

Run:
```powershell
git status --porcelain cad\hexpad_bottom_case.step
```
Expected: **no output** (file unmodified).

- [ ] **Step 4: Commit**

```powershell
git add cad\hexpad_top_plate.py cad\hexpad_assembly.step
git commit -m "feat(cad): regenerate assembly from clean plate + existing case"
```

---

## Task 7: Visual verification in Bambu Studio

**Files:** none

- [ ] **Step 1: Open the regenerated STEPs**

Run:
```powershell
& "C:\Program Files\Bambu Studio\bambu-studio.exe" cad\hexpad_top_plate.step cad\hexpad_assembly.step
```

- [ ] **Step 2: Confirm visually**

Check: plate lies flat (~3 mm), **no levitating/sinking geometry**, 6 square cutouts in a centered 3×2 grid, the encoder hole above them, 4 corner posts on the underside, and in the assembly the plate seats on the case rim. Capture a screenshot if running headless review.

---

## Task 8: Cleanup + housekeeping

**Files:**
- Modify: `.gitignore`
- Delete: `cad/_analyze_step.py`, `cad/_extract_geom.py`

- [ ] **Step 1: Ignore the venv and pycache**

Append to `.gitignore`:
```
# Python / build123d
cad/.venv/
__pycache__/
*.pyc
```

- [ ] **Step 2: Remove the temporary analysis scripts**

Run:
```powershell
Remove-Item cad\_analyze_step.py, cad\_extract_geom.py
```

- [ ] **Step 3: Commit**

```powershell
git add .gitignore cad\_analyze_step.py cad\_extract_geom.py
git commit -m "chore(cad): ignore venv, remove reverse-engineering scripts"
```

- [ ] **Step 4: Final review of the branch**

Run:
```powershell
git log --oneline master..HEAD
git diff --stat master..HEAD
```
Expected: commits for spec, base plate, posts, cutouts, encoder, assembly, cleanup; `hexpad_bottom_case.step` absent from the diff.

---

## Verification Summary (maps to spec)

- Outline 76×74 + corner notches → Task 2 (analyzer size `76.0x74.0`).
- 3 mm body, stepped 14/16 mm cutouts → Task 4.
- 6 keys, 3×2, 19.05 mm, centered → Task 4 Step 3.
- Encoder Ø7 at (0,26) → Task 5.
- 4 corner posts (±31,±31), 3.5 mm, Ø1.7 pilots → Task 3.
- Clean Z extents, no −74.5 slab → Tasks 2–6 analyzer checks.
- Assembly = clean plate + untouched case → Task 6.
- Visual confirmation → Task 7.
