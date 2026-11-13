# SPDX-License-Identifier: Apache-2.0
"""Export the CL-05 reference layout for the interactive general-arrangement sheet (docs/3d/SUS-M1.html).

    /opt/b3d/bin/python tools/cad/b3d/cl05_web.py [--tolerance 0.004]

Builds the build123d model of tools/cad/b3d/cl05.py in the standing pose and along four clips, all posed by the
same code and parameters (cad/params/CL-05.yaml) as the review renders and the Blender walk:

  kneel   standing -> kneeling for egress (hip lowered with the feet planted, arms stowed, ladder deployed last)
  carry   standing -> carrying the placeholder load (arm angles eased to the solved carry pose, load appears last)
  egress  standing -> emergency exit (hatch open, escape ladder deployed)
  walk    standing -> walking stance, then one walk cycle (the gait of walk:, arms stowed per SYS-017)

The in-between frames of kneel and carry ease the posture parameters (hip height, arm angles) between the two
poses the layout defines; they are concept kinematics for viewing, not analysed poses. Every solid of the
standing pose is tessellated once; for each frame each solid is either an affine transform of its standing mesh
(fitted, residual under half a millimetre) or, where the shape itself changes (a hose, a stretching limb), its own
mesh for that frame. Writes docs/3d/assets/sus-m1.js: the mesh table, clips and info, and one base64 buffer of
int16 positions, uint16 indices and float32 3x4 transforms. No dynamics, balance or load model.
"""
from __future__ import annotations

import argparse
import base64
import copy
import json
import math
import sys
from pathlib import Path

import numpy as np
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cl05  # noqa: E402

ROOT = cl05.ROOT
OUT = ROOT / "docs/3d/assets"
STEP = 0.0003            # position quantum, metres (int16 covers +/- 9.8 m about ORIGIN)
ORIGIN = (0.0, 0.0, 2.3)
FIT_MM = 0.5             # largest residual of an affine fit, millimetres


def tessellate(parts: dict, tol: float) -> list[tuple[str, np.ndarray, np.ndarray]]:
    out = []
    for cls in cl05.CLASSES:
        for shape in parts.get(cls, []):
            for s in shape.solids():
                vs, tr = s.tessellate(tol * (2.5 if cls == "hose" else 1.0), 0.4)  # tubes: coarser
                out.append((cls, np.array([(v.X, v.Y, v.Z) for v in vs], dtype=float), np.array(tr, dtype=np.int64)))
    return out


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def ease(t: float) -> float:
    return 0.5 - 0.5 * math.cos(math.pi * t)


def standing_hip(p: dict) -> float:
    L = p["leg"]
    ax, kf = L.get("ankle_forward", 0.0), L["knee_forward"]
    knee_z = L["ankle_height"] + math.sqrt(L["shank"] ** 2 - (ax - kf) ** 2)
    return knee_z + math.sqrt(L["thigh"] ** 2 - kf ** 2)


def gait_legs(p: dict, W: dict, phase: float) -> dict:
    """Ankle (forward offset, lift) per side at a walk phase: the same gait as cl05.walk_frames."""
    S, duty, h = W["stride"], W["duty"], W["lift"]
    ax = p["leg"].get("ankle_forward", 0.0)
    legs = {}
    for s, offset in ((1, 0.0), (-1, 0.5)):
        f = (phase + offset) % 1.0
        if f < duty:
            legs[s] = (ax + S * (duty / 2 - f), 0.0)
        else:
            g = (f - duty) / (1 - duty)
            legs[s] = (ax + S * duty * (g - 0.5), h * math.sin(math.pi * g))
    return legs


