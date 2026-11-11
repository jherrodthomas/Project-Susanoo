# SPDX-License-Identifier: Apache-2.0
"""Dimensioned A3 drawing sheets of the concept layouts (SUS-CAD-001), one per layout.

    $FREECAD_PYTHON tools/cad/drawings.py [CL-01 ...]     # writes cad/drawings/CL-nn.svg

Each sheet is third-angle: side elevation (principal view), plan view above it, front view to the right,
all at 1:50, projected with FreeCAD TechDraw hidden-line removal. Dimensions come from the geometry and from
cad/metrics.json, so they match the review page. Concept layouts only: placeholder geometry, not for
manufacture.
"""
from __future__ import annotations

import json
import math
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_concepts as bc  # noqa: E402  (adds the FreeCAD library path)
import FreeCAD  # noqa: E402
import Part  # noqa: E402
import TechDraw  # noqa: E402
import yaml  # noqa: E402

ROOT = bc.ROOT
OUT = ROOT / "cad/drawings"
SCALE = 50                      # 1:50, the same for every layout so sheets compare directly
SHEET_W, SHEET_H = 420.0, 297.0  # A3 landscape, mm
DEFLECTION = 6.0                # mm in the world: finer than a line width at 1:30
V = FreeCAD.Vector

# View direction and the map from TechDraw's 2D frame (u, v) to world-axis sheet coordinates (h, up).
# Established empirically for FreeCAD 1.1: see the probe in the commit that added this file.
VIEWS = {
    "side":  (V(0, -1, 0), lambda u, v: (v, -u)),   # h = x (front to the right), up = z
    "front": (V(1, 0, 0),  lambda u, v: (-v, u)),   # h = y (walker's left to the right), up = z
    "top":   (V(0, 0, 1),  lambda u, v: (u, v)),    # h = x, up = y
}


def project(shape, view):
    """Visible edges of shape seen in view, as polylines in world metres (h, up)."""
    direction, frame = VIEWS[view]
    out = []
    groups = TechDraw.projectEx(shape, direction)
    for comp in (groups[0], groups[3]):  # visible sharp edges and visible outlines
        if comp is None or comp.isNull():
            continue
        for edge in comp.Edges:
            pts = edge.discretize(Deflection=DEFLECTION) if edge.Length > DEFLECTION else [edge.Vertexes[0].Point, edge.Vertexes[-1].Point]
            out.append([frame(p.x / 1000.0, p.y / 1000.0) for p in pts])
    return out


def world_extent(view, bb):
    """(hmin, hmax, upmin, upmax) of a world bounding box (metres) in view coordinates."""
    if view == "side":
        return bb.XMin, bb.XMax, bb.ZMin, bb.ZMax
    if view == "front":
        return bb.YMin, bb.YMax, bb.ZMin, bb.ZMax
    return bb.XMin, bb.XMax, bb.YMin, bb.YMax


class Sheet:
    def __init__(self):
        self.parts: list[str] = []

    def add(self, s: str):
        self.parts.append(s)

    def polyline(self, pts, cls):
        d = "M" + " L".join(f"{x:.2f} {y:.2f}" for x, y in pts)
        self.add(f'<path class="{cls}" d="{d}"/>')

    def text(self, x, y, s, cls="t", anchor="start", rotate=None):
        tr = f' transform="rotate({rotate} {x:.2f} {y:.2f})"' if rotate is not None else ""
        self.add(f'<text class="{cls}" x="{x:.2f}" y="{y:.2f}" text-anchor="{anchor}"{tr}>{s}</text>')


