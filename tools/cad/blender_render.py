# SPDX-License-Identifier: Apache-2.0
"""Photoreal Blender (Cycles) renders of the concept layouts, from the meshes the FreeCAD pipeline exports.

    /opt/bpy/bin/python tools/cad/blender_render.py [--samples 96] [--shots CL-05:hero ...]

Reads build/cad/<ID>/manifest.json and its per-class STL files (run tools/cad/build_concepts.py first) and
writes cad/renders/blender/<ID>-<shot>.jpg. Geometry is exactly what the metrics and drawings use; only
materials, light and camera are added here. Concept renders for communication: placeholder geometry,
not a design. Needs the `bpy` module (Blender as a Python module, `pip install bpy==5.3.0`).
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import bpy  # noqa: I001  (bpy must load first: it provides bmesh and mathutils)
import bmesh
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
EXPOSURE = -3.6  # the physical sky and sun are scene-referred; this brings them to a normal daylight exposure
BUILD = ROOT / "build/cad"
OUT = ROOT / "cad/renders/blender"

# Physically plausible finishes per part class: (base colour, metallic, roughness, extra)
FINISH = {
    "armor":     ((0.20, 0.22, 0.24), 0.10, 0.45, {"coat": 0.25}),     # painted armour plate
    "structure": ((0.06, 0.065, 0.07), 0.70, 0.48, {}),                # gunmetal frame and legs
    "actuator":  ((0.55, 0.38, 0.08), 0.60, 0.35, {}),                # brass-yellow hydraulics
    "arm":       ((0.12, 0.13, 0.14), 0.70, 0.45, {}),
    "cage":      ((0.85, 0.30, 0.05), 0.10, 0.40, {"coat": 0.4}),     # safety-orange roll bar
    "seat":      ((0.05, 0.05, 0.06), 0.00, 0.70, {}),
    "occupant":  ((0.10, 0.22, 0.50), 0.00, 0.80, {}),                # pilot coverall
    "power":     ((0.13, 0.30, 0.20), 0.20, 0.45, {"coat": 0.2}),
    "safety":    ((0.80, 0.05, 0.04), 0.10, 0.35, {"emit": 0.6}),     # beacon and e-stops
    "dock":      ((0.35, 0.36, 0.38), 0.85, 0.35, {}),                # anodised aluminium
    "uav":       ((0.05, 0.25, 0.45), 0.10, 0.35, {}),
    "rotor":     ((0.60, 0.70, 0.80), 0.00, 0.20, {"alpha": 0.25}),   # spinning-disc impression
    "hose":      ((0.02, 0.02, 0.02), 0.00, 0.85, {}),                # rubber
    "access":    ((0.75, 0.52, 0.01), 0.10, 0.45, {}),                # safety-yellow steps and rails
    "escape":    ((0.85, 0.20, 0.03), 0.00, 0.75, {}),                # webbing ladder
    "reference": ((0.35, 0.36, 0.38), 0.00, 0.60, {}),                # 1.75 m scale figure
}

# Military livery: the same unarmed machine in a subdued military paint scheme (olive drab and coyote tan).
# Access and safety items keep a muted but visible colour: they are safety markings, not decoration.
LIVERIES = {
    "industrial": {},
    "military": {
        "armor":  ((0.16, 0.18, 0.10), 0.05, 0.62, {}),   # olive drab, matte
        "arm":    ((0.36, 0.30, 0.20), 0.10, 0.60, {}),   # coyote tan
        "cage":   ((0.30, 0.26, 0.17), 0.10, 0.55, {}),   # tan roll bar
        "power":  ((0.14, 0.15, 0.09), 0.05, 0.65, {}),
        "dock":   ((0.20, 0.21, 0.16), 0.40, 0.55, {}),
        "access": ((0.55, 0.45, 0.10), 0.10, 0.55, {}),   # subdued yellow: still a safety marking
        "escape": ((0.55, 0.22, 0.06), 0.00, 0.75, {}),
        "uav":    ((0.18, 0.20, 0.14), 0.10, 0.50, {}),
        "occupant": ((0.24, 0.27, 0.17), 0.00, 0.85, {}),
        "actuator": ((0.22, 0.19, 0.12), 0.55, 0.45, {}),  # dark bronze hydraulics
    },
}

# Shots: layout folder, camera position relative to the walker's footprint centre, look-at height fraction, lens
SHOTS = {
    "hero":      {"src": "CL-05",           "cam": (7.2, -5.0, 1.70), "look": 0.48, "lens": 35},
    "rear":      {"src": "CL-05",           "cam": (-7.0, -7.5, 2.8), "look": 0.45, "lens": 35},
    "kneel":     {"src": "CL-05-kneel",     "cam": (6.4, -4.2, 1.60), "look": 0.45, "lens": 35},
    "emergency": {"src": "CL-05-emergency", "cam": (2.2, -8.0, 2.4),  "look": 0.50, "lens": 35},
}


def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    return scene


def material(name, color, metallic, roughness, extra):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    if "coat" in extra and "Coat Weight" in bsdf.inputs:
        bsdf.inputs["Coat Weight"].default_value = extra["coat"]
    if "emit" in extra:
        bsdf.inputs["Emission Color"].default_value = (*color, 1.0)
        bsdf.inputs["Emission Strength"].default_value = extra["emit"]
    if "alpha" in extra:
        bsdf.inputs["Alpha"].default_value = extra["alpha"]
    return mat


def concrete():
    mat = bpy.data.materials.new("concrete")
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 400.0
    noise.inputs["Detail"].default_value = 8.0
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (0.30, 0.30, 0.29, 1)
    ramp.color_ramp.elements[1].color = (0.46, 0.45, 0.43, 1)
    nt.links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.85
    return mat


def import_mesh(path: Path, mat):
    before = set(bpy.data.objects)
    bpy.ops.wm.stl_import(filepath=str(path), global_scale=0.001)
    obj = next(o for o in bpy.data.objects if o not in before)
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0004)  # STL triangles share no vertices
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.materials.append(mat)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    try:
        bpy.ops.object.shade_auto_smooth(angle=math.radians(35))
    except Exception:  # noqa: BLE001  (older or newer API: flat shading is still correct geometry)
        pass
    obj.select_set(False)
    return obj


def world_and_lights(scene):
    world = bpy.data.worlds.new("sky")
    scene.world = world
    world.use_nodes = True
    nt = world.node_tree
    bg = nt.nodes.get("Background")
    sky = nt.nodes.new("ShaderNodeTexSky")
    for kind in ("MULTIPLE_SCATTERING", "NISHITA", "HOSEK_WILKIE"):
        try:
            sky.sky_type = kind
            break
        except TypeError:
            continue
    if hasattr(sky, "sun_elevation"):
        sky.sun_elevation = math.radians(32)
        sky.sun_rotation = math.radians(215)
    nt.links.new(sky.outputs["Color"], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = 0.35
    sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN"))
    sun.data.energy = 4.0
    sun.data.angle = math.radians(2.0)
    sun.rotation_euler = (math.radians(55), 0, math.radians(215))
    scene.collection.objects.link(sun)
    fill = bpy.data.objects.new("fill", bpy.data.lights.new("fill", "AREA"))
    fill.data.energy = 900
    fill.data.size = 6
    fill.location = (6, 6, 5)
    fill.rotation_euler = (math.radians(55), 0, math.radians(135))
    scene.collection.objects.link(fill)


def ground(scene):
    bpy.ops.mesh.primitive_plane_add(size=1500, location=(0, 0, 0))
    plane = bpy.context.active_object
    plane.data.materials.append(concrete())
    return plane


def camera(scene, pos, target, lens):
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    cam.data.lens = lens
    cam.location = pos
    scene.collection.objects.link(cam)
    direction = Vector(target) - Vector(pos)
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    scene.camera = cam


def render(shot: str, spec: dict, samples: int, size=(1600, 1000), livery: str = "industrial") -> Path:
    src = BUILD / spec["src"]
    man = json.loads((src / "manifest.json").read_text())
    scene = reset_scene()
    for m in man["meshes"]:
        f = LIVERIES[livery].get(m["cls"]) or FINISH.get(m["cls"], ((0.5, 0.5, 0.5), 0.0, 0.5, {}))
        import_mesh(src / m["file"], material(m["cls"], *f))
    world_and_lights(scene)
    ground(scene)
    poly = man["metrics"]["support_polygon_m"]
    cx = sum(p[0] for p in poly) / len(poly)
    cy = sum(p[1] for p in poly) / len(poly)
    h = man["metrics"]["height_m"]
    cpos = (cx + spec["cam"][0], cy + spec["cam"][1], spec["cam"][2])
    camera(scene, cpos, (cx, cy, h * spec["look"]), spec["lens"])
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = samples
    scene.cycles.use_denoising = True
    scene.render.resolution_x, scene.render.resolution_y = size
    scene.render.resolution_percentage = 100
    scene.view_settings.view_transform = "AgX" if "AgX" in [v.identifier for v in type(scene.view_settings).bl_rna.properties["view_transform"].enum_items] else "Filmic"
    scene.view_settings.exposure = EXPOSURE
    scene.render.image_settings.file_format = "JPEG"
    scene.render.image_settings.quality = 90
    OUT.mkdir(parents=True, exist_ok=True)
    suffix = "" if livery == "industrial" else f"-{livery}"
    out = OUT / f"{man['id'].split('-')[0]}-{man['id'].split('-')[1]}-{shot}{suffix}.jpg"
    scene.render.filepath = str(out)
    bpy.ops.render.render(write_still=True)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--samples", type=int, default=96)
    ap.add_argument("--shots", nargs="*", default=list(SHOTS))
    ap.add_argument("--livery", choices=list(LIVERIES), default="industrial")
    args = ap.parse_args()
    for shot in args.shots:
        out = render(shot, SHOTS[shot], args.samples, livery=args.livery)
        print(f"wrote {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
