# SPDX-License-Identifier: Apache-2.0
"""Pose the CL-05 walk cycle on the terrains of sim/scenes3d/terrain.yaml for sheet 3 (docs/3d/SUS-M1-terrain.html).

    /opt/b3d/bin/python tools/cad/b3d/cl05_terrain.py [--frames 12]            # docs/3d/assets/sus-m1-terrain.js
    /opt/b3d/bin/python tools/cad/b3d/cl05_terrain.py --loaded                 # docs/3d/assets/sus-m1-terrain-loaded.js

Each terrain is periodic over one walk cycle, so one cycle posed on it loops. Every frame is the build123d model of
tools/cad/b3d/cl05.py posed by the gait of cad/params/CL-05.yaml walk: (the same foot timing as the flat walk), with
each foot placed on the ground under it:

- a planted foot stands on the ground at its footprint; a swinging foot travels between its two footprints on an arc
  that clears the ground between them by the walk's lift;
- the hip keeps the walk's crouch and bob above the mean height of the ground under the two feet, and is lowered only
  when a leg cannot otherwise reach its foot (thigh + shank, 0.5 % short of straight); the knees are solved by the
  CAD's own fold_knee, as in the flat walk;
- the pod stays level and the arms stay stowed (SYS-017): the layout has no body-pitch or balance model;
- with --loaded: the loaded gait of walk: loaded: (shorter, lower steps) with the arms holding the placeholder load
  in the carry pose of postures: carry, the load riding with the hip (SYS-019, load mass TBD). A terrain whose period
  does not repeat with the loaded stride (the 1.0 m ledges) is listed as not posed.

For each terrain the export records the largest hip drop, the lowest clearance of anything but the legs and feet above
the ground (pod, arms, power pack, hoses), and any frame the leg geometry cannot solve. Matching re-uses the standing
meshes of docs/3d/assets/sus-m1.js (tools/cad/b3d/cl05_web.py): each solid is an affine or rigid transform of its
standing mesh or, where its shape changes, its own mesh. Writes docs/3d/assets/sus-m1-terrain.js with the clips, the
ground height map of each terrain (one period) and the kinematic findings. Concept kinematics only: no dynamics,
balance, foot slip or ground model.
"""
from __future__ import annotations

import argparse
import base64
import json
import math
import re
import sys
from pathlib import Path

import numpy as np
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cl05  # noqa: E402
from cl05_web import FIT_MM, Packer, Rigid, fit, moments, standing_hip, tessellate  # noqa: E402,F401

ROOT = cl05.ROOT
OUT = ROOT / "docs/3d/assets/sus-m1-terrain.js"
OUT_LOADED = ROOT / "docs/3d/assets/sus-m1-terrain-loaded.js"
GEOM = ROOT / "docs/3d/assets/sus-m1.js"
REACH = 0.995  # a leg is used up to 99.5 % of thigh + shank


def load_base() -> tuple[list, list]:
    """The standing meshes of sus-m1.js, dequantised exactly as the page does, with their mesh ids."""
    text = GEOM.read_text()
    meta = json.loads(re.search(r"meta: (\{.*?\}),\nbin:", text, re.S).group(1))
    raw = base64.b64decode(re.search(r'bin: "([^"]+)"', text).group(1))
    po, pl = meta["layout"]["positions"]
    io, il = meta["layout"]["indices"]
    P = np.frombuffer(raw[po:po + pl], dtype="<i2").reshape(-1, 3).astype(float)
    I = np.frombuffer(raw[io:io + il], dtype="<u2")
    q, o = meta["quantum_m"], np.array(meta["origin_m"])
    base = []
    for mid in meta["base"]:
        m = meta["meshes"][mid]
        (vo, vn), (ix, inn) = m["v"], m["i"]
        base.append((m["cls"], P[vo:vo + vn] * q + o, I[ix:ix + inn].astype(np.int64).reshape(-1, 3)))
    return base, meta["base"]


class Ground:
    """Height of a terrain of terrain.yaml at world (x, y), x along the walk; periodic over `period` with `rise`."""

    def __init__(self, t: dict, period: float):
        self.t, self.period = t, period
        k = t["kind"]
        if k == "plane":
            self.gx, self.gy = math.tan(math.radians(t.get("pitch_deg", 0))), math.tan(math.radians(t.get("roll_deg", 0)))
        elif k not in ("ledges", "rubble"):
            raise ValueError(f"unknown terrain kind {k}")
        if k == "ledges" and abs(period / t["run_m"] - round(period / t["run_m"])) > 1e-9:
            raise ValueError("ledge run must divide the stride, or the cycle does not repeat")

    def __call__(self, x: float, y: float) -> float:
        t = self.t
        if t["kind"] == "plane":
            return x * self.gx - y * self.gy   # roll > 0: right side (y < 0) down
        if t["kind"] == "ledges":
            return math.floor(x / t["run_m"] + 1e-9) * t["rise_m"]
        a, P = t["amp_m"], self.period       # rubble: two bump trains across the track, out of phase
        return a * math.sin(2 * math.pi * x / P + 1.7 * math.tanh(2 * y)) * (0.75 + 0.25 * math.cos(2.4 * y))

    def rise(self) -> float:
        return self(self.period, 0.0) - self(0.0, 0.0)