class ViewPort:
    """Places one view on the sheet: world metres -> sheet mm at 1:SCALE, origin at sheet point (ox, oy)."""

    def __init__(self, sheet, ox, oy, h0, up0):
        self.s, self.ox, self.oy, self.h0, self.up0 = sheet, ox, oy, h0, up0

    def xy(self, h, up):
        return self.ox + (h - self.h0) * 1000 / SCALE, self.oy - (up - self.up0) * 1000 / SCALE

    def lines(self, polys, cls):
        for poly in polys:
            self.s.polyline([self.xy(h, u) for h, u in poly], cls)

    def dim(self, a, b, offset_mm, label=None, side="h"):
        """Linear dimension between world points a and b (h, up), offset perpendicular by offset_mm on the sheet."""
        (x1, y1), (x2, y2) = self.xy(*a), self.xy(*b)
        if side == "h":   # horizontal dimension: measure along sheet x
            yd = (min(y1, y2) if offset_mm < 0 else max(y1, y2)) + offset_mm
            self.s.polyline([(x1, y1), (x1, yd + (1.5 if offset_mm > 0 else -1.5))], "ext")
            self.s.polyline([(x2, y2), (x2, yd + (1.5 if offset_mm > 0 else -1.5))], "ext")
            self.s.add(f'<path class="dim" marker-start="url(#arr)" marker-end="url(#arr)" d="M{x1:.2f} {yd:.2f} L{x2:.2f} {yd:.2f}"/>')
            val = abs(a[0] - b[0]) * 1000
            self.s.text((x1 + x2) / 2, yd - 1.2, label or f"{val:.0f}", "dt", "middle")
        else:             # vertical dimension: measure along sheet y
            xd = (min(x1, x2) if offset_mm < 0 else max(x1, x2)) + offset_mm
            self.s.polyline([(x1, y1), (xd + (1.5 if offset_mm > 0 else -1.5), y1)], "ext")
            self.s.polyline([(x2, y2), (xd + (1.5 if offset_mm > 0 else -1.5), y2)], "ext")
            self.s.add(f'<path class="dim" marker-start="url(#arr)" marker-end="url(#arr)" d="M{xd:.2f} {y1:.2f} L{xd:.2f} {y2:.2f}"/>')
            val = abs(a[1] - b[1]) * 1000
            self.s.text(xd - 1.2, (y1 + y2) / 2, label or f"{val:.0f}", "dt", "middle", rotate=-90)

    def cg(self, h, up):
        x, y = self.xy(h, up)
        r = 2.2
        self.s.add(f'<circle class="cgo" cx="{x:.2f}" cy="{y:.2f}" r="{r}"/>'
                   f'<path class="cgf" d="M{x:.2f} {y:.2f} L{x + r:.2f} {y:.2f} A{r} {r} 0 0 0 {x:.2f} {y - r:.2f} Z"/>'
                   f'<path class="cgf" d="M{x:.2f} {y:.2f} L{x - r:.2f} {y:.2f} A{r} {r} 0 0 0 {x:.2f} {y + r:.2f} Z"/>')

    def leader(self, h, up, text, to_x):
        """Label outside the view at sheet x to_x, with a leader line back to the world point (h, up)."""
        x, y = self.xy(h, up)
        elbow = to_x - 2 if to_x > x else to_x + 2
        self.s.polyline([(x, y), (elbow, y - 4), (to_x, y - 4)], "ext")
        self.s.text(to_x + (1 if to_x > x else -1), y - 3.2, text, "lt", "start" if to_x > x else "end")

    def label(self, h, up, s, dx=0, dy=0, anchor="start"):
        x, y = self.xy(h, up)
        self.s.text(x + dx, y + dy, s, "lt", anchor)


STYLE = """
  .vis{fill:none;stroke:#111;stroke-width:0.30;stroke-linejoin:round;stroke-linecap:round}
  .ref{fill:none;stroke:#8a8f98;stroke-width:0.22}
  .uav{fill:none;stroke:#1d4f91;stroke-width:0.20}
  .frame{fill:none;stroke:#111;stroke-width:0.7}
  .thin{fill:none;stroke:#111;stroke-width:0.25}
  .ground{fill:none;stroke:#111;stroke-width:0.35}
  .ctr{fill:none;stroke:#555;stroke-width:0.18;stroke-dasharray:6 1.5 1 1.5}
  .poly{fill:#14b8a6;fill-opacity:0.12;stroke:#0f766e;stroke-width:0.30;stroke-dasharray:2 1}
  .ext{fill:none;stroke:#333;stroke-width:0.15}
  .dim{fill:none;stroke:#333;stroke-width:0.18}
  .cgo{fill:#fff;stroke:#111;stroke-width:0.25}
  .cgf{fill:#111}
  text{font-family:'DejaVu Sans','Liberation Sans',Arial,sans-serif;fill:#111}
  .t{font-size:3.2px}
  .dt{font-size:2.6px}
  .lt{font-size:2.5px;fill:#333}
  .vt{font-size:3.0px;font-weight:bold;letter-spacing:0.2px}
  .tb{font-size:2.4px;fill:#444}
  .tbv{font-size:3.4px;font-weight:bold}
  .big{font-size:5.2px;font-weight:bold}
  .warn{font-size:3.2px;font-weight:bold;fill:#b45309}
"""


