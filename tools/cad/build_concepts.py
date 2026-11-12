# SPDX-License-Identifier: Apache-2.0
"""Build the Susanoo concept layouts in FreeCAD from cad/params/*.yaml.

    tools/cad/make.sh                       # build, render and regenerate the review page
    $FREECAD_PYTHON tools/cad/build_concepts.py [--out build/cad] [CL-01 ...]

Runs under the Python of a FreeCAD 1.1 install (tools/cad/environment.yml). For each concept it writes,
under --out/<ID>/: <ID>.FCStd, <ID>.step, one STL per part class and manifest.json (for the renderer),
and it writes cad/metrics.json, the committed summary that the review page is generated from.

These are concept layouts for review and alignment: primitive solids placed by placeholder parameters.
They are not designs, and every metric is a property of the placeholder geometry.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
from pathlib import Path

sys.path.append(os.environ.get("FREECAD_LIB", str(Path(sys.executable).resolve().parents[1] / "lib")))
import FreeCAD  # noqa: E402
import MeshPart  # noqa: E402
import Part  # noqa: E402
import yaml  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
PARAMS = ROOT / "cad/params"
MM = 1000.0

# Part class -> render colour, opacity and the architecture component it belongs to.
CLASSES = {
    "structure": ("#5b6676", 1.0, "SUS-M1-WLK"),
    "actuator":  ("#c9a33a", 1.0, "SUS-M1-WLK"),
    "arm":       ("#7b8797", 1.0, "SUS-M1-MAN"),
    "cage":      ("#e2701f", 1.0, "SUS-M1-PIL"),
    "seat":      ("#2b313b", 1.0, "SUS-M1-PIL"),
    "occupant":  ("#3a78d6", 1.0, "SUS-M1-PIL"),
    "power":     ("#2f8a5b", 1.0, "SUS-M1-PWR"),
    "safety":    ("#d42a2a", 1.0, "SUS-M1-SAF"),
    "dock":      ("#7d55c7", 1.0, "SUS-M1-DCK"),
    "uav":       ("#1597c9", 1.0, "SUS-A1"),
    "rotor":     ("#1597c9", 0.35, "SUS-A1"),
        "armor":     ("#8d97a5", 1.0, "SUS-M1-PIL"),
    "hose":      ("#2e343d", 1.0, "SUS-M1-PWR"),
    "access":    ("#e0b100", 1.0, "SUS-M1-PIL"),
    "escape":    ("#d9480f", 1.0, "SUS-M1-PIL"),
    "reference": ("#a3acb9", 1.0, None),
    "payload":   ("#b08850", 1.0, None),   # carried load: not part of the walker, mass TBD (SYS-020)
}
DENSITY_CLASS = {"arm": "structure", "seat": "structure", "rotor": "uav", "hose": "structure", "access": "structure", "escape": "structure"}


def V(x, y, z):
    return FreeCAD.Vector(x * MM, y * MM, z * MM)


class Model:
    """Parts in metres; each part has a class (colour, density) and a group (walker, uav, offboard, reference)."""

    def __init__(self):
        self.parts: list[dict] = []
        self.feet: list[tuple[float, float]] = []  # ground contact points for the support polygon
        self.group = "walker"

    def add(self, name, cls, shape):
        self.parts.append({"name": name, "cls": cls, "shape": shape, "group": self.group})

    def box(self, name, cls, lo, size):
        self.add(name, cls, Part.makeBox(size[0] * MM, size[1] * MM, size[2] * MM, V(*lo)))

    def cbox(self, name, cls, center, size):
        self.box(name, cls, [c - s / 2 for c, s in zip(center, size)], size)

    def cyl(self, name, cls, p1, p2, r):
        a, b = V(*p1), V(*p2)
        d = b.sub(a)
        self.add(name, cls, Part.makeCylinder(r * MM, d.Length, a, d))

    def sph(self, name, cls, c, r):
        self.add(name, cls, Part.makeSphere(r * MM, V(*c)))

    def obox(self, name, cls, p1, p2, w, d, shift=(0, 0, 0), fillet=0.0):
        """Box of width w (y) and depth d (x) running along the segment p1 -> p2, moved by shift."""
        a, b = V(*add(p1, shift)), V(*add(p2, shift))
        axis = b.sub(a)
        shape = Part.makeBox(d * MM, w * MM, axis.Length, V(-d / 2, -w / 2, 0))
        if fillet:
            shape = shape.makeFillet(fillet * MM, shape.Edges)
        shape.Placement = FreeCAD.Placement(a, FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), axis))
        self.add(name, cls, shape)

    def rbox(self, name, cls, lo, size, fillet):
        shape = Part.makeBox(*(s * MM for s in size), V(*lo))
        self.add(name, cls, shape.makeFillet(fillet * MM, shape.Edges))


def lerp(a, b, t):
    return [x + (y - x) * t for x, y in zip(a, b)]


def add(a, b):
    return [x + y for x, y in zip(a, b)]


# --- Shared assemblies ----------------------------------------------------------------------------

def hydraulic(m, name, p1, p2, r=0.06):
    """Barrel and rod between two points: the visual cue for the TS-001 hydraulic hypothesis."""
    mid = lerp(p1, p2, 0.6)
    m.cyl(f"{name}-barrel", "actuator", p1, mid, r)
    m.cyl(f"{name}-rod", "actuator", mid, p2, r * 0.45)


def cage(m, x0, y0, z0, dx, dy, dz, r):
    """Protective open-frame cockpit cage: the 12 box edges, side braces and a floor plate."""
    xs, ys, zs = (x0, x0 + dx), (y0, y0 + dy), (z0, z0 + dz)
    n = 0
    for y in ys:
        for z in zs:
            m.cyl(f"cage-x{n}", "cage", [xs[0], y, z], [xs[1], y, z], r); n += 1
    for x in xs:
        for z in zs:
            m.cyl(f"cage-y{n}", "cage", [x, ys[0], z], [x, ys[1], z], r); n += 1
    for x in xs:
        for y in ys:
            m.cyl(f"cage-z{n}", "cage", [x, y, zs[0]], [x, y, zs[1]], r); n += 1
    for y in ys:  # diagonal side braces below the window line
        m.cyl(f"cage-brace{n}", "cage", [xs[0], y, zs[0]], [xs[1], y, zs[0] + dz * 0.45], r * 0.8); n += 1
    m.box("cockpit-floor", "cage", [x0, y0, z0 - 0.04], [dx, dy, 0.04])


def pilot(m, floor, x_back, facing=1.0):
    """Seated pilot mannequin (about 1.75 m standing), seat and console. Returns the eye point."""
    h = [x_back + 0.30 * facing, 0.0, floor + 0.47]  # H-point
    m.cbox("seat-pan", "seat", [h[0] + 0.05, 0, floor + 0.38], [0.50, 0.50, 0.08])
    m.cbox("seat-back", "seat", [h[0] - 0.22, 0, floor + 0.75], [0.08, 0.50, 0.70])
    m.cyl("seat-post", "seat", [h[0], 0, floor], [h[0], 0, floor + 0.34], 0.05)
    neck = [h[0] - 0.06, 0, h[2] + 0.58]
    m.sph("pilot-pelvis", "occupant", h, 0.15)
    m.cyl("pilot-torso", "occupant", h, neck, 0.16)
    head = [neck[0] + 0.02, 0, neck[2] + 0.16]
    m.sph("pilot-head", "occupant", head, 0.11)
    for s in (1, -1):
        knee = [h[0] + 0.45, s * 0.11, h[2] + 0.02]
        m.cyl(f"pilot-thigh{s}", "occupant", [h[0], s * 0.11, h[2]], knee, 0.075)
        m.cyl(f"pilot-shin{s}", "occupant", knee, [knee[0] + 0.05, s * 0.11, floor + 0.06], 0.055)
        sh = [neck[0], s * 0.20, neck[2] - 0.05]
        hand = [h[0] + 0.48, s * 0.20, h[2] + 0.20]
        m.cyl(f"pilot-arm{s}", "occupant", sh, hand, 0.045)
    m.cbox("console", "seat", [h[0] + 0.62, 0, h[2] + 0.12], [0.16, 0.70, 0.22])
    return [head[0] + 0.07, 0.0, head[2]]


def manipulator(m, side, shoulder, upper, fore, r, root=None):
    s = side
    if root:
        m.cyl(f"arm-root{s}", "structure", root, shoulder, r * 1.1)
    m.sph(f"arm-shoulder{s}", "actuator", shoulder, r * 1.7)
    elbow = add(shoulder, [upper * math.cos(math.radians(40)), 0, -upper * math.sin(math.radians(40))])
    wrist = add(elbow, [fore * math.cos(math.radians(8)), 0, fore * math.sin(math.radians(8))])
    m.cyl(f"arm-upper{s}", "arm", shoulder, elbow, r)
    hydraulic(m, f"arm-cyl-a{s}", add(shoulder, [0.05, 0, 0.18]), add(lerp(shoulder, elbow, 0.75), [0, 0, 0.12]), 0.045)
    m.sph(f"arm-elbow{s}", "actuator", elbow, r * 1.35)
    m.cyl(f"arm-fore{s}", "arm", elbow, wrist, r * 0.85)
    m.sph(f"arm-wrist{s}", "actuator", wrist, r * 1.1)
    for k, dy in enumerate((0.07, -0.07)):
        m.cbox(f"arm-finger{s}{k}", "arm", add(wrist, [0.20, dy, 0]), [0.32, 0.04, 0.09])


def uav(m, common, base, tag="uav"):
    """SUS-A1 quadrotor standing on its skids at base (x, y, z of the skid bottom). Returns rotor parts' names."""
    c = common["uav"]
    bx, by, bz = c["body"]
    z = base[2] + c["skid_height"]
    m.cbox(f"{tag}-body", "uav", [base[0], base[1], z + bz / 2], c["body"])
    m.sph(f"{tag}-camera", "uav", [base[0] + bx / 2, base[1], z + 0.02], 0.045)
    for k, (dx, dy) in enumerate(((1, 1), (1, -1), (-1, 1), (-1, -1))):
        reach = c["arm_reach"] / math.sqrt(2)
        hub = [base[0] + dx * reach, base[1] + dy * reach, z + bz * 0.7]
        m.cyl(f"{tag}-arm{k}", "uav", [base[0], base[1], z + bz * 0.7], hub, 0.014)
        m.cyl(f"{tag}-motor{k}", "uav", hub, add(hub, [0, 0, 0.05]), 0.028)
        m.cyl(f"{tag}-rotor{k}", "rotor", add(hub, [0, 0, 0.055]), add(hub, [0, 0, 0.065]), c["rotor_radius"])
    for dy in (bx * 0.35, -bx * 0.35):
        m.cyl(f"{tag}-skid{dy:+.2f}", "uav", [base[0] - 0.14, base[1] + dy, base[2] + 0.01], [base[0] + 0.14, base[1] + dy, base[2] + 0.01], 0.01)
        for dx in (-0.08, 0.08):
            m.cyl(f"{tag}-strut{dx:+.2f}{dy:+.2f}", "uav", [base[0] + dx, base[1] + dy, base[2]], [base[0] + dx * 0.6, base[1] + dy * 0.6, z], 0.008)


