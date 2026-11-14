"""Mass properties of CL-05 per walker link (torso, and thigh, shank and foot of each leg) -> cad/links.json.

Usage (build123d environment, tools/cad/b3d/environment.yml):
  python tools/cad/b3d/cl05_links.py           write cad/links.json
  python tools/cad/b3d/cl05_links.py --check   fail if cad/links.json is out of date

Builds CL-05 standing with tools/cad/b3d/cl05.py and puts every solid on a link: a solid of a leg class (structure,
actuator, armour, hose) below the hips belongs to the nearer leg; below 0.6 x the ankle height it is that leg's
foot, otherwise its thigh or shank as it lies above or below the knee along the hip-ankle line (parts centred on
the knee go to the thigh). Everything else is the
torso. Each solid is weighed as tools/cad/build_concepts.py weighs it (volume x the effective density of its class,
payload left out), so the link masses add up to cad/metrics.json placeholder_mass_kg. Inertia is about each link's
centre of mass, in the layout frame (x forward, y left, z up), in the standing posture.

Properties of placeholder concept geometry, not of a design. Read by sim/spec/walker_l2.yaml (the level-2 masses
and inertias) and checked against it by sim/tests/test_sim.py.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import yaml
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
import cl05  # noqa: E402

OUT = ROOT / "cad" / "links.json"
# As tools/cad/build_concepts.py (sim/tests/test_sim.py checks the two agree).
DENSITY_CLASS = {"arm": "structure", "seat": "structure", "rotor": "uav", "hose": "structure", "access": "structure",
                 "escape": "structure"}
LEG_CLASSES = ("structure", "actuator", "armor", "hose")
SIDES = (("left", 1.0), ("right", -1.0))


def seg_fraction(p, a, b):
    """Position of p's projection along a->b (0 at a, 1 at b)."""
    d = [b[i] - a[i] for i in range(3)]
    return sum((p[i] - a[i]) * d[i] for i in range(3)) / sum(c * c for c in d)


def props(solid):
    g = GProp_GProps()
    BRepGProp.VolumeProperties_s(solid.wrapped, g)
    c, m = g.CentreOfMass(), g.MatrixOfInertia()      # inertia about the centre of mass, for unit density
    return g.Mass(), (c.X(), c.Y(), c.Z()), [[m.Value(i, j) for j in (1, 2, 3)] for i in (1, 2, 3)]


def link_of(cls, c, legs, hip_z, ankle_h):
    if cls in LEG_CLASSES and c[2] < hip_z + 0.15:
        for side, leg in legs.items():
            if abs(c[1] - leg["hip"][1]) < 0.45:
                if c[2] < ankle_h * 0.6:
                    return f"foot_{side}"
                # above or below the knee along the hip-ankle line, however far the knee is bent; parts centred on the
                # knee (its drive and joint block) go to the thigh, so rounding cannot put them on either side
                above_knee = (math.dist(c, leg["knee"]) < 0.02 or
                              seg_fraction(c, leg["hip"], leg["ankle"]) < seg_fraction(leg["knee"], leg["hip"], leg["ankle"]))
                return f"{'thigh' if above_knee else 'shank'}_{side}"
    return "torso"


def build() -> dict:
    p = yaml.safe_load((ROOT / "cad/params/CL-05.yaml").read_text())
    common = yaml.safe_load((ROOT / "cad/params/common.yaml").read_text())
    parts, info = cl05.build(p, common, "standing")
    L = p["leg"]
    hip_z, (kx, kz) = info["hip_z"], info["knee"]
    legs = {side: {"hip": [0.0, s * L["hip_half_width"], hip_z], "knee": [kx, s * L["hip_half_width"], kz],
                   "ankle": [L.get("ankle_forward", 0.0), s * L["hip_half_width"], L["ankle_height"]]}
            for side, s in SIDES}
    dens = common["effective_density"]
    acc = {}
    for cls, shapes in parts.items():
        if cls == "payload":
            continue
        rho = dens[DENSITY_CLASS.get(cls, cls)]
        for shape in shapes:
            for solid in shape.solids():
                vol, c, inertia = props(solid)
                acc.setdefault(link_of(cls, c, legs, hip_z, L["ankle_height"]), []).append((vol * rho, c, inertia, rho))
    links = {}
    for name, items in sorted(acc.items()):
        mass = sum(m for m, *_ in items)
        com = [sum(m * c[i] for m, c, *_ in items) / mass for i in range(3)]
        tensor = [[0.0] * 3 for _ in range(3)]
        for m, c, inertia, rho in items:          # parallel-axis shift of each solid to the link's centre of mass
            r = [c[i] - com[i] for i in range(3)]
            r2 = sum(x * x for x in r)
            for i in range(3):
                for j in range(3):
                    tensor[i][j] += rho * inertia[i][j] + m * ((r2 if i == j else 0.0) - r[i] * r[j])
        entry = {"mass_kg": round(mass, 1), "com_m": [round(x, 3) for x in com],
                 "inertia_kgm2": [[round(x) for x in row] for row in tensor], "solids": len(items)}
        side = name.split("_")[-1]
        if name.startswith(("thigh", "shank")):
            a, b = (legs[side]["hip"], legs[side]["knee"]) if name.startswith("thigh") else (legs[side]["knee"], legs[side]["ankle"])
            entry["along_segment"] = round(seg_fraction(com, a, b), 3)
        links[name] = entry
    total = sum(v["mass_kg"] for v in links.values())
    com = [sum(v["mass_kg"] * v["com_m"][i] for v in links.values()) / total for i in range(3)]
    return {"generator": "tools/cad/b3d/cl05_links.py", "layout": "CL-05", "posture": "standing",
            "note": "Properties of placeholder concept geometry, not of a design. Inertia about each link's centre of mass, "
                    "layout frame (x forward, y left, z up); along_segment: the centre of mass projected on hip-knee "
                    "(thigh) or knee-ankle (shank), 0 at the upper joint.",
            "joints_m": {side: {k: [round(x, 3) for x in v] for k, v in leg.items()} for side, leg in legs.items()},
            "total": {"mass_kg": round(total, 1), "com_m": [round(x, 3) for x in com]}, "links": links}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    text = json.dumps(build(), indent=1) + "\n"
    if a.check:
        if not OUT.is_file() or OUT.read_text() != text:
            print(f"{OUT.relative_to(ROOT)} is out of date: run tools/cad/b3d/cl05_links.py")
            return 1
        print(f"{OUT.relative_to(ROOT)} is current")
        return 0
    OUT.write_text(text)
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