def gait(p: dict, W: dict, phase: float) -> dict:
    """Per side: (ankle forward of the hip, swing fraction or None when planted, world x of the lift-off and touch-down
    footprints relative to the body at phase 0). Same timing as cl05.walk_frames."""
    S, duty = W["stride"], W["duty"]
    ax = p["leg"].get("ankle_forward", 0.0)
    out = {}
    for s, offset in ((1, 0.0), (-1, 0.5)):
        f = (phase + offset) % 1.0
        if f < duty:
            out[s] = (ax + S * (duty / 2 - f), None)
        else:
            g = (f - duty) / (1 - duty)
            out[s] = (ax + S * duty * (g - 0.5), g)
    return out


def pose(p: dict, W: dict, G: Ground, phase: float, hip0: float) -> dict:
    """Leg targets, hip height and ground reference for one frame on terrain G."""
    S, h = W["stride"], W["lift"]
    L = p["leg"]
    R = (L["thigh"] + L["shank"]) * REACH
    xb = S * phase                               # body (hip) x in the world
    legs, zf, zg = {}, {}, {}
    for s, (rel, g) in gait(p, W, phase).items():
        y = s * L["hip_half_width"]
        xf = xb + rel
        ground = G(xf, y)
        if g is None:
            zf[s] = ground
        else:                                    # swing: from the lift-off footprint to the touch-down footprint
            x_off = xf - S * g                   # the foot travels one stride from lift-off to touch-down
            x_on = x_off + S
            g_off, g_on = G(x_off, y), G(x_on, y)
            ahead = min(1.0, g + 0.35)           # clear what lies just ahead of the foot (a ledge's riser) in time
            path = max(G(x_off + S * k / 40 * ahead, y) for k in range(41))
            base = max(g_off + (g_on - g_off) * g, path)
            zf[s] = base + h * math.sin(math.pi * g)
        zg[s] = ground
        legs[s] = rel
    gref = (zg[1] + zg[-1]) / 2
    hip_nom = hip0 - W["crouch"] - W["bob"] * math.cos(4 * math.pi * phase)
    hip_z = hip_nom
    for s, rel in legs.items():                  # lower the hip only as far as a leg needs to reach its foot
        az = L["ankle_height"] + zf[s] - gref
        if abs(rel) < R:
            hip_z = min(hip_z, az + math.sqrt(R * R - rel * rel))
    return {"xb": xb, "gref": gref, "hip_z": hip_z, "drop": hip_nom - hip_z,
            "legs": {s: (legs[s], zf[s] - gref) for s in legs}}