def reference_human(m, at, height):
    """Standing 1.75 m figure for scale."""
    k = height / 1.75
    g, m.group = m.group, "reference"
    x, y = at
    for s in (1, -1):
        m.cyl(f"ref-leg{s}", "reference", [x, y + s * 0.1 * k, 0], [x, y + s * 0.1 * k, 0.86 * k], 0.07 * k)
        m.cyl(f"ref-arm{s}", "reference", [x, y + s * 0.24 * k, 1.42 * k], [x, y + s * 0.27 * k, 0.80 * k], 0.045 * k)
    m.cyl("ref-torso", "reference", [x, y, 0.84 * k], [x, y, 1.48 * k], 0.17 * k)
    m.sph("ref-head", "reference", [x, y, 1.63 * k], 0.11 * k)
    m.group = g


def safety_items(m, beacon_at, estops):
    m.cyl("saf-beacon-base", "safety", beacon_at, add(beacon_at, [0, 0, 0.05]), 0.09)
    m.cyl("saf-beacon", "safety", add(beacon_at, [0, 0, 0.05]), add(beacon_at, [0, 0, 0.17]), 0.06)
    for k, (p, n) in enumerate(estops):
        m.cyl(f"saf-estop{k}", "safety", p, add(p, [x * 0.06 for x in n]), 0.045)


