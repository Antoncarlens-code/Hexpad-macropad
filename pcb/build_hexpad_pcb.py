"""Generate the hexpad PCB (KiCad 10 / pcbnew) from the electronics design spec.

Spec: docs/electronics/hexpad-pcb-design.md
6-key (3x2) macropad + EC11 encoder, driven by a Seeed XIAO RP2040.
No matrix / no diodes -- each switch wires direct to a GPIO, other leg to GND.

Run with KiCad's bundled Python:
    & "C:/Program Files/KiCad/10.0/bin/python.exe" pcb/build_hexpad_pcb.py

Coordinates follow the CAD/spec frame (origin = board center, +Y = rear).
KiCad uses Y-down, so every Y is negated on the way in (yk = -y). The layout is
Y-symmetric except the encoder (+26) and XIAO (rear/front), so this only flips
front/back consistently for the whole board.
"""
import os
import pcbnew
from pcbnew import VECTOR2I, FromMM

KICAD = r"C:/Program Files/KiCad/10.0/share/kicad/footprints"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hexpad.kicad_pcb")

TRACK_W = FromMM(0.40)
CLEAR = FromMM(0.20)


def xy(x, y):
    """Spec mm -> KiCad VECTOR2I (Y negated)."""
    return VECTOR2I(FromMM(x), FromMM(-y))


