"""Generate hexpad.kicad_sch (schematic) matching the PCB's nets, via kiutils.

12 components: U1 (XIAO RP2040), SW1-6 (SW_Push), ENC1 (RotaryEncoder_Switch),
H1-4 (MountingHole), plus a PWR_FLAG on GND. Pins are connected with global
labels named after the board nets (SW1..SW6, ENCA, ENCB, ENCSW, GND); unused
XIAO pins get no-connects. Verify with: kicad-cli sch erc.

Run: python pcb/build_hexpad_sch.py
"""
import copy, os, uuid as uuidlib
from kiutils.schematic import Schematic
from kiutils.symbol import SymbolLib
from kiutils.items.schitems import SchematicSymbol, GlobalLabel, NoConnect, Connection
from kiutils.items.common import Position, Property, Effects, Font

SYM = r"C:/Program Files/KiCad/10.0/share/kicad/symbols"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hexpad.kicad_sch")
GRID = 1.27  # KiCad schematic connection grid (50 mil)

def U():
    return str(uuidlib.uuid4())

def g(v):  # snap to connection grid
    return round(v / GRID) * GRID

def load(libfile, name):
    lib = SymbolLib.from_file(os.path.join(SYM, libfile))
    for s in lib.symbols:
        if s.entryName == name:
            return copy.deepcopy(s)
    raise SystemExit(f"symbol not found: {name}")

# ---- XIAO symbol from a 14-pin connector, pins renamed ----
XIAO_PINS = {1:"D0",2:"D1",3:"D2",4:"D3",5:"D4",6:"D5",7:"D6",
             8:"D7",9:"D8",10:"D9",11:"D10",12:"3V3",13:"GND",14:"5V"}
xiao = load("Connector_Generic.kicad_sym", "Conn_01x14")
xiao.libId = "hexpad:XIAO-RP2040"
xiao.entryName = "XIAO-RP2040"
for u in xiao.units:
    for p in u.pins:
        p.name = XIAO_PINS[int(p.number)]
for pr in xiao.properties:
    if pr.key == "Value":
        pr.value = "XIAO-RP2040"
xiao_local = {int(p.number): (p.position.X, p.position.Y)
              for u in xiao.units for p in u.pins}

# standard symbols keep their real library nicknames (no "lib not configured" warning)
sw = load("Switch.kicad_sym", "SW_Push");                 sw.libId = "Switch:SW_Push"
enc = load("Device.kicad_sym", "RotaryEncoder_Switch");   enc.libId = "Device:RotaryEncoder_Switch"
mh = load("Mechanical.kicad_sym", "MountingHole");        mh.libId = "Mechanical:MountingHole"
pf = load("power.kicad_sym", "PWR_FLAG");                 pf.libId = "power:PWR_FLAG"

sch = Schematic.create_new()
sch.libSymbols = [xiao, sw, enc, mh, pf]

def eff():
    return Effects(font=Font(height=1.27, width=1.27))

def add_symbol(nick, entry, ref, value, x, y, angle=0):
    x, y = g(x), g(y)
    s = SchematicSymbol(libraryNickname=nick, entryName=entry,
                        position=Position(x, y, angle), unit=1, uuid=U())
    s.properties = [
        Property(key="Reference", value=ref, id=0, position=Position(x + 6.35, y - 2.54, 0), effects=eff()),
        Property(key="Value", value=value, id=1, position=Position(x + 6.35, y + 2.54, 0), effects=eff()),
    ]
    sch.schematicSymbols.append(s)
    return x, y

def label(net, x, y, angle=0):
    sch.globalLabels.append(
        GlobalLabel(text=net, shape="bidirectional", position=Position(x, y, angle), effects=eff()))

def noconn(x, y):
    sch.noConnects.append(NoConnect(position=Position(x, y)))

STUB = 5.08  # 200 mil wire stub so each label sits clear of its symbol

def wire(x1, y1, x2, y2):
    c = Connection(type="wire", points=[Position(g(x1), g(y1)), Position(g(x2), g(y2))])
    c.uuid = U()
    sch.graphicalItems.append(c)