# --- Concept builders -----------------------------------------------------------------------------

def build_biped(p, common):
    m = Model()
    L = p["leg"]
    kf = L["knee_forward"]
    knee_z = L["ankle_height"] + math.sqrt(L["shank"] ** 2 - kf ** 2)
    hip_z = knee_z + math.sqrt(L["thigh"] ** 2 - kf ** 2)
    fl, fw, ft = L["foot"]
    for s in (1, -1):
        y = s * L["hip_half_width"]
        hip, knee, ankle = [0, y, hip_z], [kf, y, knee_z], [0, y, L["ankle_height"]]
        m.cyl(f"thigh{s}", "structure", hip, knee, L["radius"])
        m.cyl(f"shank{s}", "structure", knee, ankle, L["radius"] * 0.9)
        for nm, pt, r in (("hip", hip, L["joint_radius"]), ("knee", knee, L["joint_radius"] * 0.85), ("ankle", ankle, L["joint_radius"] * 0.7)):
            m.sph(f"{nm}{s}", "actuator", pt, r)
        hydraulic(m, f"thigh-cyl{s}", [-0.30, y + s * 0.20, hip_z + 0.30], add(lerp(hip, knee, 0.65), [-0.14, s * 0.20, 0]))
        hydraulic(m, f"shank-cyl{s}", add(lerp(hip, knee, 0.55), [0.17, 0, 0]), add(lerp(knee, ankle, 0.6), [0.16, 0, 0]))
        x0 = -0.32 * fl
        m.box(f"foot{s}", "structure", [x0, y - fw / 2, 0], [fl, fw, ft])
        m.cyl(f"ankle-link{s}", "structure", ankle, [0, y, ft], L["radius"] * 0.8)
        m.feet += [(x0, y - fw / 2), (x0 + fl, y - fw / 2), (x0, y + fw / 2), (x0 + fl, y + fw / 2)]
    T = p["torso"]
    cd, cw, ch = T["core"]
    tz0 = hip_z - T["bottom_offset"]
    cx1 = 0.25
    cx0 = cx1 - cd
    m.box("torso-core", "structure", [cx0, -cw / 2, tz0], [cd, cw, ch])
    m.cyl("hip-housing", "structure", [0, -L["hip_half_width"] - 0.15, hip_z], [0, L["hip_half_width"] + 0.15, hip_z], 0.24)
    C = p["cockpit"]
    fx, fy, fz = C["frame"]
    floor = tz0 + C["floor_offset"]
    cage(m, cx1, -fy / 2, floor, fx, fy, fz, C["tube_radius"])
    eye = pilot(m, floor, cx1 + 0.02)
    A = p["arm"]
    for s in (1, -1):
        sh = [0.05, s * A["shoulder_y"], tz0 + ch - A["shoulder_drop"]]
        manipulator(m, s, sh, A["upper"], A["fore"], A["radius"], root=[0.05, s * cw / 2, sh[2]])
    P = p["power"]["pack"]
    m.box("power-pack", "power", [cx0 - P[0], -P[1] / 2, tz0 + 0.15], P)
    m.cbox("saf-controller", "safety", [cx0 + 0.35, cw / 2 + 0.08, tz0 + 0.55], [0.30, 0.16, 0.28])
    safety_items(m, [cx0 + 0.25, 0, tz0 + ch], [([cx1 + fx - 0.2, fy / 2 + 0.04, floor + 0.9], [0, 1, 0]),
                                               ([cx0 - P[0], 0.3, tz0 + 0.6], [-1, 0, 0])])
    walker_dock(m, common, p["dock"], top=tz0 + ch, rear_x=cx0)
    return m, {"hip_z": hip_z, "floor": floor, "eye": eye, "dock": "offboard" if p["dock"]["type"] == "ground-station" else "onboard"}