def clearance(sol: list, G: Ground, xb: float, gref: float) -> float:
    """Lowest height above the ground of any vertex of the pod, arms, power pack and other non-leg parts."""
    low = math.inf
    for cls, v, _ in sol:
        if cls in ("structure", "actuator"):    # legs, joints and feet: they stand on the ground by construction
            continue
        for x, y, z in v[:: max(1, len(v) // 400)]:
            low = min(low, z + gref - G(xb + x, y))
    return low


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--frames", type=int, default=12, help="frames per walk cycle (the page interpolates between them)")
    ap.add_argument("--tolerance", type=float, default=0.004, help="tessellation tolerance, metres (the one sus-m1.js was made with)")
    ap.add_argument("--only", nargs="*", help="terrain keys to export (default all)")
    ap.add_argument("--loaded", action="store_true", help="the loaded walk (walk: loaded:, arms in the carry pose holding the placeholder load)")
    ap.add_argument("--out", type=Path, default=None)
    a = ap.parse_args()
    p = yaml.safe_load((ROOT / "cad/params/CL-05.yaml").read_text())
    common = yaml.safe_load((ROOT / "cad/params/common.yaml").read_text())
    course = yaml.safe_load((ROOT / "sim/scenes3d/terrain.yaml").read_text())
    W = dict(p["walk"])
    if a.loaded:   # shorter, lower steps; the load rides with the hip as in cl05.walk_frames(loaded=True) (SYS-019)
        W.update(W.get("loaded") or {})
    out_path = a.out or (OUT_LOADED if a.loaded else OUT)
    S, hip0 = W["stride"], standing_hip(p)
    base, base_ids = load_base()
    rigid = Rigid(base)
    pk = Packer()
    mats: list[np.ndarray] = []
    out = []
    for t in course["terrains"]:
        if a.only and t["key"] not in a.only:
            continue
        try:
            G = Ground(t, S)
        except ValueError as e:                  # e.g. ledges whose run does not repeat with this stride
            out.append({"key": t["key"], "skipped": f"not posed: {e} (stride {S} m)"})
            print(f"{t['key']}: skipped ({e})", flush=True)
            continue
        frames, worst_drop, low, unsolved = [], 0.0, math.inf, []
        for i in range(a.frames):
            phase = i / a.frames
            ps = pose(p, W, G, phase, hip0)
            try:
                arms = W["arms"]
                if a.loaded:                     # carry pose, the hand target moving with the hip
                    carry = dict(p["postures"]["carry"]["carry"])
                    carry["hand_height"] += ps["hip_z"] - hip0
                    arms = {"carry": carry}
                parts, _ = cl05.build(p, common, "standing", gait={"hip_z": ps["hip_z"], "legs": ps["legs"], "arms": arms})
            except ValueError as e:              # the leg geometry cannot reach: record it, hold the previous frame
                unsolved.append({"phase": round(phase, 3), "why": str(e)})
                frames.append(frames[-1] if frames else None)
                continue
            sol = tessellate(parts, a.tolerance)
            low = min(low, clearance(sol, G, ps["xb"], ps["gref"]))
            worst_drop = max(worst_drop, ps["drop"])
            used, mp, extras = set(), [], []
            for cls, v, tr in sol:
                hit = None
                for j, (bcls, bv, bt) in enumerate(base):
                    if j in used or bcls != cls or bv.shape != v.shape or bt.shape != tr.shape:
                        continue
                    M = fit(bv, v)
                    if M is not None:
                        hit = (j, M)
                        break
                if hit is None:
                    fm, tf = moments(v, tr), rigid.tree(v)
                    for j, (bcls, bv, bt) in enumerate(base):
                        if j not in used and bcls == cls:
                            M = rigid.match(j, bv, v, fm, tf, a.tolerance)
                            if M is not None:
                                hit = (j, M)
                                break
                if hit:
                    used.add(hit[0]); mats.append(hit[1]); mp.append([base_ids[hit[0]], len(mats) - 1])
                else:
                    extras.append(pk.mesh(cls, v, tr))
            frames.append({"xb": round(ps["xb"], 4), "gref": round(ps["gref"], 4), "map": mp, "extras": extras})
            print(f"{t['key']}: frame {i + 1}/{a.frames} ({len(extras)} own meshes)", flush=True)
        if frames and frames[0] is None:
            frames = [f for f in frames if f is not None] or []
        frames = [f if f is not None else frames[0] for f in frames]
        nx = int(round(S / course["sample_m"]))
        ny = int(round(course["width_m"] / course["sample_m"])) + 1
        ys = [-course["width_m"] / 2 + k * course["sample_m"] for k in range(ny)]
        hmap = [[round(G(k * course["sample_m"], y), 4) for y in ys] for k in range(nx)]
        out.append({"key": t["key"], "rise": round(G.rise(), 4), "frames": frames, "hmap": hmap,
                    "findings": {"max_hip_drop_m": round(worst_drop, 3), "min_body_clearance_m": round(low, 3) if low < math.inf else None,
                                 "unsolved_frames": unsolved}})
    pos = np.concatenate(pk.pos).tobytes() if pk.pos else b""
    idx = np.concatenate(pk.idx).tobytes() if pk.idx else b""
    pad = (-(len(pos) + len(idx))) % 4
    idx += b"\0" * pad
    mat = np.array(mats, dtype="<f4").reshape(-1).tobytes()
    meta = {
        "about": ("CL-05 " + ("loaded walk (arms in the carry pose holding the placeholder load, mass TBD)" if a.loaded else "walk")
                  + " posed on the terrains of sim/scenes3d/terrain.yaml (tools/cad/b3d/cl05_terrain.py): concept kinematics only, "
                  "no dynamics, balance, foot slip or ground model; the pod stays level"
                  + ("." if a.loaded else " and the arms stowed.")),
        "generator": "tools/cad/b3d/cl05_terrain.py", "mode": "loaded" if a.loaded else "unloaded", "stride_m": S,
        "lift_m": W["lift"], "frames_per_cycle": a.frames,
        "sample_m": course["sample_m"], "width_m": course["width_m"], "quantum_m": 0.0003, "origin_m": [0.0, 0.0, 2.3],
        "layout": {"positions": [0, len(pos)], "indices": [len(pos), len(idx)], "matrices": [len(pos) + len(idx), len(mat)]},
        "meshes": pk.meshes, "terrains": out,
    }
    blob = pos + idx + mat
    out_path.parent.mkdir(parents=True, exist_ok=True)
    var = "SUS_M1_TERRAIN_LOADED" if a.loaded else "SUS_M1_TERRAIN"
    out_path.write_text("// GENERATED by tools/cad/b3d/cl05_terrain.py from cad/params/CL-05.yaml and sim/scenes3d/terrain.yaml; do not edit.\n"
                     f"window.{var} = {{meta: {json.dumps(meta, separators=(',', ':'))},\nbin: \"{base64.b64encode(blob).decode()}\"}};\n")
    print(f"wrote {out_path} ({len(blob) / 1e6:.2f} MB, {len(pk.meshes)} own meshes, {len(mats)} transforms)")
    for t in out:
        if "skipped" in t:
            print(f"  {t['key']:8s} {t['skipped']}")
            continue
        f = t["findings"]
        print(f"  {t['key']:8s} rise {t['rise']:+.3f} m/cycle · hip drop {f['max_hip_drop_m']:.3f} m · body clearance "
              f"{f['min_body_clearance_m']} m · unsolved {len(f['unsolved_frames'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
