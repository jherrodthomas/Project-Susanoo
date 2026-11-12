# SPDX-License-Identifier: Apache-2.0
"""Walk animation of the CL-05 reference layout, rendered in Blender (Cycles) from the CAD walk frames.

    /opt/b3d/bin/python tools/cad/b3d/cl05.py --walk 48 [--loaded]   # per-frame meshes (build/cad-src/CL-05-walk[-loaded])
    /opt/bpy/bin/python tools/cad/blender_walk.py [--livery military] [--cycles 2] [--samples 16]

Every frame is the build123d model posed by the gait in cad/params/CL-05.yaml (walk:), with the knees solved
for the reverse-jointed legs, so the legs are exactly the CAD's. The walker advances one stride per cycle
while the camera tracks alongside; a 1.75 m person stands still for scale. Writes
cad/renders/blender/CL-05-walk[-loaded][-<livery>].mp4 (--loaded: carrying the placeholder load in the carry pose). Concept kinematics only: no dynamics, balance or load model.
"""
from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import blender_render as br  # noqa: E402  (loads bpy)
import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

ROOT = br.ROOT
SRC_DIR = ROOT / "build/cad-src"
REF = ROOT / "build/cad/CL-05/reference.stl"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--livery", choices=list(br.LIVERIES), default="military")
    ap.add_argument("--cycles", type=int, default=2)
    ap.add_argument("--samples", type=int, default=16)
    ap.add_argument("--fps", type=int, default=16)
    ap.add_argument("--size", default="1280x720")
    ap.add_argument("--loaded", action="store_true", help="render the loaded walk (cl05.py --walk N --loaded)")
    args = ap.parse_args()
    name = "CL-05-walk-loaded" if args.loaded else "CL-05-walk"
    SRC = SRC_DIR / name
    meta = json.loads((SRC / "walk.json").read_text())
    n, stride = meta["frames"], meta["stride_m"]
    w, h = (int(v) for v in args.size.split("x"))

    scene = br.reset_scene()
    br.world_and_lights(scene)
    br.ground(scene)
    mats = {}
    for cls, f in br.FINISH.items():
        f = br.LIVERIES[args.livery].get(cls) or f
        mats[cls] = br.material(f"{cls}", *f)
    if REF.is_file():  # the scale figure stays where the walk starts
        br.import_mesh(REF, mats["reference"])
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = args.samples
    scene.cycles.use_denoising = True
    scene.render.resolution_x, scene.render.resolution_y = w, h
    scene.view_settings.exposure = br.EXPOSURE
    scene.render.image_settings.file_format = "PNG"
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    cam.data.lens = 32
    scene.collection.objects.link(cam)
    scene.camera = cam

    frames_dir = ROOT / "build/walk-frames"
    shutil.rmtree(frames_dir, ignore_errors=True)
    frames_dir.mkdir(parents=True)
    walker = []
    total = n * args.cycles
    for k in range(total):
        for obj in walker:
            bpy.data.objects.remove(obj, do_unlink=True)
        walker = []
        src = SRC / f"f{k % n:03d}"
        for stl in sorted(src.glob("*.stl")):
            walker.append(br.import_mesh(stl, mats.get(stl.stem, mats["structure"])))
        x = stride * (k // n) + meta["body_x"][k % n]
        for obj in walker:
            obj.location.x = x
        # Camera tracks alongside, slightly ahead, at eye height, looking at the pod
        pos = Vector((x + 1.6, -8.4, 1.9))
        cam.location = pos
        cam.rotation_euler = (Vector((x + 0.1, 0.0, 2.1)) - pos).to_track_quat("-Z", "Y").to_euler()
        scene.render.filepath = str(frames_dir / f"{k:04d}.png")
        bpy.ops.render.render(write_still=True)
        print(f"rendered {k + 1}/{total}", flush=True)

    suffix = "" if args.livery == "industrial" else f"-{args.livery}"
    out = ROOT / f"cad/renders/blender/{name}{suffix}.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(args.fps), "-i", str(frames_dir / "%04d.png"),
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "24", "-preset", "slow", "-movflags", "+faststart",
                    str(out)], check=True)
    print(f"wrote {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