def walker_dock(m, common, D, top, rear_x):
    """TS-004 alternatives. On-board docks are a platform on struts above the hull top, placed by `center`
    (x from the rear edge of the core, y, height above the top); the ground station stands beside the walker."""
    if D["type"] in ("rear-backpack", "shoulder"):
        px, py, pz = D["platform"]
        c = [rear_x + D["center"][0], D["center"][1], top + D["center"][2]]
        m.cbox("dock-platform", "dock", add(c, [0, 0, pz / 2]), [px, py, pz])
        s = min(px, py) / 2 - 0.08
        for k, (dx, dy) in enumerate(((s, s), (s, -s), (-s, s), (-s, -s))):
            m.cyl(f"dock-strut{k}", "dock", [c[0] + dx, c[1] + dy, top], [c[0] + dx, c[1] + dy, c[2]], 0.03)
        for k, dy in enumerate((0.16, -0.16)):
            m.cbox(f"dock-latch{k}", "dock", [c[0], c[1] + dy, c[2] + pz + 0.03], [0.10, 0.05, 0.06])
        m.group = "uav"
        uav(m, common, [c[0], c[1], c[2] + pz])
    elif D["type"] == "ground-station":
        sx_, sy_, sz_ = D["station"]
        x, y = D["position"]
        m.group = "offboard"
        m.cbox("station-box", "dock", [x, y, sz_ / 2], [sx_, sy_, sz_])
        for k, dy in enumerate((0.16, -0.16)):
            m.cbox(f"station-latch{k}", "dock", [x, y + dy, sz_ + 0.03], [0.10, 0.05, 0.06])
        m.cyl("station-handle", "dock", [x - sx_ / 2 - 0.05, y - 0.3, sz_ * 0.7], [x - sx_ / 2 - 0.05, y + 0.3, sz_ * 0.7], 0.025)
        uav(m, common, [x, y, sz_])
    else:
        raise ValueError(f"unknown dock type {D['type']!r}")
    m.group = "walker"