# ---------------------------------------------------------------- nets
def main():
    board = pcbnew.BOARD()

    # design rules: 0.2mm clearance, 0.4mm default track
    ds = board.GetDesignSettings()
    ds.m_TrackMinWidth = FromMM(0.20)
    ds.m_MinClearance = CLEAR

    nets = {}
    def net(name):
        if name not in nets:
            n = pcbnew.NETINFO_ITEM(board, name)
            board.Add(n)
            nets[name] = n
        return nets[name]

    GND = net("GND")
    for nm in ("SW1", "SW2", "SW3", "SW4", "SW5", "SW6", "ENCA", "ENCB", "ENCSW"):
        net(nm)

    # ---------------------------------------------------------- footprints
    def load(lib, name):
        fp = pcbnew.FootprintLoad(os.path.join(KICAD, lib), name)
        if fp is None:
            raise RuntimeError(f"footprint not found: {lib}/{name}")
        board.Add(fp)
        return fp

    def setnet(fp, padnum, netobj):
        for p in fp.Pads():
            if p.GetNumber() == str(padnum):
                p.SetNet(netobj)
                return
        raise RuntimeError(f"pad {padnum} not on {fp.GetReference()}")

    def place(fp, ref, val, x, y, rot=0, back=False):
        fp.SetReference(ref)
        fp.SetValue(val)
        fp.SetPosition(xy(x, y))
        if rot:
            fp.SetOrientationDegrees(rot)
        if back:
            fp.Flip(fp.GetPosition(), False)

    # switches: SW pad "1" = signal (to GPIO), pad "2" = GND
    sw_pos = {
        "SW1": (-19.05, -9.525, "SW1"),
        "SW2": (0.00, -9.525, "SW2"),
        "SW3": (19.05, -9.525, "SW3"),
        "SW4": (-19.05, 9.525, "SW4"),
        "SW5": (0.00, 9.525, "SW5"),
        "SW6": (19.05, 9.525, "SW6"),
    }
    for ref, (x, y, signet) in sw_pos.items():
        fp = load("Button_Switch_Keyboard.pretty", "SW_Cherry_MX_1.00u_PCB")
        place(fp, ref, "SW_MX", x, y)
        setnet(fp, 1, net(signet))
        setnet(fp, 2, GND)

    # encoder: A,B -> ENCA,ENCB ; S1 -> ENCSW ; C,S2,MP -> GND
    enc = load("Rotary_Encoder.pretty", "RotaryEncoder_Alps_EC11E-Switch_Vertical_H20mm")
    place(enc, "ENC1", "EC11", 0.0, 26.0)
    setnet(enc, "A", net("ENCA"))
    setnet(enc, "B", net("ENCB"))
    setnet(enc, "S1", net("ENCSW"))
    for pn in ("C", "S2", "MP"):
        setnet(enc, pn, GND)

    # mounting holes (mechanical, no net) -- X=32 to match the case screw bosses
    for ref, (x, y) in {"H1": (32, 31), "H2": (-32, 31),
                        "H3": (32, -31), "H4": (-32, -31)}.items():
        h = load("MountingHole.pretty", "MountingHole_2.2mm_M2")
        place(h, ref, "M2", x, y)

    # ---------------------------------------------------------- XIAO (built in code)
    xiao = pcbnew.FOOTPRINT(board)
    xiao.SetReference("U1")
    xiao.SetValue("XIAO-RP2040")
    # 14 THT pads, 2.54 pitch, rows +/-7.62 ; pin1=D0..pin11=D10, 12=3V3,13=GND,14=5V
    pad_x_top = [7.62, 5.08, 2.54, 0.0, -2.54, -5.08, -7.62]      # pads 1..7
    pad_x_bot = [-7.62, -5.08, -2.54, 0.0, 2.54, 5.08, 7.62]      # pads 8..14
    layout = [(i + 1, pad_x_top[i], -7.62) for i in range(7)] + \
             [(i + 8, pad_x_bot[i], 7.62) for i in range(7)]
    for num, px, py in layout:
        pad = pcbnew.PAD(xiao)
        pad.SetNumber(str(num))
        pad.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
        pad.SetAttribute(pcbnew.PAD_ATTRIB_PTH)
        pad.SetSize(VECTOR2I(FromMM(1.524), FromMM(1.524)))
        pad.SetDrillSize(VECTOR2I(FromMM(0.889), FromMM(0.889)))
        pad.SetPosition(VECTOR2I(FromMM(px), FromMM(py)))
        pad.SetLayerSet(pad.PTHMask())
        xiao.Add(pad)
    board.Add(xiao)
    place(xiao, "U1", "XIAO-RP2040", -10.0, -27.0, rot=90, back=True)
    # net map per spec section 3
    xiao_nets = {1: "SW1", 2: "SW2", 3: "SW3", 4: "SW4", 7: "SW5", 8: "SW6",
                 9: "ENCA", 10: "ENCB", 11: "ENCSW", 13: "GND"}
    for pn, netname in xiao_nets.items():
        setnet(xiao, pn, GND if netname == "GND" else net(netname))

    # ---------------------------------------------------------- board outline
    # 76x74 rectangle (X +/-38, Y +/-37) with 3x3 corner notches (12 verts)
    outline = [
        (-35, 37), (35, 37), (35, 34), (38, 34), (38, -34), (35, -34),
        (35, -37), (-35, -37), (-35, -34), (-38, -34), (-38, 34), (-35, 34),
    ]
    for i in range(len(outline)):
        a = outline[i]
        b = outline[(i + 1) % len(outline)]
        seg = pcbnew.PCB_SHAPE(board)
        seg.SetShape(pcbnew.SHAPE_T_SEGMENT)
        seg.SetStart(xy(*a))
        seg.SetEnd(xy(*b))
        seg.SetLayer(pcbnew.Edge_Cuts)
        seg.SetWidth(FromMM(0.15))
        board.Add(seg)

    # ---------------------------------------------------------- GND pour (B.Cu)
    # Bottom ground plane; signals route on F.Cu. Outline only -- the fill is
    # done in route_and_export.py (headless ZONE_FILLER is unstable mid-build).
    zone = pcbnew.ZONE(board)
    zone.SetLayer(pcbnew.B_Cu)
    zone.SetNet(GND)
    zone.SetLocalClearance(CLEAR)
    sps = zone.Outline()
    sps.NewOutline()
    for (x, y) in outline:
        sps.Append(FromMM(x), FromMM(-y))
    board.Add(zone)

    # ---------------------------------------------------------- branding (silk)
    # Hackpad rule: every part must carry the hackpad's name. Front silkscreen,
    # centered along the front edge between the two front mounting holes.
    brand = pcbnew.PCB_TEXT(board)
    brand.SetText("Hexpad")
    brand.SetLayer(pcbnew.F_SilkS)
    brand.SetPosition(xy(0.0, -31.0))
    brand.SetTextSize(VECTOR2I(FromMM(2.2), FromMM(2.2)))
    brand.SetTextThickness(FromMM(0.3))
    board.Add(brand)

    board.BuildConnectivity()
    pcbnew.SaveBoard(OUT, board)
    print(f"saved {OUT}")
    print(f"footprints: {len(board.GetFootprints())}  nets: {board.GetNetCount()}  "
          f"zones: {len(board.Zones())}")


if __name__ == "__main__":
    main()