def draw(p: dict, common: dict, met: dict, doc_rev: str, posture: str = "standing") -> str:
    m, info = bc.build_layout(p, common, posture)
    source = f"cad/params/{p['id']}.yaml"
    if posture != "standing":
        p = {**p, "id": f"{p['id']}-{posture}", "title": f"{p['title']} — {posture.upper()} for egress"}
    walker = Part.makeCompound([pt["shape"] for pt in m.parts if pt["group"] in ("walker",)])
    uav = [pt["shape"] for pt in m.parts if pt["group"] in ("uav", "offboard")]
    uav = Part.makeCompound(uav) if uav else None
    ref = Part.makeCompound([pt["shape"] for pt in m.parts if pt["group"] == "reference"])
    everything = Part.makeCompound([walker] + ([uav] if uav else []) + [ref])
    bb = everything.BoundBox
    bbm = FreeCAD.BoundBox(bb.XMin / 1000, bb.YMin / 1000, bb.ZMin / 1000, bb.XMax / 1000, bb.YMax / 1000, bb.ZMax / 1000)
    wb = Part.makeCompound([walker] + ([uav] if uav and info["dock"] == "onboard" else [])).BoundBox
    wbm = FreeCAD.BoundBox(wb.XMin / 1000, wb.YMin / 1000, wb.ZMin / 1000, wb.XMax / 1000, wb.YMax / 1000, wb.ZMax / 1000)

    s = Sheet()
    k = 1000 / SCALE  # sheet mm per metre
    # Layout: side view bottom-left, plan view above it (aligned in x), front view to the right (aligned in z).
    side_h0, side_h1, z0, z1 = world_extent("side", bbm)
    pb = Part.makeCompound([walker] + ([uav] if uav else [])).BoundBox  # plan without the scale person
    pbm = FreeCAD.BoundBox(pb.XMin / 1000, pb.YMin / 1000, pb.ZMin / 1000, pb.XMax / 1000, pb.YMax / 1000, pb.ZMax / 1000)
    top_h0, top_h1, y0, y1 = world_extent("top", pbm)
    fr_h0, fr_h1, _, _ = world_extent("front", bbm)
    side_w = (side_h1 - side_h0) * k
    side_hgt = (z1 - z0) * k
    left, ground_y = 44.0, 226.0
    sv = ViewPort(s, left, ground_y, side_h0, 0.0)
    tv = ViewPort(s, left, ground_y - side_hgt - 24, side_h0, y0)  # plan: its y0 edge 24 mm above the side view
    fv = ViewPort(s, left + side_w + 62, ground_y, fr_h0, 0.0)

    for view, vp in (("side", sv), ("top", tv), ("front", fv)):
        vp.lines(project(walker, view), "vis")
        if uav:
            vp.lines(project(uav, view), "uav")
        if view != "top":
            vp.lines(project(ref, view), "ref")
    # Ground lines and view titles
    for vp, (h0, h1) in ((sv, (side_h0, side_h1)), (fv, (fr_h0, fr_h1))):
        a, b = vp.xy(h0 - 0.3, 0), vp.xy(h1 + 0.3, 0)
        s.polyline([a, b], "ground")
        for i in range(int((b[0] - a[0]) / 3)):
            x = a[0] + i * 3
            s.polyline([(x, a[1]), (x - 1.6, a[1] + 1.6)], "thin")
    s.text(sv.xy(side_h0, 0)[0], ground_y + 20, "SIDE ELEVATION (from the right, front →)", "vt")
    s.text(tv.xy(side_h0, y0)[0], tv.xy(side_h0, y1)[1] - 4, "PLAN (from above, front →)", "vt")
    s.text(fv.xy(fr_h0, 0)[0], ground_y + 20, "FRONT VIEW (from the front)", "vt")

    # --- Dimensions: side elevation ---
    H = met["height_m"]
    sv.dim((wbm.XMax, 0), (wbm.XMax, H), 6, side="v")
    sv.dim((wbm.XMin, 0), (wbm.XMax, 0), 7, side="h")
    sv.dim((wbm.XMax, 0), (wbm.XMax, info["eye"][2]), 12, f"pilot eye {info['eye'][2] * 1000:.0f}", side="v")
    sv.dim((wbm.XMax, 0), (wbm.XMax, info["floor"]), 18, f"cockpit floor {info['floor'] * 1000:.0f}", side="v")
    sv.dim((wbm.XMax, 0), (wbm.XMax, info["hip_z"]), 24, f"hip {info['hip_z'] * 1000:.0f}", side="v")
    cgx, cgy, cgz = met["cg_m"]
    sv.cg(cgx, cgz)
    sv.leader(cgx, cgz, f"CG height {cgz * 1000:.0f}", sv.xy(side_h0, 0)[0] - 2)
    a, b = sv.xy(cgx, cgz), sv.xy(cgx, 0)
    s.polyline([a, b], "ctr")

    # --- Dimensions: front view ---
    fv.dim((wbm.YMin, 0), (wbm.YMax, 0), 7, side="h")
    feet_y = sorted({round(pt[1], 3) for pt in met["support_polygon_m"]})
    fv.dim((feet_y[0], 0), (feet_y[-1], 0), 13, f"track {(feet_y[-1] - feet_y[0]) * 1000:.0f}", side="h")
    fv.cg(cgy, cgz)
    a, b = fv.xy(cgy, cgz), fv.xy(cgy, 0)
    s.polyline([a, b], "ctr")

    # --- Plan view: support polygon, CG and static margin ---
    poly = met["support_polygon_m"]
    pts = " ".join(f"{x:.2f},{y:.2f}" for x, y in (tv.xy(px, py) for px, py in poly))
    s.add(f'<polygon class="poly" points="{pts}"/>')
    tv.cg(cgx, cgy)
    margin = met["static_margin_m"]
    right = tv.xy(top_h1, 0)[0] + 6
    tv.leader(cgx, cgy, f"CG · static margin {margin * 1000:.0f} · tip angle {met['static_tip_angle_deg']:.1f}°", right)
    corner = max(poly, key=lambda q: (q[0], -q[1]))
    tv.leader(corner[0], corner[1], "support polygon (feet)", right)

    # --- Notes ---
    notes = [
        "NOTES",
        "1. Concept layout for review and alignment. Placeholder geometry: not a design, not for manufacture.",
        f"2. Dimensions in millimetres; scale 1:{SCALE} on A3. Third-angle projection.",
        "3. Centre of gravity uses placeholder effective densities (cad/params/common.yaml).",
        "4. Static margin: shortest distance from CG to the support-polygon edge; tip angle = atan(margin / CG height).",
        f"5. Docked rotor to pilot {met['rotor_to_pilot_m'] * 1000:.0f}; UAV drawn in blue; 1.75 m person in grey.",
    ]
    nx, ny = SHEET_W - 10 - 180, 22
    for i, n in enumerate(notes):
        s.text(nx, ny + i * 4.6, n, "vt" if i == 0 else "lt")
    flags = []
    if margin < 0.3:
        flags.append(f"⚠ static margin {margin * 1000:.0f} mm is under the 300 mm review flag")
    if met["rotor_to_pilot_m"] < 1.0:
        flags.append(f"⚠ docked rotor {met['rotor_to_pilot_m'] * 1000:.0f} mm from the pilot: under the 1000 mm flag")
    for i, f_ in enumerate(flags):
        s.text(nx, ny + len(notes) * 4.6 + 3 + i * 4.6, f_, "warn")

    # --- Frame and title block ---
    s.add(f'<rect class="frame" x="10" y="10" width="{SHEET_W - 20}" height="{SHEET_H - 20}"/>')
    tbx, tby, tbw, tbh = SHEET_W - 10 - 180, SHEET_H - 10 - 32, 180, 32
    s.add(f'<rect class="frame" x="{tbx}" y="{tby}" width="{tbw}" height="{tbh}"/>')
    for yy in (tby + 11, tby + 21.5):
        s.polyline([(tbx, yy), (tbx + tbw, yy)], "thin")
    for xx in (tbx + 60, tbx + 100, tbx + 140):
        s.polyline([(xx, tby + 11), (xx, tby + tbh)], "thin")
    s.text(tbx + 3, tby + 4.5, "PROJECT SUSANOO · SUS-M1 / SUS-A1 / SUS-I1", "tb")
    s.text(tbx + 3, tby + 9.2, f"{p['id']} · {p['title']}", "tbv")
    cells = [("DRAWING", f"SUS-CAD-001-{p['id']}"), ("SCALE / SHEET", f"1:{SCALE} · A3"), ("UNITS", "mm"), ("REVISION", doc_rev),
             ("STATUS", "CONCEPT, NOT REVIEWED"), ("DRAWN", "Claude (AI-drafted), I0"), ("SOURCE", source),
             ("LICENCE", "CC BY 4.0")]
    for i, (lab, val) in enumerate(cells):
        cx = [tbx + 3, tbx + 63, tbx + 103, tbx + 143][i % 4]
        cy = tby + 15 if i < 4 else tby + 25.5
        s.text(cx, cy, lab, "tb")
        s.text(cx, cy + 4.2, val, "tbv" if len(val) <= 17 or i % 4 == 0 else "tb")
    # third-angle projection symbol
    px_, py_ = tbx - 26, tby + 16
    s.add(f'<path class="thin" d="M{px_} {py_ - 5} L{px_ + 8} {py_ - 3} L{px_ + 8} {py_ + 3} L{px_} {py_ + 5} Z"/>'
          f'<circle class="thin" cx="{px_ + 17}" cy="{py_}" r="5"/><circle class="thin" cx="{px_ + 17}" cy="{py_}" r="2.4"/>')
    s.text(px_ - 2, py_ + 10, "third-angle", "tb")

    body = "\n".join(s.parts)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{SHEET_W}mm" height="{SHEET_H}mm" '
            f'viewBox="0 0 {SHEET_W} {SHEET_H}">\n<title>{p["id"]} concept layout drawing</title>\n'
            f'<defs><style>{STYLE}</style><marker id="arr" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="3.2" '
            f'markerHeight="3.2" orient="auto-start-reverse"><path d="M0 1.5 L10 5 L0 8.5 Z" fill="#333"/></marker></defs>\n'
            f'<rect x="0" y="0" width="{SHEET_W}" height="{SHEET_H}" fill="#fff"/>\n{body}\n</svg>\n')


def main() -> int:
    ids = sys.argv[1:]
    common = yaml.safe_load((bc.PARAMS / "common.yaml").read_text())
    metrics = json.loads((ROOT / "cad/metrics.json").read_text())["concepts"]
    docs = yaml.safe_load((ROOT / "pdac/documents.yaml").read_text())["items"]
    rev = next(d["revision"] for d in docs if d["id"] == "SUS-CAD-001")
    OUT.mkdir(parents=True, exist_ok=True)
    for path in sorted(bc.PARAMS.glob("CL-*.yaml")):
        p = yaml.safe_load(path.read_text())
        if ids and p["id"] not in ids:
            continue
        svg = draw(p, common, metrics[p["id"]], rev)
        (OUT / f"{p['id']}.svg").write_text(svg)
        for posture in (p.get("postures") or {}):
            psvg = draw(p, common, metrics[p["id"]]["postures"][posture], rev, posture)
            (OUT / f"{p['id']}-{posture}.svg").write_text(psvg)
            print(f"wrote cad/drawings/{p['id']}-{posture}.svg")
        print(f"wrote cad/drawings/{p['id']}.svg ({len(svg) // 1024} KiB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