def build_pod(p, common):
    """Armoured-pod biped (CL-04, CL-05): enclosed hull, faceted front opening, shoulder plates, roll bar.
    Options: reverse-jointed legs (knee_forward < 0 with ankle_forward), claw hands, side windows."""
    m = Model()
    L = p["leg"]
    kf = L["knee_forward"]          # negative: the knee sits behind the hip (reverse-jointed, digitigrade)
    ax = L.get("ankle_forward", 0.0)  # ankle ahead of the hip, raised on a long ankle link
    knee_z = L["ankle_height"] + math.sqrt(L["shank"] ** 2 - (ax - kf) ** 2)
    hip_z = knee_z + math.sqrt(L["thigh"] ** 2 - kf ** 2)
    fl, fw, ft = L["foot"]
    aw, ad = L["armour"]
    for s in (1, -1):
        y = s * L["hip_half_width"]
        hip, knee, ankle = [0, y, hip_z], [kf, y, knee_z], [ax, y, L["ankle_height"]]
        m.cyl(f"thigh{s}", "structure", hip, knee, L["radius"])
        m.cyl(f"shank{s}", "structure", knee, ankle, L["radius"] * 0.9)
        m.sph(f"hip{s}", "actuator", hip, L["joint_radius"])
        m.sph(f"knee{s}", "actuator", knee, L["joint_radius"] * 0.9)
        m.sph(f"ankle{s}", "actuator", ankle, L["joint_radius"] * 0.75)
        # Armour plates on the outside of thigh and shin, a knee cap in front
        m.obox(f"thigh-plate{s}", "armor", lerp(hip, knee, 0.12), lerp(hip, knee, 0.88), aw, ad * 0.55, (0.10, s * 0.06, 0), 0.03)
        m.obox(f"shin-plate{s}", "armor", lerp(knee, ankle, 0.10), lerp(knee, ankle, 0.85), aw, ad * 0.6, (0.14, 0, 0), 0.03)
        cap_x = kf + 0.12 if kf >= 0 else kf - 0.28  # cap on the outside of the bend
        m.rbox(f"knee-cap{s}", "armor", [cap_x, y - 0.19, knee_z - 0.18], [0.16, 0.38, 0.36], 0.05)
        hydraulic(m, f"thigh-cyl{s}", [-0.28, y + s * 0.22, hip_z + 0.22], add(lerp(hip, knee, 0.65), [-0.16, s * 0.22, 0]))
        hydraulic(m, f"shank-cyl{s}", add(lerp(hip, knee, 0.5), [-0.20, s * 0.20, 0]), add(lerp(knee, ankle, 0.6), [-0.18, s * 0.20, 0]))
        x0 = ax - 0.35 * fl
        m.rbox(f"foot{s}", "structure", [x0, y - fw / 2, 0], [fl, fw, ft], 0.05)
        m.rbox(f"toe-plate{s}", "armor", [x0 + fl * 0.55, y - fw / 2 - 0.02, ft - 0.02], [fl * 0.45, fw + 0.04, 0.10], 0.03)
        m.rbox(f"heel-guard{s}", "armor", [x0 - 0.02, y - fw / 2 + 0.05, ft - 0.02], [0.25, fw - 0.10, 0.22], 0.04)
        m.cyl(f"ankle-link{s}", "structure", ankle, [ax, y, ft], L["radius"] * 0.85)
        m.feet += [(x0, y - fw / 2), (x0 + fl, y - fw / 2), (x0, y + fw / 2), (x0 + fl, y + fw / 2)]
        # Hydraulic hose loop from the hull to the knee
        h0 = [-0.25, y + s * 0.30, hip_z - 0.05]
        h1 = [-0.42, y + s * 0.34, hip_z - 0.45]
        h2 = [-0.30, y + s * 0.32, knee_z + 0.10]
        h3 = [-0.12, y + s * 0.26, knee_z - 0.05]
        for k, (a, b) in enumerate(((h0, h1), (h1, h2), (h2, h3))):
            m.cyl(f"hose{s}{k}", "hose", a, b, 0.035)
            m.sph(f"hose-bend{s}{k}", "hose", b, 0.035)

    P = p["pod"]
    dx, wy, hz = P["size"]
    x1 = P["x_front"]
    x0 = x1 - dx
    z0 = hip_z - P["bottom_offset"]
    z1 = z0 + hz
    outer = Part.makeBox(dx * MM, wy * MM, hz * MM, V(x0, -wy / 2, z0))
    outer = outer.makeFillet(P["edge_radius"] * MM, outer.Edges)
    w = P["wall"]
    inner = Part.makeBox((dx - 2 * w) * MM, (wy - 2 * w) * MM, (hz - 2 * w) * MM, V(x0 + w, -wy / 2 + w, z0 + w))
    floor = z0 + P["floor_offset"]
    ow, oh, osill = P["opening"]
    zb = floor + 0.5 + osill
    c = 0.18  # chamfered corners give the arched, faceted opening
    pts = [(-ow / 2, zb), (ow / 2, zb), (ow / 2, zb + oh - c), (ow / 2 - c, zb + oh), (-ow / 2 + c, zb + oh), (-ow / 2, zb + oh - c)]
    wire = Part.makePolygon([V(x1 - 0.5, y_, z_) for y_, z_ in pts] + [V(x1 - 0.5, pts[0][0], pts[0][1])])
    window = Part.Face(wire).extrude(V(1.0, 0, 0))
    hull = outer.cut(inner).cut(window)
    if P.get("side_window"):  # a window through both sides, centred on the pilot's head
        swx, swz = P["side_window"]
        cx = x1 - P["seat_back_from_front"] + 0.25
        hull = hull.cut(Part.makeBox(swx * MM, (wy + 0.4) * MM, swz * MM, V(cx - swx / 2, -wy / 2 - 0.2, floor + 0.80)))
    m.add("pod-hull", "armor", hull)
    m.box("cockpit-floor", "seat", [x0 + w, -wy / 2 + w, floor - 0.04], [dx - 2 * w, wy - 2 * w, 0.04])
    eye = pilot(m, floor, x1 - P["seat_back_from_front"])
    # Chest plate below the opening, standing proud of the hull like the reference's front plate
    m.rbox("chest-plate", "armor", [x1 - 0.04, -0.42, zb - 0.55], [0.16, 0.84, 0.50], 0.04)
    m.sph("chest-boss", "actuator", [x1 + 0.13, 0, zb - 0.30], 0.08)
    m.cyl("hip-housing", "structure", [0, -L["hip_half_width"] - 0.12, hip_z], [0, L["hip_half_width"] + 0.12, hip_z], 0.25)

    S = p["shoulder"]
    sx, sy, sz = S["plate"]
    A = p["arm"]
    ang = math.radians(A["drop_angle_deg"])
    for s in (1, -1):
        yc = s * (wy / 2 + sy / 2 - 0.08)
        m.rbox(f"shoulder-plate{s}", "armor", [x1 - sx - 0.05, yc - sy / 2, z1 - S["drop"] - sz], [sx, sy, sz], 0.10)
        sh = [x1 - sx / 2 - 0.05, s * (wy / 2 + 0.18), z1 - S["drop"] - sz - 0.05]
        m.sph(f"arm-shoulder{s}", "actuator", sh, A["radius"] * 1.8)
        elbow = add(sh, [A["upper"] * math.cos(ang), 0, -A["upper"] * math.sin(ang)])
        fa = math.radians(A.get("fore_angle_deg", 12))  # forearm angle above horizontal (negative: hanging)
        wrist = add(elbow, [A["fore"] * math.cos(fa), 0, A["fore"] * math.sin(fa)])
        m.cyl(f"arm-upper{s}", "arm", sh, elbow, A["radius"])
        m.obox(f"arm-upper-plate{s}", "armor", lerp(sh, elbow, 0.15), lerp(sh, elbow, 0.85), 0.30, 0.20, (0, s * 0.07, 0), 0.03)
        m.sph(f"arm-elbow{s}", "actuator", elbow, A["radius"] * 1.35)
        m.cyl(f"arm-fore{s}", "arm", elbow, wrist, A["radius"] * 0.9)
        m.obox(f"arm-fore-plate{s}", "armor", lerp(elbow, wrist, 0.15), lerp(elbow, wrist, 0.80), 0.28, 0.26, (0, 0, 0.03), 0.03)
        m.rbox(f"hand{s}", "arm", [wrist[0] - 0.05, wrist[1] - 0.12, wrist[2] - 0.11], [0.22, 0.24, 0.22], 0.03)
        for k, dy in enumerate((-0.08, 0.0, 0.08)):
            if A.get("claw"):  # long curved claw: four segments bending down and back
                pts = [add(wrist, [0.10, dy, -0.04])]
                for step in ([0.16, 0, -0.22], [0.06, 0, -0.30], [-0.06, 0, -0.26], [-0.14, 0, -0.12]):
                    pts.append(add(pts[-1], step))
                for j, (a, b) in enumerate(zip(pts, pts[1:])):
                    m.cyl(f"claw{s}{k}{j}", "arm", a, b, 0.04 - j * 0.006)
                    m.sph(f"claw-joint{s}{k}{j}", "arm", b, 0.04 - j * 0.006)
            else:
                m.obox(f"finger{s}{k}", "arm", [wrist[0] + 0.15, wrist[1] + dy, wrist[2]], [wrist[0] + 0.36, wrist[1] + dy, wrist[2] - 0.10], 0.05, 0.06)
        m.obox(f"thumb{s}", "arm", [wrist[0] + 0.08, wrist[1] - s * 0.13, wrist[2] - 0.05], [wrist[0] + 0.24, wrist[1] - s * 0.16, wrist[2] - 0.14], 0.05, 0.05)

    W = p["power"]
    px, py, pz = W["pack"]
    pk0 = x0 - px + 0.06
    m.rbox("power-pack", "power", [pk0, -py / 2, z0 + 0.35], [px, py, pz], 0.08)
    for k in range(W["vents"]):
        yv = (k - (W["vents"] - 1) / 2) * 0.17
        m.cyl(f"vent{k}", "power", [pk0 + px * 0.55, yv, z0 + 0.35 + pz], [pk0 + px * 0.55, yv, z0 + 0.35 + pz + 0.10], 0.065)

    R = p["rollbar"]
    rt = R["tube_radius"]
    top = z1 + R["rise"]
    for s in (1, -1):
        yb = s * (wy / 2 - 0.22)
        m.cyl(f"rollbar-post{s}", "cage", [x0 + 0.20, yb, z1 - 0.05], [x0 + 0.20, yb, top], rt)
        m.cyl(f"rollbar-fwd{s}", "cage", [x0 + 0.20, yb, top], [x0 + 0.85, yb, top - 0.10], rt)
        m.cyl(f"rollbar-drop{s}", "cage", [x0 + 0.85, yb, top - 0.10], [x0 + 0.95, yb, z1 - 0.02], rt)
        m.sph(f"rollbar-bend{s}", "cage", [x0 + 0.20, yb, top], rt)
        m.sph(f"rollbar-bend2{s}", "cage", [x0 + 0.85, yb, top - 0.10], rt)
    m.cyl("rollbar-cross", "cage", [x0 + 0.20, -(wy / 2 - 0.22), top], [x0 + 0.20, wy / 2 - 0.22, top], rt)
    m.cyl("rollbar-cross2", "cage", [x0 + 0.85, -(wy / 2 - 0.22), top - 0.10], [x0 + 0.85, wy / 2 - 0.22, top - 0.10], rt)

    safety_items(m, [x0 + 0.55, 0, z1 - 0.01], [([x1 - 0.35, wy / 2 + 0.01, z0 + 0.55], [0, 1, 0]),
                                               ([pk0, 0.35, z0 + 0.7], [-1, 0, 0])])
    m.cbox("saf-controller", "safety", [x0 + 0.40, -wy / 2 - 0.07, z0 + 0.45], [0.30, 0.14, 0.26])
    walker_dock(m, common, p["dock"], top=z0 + 0.35 + pz, rear_x=pk0)
    return m, {"hip_z": hip_z, "floor": floor, "eye": eye, "dock": "offboard" if p["dock"]["type"] == "ground-station" else "onboard"}