def clips(p: dict, common: dict, n_tween: int, n_walk: int) -> dict[str, list]:
    """Clip name -> list of (label, parts, body_x) frames. Frame 0 of every clip is the standing pose."""
    A = p["arm"]
    stand_arm = (A["drop_angle_deg"], A.get("fore_angle_deg", 12))
    hip0 = standing_hip(p)
    out: dict[str, list] = {}

    def tween(pose: dict):
        q = copy.deepcopy(p)
        q["postures"]["_tween"] = pose
        return cl05.build(q, common, "_tween")[0]

    kn = p["postures"]["kneel"]
    frames = []
    for i in range(1, n_tween):
        t = ease(i / n_tween)
        frames.append((f"kneel {i}/{n_tween}", tween({"hip_height": lerp(hip0, kn["hip_height"], t),
                                                      "arm_drop_deg": lerp(stand_arm[0], kn["arm_drop_deg"], t),
                                                      "fore_angle_deg": lerp(stand_arm[1], kn["fore_angle_deg"], t)}), 0.0))
    frames.append(("kneel", cl05.build(p, common, "kneel")[0], 0.0))
    out["kneel"] = frames

    carry_parts, carry_info = cl05.build(p, common, "carry")
    ca = carry_info["carry"]
    frames = []
    for i in range(1, n_tween):
        t = ease(i / n_tween)
        frames.append((f"carry {i}/{n_tween}", tween({"arm_drop_deg": lerp(stand_arm[0], ca["arm_drop_deg"], t),
                                                      "fore_angle_deg": lerp(stand_arm[1], ca["fore_angle_deg"], t)}), 0.0))
    frames.append(("carry", carry_parts, 0.0))
    out["carry"] = frames

    out["egress"] = [("emergency exit", cl05.build(p, common, "emergency")[0], 0.0)]

    W = p["walk"]
    first = gait_legs(p, W, 0.0)
    hip_w0 = hip0 - W["crouch"] - W["bob"]
    ax = p["leg"].get("ankle_forward", 0.0)
    frames = []
    n_in = max(n_tween // 2, 2)
    for i in range(1, n_in + 1):  # into the walking stance: crouch, stow the arms, move the feet to phase 0
        t = ease(i / n_in)
        legs = {s: (lerp(ax, first[s][0], t), lerp(0.0, first[s][1], t)) for s in (1, -1)}
        arms = {k: lerp(stand_arm[j], W["arms"][k], t) for j, k in enumerate(("arm_drop_deg", "fore_angle_deg"))}
        frames.append((f"stow {i}/{n_in}", cl05.build(p, common, "standing", gait={"hip_z": lerp(hip0, hip_w0, t), "legs": legs,
                                                                                  "arms": arms})[0], 0.0))
    for i in range(n_walk):
        phase = i / n_walk
        hip_z = hip0 - W["crouch"] - W["bob"] * math.cos(4 * math.pi * phase)
        frames.append((f"walk {i}/{n_walk}", cl05.build(p, common, "standing", gait={"hip_z": hip_z, "legs": gait_legs(p, W, phase),
                                                                                    "arms": W["arms"]})[0], W["stride"] * phase))
    out["walk"] = frames
    return out


class Packer:
    def __init__(self):
        self.pos: list[np.ndarray] = []
        self.idx: list[np.ndarray] = []
        self.npos = self.nidx = 0
        self.meshes: list[dict] = []

    def mesh(self, cls: str, verts: np.ndarray, tris: np.ndarray) -> int:
        if len(verts) >= 65536:
            raise ValueError(f"{cls} solid has {len(verts)} vertices: over the uint16 index range")
        q = np.round((verts - np.array(ORIGIN)) / STEP)
        if np.abs(q).max() > 32767:
            raise ValueError(f"{cls} solid outside the quantised range")
        self.pos.append(q.astype("<i2"))
        self.idx.append(tris.reshape(-1).astype("<u2"))
        self.meshes.append({"cls": cls, "v": [self.npos, len(verts)], "i": [self.nidx, tris.size]})
        self.npos += len(verts)
        self.nidx += tris.size
        return len(self.meshes) - 1


def fit(base: np.ndarray, frame: np.ndarray) -> np.ndarray | None:
    """Affine 3x4 matrix taking the base vertices to the frame vertices (same tessellation, vertex for vertex),
    or None if the residual is too large."""
    X = np.hstack([base, np.ones((len(base), 1))])
    A, *_ = np.linalg.lstsq(X, frame, rcond=None)
    if np.abs(X @ A - frame).max() * 1000 > FIT_MM:
        return None
    return A.T  # 3x4, row-major


def moments(v: np.ndarray, t: np.ndarray) -> tuple[float, np.ndarray, np.ndarray, np.ndarray]:
    """Surface area, centroid, principal second moments (ascending) and axes of a triangle mesh (exact per triangle)."""
    a, b, c = v[t[:, 0]], v[t[:, 1]], v[t[:, 2]]
    area = 0.5 * np.linalg.norm(np.cross(b - a, c - a), axis=1)
    A = area.sum()
    s = a + b + c
    cen = (area[:, None] * s / 3).sum(0) / A
    a0, b0, c0, s0 = a - cen, b - cen, c - cen, s - 3 * cen
    outer = lambda x: np.einsum("ni,nj->nij", x, x)  # noqa: E731
    J = (area[:, None, None] / 12 * (outer(a0) + outer(b0) + outer(c0) + outer(s0))).sum(0)
    w, E = np.linalg.eigh(J)
    return A, cen, w, E


class Rigid:
    """Rigid match of a solid whose tessellation differs from its standing mesh (same shape, moved): principal
    axes of the surface give the rotation, the surface centroid the translation; accepted when the moved standing
    mesh lies on the frame mesh (nearest-vertex distances, both ways)."""

    def __init__(self, base: list):
        from scipy.spatial import cKDTree
        self.tree = cKDTree
        self.m = [moments(v, t) for _, v, t in base]

    def match(self, j: int, bv: np.ndarray, v: np.ndarray, fm: tuple, tf, tol: float) -> np.ndarray | None:
        A0, c0, w0, E0 = self.m[j]
        A1, c1, w1, E1 = fm
        if abs(A1 - A0) > 0.01 * A0 or np.abs(w1 - w0).max() > 0.02 * w0.max():
            return None
        best = None
        for sx in (1, -1):
            for sy in (1, -1):
                D = np.diag([sx, sy, sx * sy * np.linalg.det(E1) * np.linalg.det(E0)])
                R = E1 @ D @ E0.T
                moved = (bv - c0) @ R.T + c1
                d1 = tf.query(moved)[0]
                d2 = self.tree(moved).query(v)[0]
                err = max(np.percentile(d1, 99), np.percentile(d2, 99))
                if err < 2.5 * tol and (best is None or err < best[0]):
                    best = (err, np.hstack([R, (c1 - R @ c0)[:, None]]))
        return None if best is None else best[1]


def write(path: Path, meta: dict, blob: bytes) -> None:
    """One script file the sheet loads with a <script> tag (works from a local checkout, where fetch() of files does
    not): the mesh table as JSON and the binary buffer as base64."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("// GENERATED by tools/cad/b3d/cl05_web.py from cad/params/CL-05.yaml; do not edit.\n"
                    f"window.SUS_M1_GEOMETRY = {{meta: {json.dumps(meta, separators=(',', ':'))},\n"
                    f"bin: \"{base64.b64encode(blob).decode()}\"}};\n")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--tolerance", type=float, default=0.004, help="tessellation tolerance, metres")
    ap.add_argument("--tween", type=int, default=10, help="frames per posture change")
    ap.add_argument("--walk", type=int, default=24, help="frames per walk cycle")
    ap.add_argument("--out", type=Path, default=OUT)
    a = ap.parse_args()
    p = yaml.safe_load((ROOT / "cad/params/CL-05.yaml").read_text())
    common = yaml.safe_load((ROOT / "cad/params/common.yaml").read_text())

    base_parts, info = cl05.build(p, common, "standing")
    base = tessellate(base_parts, a.tolerance)
    pk = Packer()
    base_ids = [pk.mesh(cls, v, t) for cls, v, t in base]
    mats: list[np.ndarray] = []
    out_clips = {}
    stats = {"matched": 0, "rigid": 0, "own_mesh": 0}
    rigid = Rigid(base)
    for name, frames in clips(p, common, a.tween, a.walk).items():
        rows = []
        for label, parts, body_x in frames:
            sol = tessellate(parts, a.tolerance)
            used = set()
            vis = []  # [mesh id, matrix id] ; matrix id -1 = the mesh as stored
            for cls, v, t in sol:
                hit = None
                for j, (bcls, bv, bt) in enumerate(base):
                    if j in used or bcls != cls or bv.shape != v.shape or bt.shape != t.shape:
                        continue
                    M = fit(bv, v)
                    if M is not None:
                        hit = (j, M)
                        break
                if hit is None:  # same shape, different tessellation: try a rigid match
                    fm, tf = moments(v, t), rigid.tree(v)
                    for j, (bcls, bv, bt) in enumerate(base):
                        if j in used or bcls != cls:
                            continue
                        M = rigid.match(j, bv, v, fm, tf, a.tolerance)
                        if M is not None:
                            hit = (j, M)
                            stats["rigid"] += 1
                            break
                if hit:
                    used.add(hit[0])
                    mats.append(hit[1])
                    vis.append([base_ids[hit[0]], len(mats) - 1])
                    stats["matched"] += 1
                else:
                    vis.append([pk.mesh(cls, v, t), -1])
                    stats["own_mesh"] += 1
            rows.append({"label": label, "body_x": round(body_x, 4), "vis": vis})
            print(f"{name}: {label} ({len(sol)} solids)", flush=True)
        out_clips[name] = rows

    pos = np.concatenate(pk.pos).tobytes()
    idx = np.concatenate(pk.idx).tobytes()
    if len(idx) % 4:
        idx += b"\0\0"
    mat = np.array(mats, dtype="<f4").reshape(-1).tobytes()
    meta = {
        "about": "CL-05 reference layout (build123d, cad/params/CL-05.yaml): concept geometry for review, not a design. "
                 "In-between frames ease posture parameters; concept kinematics only, no dynamics, balance or load model.",
        "generator": "tools/cad/b3d/cl05_web.py",
        "units": "metres, z up, x forward",
        "quantum_m": STEP, "origin_m": list(ORIGIN),
        "layout": {"positions": [0, len(pos)], "indices": [len(pos), len(idx)], "matrices": [len(pos) + len(idx), len(mat)]},
        "base": base_ids, "meshes": pk.meshes, "clips": out_clips,
        "info": {k: info[k] for k in ("hip_z", "floor", "eye", "feet", "knee")},
        "stats": stats,
    }
    write(a.out / "sus-m1.js", meta, pos + idx + mat)
    size = len(pos) + len(idx) + len(mat)
    print(f"wrote {a.out / 'sus-m1.js'} ({size / 1e6:.2f} MB, {len(pk.meshes)} meshes, {len(mats)} transforms, "
          f"{stats['own_mesh']} per-frame meshes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