def stub_label(net, ax, ay, angle):
    """Draw a short stub off the pin and put the global label at its far end."""
    dx = {0: STUB, 180: -STUB}.get(angle, 0)
    dy = {90: -STUB, 270: STUB}.get(angle, 0)
    ex, ey = ax + dx, ay + dy
    if dx or dy:
        wire(ax, ay, ex, ey)
    label(net, ex, ey, angle)

def apin(sx, sy, local):  # angle 0, no mirror: abs = (x+px, y-py)
    return (sx + local[0], sy - local[1])

# ---- XIAO (right) ----
ux, uy = add_symbol("hexpad", "XIAO-RP2040", "U1", "XIAO-RP2040", 190.5, 110.49)
xiao_net = {1:"SW1", 2:"SW2", 3:"SW3", 4:"SW4", 7:"SW5", 8:"SW6",
            9:"ENCA", 10:"ENCB", 11:"ENCSW", 13:"GND"}
xiao_nc = [5, 6, 12, 14]
for pn, loc in xiao_local.items():
    ax, ay = apin(ux, uy, loc)
    if pn in xiao_net:
        stub_label(xiao_net[pn], ax, ay, 180)
    elif pn in xiao_nc:
        noconn(ax, ay)

# ---- switches (left column): pin1 = signal, pin2 = GND ----
for i, net in enumerate(["SW1", "SW2", "SW3", "SW4", "SW5", "SW6"]):
    sx, sy = add_symbol("Switch", "SW_Push", f"SW{i+1}", "SW_Push", 60.96, 71.12 + i * 20.32)
    p1 = apin(sx, sy, (-5.08, 0)); stub_label(net, p1[0], p1[1], 180)
    p2 = apin(sx, sy, (5.08, 0));  stub_label("GND", p2[0], p2[1], 0)

# ---- encoder (top-left) ----
ex, ey = add_symbol("Device", "RotaryEncoder_Switch", "ENC1", "EC11", 111.76, 50.8)
for loc, net, ang in [((-7.62, 2.54), "ENCA", 180), ((-7.62, -2.54), "ENCB", 180),
                      ((-7.62, 0.0), "GND", 180), ((7.62, 2.54), "ENCSW", 0),
                      ((7.62, -2.54), "GND", 0)]:
    ax, ay = apin(ex, ey, loc); stub_label(net, ax, ay, ang)

# ---- PWR_FLAG on GND ----
px, py = add_symbol("power", "PWR_FLAG", "#FLG1", "PWR_FLAG", 190.5, 149.86)
fx, fy = apin(px, py, (0.0, 0.0)); stub_label("GND", fx, fy, 0)

# ---- mounting holes (no pins) ----
for i, (hx, hy) in enumerate([(241.3, 40.64), (241.3, 55.88), (241.3, 71.12), (241.3, 86.36)]):
    add_symbol("Mechanical", "MountingHole", f"H{i+1}", "MountingHole", hx, hy)

sch.to_file(OUT)

# project symbol library + table so the custom XIAO lib is "configured"
# (removes the last ERC "library not in configuration" warning)
PROJ = os.path.dirname(OUT)
xlib = SymbolLib()
xlib.filePath = os.path.join(PROJ, "hexpad.kicad_sym")
xiao_libcopy = copy.deepcopy(xiao)
xiao_libcopy.libId = "XIAO-RP2040"
xlib.symbols = [xiao_libcopy]
xlib.to_file(xlib.filePath)
with open(os.path.join(PROJ, "sym-lib-table"), "w") as f:
    f.write('(sym_lib_table\n  (version 7)\n'
            '  (lib (name "hexpad")(type "KiCad")'
            '(uri "${KIPRJMOD}/hexpad.kicad_sym")(options "")(descr "hexpad project symbols"))\n)\n')

print(f"wrote {OUT}: {len(sch.schematicSymbols)} symbols, "
      f"{len(sch.globalLabels)} labels, {len(sch.noConnects)} no-connects")