def build_from_b3d(p, common, posture="standing"):
    """Layouts authored in build123d (tools/cad/b3d/): import the per-class STEP files and info.json written by
    the layout's script into build/cad-src/<ID>/, so metrics, renders and drawings use the same code paths."""
    src = ROOT / "build/cad-src" / (p["id"] if posture == "standing" else f"{p['id']}-{posture}")
    info_path = src / "info.json"
    if not info_path.is_file():
        raise FileNotFoundError(f"{p['id']}: {info_path} is missing; run tools/cad/b3d/{p['id'].lower().replace('-', '')}.py first")
    info = json.loads(info_path.read_text())
    m = Model()
    for step in sorted(src.glob("*.step")):
        cls = step.stem
        if cls not in CLASSES:
            raise ValueError(f"{p['id']}: unknown part class {cls!r} in {step.name}")
        m.group = "uav" if cls in ("uav", "rotor") else "payload" if cls == "payload" else "walker"
        for k, solid in enumerate(Part.read(str(step)).Solids):
            m.add(f"{cls}-{k:03d}", cls, solid)
    m.group = "walker"
    m.feet = [tuple(f) for f in info["feet"]]
    return m, {k: info[k] for k in ("hip_z", "floor", "eye", "dock", "egress", "carry") if k in info}


# --- Metrics --------------------------------------------------------------------------------------

def hull(points):
    pts = sorted(set((round(x, 6), round(y, 6)) for x, y in points))
    if len(pts) < 3:
        return pts

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lower, upper = [], []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def margin(poly, pt):
    """Signed distance from pt to the edges of a counter-clockwise convex polygon (positive inside)."""
    best = float("inf")
    for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]):
        ex, ey = x2 - x1, y2 - y1
        d = ((pt[0] - x1) * ey - (pt[1] - y1) * ex) / math.hypot(ex, ey)
        best = min(best, -d)
    return best


