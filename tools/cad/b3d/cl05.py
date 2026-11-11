# SPDX-License-Identifier: Apache-2.0
"""CL-05 reference layout, authored in build123d (the layout the project lead chose to develop, 2026-11-11).

    /opt/b3d/bin/python tools/cad/b3d/cl05.py [--out build/cad-src/CL-05]

Reads cad/params/CL-05.yaml (the same parameters as the FreeCAD primitive layout, plus a `detail` block) and
writes one STEP file per part class (structure, actuator, armor, arm, cage, seat, occupant, power, safety, dock,
uav, rotor, hose) and info.json (hip height, cockpit floor, eye point, ground contacts, dock type). The FreeCAD
pipeline (tools/cad/build_concepts.py, style "build123d") imports these for metrics, renders and drawing
sheets, so the analysis tools do not depend on how the geometry was authored.

Units: modelled in metres, exported in millimetres. Concept geometry for review and alignment, not a design.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import yaml
from build123d import (Box, Circle, Compound, Plane, Pos, Rectangle, Rot, Solid, Sphere,
                       Spline, Vector, export_step, extrude, fillet, loft, make_face, Polyline, sweep, FilletPolyline)

ROOT = Path(__file__).resolve().parents[3]
CLASSES = ["structure", "actuator", "armor", "arm", "cage", "seat", "occupant", "power", "safety", "dock", "uav",
           "rotor", "hose"]


# --- Helpers (metres) -----------------------------------------------------------------------------

def v(*a):
    return Vector(*a)


def plane_along(p1, p2):
    """Plane at p1 whose z axis points to p2 and whose x axis stays in the plane of the segment and world Y."""
    z = (v(*p2) - v(*p1)).normalized()
    ref = v(0, 1, 0) if abs(z.Y) < 0.95 else v(1, 0, 0)
    x = ref.cross(z).normalized()
    return Plane(origin=v(*p1), x_dir=x, z_dir=z)


def cyl(p1, p2, r):
    d = v(*p2) - v(*p1)
    return Solid.make_cylinder(r, d.length, plane_along(p1, p2))


def ycyl(c, r, width):
    """Cylinder along world Y centred at c: joint axles, wheels of the dock latch, bolts."""
    return Solid.make_cylinder(r, width, Plane(origin=v(c[0], c[1] - width / 2, c[2]), x_dir=v(1, 0, 0), z_dir=v(0, 1, 0)))


def soft(part, r):
    """Fillet every edge if the kernel allows it; otherwise return the part unchanged (concept geometry)."""
    try:
        return fillet(part.edges(), r)
    except Exception:  # noqa: BLE001
        return part


def limb(p1, p2, d1, w1, d2, w2, r=0.025):
    """Tapered limb: a loft between rectangles (depth d in the segment's plane, width w along Y)."""
    a, b = plane_along(p1, p2), plane_along(p2, p1)
    b = Plane(origin=b.origin, x_dir=a.x_dir, z_dir=a.z_dir)
    part = loft([a * Rectangle(d1, w1), b * Rectangle(d2, w2)])
    return soft(part, r)


def tube(points, r, bend=None):
    """Circular tube swept along a polyline (with filleted corners) or a spline through the points."""
    path = FilletPolyline(*[v(*p) for p in points], radius=bend) if bend else Spline(*[v(*p) for p in points])
    return sweep(Plane(origin=path @ 0, z_dir=path % 0) * Circle(r), path=path)


def hydraulic(p1, p2, r=0.055):
    """Cylinder barrel, rod and clevis eyes at both ends."""
    mid = v(*p1) + (v(*p2) - v(*p1)) * 0.58
    parts = [cyl(p1, tuple(mid), r), cyl(tuple(mid), p2, r * 0.42)]
    for p in (p1, p2):
        parts.append(ycyl(p, r * 0.75, r * 2.2))
    return parts


def add(a, b):
    return tuple(x + y for x, y in zip(a, b))


def lerp(a, b, t):
    return tuple(x + (y - x) * t for x, y in zip(a, b))


# --- Model ----------------------------------------------------------------------------------------

def build(p: dict, common: dict):
    parts: dict[str, list] = {c: [] for c in CLASSES}
    put = lambda cls, *shapes: parts[cls].extend(shapes)  # noqa: E731
    D = p.get("detail", {})

    # Legs: reverse-jointed (knee behind the hip), raised ankle, two-toe foot with a heel spur
    L = p["leg"]
    kf, ax = L["knee_forward"], L.get("ankle_forward", 0.0)
    knee_z = L["ankle_height"] + math.sqrt(L["shank"] ** 2 - (ax - kf) ** 2)
    hip_z = knee_z + math.sqrt(L["thigh"] ** 2 - kf ** 2)
    fl, fw, ft = L["foot"]
    feet = []
    for s in (1, -1):
        y = s * L["hip_half_width"]
        hip, knee, ankle = (0, y, hip_z), (kf, y, knee_z), (ax, y, L["ankle_height"])
        put("structure", limb(hip, knee, 0.30, 0.26, 0.22, 0.22), limb(knee, ankle, 0.22, 0.22, 0.16, 0.18))
        put("actuator", ycyl(hip, 0.20, 0.40), ycyl(knee, 0.16, 0.34), ycyl(ankle, 0.12, 0.28))
        for c, r_, w in ((hip, 0.11, 0.46), (knee, 0.09, 0.40), (ankle, 0.07, 0.32)):
            put("structure", ycyl(c, r_, w))  # axle caps
        # Armour: thigh plate on the outside, shin guard on the front of the forward-sloping shin
        put("armor", limb(lerp(hip, knee, 0.15), lerp(hip, knee, 0.85), 0.34, 0.06, 0.28, 0.06, 0.02).moved(
            Pos(0, s * 0.16, 0)))
        shin_dir = (v(*ankle) - v(*knee)).normalized()
        normal = shin_dir.cross(v(0, 1, 0)).normalized() * -1
        off = tuple(normal * 0.12)
        put("armor", limb(add(lerp(knee, ankle, 0.12), off), add(lerp(knee, ankle, 0.82), off), 0.05, 0.26, 0.05, 0.22, 0.015))
        put("armor", soft(Pos(kf - 0.20, y, knee_z) * Box(0.16, 0.32, 0.34), 0.05))  # knee guard behind the joint
        put("actuator", *hydraulic((-0.05, y + s * 0.20, hip_z + 0.28), add(lerp(hip, knee, 0.75), (0, s * 0.20, 0))))
        put("actuator", *hydraulic(add(lerp(hip, knee, 0.45), (0.10, s * 0.19, 0)), add(lerp(knee, ankle, 0.7), (0.06, s * 0.19, 0)), 0.048))
        # Foot: two toes forward, a heel spur behind, a pad under the ankle link
        x0 = ax - 0.35 * fl
        pad = soft(Pos(ax, y, ft / 2) * Box(0.34, fw * 0.8, ft), 0.04)
        toes = [soft(Pos(ax + fl * 0.32, y + dy, ft * 0.4) * Box(fl * 0.42, fw * 0.36, ft * 0.8), 0.04) for dy in (-fw * 0.24, fw * 0.24)]
        spur = soft(Pos(ax - fl * 0.28, y, ft * 0.35) * Box(fl * 0.28, fw * 0.32, ft * 0.7), 0.03)
        put("structure", pad, *toes, spur, cyl(ankle, (ax, y, ft), 0.09))
        for solid in (pad, *toes, spur):  # ground contacts from the real foot solids, not a nominal rectangle
            bb = solid.bounding_box()
            feet += [(bb.min.X, bb.min.Y), (bb.max.X, bb.min.Y), (bb.min.X, bb.max.Y), (bb.max.X, bb.max.Y)]
        # Hose from the hull down the back of the thigh to the knee actuator
        put("hose", tube([(-0.30, y + s * 0.30, hip_z + 0.10), (-0.48, y + s * 0.34, hip_z - 0.35),
                          (kf - 0.15, y + s * 0.30, knee_z + 0.25), (kf + 0.02, y + s * 0.24, knee_z + 0.05)], 0.032))

    # Pod: shell with a chamfered chin, faceted front window with a raised frame, side windows, panel grooves
    P = p["pod"]
    dx, wy, hz = P["size"]
    x1 = P["x_front"]
    x0 = x1 - dx
    z0 = hip_z - P["bottom_offset"]
    z1 = z0 + hz
    w = P["wall"]
    floor = z0 + P["floor_offset"]
    cx = x0 + dx / 2
    outer = soft(Pos(cx, 0, z0 + hz / 2) * Box(dx, wy, hz), P["edge_radius"])
    inner = Pos(cx, 0, z0 + hz / 2) * Box(dx - 2 * w, wy - 2 * w, hz - 2 * w)
    ch = D.get("chin_chamfer", 0.25)  # sloped lower front, like the reference's chin
    chin = Pos(x1, 0, z0) * Rot(0, 45, 0) * Box(ch * math.sqrt(2), wy + 0.2, ch * math.sqrt(2))
    ow, oh, osill = P["opening"]
    zb = floor + 0.5 + osill
    c = 0.16
    pts = [(-ow / 2, zb), (ow / 2, zb), (ow / 2, zb + oh - c), (ow / 2 - c, zb + oh), (-ow / 2 + c, zb + oh), (-ow / 2, zb + oh - c)]
    yz = Plane(origin=(x1 - 0.5, 0, 0), x_dir=(0, 1, 0), z_dir=(1, 0, 0))
    window = extrude(yz * make_face(Polyline(*pts, close=True)), amount=1.0)
    hull = outer - inner - chin - window
    swx, swz = P["side_window"]
    wx = x1 - P["seat_back_from_front"] + 0.25
    hull = hull - Pos(wx, 0, floor + 0.80 + swz / 2) * Box(swx, wy + 0.4, swz)
    for gz in D.get("groove_heights", []):  # shallow panel grooves around the hull
        ring = Pos(cx, 0, z0 + gz) * Box(dx + 0.1, wy + 0.1, 0.014) - Pos(cx, 0, z0 + gz) * Box(dx - 0.024, wy - 0.024, 0.02)
        hull = hull - ring
    put("armor", hull)
    big = [(x * 1.14, (z - zb) * 1.12 + zb - 0.05) for x, z in pts]
    frame = extrude(Plane(origin=(x1 - 0.01, 0, 0), x_dir=(0, 1, 0), z_dir=(1, 0, 0)) *
                    (make_face(Polyline(*big, close=True)) - make_face(Polyline(*pts, close=True))), amount=0.05)
    put("armor", frame)
    for side in (1, -1):  # side window frames
        put("armor", Pos(wx, side * (wy / 2 + 0.015), floor + 0.80 + swz / 2) * (Box(swx + 0.10, 0.03, swz + 0.10) - Box(swx, 0.05, swz)))
    for bx, bz in ((ow / 2 + 0.05, zb - 0.03), (-ow / 2 - 0.05, zb - 0.03), (ow / 2 - c + 0.04, zb + oh + 0.07), (-ow / 2 + c - 0.04, zb + oh + 0.07)):
        put("structure", cyl((x1 + 0.04, bx, bz), (x1 + 0.07, bx, bz), 0.022))  # bolt heads on the frame
    put("seat", Pos(cx, 0, floor - 0.02) * Box(dx - 2 * w, wy - 2 * w, 0.04))
    put("structure", ycyl((0, 0, hip_z), 0.26, 2 * L["hip_half_width"] + 0.10))  # hip drive housing

    # Seated pilot, seat and console
    h = (x1 - P["seat_back_from_front"] + 0.30, 0, floor + 0.47)
    put("seat", Pos(h[0] + 0.05, 0, floor + 0.38) * soft(Box(0.50, 0.50, 0.08), 0.02),
        Pos(h[0] - 0.22, 0, floor + 0.75) * soft(Box(0.08, 0.50, 0.70), 0.02), cyl((h[0], 0, floor), (h[0], 0, floor + 0.34), 0.05),
        Pos(h[0] + 0.62, 0, h[2] + 0.12) * soft(Box(0.16, 0.70, 0.22), 0.02))
    neck = (h[0] - 0.06, 0, h[2] + 0.58)
    head = (neck[0] + 0.02, 0, neck[2] + 0.16)
    put("occupant", Pos(*h) * Sphere(0.15), cyl(h, neck, 0.16), Pos(*head) * Sphere(0.11))
    for s in (1, -1):
        kn = (h[0] + 0.45, s * 0.11, h[2] + 0.02)
        put("occupant", cyl((h[0], s * 0.11, h[2]), kn, 0.075), cyl(kn, (kn[0] + 0.05, s * 0.11, floor + 0.06), 0.055),
            cyl((neck[0], s * 0.20, neck[2] - 0.05), (h[0] + 0.48, s * 0.20, h[2] + 0.20), 0.045))
    eye = (head[0] + 0.07, 0, head[2])

    # Arms: low shoulders, long hanging forearms, three curved claws per hand
    S, A = p["shoulder"], p["arm"]
    sx, sy, sz = S["plate"]
    ang, fa = math.radians(A["drop_angle_deg"]), math.radians(A.get("fore_angle_deg", 12))
    for s in (1, -1):
        yc = s * (wy / 2 + sy / 2 - 0.08)
        put("armor", soft(Pos(x1 - sx / 2 - 0.05, yc, z1 - S["drop"] - sz / 2) * Box(sx, sy, sz), 0.09))
        sh = (x1 - sx / 2 - 0.05, s * (wy / 2 + 0.18), z1 - S["drop"] - sz - 0.05)
        el = add(sh, (A["upper"] * math.cos(ang), 0, -A["upper"] * math.sin(ang)))
        wr = add(el, (A["fore"] * math.cos(fa), 0, A["fore"] * math.sin(fa)))
        put("actuator", ycyl(sh, 0.17, 0.30), ycyl(el, 0.13, 0.26), ycyl(wr, 0.10, 0.22))
        put("arm", limb(sh, el, 0.22, 0.20, 0.17, 0.17), limb(el, wr, 0.17, 0.17, 0.13, 0.15))
        put("armor", limb(lerp(sh, el, 0.15), lerp(sh, el, 0.85), 0.26, 0.05, 0.22, 0.05, 0.015).moved(Pos(0, s * 0.12, 0)))
        put("actuator", *hydraulic(add(sh, (0.10, 0, 0.16)), add(lerp(sh, el, 0.8), (0.0, 0, 0.12)), 0.042))
        put("arm", soft(Pos(wr[0], wr[1], wr[2] - 0.08) * Box(0.20, 0.26, 0.18), 0.03))
        for k, dy in enumerate((-0.08, 0.0, 0.08)):
            base = (wr[0] + 0.06, wr[1] + dy, wr[2] - 0.16)
            cl = D.get("claw_length", 0.45)  # claw drop below the hand; scales the curve
            pts_ = [base] + [add(base, (dx_ * cl, 0, dz_ * cl)) for dx_, dz_ in ((0.25, -0.30), (0.33, -0.70), (0.15, -0.95), (-0.08, -1.05))]
            put("arm", tube(pts_, 0.034))
            tip_dir = v(*pts_[-1]) - v(*pts_[-2])
            put("arm", Solid.make_cone(0.034, 0.0, 0.10, Plane(origin=v(*pts_[-1]), z_dir=tip_dir)))

    # Roll bar (swept tube with bent corners), power pack with fins and vents, safety items
    R = p["rollbar"]
    top = z1 + R["rise"]
    for s in (1, -1):
        yb = s * (wy / 2 - 0.22)
        put("cage", tube([(x0 + 0.20, yb, z1 - 0.05), (x0 + 0.20, yb, top), (x0 + 0.85, yb, top - 0.10), (x0 + 0.95, yb, z1 - 0.02)], R["tube_radius"], bend=0.10))
    put("cage", cyl((x0 + 0.20, -(wy / 2 - 0.22), top), (x0 + 0.20, wy / 2 - 0.22, top), R["tube_radius"]),
        cyl((x0 + 0.85, -(wy / 2 - 0.22), top - 0.10), (x0 + 0.85, wy / 2 - 0.22, top - 0.10), R["tube_radius"]))
    W = p["power"]
    px, py, pz = W["pack"]
    pk0 = x0 - px + 0.06
    pc = (pk0 + px / 2, 0, z0 + 0.35 + pz / 2)
    put("power", soft(Pos(*pc) * Box(px, py, pz), 0.06))
    for k in range(D.get("fins", 7)):
        zf = z0 + 0.45 + k * (pz - 0.2) / max(1, D.get("fins", 7) - 1)
        put("power", Pos(pk0 - 0.03, 0, zf) * Box(0.06, py * 0.8, 0.025))
    for k in range(W["vents"]):
        yv = (k - (W["vents"] - 1) / 2) * 0.17
        put("power", cyl((pk0 + px * 0.55, yv, z0 + 0.35 + pz), (pk0 + px * 0.55, yv, z0 + 0.35 + pz + 0.10), 0.065))
    put("safety", cyl((x0 + 0.55, 0, z1), (x0 + 0.55, 0, z1 + 0.05), 0.09), cyl((x0 + 0.55, 0, z1 + 0.05), (x0 + 0.55, 0, z1 + 0.17), 0.06),
        cyl((x1 - 0.35, wy / 2, z0 + 0.55), (x1 - 0.35, wy / 2 + 0.06, z0 + 0.55), 0.045),
        cyl((pk0, 0.35, z0 + 0.7), (pk0 - 0.06, 0.35, z0 + 0.7), 0.045),
        Pos(x0 + 0.40, -wy / 2 - 0.07, z0 + 0.45) * Box(0.30, 0.14, 0.26))

    # Rear dock with latches and the SUS-A1 quadrotor on it
    Dk = p["dock"]
    pxd, pyd, pzd = Dk["platform"]
    ptop = z0 + 0.35 + pz
    dc = (pk0 + Dk["center"][0], Dk["center"][1], ptop + Dk["center"][2])
    put("dock", soft(Pos(dc[0], dc[1], dc[2] + pzd / 2) * Box(pxd, pyd, pzd), 0.015))
    sdx = min(pxd, pyd) / 2 - 0.08
    for ddx, ddy in ((sdx, sdx), (sdx, -sdx), (-sdx, sdx), (-sdx, -sdx)):
        put("dock", cyl((dc[0] + ddx, dc[1] + ddy, ptop), (dc[0] + ddx, dc[1] + ddy, dc[2]), 0.03))
    for ddy in (0.16, -0.16):
        put("dock", Pos(dc[0], dc[1] + ddy, dc[2] + pzd + 0.03) * Box(0.10, 0.05, 0.06))
    U = common["uav"]
    bx, by, bz = U["body"]
    base = (dc[0], dc[1], dc[2] + pzd)
    zu = base[2] + U["skid_height"]
    put("uav", soft(Pos(base[0], base[1], zu + bz / 2) * Box(bx, by, bz), 0.02), Pos(base[0] + bx / 2, base[1], zu + 0.02) * Sphere(0.045))
    for ddx, ddy in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
        reach = U["arm_reach"] / math.sqrt(2)
        hub = (base[0] + ddx * reach, base[1] + ddy * reach, zu + bz * 0.7)
        put("uav", cyl((base[0], base[1], zu + bz * 0.7), hub, 0.014), cyl(hub, add(hub, (0, 0, 0.05)), 0.028))
        put("rotor", cyl(add(hub, (0, 0, 0.055)), add(hub, (0, 0, 0.065)), U["rotor_radius"]))
    for ddy in (bx * 0.35, -bx * 0.35):
        put("uav", cyl((base[0] - 0.14, base[1] + ddy, base[2] + 0.01), (base[0] + 0.14, base[1] + ddy, base[2] + 0.01), 0.01))

    info = {"hip_z": hip_z, "floor": floor, "eye": list(eye), "feet": [list(f) for f in feet], "dock": "onboard"}
    return parts, info


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=ROOT / "build/cad-src/CL-05")
    args = ap.parse_args()
    p = yaml.safe_load((ROOT / "cad/params/CL-05.yaml").read_text())
    common = yaml.safe_load((ROOT / "cad/params/common.yaml").read_text())
    parts, info = build(p, common)
    args.out.mkdir(parents=True, exist_ok=True)
    for cls, shapes in parts.items():
        if shapes:
            export_step(Compound(shapes).scale(1000), str(args.out / f"{cls}.step"))
    (args.out / "info.json").write_text(json.dumps(info, indent=1))
    print(f"CL-05 (build123d): {sum(len(s) for s in parts.values())} solids in {sum(1 for s in parts.values() if s)} classes -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