def metrics(m: Model, info: dict, common: dict) -> dict:
    dens = common["effective_density"]
    on = [pt for pt in m.parts if pt["group"] == "walker" or (pt["group"] == "uav")]
    mass = 0.0
    mom = FreeCAD.Vector(0, 0, 0)
    for pt in on:
        rho = dens[DENSITY_CLASS.get(pt["cls"], pt["cls"])]
        for solid in pt["shape"].Solids:  # cut shapes come back as compounds
            kg = solid.Volume / MM ** 3 * rho
            mass += kg
            mom = mom.add(solid.CenterOfMass.multiply(kg))
    cg = mom.multiply(1.0 / mass).multiply(1.0 / MM)
    bb = Part.makeCompound([pt["shape"] for pt in on]).BoundBox
    poly = hull(m.feet)
    marg = margin(poly, (cg.x, cg.y))
    occupant = Part.makeCompound([pt["shape"] for pt in m.parts if pt["cls"] == "occupant"])
    rotors = Part.makeCompound([pt["shape"] for pt in m.parts if pt["cls"] == "rotor"])
    dist, pairs, _ = occupant.distToShape(rotors)
    clearance = dist / MM
    structure = Part.makeCompound([pt["shape"] for pt in m.parts if pt["group"] == "walker" and pt["cls"] not in ("dock",)])
    rotor_structure = rotors.distToShape(structure)[0] / MM if info["dock"] == "onboard" else None
    info["rotor_pilot_points"] = [[round(c / MM, 3) for c in pairs[0][0]], [round(c / MM, 3) for c in pairs[0][1]]]
    return {
        "envelope_m": [round(bb.XLength / MM, 2), round(bb.YLength / MM, 2), round(bb.ZLength / MM, 2)],
        "height_m": round(bb.ZMax / MM, 2),
        "hip_height_m": round(info["hip_z"], 2),
        "cockpit_floor_m": round(info["floor"], 2),
        "pilot_eye_m": round(info["eye"][2], 2),
        "placeholder_mass_kg": int(round(mass, -1)),
        "cg_m": [round(cg.x, 3), round(cg.y, 3), round(cg.z, 3)],
        "support_polygon_m": [[round(x, 3), round(y, 3)] for x, y in poly],
        "static_margin_m": round(marg, 3),
        "static_tip_angle_deg": round(math.degrees(math.atan2(marg, cg.z)), 1),
        "uav_dock": info["dock"],
        "rotor_to_pilot_m": round(clearance, 2),
        "rotor_to_structure_m": None if rotor_structure is None else round(rotor_structure, 2),
        "arm_ground_clearance_m": round(Part.makeCompound([pt["shape"] for pt in m.parts if pt["cls"] == "arm"]).BoundBox.ZMin / MM, 2),
        **({"egress_sill_m": round(info["egress"]["sill"], 2), "max_step_rise_m": round(info["egress"]["max_rise"], 2),
            "steps": len(info["egress"]["treads"])} if info.get("egress") else {}),
        **(emergency_metrics(m, info["egress"]["emergency"]) if (info.get("egress") or {}).get("emergency") else {}),
        **(carry_metrics(info["carry"], mass, cg, poly) if info.get("carry") else {}),
    }


FLAG_MARGIN = 0.30  # provisional review flag for static margin (m), as on the review images


def carry_metrics(c: dict, mass: float, cg, poly) -> dict:
    """Carry pose (SYS-020). The load's mass is TBD, so it is left out of the walker's mass and CG; instead this
    reports the load mass at which the standstill static margin falls to the review flag and to zero (tip-over),
    with the load's centre of mass at the centre of its envelope. Relative to placeholder walker mass only."""
    lc = c["load_center"]

    def marg(kg):
        tot = mass + kg
        return margin(poly, ((cg.x * mass + lc[0] * kg) / tot, (cg.y * mass + lc[1] * kg) / tot))

    def first_below(target):
        kg, step = 0.0, 10.0
        peak = marg(0.0)
        while kg < 50 * mass:
            kg += step
            mk = marg(kg)
            peak = max(peak, mk)
            if mk < target and mk < peak:
                lo, hi = kg - step, kg
                for _ in range(40):
                    mid = (lo + hi) / 2
                    lo, hi = (mid, hi) if marg(mid) >= target else (lo, mid)
                return lo
        return None

    best = max(range(0, int(mass), 10), key=lambda k: marg(float(k)))
    return {
        "carry_load_envelope_m": [round(v, 2) for v in c["load_size"]],
        "carry_load_centre_m": [round(v, 3) for v in c["load_center"]],
        "carry_load_bottom_m": round(c["load_bottom"], 2),
        "carry_arm_angles_deg": [c["arm_drop_deg"], c["fore_angle_deg"]],
        "carry_margin_peak": {"load_kg": int(round(best, -1)), "static_margin_m": round(marg(float(best)), 3)},
        "carry_load_at_margin_flag_kg": None if (k := first_below(FLAG_MARGIN)) is None else int(round(k, -1)),
        "carry_load_at_tipover_kg": None if (k := first_below(0.0)) is None else int(round(k, -1)),
        "ground_seen_ahead_unloaded_m": round(c["ground_seen_unloaded"], 2),
        "ground_seen_ahead_loaded_m": round(c["ground_seen_loaded"], 2),
    }


def emergency_metrics(m: Model, em: dict) -> dict:
    """Emergency hatch sill and clear opening; when the escape ladder is deployed, its clearance to the walker."""
    out = {"emergency_sill_m": round(em["sill"], 2), "emergency_clear_m": [round(v, 2) for v in em["clear"]]}
    if em.get("ledge"):
        out["hatch_step_m"] = round(em["ledge"]["height"], 2)
        out["step_to_ladder_gap_m"] = round(em["ladder_y"] - em["ledge"]["outer_y"], 2)
    ladder = [pt["shape"] for pt in m.parts if pt["cls"] == "escape"]
    if ladder:
        rest = [pt["shape"] for pt in m.parts if pt["group"] == "walker" and pt["cls"] not in ("escape", "access")]
        out["escape_clearance_m"] = round(Part.makeCompound(ladder).distToShape(Part.makeCompound(rest))[0] / MM, 2)
    return out


# --- Export ---------------------------------------------------------------------------------------

def export(m: Model, cid: str, out: Path, met: dict, info: dict, title: str) -> None:
    out.mkdir(parents=True, exist_ok=True)
    doc = FreeCAD.newDocument(cid.replace("-", "_"))
    for pt in m.parts:
        if pt["group"] == "reference":
            continue
        obj = doc.addObject("Part::Feature", pt["name"].replace("-", "_").replace("+", "p").replace(".", "_"))
        obj.Shape = pt["shape"]
        obj.Label = f"{pt['cls']}:{pt['name']}"
    doc.recompute()
    doc.saveAs(str(out / f"{cid}.FCStd"))
    FreeCAD.closeDocument(doc.Name)
    Part.makeCompound([pt["shape"] for pt in m.parts if pt["group"] != "reference"]).exportStep(str(out / f"{cid}.step"))
    meshes = []
    for cls in sorted({pt["cls"] for pt in m.parts}):
        shape = Part.makeCompound([pt["shape"] for pt in m.parts if pt["cls"] == cls])
        mesh = MeshPart.meshFromShape(Shape=shape, LinearDeflection=4.0, AngularDeflection=0.25)
        mesh.write(str(out / f"{cls}.stl"))
        color, opacity, comp = CLASSES[cls]
        meshes.append({"file": f"{cls}.stl", "cls": cls, "color": color, "opacity": opacity, "component": comp})
    (out / "manifest.json").write_text(json.dumps({"id": cid, "title": title, "meshes": meshes, "metrics": met,
                                                   "rotor_pilot_points": info["rotor_pilot_points"],
                                                   "eye": [round(c, 3) for c in info["eye"]]}, indent=1))


BUILDERS = {"open-frame": build_biped, "armored-pod": build_pod, "build123d": build_from_b3d}  # all bipedal: TS-003 decided (project lead, 2026-11-11)


def build_layout(p: dict, common: dict, posture: str = "standing") -> tuple[Model, dict]:
    """Build one layout (in one of its postures) with the 1.75 m reference person placed beside it."""
    if p["locomotion"] != "biped":
        raise ValueError(f"{p['id']}: TS-003 is decided as bipedal; locomotion {p['locomotion']!r} is not built")
    if posture != "standing":
        if p.get("style") != "build123d":
            raise ValueError(f"{p['id']}: postures are only built for build123d layouts")
        m, info = build_from_b3d(p, common, posture)
    else:
        m, info = BUILDERS[p.get("style", "open-frame")](p, common)
    bb = Part.makeCompound([pt["shape"] for pt in m.parts if pt["group"] != "reference"]).BoundBox
    reference_human(m, (bb.XMin / MM - 0.55, bb.YMin / MM - 0.9), common["reference_human"]["height"])
    return m, info


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=ROOT / "build/cad")
    ap.add_argument("ids", nargs="*")
    args = ap.parse_args()
    common = yaml.safe_load((PARAMS / "common.yaml").read_text())
    summary = {}
    for path in sorted(PARAMS.glob("CL-*.yaml")):
        p = yaml.safe_load(path.read_text())
        if args.ids and p["id"] not in args.ids:
            continue
        m, info = build_layout(p, common)
        met = metrics(m, info, common)
        export(m, p["id"], args.out / p["id"], met, info, p["title"])
        summary[p["id"]] = {"title": p["title"], "locomotion": p["locomotion"], "dock": p["dock"]["type"], **met}
        for posture, pose in (p.get("postures") or {}).items():
            pm, pinfo = build_layout(p, common, posture)
            pmet = metrics(pm, pinfo, common)
            export(pm, f"{p['id']}-{posture}", args.out / f"{p['id']}-{posture}", pmet, pinfo, f"{p['title']} — {pose.get('label', posture)}")
            summary[p["id"]].setdefault("postures", {})[posture] = pmet
            print(f"{p['id']} {posture}: cockpit floor {pmet['cockpit_floor_m']} m, CG z {pmet['cg_m'][2]} m, "
                  f"static margin {pmet['static_margin_m']} m, arm clearance {pmet['arm_ground_clearance_m']} m")
        print(f"{p['id']}: {len(m.parts)} parts, height {met['height_m']} m, CG z {met['cg_m'][2]} m, "
              f"static margin {met['static_margin_m']} m, rotor-to-pilot {met['rotor_to_pilot_m']} m")
    if not args.ids:
        (ROOT / "cad/metrics.json").write_text(json.dumps(
            {"generator": "tools/cad/build_concepts.py", "freecad": ".".join(FreeCAD.Version()[:3]),
             "note": "Properties of placeholder concept geometry, not of a design.", "concepts": summary}, indent=1) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
