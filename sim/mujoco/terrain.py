"""Level-2 terrain walk: CL-05 as a 3D multibody in MuJoCo, walking the terrain course of sheet 3.

Usage: python -m sim.mujoco.terrain [--compare | --check]
  (no flag)   run every terrain unloaded and loaded; write sim/results/l2-terrain.{json,md} and the page asset
              docs/3d/assets/sus-m1-terrain-physics.js (the frames the sheet replays)
  --compare   re-run and compare with the committed results (outcomes and attribution exactly, numbers within
              tolerance: MuJoCo results can differ in the last digits across CPUs)
  --check     check that the report and the page asset match the committed JSON (no simulation)

Model (generated from the records, never hand-edited):
  - links: cad/links.json (mass, centre of mass, inertia, joint positions of CL-05 standing); a free torso, and per
    leg hip roll and pitch, knee, ankle pitch and roll, so the zero pose is the CAD's standing pose;
  - feet: boxes over the CL-05 support footprint (cad/metrics.json), on a MuJoCo height field of the terrain
    (sim/scenes3d/terrain.yaml, the same ground function as tools/cad/b3d/cl05_terrain.py);
  - torque limits, friction and time step: sim/spec/walker_l2.yaml; gait: cad/params/CL-05.yaml walk: at the cycle
    time of sim/spec/walker.yaml; loaded runs carry the CAD's margin-peak load (cad/metrics.json) at its load centre.
Controller (drafted, I0; settings in sim/mujoco/terrain.yaml):
  - footholds: each footprint of the gait moved along the walk, at most foothold_shift_m, to where the foot plate bears
    on the most ground; the foot set level, to the ground under it, or to the terrain's slope, whichever bears most;
  - walking pattern: the zero-moment point (ZMP) on each stance foot's bearing area, and a centre-of-mass path from
    preview control of the linear inverted pendulum; joint targets from inverse kinematics with the torso level;
  - joints follow by position servo, with the weight carried by each stance foot as a feed-forward, the torso kept
    level by the stance hips, and capture-point feedback on the stance ankles; a swinging foot is steered to its
    target from the torso as it actually is; every torque is clipped to its limit.
A fall is attributed by re-running with every limit raised by attribution.boost: if it still falls, the controller
cannot walk that terrain and the run says nothing about CL-05; if it walks, the joint group whose raised limit alone
makes it walk is named, with the limit it needs. Synthetic, no evidence credit.
"""
from __future__ import annotations

import argparse
import base64
import json
import math
import re
import sys

import mujoco
import numpy as np

from sim.common import ABOUT, ROOT, SIM, dumps, label_table
from tools.pdac.load import _read_yaml
from tools.terms.terms import decorate

CFG = SIM / "mujoco" / "terrain.yaml"
OUT_JSON = ROOT / "sim" / "results" / "l2-terrain.json"
OUT_MD = ROOT / "sim" / "results" / "l2-terrain.md"
OUT_JS = ROOT / "docs" / "3d" / "assets" / "sus-m1-terrain-physics.js"
GEOM = ROOT / "docs" / "3d" / "assets" / "sus-m1.js"
SIDES = {"left": 1, "right": -1}
JNAMES = ["hip_roll", "hip_pitch", "knee", "ankle_pitch", "ankle_roll"]
BODIES = ["torso", "thigh_left", "shank_left", "foot_left", "thigh_right", "shank_right", "foot_right"]
G0 = 9.81


# ------------------------------------------------------------------------------------------------------ inputs
def load_params() -> dict:
    spec = _read_yaml(SIM / "spec" / "walker.yaml")["params"]
    l2 = _read_yaml(SIM / "spec" / "walker_l2.yaml")["params"]
    cl = _read_yaml(ROOT / "cad" / "params" / "CL-05.yaml")
    metrics = json.loads((ROOT / "cad" / "metrics.json").read_text())["concepts"]["CL-05"]
    carry = metrics["postures"]["carry"]
    cfg = _read_yaml(CFG)
    hip, knee, ankle = (l2[f"{j}_torque_max_nm"]["value"] for j in ("hip", "knee", "ankle"))
    return {
        "cfg": cfg, "links": json.loads((ROOT / "cad" / "links.json").read_text()), "leg": cl["leg"], "walk": cl["walk"],
        "T": spec["sway_period_s"]["value"], "dt": l2["timestep_s"]["value"], "mu": l2["ground_friction"]["value"],
        "tau": {"hip_roll": hip, "hip_pitch": hip, "knee": knee, "ankle_pitch": ankle, "ankle_roll": ankle},
        "support": metrics["support_polygon_m"], "course": _read_yaml(SIM / "scenes3d" / "terrain.yaml"),
        "load": {"mass_kg": carry[cfg["load"]["source"]]["load_kg"], "centre_m": carry["carry_load_centre_m"],
                 "envelope_m": carry["carry_load_envelope_m"]},
    }


class Ground:
    """Height of a terrain of terrain.yaml at world (x, y), x along the walk; the ground function of
    tools/cad/b3d/cl05_terrain.py (sim/tests check it against the height map exported to the page)."""

    def __init__(self, t: dict, period: float):
        self.t, self.period = t, period
        if t["kind"] == "plane":
            self.gx, self.gy = math.tan(math.radians(t.get("pitch_deg", 0))), math.tan(math.radians(t.get("roll_deg", 0)))
        elif t["kind"] not in ("ledges", "rubble"):
            raise ValueError(f"unknown terrain kind {t['kind']}")

    def __call__(self, x: float, y: float) -> float:
        t = self.t
        if t["kind"] == "plane":
            return x * self.gx - y * self.gy
        if t["kind"] == "ledges":
            return math.floor(x / t["run_m"] + 1e-9) * t["rise_m"]
        a, P = t["amp_m"], self.period
        return a * math.sin(2 * math.pi * x / P + 1.7 * math.tanh(2 * y)) * (0.75 + 0.25 * math.cos(2.4 * y))


def gait_of(p: dict, loaded: bool) -> dict:
    W = {k: v for k, v in p["walk"].items() if k != "loaded"}
    if loaded:
        W.update(p["walk"]["loaded"])
    return W


def skipped(t: dict, W: dict) -> str | None:
    """Why a terrain is not run with gait W: as the kinematic course, a ledge run must divide the stride."""
    if t["kind"] == "ledges" and abs(W["stride"] / t["run_m"] - round(W["stride"] / t["run_m"])) > 1e-9:
        return f"the {t['run_m']} m ledge run does not divide the {W['stride']} m stride (not posed on the kinematic course either)"
    return None


# ------------------------------------------------------------------------------------------------------- model
def _fmt(v) -> str:
    return " ".join(f"{x:.5g}" for x in v)


def _inertial(link: dict, origin) -> str:
    c = np.array(link["com_m"]) - np.array(origin)
    I = np.array(link["inertia_kgm2"], float)
    return (f'<inertial pos="{_fmt(c)}" mass="{link["mass_kg"]}" '
            f'fullinertia="{I[0, 0]} {I[1, 1]} {I[2, 2]} {I[0, 1]} {I[0, 2]} {I[1, 2]}"/>')


def foot_box(p: dict) -> tuple[float, float, float, float]:
    """Foot plate relative to the ankle: x from heel spur to toes and the half-width over the outer edge, from the
    CL-05 support footprint; and its thickness."""
    poly = np.array(p["support"])
    ax, hw = p["leg"]["ankle_forward"], p["leg"]["hip_half_width"]
    return poly[:, 0].min() - ax, poly[:, 0].max() - ax, poly[:, 1].max() - hw, p["leg"]["foot"][2]


def mjcf(p: dict, ground: Ground, x_range, width: float, load: dict | None = None, sample: float = 0.05):
    links, J = p["links"]["links"], p["links"]["joints_m"]
    hip_z = J["left"]["hip"][2]
    a_h = J["left"]["ankle"][2]
    x0, x1, yo, ft = foot_box(p)
    xs = np.arange(x_range[0], x_range[1] + 1e-9, sample)
    ys = np.arange(-width / 2, width / 2 + 1e-9, sample)
    H = np.array([[ground(x, y) for x in xs] for y in ys])
    zmin, elev = H.min(), max(H.max() - H.min(), 0.01)
    legs = []
    for side in SIDES:
        h, k, a = (np.array(J[side][j]) for j in ("hip", "knee", "ankle"))
        legs.append(f"""
      <body name="thigh_{side}" pos="{_fmt(h - [0, 0, hip_z])}">
        <joint name="hip_roll_{side}" axis="1 0 0" range="-0.6 0.6"/>
        <joint name="hip_pitch_{side}" axis="0 1 0" range="-1.6 1.6"/>
        {_inertial(links['thigh_' + side], h)}
        <geom type="capsule" fromto="0 0 0 {_fmt(k - h)}" size="0.13" contype="0" conaffinity="0"/>
        <body name="shank_{side}" pos="{_fmt(k - h)}">
          <joint name="knee_{side}" axis="0 1 0" range="-1.8 1.8"/>
          {_inertial(links['shank_' + side], k)}
          <geom type="capsule" fromto="0 0 0 {_fmt(a - k)}" size="0.11" contype="0" conaffinity="0"/>
          <body name="foot_{side}" pos="{_fmt(a - k)}">
            <joint name="ankle_pitch_{side}" axis="0 1 0" range="-1.2 1.2"/>
            <joint name="ankle_roll_{side}" axis="1 0 0" range="-0.6 0.6"/>
            {_inertial(links['foot_' + side], a)}
            <geom name="sole_{side}" type="box" size="{(x1 - x0) / 2:.4f} {yo:.4f} {ft / 2:.4f}" pos="{(x0 + x1) / 2:.4f} 0 {-a_h + ft / 2:.4f}"/>
            <site name="sole_{side}" pos="0 0 {-a_h:.4f}"/>
          </body>
        </body>
      </body>""")
    cargo = ""
    if load:
        c, e = np.array(load["centre_m"]) - [0, 0, hip_z], np.array(load["envelope_m"]) / 2
        cargo = (f'\n      <body name="load" pos="{_fmt(c)}"><geom type="box" size="{_fmt(e)}" mass="{load["mass_kg"]}" '
                 'contype="0" conaffinity="0"/></body>')
    acts = "\n".join(f'    <motor name="{j}_{s}" joint="{j}_{s}" ctrlrange="{-p["tau"][j]} {p["tau"][j]}"/>' for s in SIDES for j in JNAMES)
    xml = f"""<mujoco model="sus-m1-terrain">
  <compiler angle="radian" autolimits="true"/>
  <option timestep="{p['dt']}" integrator="implicitfast" gravity="0 0 -{G0}"/>
  <default>
    <joint type="hinge" damping="200" armature="20"/>
    <geom friction="{p['mu']} 0.01 0.001" solref="0.01 1" solimp="0.95 0.99 0.001"/>
  </default>
  <asset><hfield name="ground" nrow="{len(ys)}" ncol="{len(xs)}" size="{(xs[-1] - xs[0]) / 2:.4f} {(ys[-1] - ys[0]) / 2:.4f} {elev:.4f} 0.5"/></asset>
  <worldbody>
    <geom name="ground" type="hfield" hfield="ground" pos="{(xs[0] + xs[-1]) / 2:.4f} 0 {zmin:.4f}"/>
    <body name="torso" pos="0 0 {hip_z:.4f}">
      <freejoint name="root"/>
      {_inertial(links['torso'], [0, 0, hip_z])}{cargo}{''.join(legs)}
    </body>
  </worldbody>
  <actuator>
{acts}
  </actuator>
</mujoco>"""
    return xml, (H - zmin) / elev


def build(p: dict, ground: Ground, x_range, load: dict | None = None, width: float = 4.0):
    xml, hdata = mjcf(p, ground, x_range, width, load)
    m = mujoco.MjModel.from_xml_string(xml)
    m.hfield_data[:] = hdata.ravel()
    return m


# ---------------------------------------------------------------------------------------------- walking pattern
class Gait:
    """Footsteps of the CL-05 walk on terrain G: the foot timing of cl05_terrain.py with a minimum-jerk swing (the foot
    leaves and lands at rest), footholds chosen for bearing, as sole targets (the point under the ankle)."""

    def __init__(self, p: dict, G: Ground, W: dict):
        self.p, self.G, self.W = p, G, W
        L = p["leg"]
        self.ax, self.hw, self.ah = L["ankle_forward"], L["hip_half_width"], L["ankle_height"]
        self.R = (L["thigh"] + L["shank"]) * 0.995
        self.x0, self.x1, self.yo, _ = foot_box(p)
        self.shift = p["cfg"]["foothold_shift_m"]
        self.off = {"left": 0.0, "right": 0.5}
        self._grid = np.array([(dx, dy) for dx in np.linspace(self.x0, self.x1, 25) for dy in np.linspace(-self.yo, self.yo, 5)])
        self._holds, self._place = {}, {}

    def _rest(self, x, y, ry, rx):
        """The plate turned by (ry, rx) lowered onto the ground with the ankle over (x, y): sole z under the ankle, and
        the bearing part (within 1 cm of the ground) as (centre ahead of the ankle, score = fraction x half-extent)."""
        P = self._grid
        need = np.array([self.G(x + dx, y + dy) for dx, dy in P]) + math.tan(ry) * P[:, 0] - math.tan(rx) * P[:, 1]
        z = float(need.max())
        on = P[need > z - 0.01]
        hx, hy = np.ptp(on[:, 0]) / 2, np.ptp(on[:, 1]) / 2
        return z, float((on[:, 0].min() + on[:, 0].max()) / 2), len(on) / len(P) * min(hx, 2 * hy)

    def hold(self, x, y):
        """Foothold with the ankle over (x, y), the foot set to the plane fitted under the plate, level, or to the slope
        over two metres, whichever bears most: (sole z, rotation about y (nose down +), about x (left up +), bearing
        centre ahead of the ankle, score)."""
        key = (round(x, 4), round(y, 4))
        if key not in self._holds:
            def plane(xs, ys):
                Q = np.array([(dx, dy, self.G(x + dx, y + dy)) for dx in xs for dy in ys])
                _, b, c = np.linalg.lstsq(np.c_[np.ones(len(Q)), Q[:, :2]], Q[:, 2], rcond=None)[0]
                return round(-math.atan(b), 9), round(math.atan(c), 9)
            cands = sorted({plane(np.linspace(self.x0, self.x1, 13), np.linspace(-self.yo, self.yo, 5)), (0.0, 0.0),
                            plane(np.linspace(-1.0, 1.0, 21), np.linspace(-0.5, 0.5, 5))})
            best = None
            for ry, rx in cands:
                z, cx, score = self._rest(x, y, ry, rx)
                if best is None or score > best[4] + 1e-6:
                    best = (z, ry, rx, cx, score)
            self._holds[key] = best
        return self._holds[key]

    def place(self, x, y):
        """The footprint moved along the walk, at most `shift`, to the best-bearing foothold (the smallest move within
        5 % of the best); on a plane it stays where the gait puts it."""
        key = (round(x, 4), round(y, 4))
        if key not in self._place:
            n = int(round(self.shift / 0.02))
            shifts = np.round(np.arange(-n, n + 1) * 0.02, 3)
            score = {s: self.hold(x + s, y)[4] for s in shifts}
            top = max(score.values())
            self._place[key] = x + float(min((s for s in shifts if score[s] >= 0.95 * top), key=abs))
        return self._place[key]

    def foot(self, side, phi):
        """(sole x, y, z, rot_y, rot_x, swing fraction or None, bearing centre ahead of the ankle) at gait phase phi."""
        S, duty, lift = self.W["stride"], self.W["duty"], self.W["lift"]
        y = SIDES[side] * self.hw
        f, c = (phi + self.off[side]) % 1.0, math.floor(phi + self.off[side])
        x_nom = S * (c - self.off[side]) + self.ax + S * duty / 2
        x_st = self.place(x_nom, y)
        a = self.hold(x_st, y)
        if f < duty:
            return (x_st, y, a[0], a[1], a[2], None, a[3])
        g = (f - duty) / (1 - duty)
        g = g * g * g * (10 - 15 * g + 6 * g * g)
        x_on = self.place(x_nom + S, y)
        b = self.hold(x_on, y)
        ry, rx = a[1] + (b[1] - a[1]) * g, a[2] + (b[2] - a[2]) * g
        ahead, tb = min(1.0, g + 0.35), -math.tan(ry)       # the plate, turned as it is, clears the ground just ahead
        path = max(self.G(xs + dx, y) - tb * dx for xs in np.linspace(x_st, x_st + (x_on - x_st) * ahead, 21)
                   for dx in np.linspace(self.x0, self.x1, 9))
        z = max(a[0] + (b[0] - a[0]) * g, path) + lift * math.sin(math.pi * g)
        return (x_st + (x_on - x_st) * g, y, z, ry, rx, g, b[3])

    def hip_z(self, phi, hip0):
        """Hip-line height: the walk's crouch and bob above the mean ground under the feet, lowered only as far as a leg
        needs to reach its foot (as cl05_terrain.pose)."""
        W = self.W
        fs = {s: self.foot(s, phi) for s in SIDES}
        gref = sum(self.G(fs[s][0], fs[s][1]) for s in SIDES) / 2
        xb = W["stride"] * phi
        hz = hip0 - W["crouch"] - W["bob"] * math.cos(4 * math.pi * phi)
        for s in SIDES:
            rel = fs[s][0] - xb
            if abs(rel) < self.R:
                hz = min(hz, self.ah + fs[s][2] - gref + math.sqrt(self.R ** 2 - rel ** 2))
        return gref + hz

    def _split(self, phi):
        duty = self.W["duty"]
        fs = {s: self.foot(s, phi) for s in SIDES}
        st = [s for s in SIDES if fs[s][5] is None]
        if len(st) == 1:
            return fs, st[0], st[0], 0.0
        fa = {s: (phi + self.off[s]) % 1.0 for s in SIDES}
        a = max(SIDES, key=lambda s: fa[s])                  # lifts next
        return fs, a, ("left" if a == "right" else "right"), (fa[a] - 0.5) / (duty - 0.5)

    def zmp(self, phi):
        """ZMP reference: on the stance foot's bearing centre, moving to the foot just landed in double support."""
        fs, a, b, w = self._split(phi)
        c = {s: np.array([fs[s][0] + fs[s][6], fs[s][1]]) for s in SIDES}
        return c[a] + w * (c[b] - c[a])

    def share(self, phi):
        _, a, b, w = self._split(phi)
        return {a: 1 - w, b: w} if a != b else {s: float(s == a) for s in SIDES}


def preview_gains(zc, dt, n, Qe=1.0, R=1e-6):
    """Preview control of the linear inverted pendulum (cart-table model, jerk input), gains by Riccati iteration."""
    A = np.array([[1, dt, dt * dt / 2], [0, 1, dt], [0, 0, 1]])
    B = np.array([[dt ** 3 / 6], [dt * dt / 2], [dt]])
    C = np.array([[1, 0, -zc / G0]])
    At = np.block([[np.eye(1), C @ A], [np.zeros((3, 1)), A]])
    Bt = np.vstack([C @ B, B])
    Q = np.zeros((4, 4)); Q[0, 0] = Qe
    P = Q.copy()
    for _ in range(10000):
        Pn = Q + At.T @ P @ At - At.T @ P @ Bt @ np.linalg.inv(R + Bt.T @ P @ Bt) @ Bt.T @ P @ At
        done = np.abs(Pn - P).max() < 1e-10 * max(1.0, np.abs(P).max())
        P = Pn
        if done:
            break
    S = np.linalg.inv(R + Bt.T @ P @ Bt)
    K = S @ Bt.T @ P @ At
    Ac = At - Bt @ K
    X = -Ac.T @ P @ np.array([[1], [0], [0], [0]])
    Gd = []
    for _ in range(1, n):
        Gd.append((S @ Bt.T @ X)[0, 0])
        X = Ac.T @ X
    return A, B, C, K[0, 0], K[0, 1:], np.array(Gd)


def com_pattern(zref, zc, dt, preview_s):
    """Centre-of-mass path (N x 2) whose ZMP follows zref (N x 2)."""
    n = int(round(preview_s / dt))
    A, B, C, Gi, Gx, Gd = preview_gains(zc, dt, n)
    pad = np.vstack([zref, np.repeat(zref[-1:], n, 0)])
    out = np.zeros_like(zref)
    for ax in range(2):
        x, e = np.array([zref[0, ax], 0.0, 0.0]), 0.0
        for k in range(len(zref)):
            out[k, ax] = x[0]
            e += (C @ x)[0] - zref[k, ax]
            x = A @ x + B[:, 0] * (-Gi * e - Gx @ x - Gd @ pad[k + 1:k + n, ax])
    return out


def rot_y(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def rot_x(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


class IK:
    """Leg joint angles, relative to the CL-05 standing pose, that put a sole on its target. With no hip yaw a foot
    cannot take every orientation: its up axis (so the sole position) is exact, its heading can differ slightly."""

    def __init__(self, p):
        J = p["links"]["joints_m"]["left"]
        h, k, a = (np.array(J[j]) for j in ("hip", "knee", "ankle"))
        t0, s0 = k - h, a - k
        self.L1, self.L2 = np.linalg.norm(t0), np.linalg.norm(s0)
        self.at0, self.as0 = math.atan2(t0[0], -t0[2]), math.atan2(s0[0], -s0[2])
        self.ah, self.hw = a[2], p["leg"]["hip_half_width"]

    def leg(self, side, torso, sole, ry, rx, R=None):
        """Joints putting the sole at `sole` with the foot turned by ry about y and rx about x (world), the torso at
        `torso` in orientation R (level when None)."""
        R = np.eye(3) if R is None else R
        hip = torso + R @ np.array([0, SIDES[side] * self.hw, 0])
        Rf = R.T @ rot_y(ry) @ rot_x(rx)
        d = R.T @ (sole - hip) + Rf @ np.array([0, 0, self.ah])
        hr = math.atan2(d[1], -d[2])
        dz = -math.hypot(d[1], d[2])
        D = min(math.hypot(d[0], dz), (self.L1 + self.L2) * 0.999)
        al = math.atan2(d[0], -dz)
        be = math.acos(max(-1.0, min(1.0, (self.L1 ** 2 + D * D - self.L2 ** 2) / (2 * self.L1 * D))))
        ga = math.acos(max(-1.0, min(1.0, (self.L2 ** 2 + D * D - self.L1 ** 2) / (2 * self.L2 * D))))
        th_t, th_s = -((al - be) - self.at0), -((al + ga) - self.as0)
        z = rot_x(-hr) @ Rf[:, 2]          # the foot's up axis in the leg plane: the ankle pitch and roll that give it
        return [hr, th_t, th_s - th_t, math.atan2(z[0], z[2]) - th_s, math.atan2(-z[1], math.hypot(z[0], z[2]))]


def reference(p: dict, G: Ground, W: dict, load: dict | None):
    """The walk sampled every pattern_dt_s: ZMP and centre-of-mass references, level-torso position, joint targets,
    foot targets and each foot's share of the weight."""
    cfg = p["cfg"]
    dt, cycles, stand, hold = cfg["pattern_dt_s"], cfg["cycles"], cfg["stand_s"], cfg["hold_s"]
    gait, ik, T = Gait(p, G, W), IK(p), p["T"]
    hip0 = p["links"]["joints_m"]["left"]["hip"][2]
    walk = cycles * T
    ts = np.arange(0, stand + walk + hold, dt)
    phis = np.clip((ts - stand) / T, 0, cycles)
    zr = np.array([gait.zmp(ph) for ph in phis])
    mid = {ph: np.mean([[gait.foot(s, ph)[0] + gait.foot(s, ph)[6], gait.foot(s, ph)[1]] for s in SIDES], 0) for ph in (0, cycles)}
    for i, t in enumerate(ts):                                # standing: from between the feet to the first stance foot
        if t < stand:
            zr[i] = mid[0] + min(1, max(0, (t - 0.5) / (stand - 0.5))) * (gait.zmp(0) - mid[0])
        elif t > stand + walk:
            zr[i] = gait.zmp(cycles) + min(1, (t - stand - walk) / 0.8) * (mid[cycles] - gait.zmp(cycles))
    m = mujoco.MjModel.from_xml_string(mjcf(p, G, (-1, 1), 1.0, load)[0])
    d = mujoco.MjData(m)
    d.qpos[:] = 0; d.qpos[3] = 1; d.qpos[2] = hip0
    mujoco.mj_kinematics(m, d); mujoco.mj_comPos(m, d)
    zc = float(d.subtree_com[1][2]) - W["crouch"]
    off = d.subtree_com[1][:2] - d.xpos[1][:2]
    com = com_pattern(zr, zc, dt, cfg["preview_s"])
    qref, torso, feet, share = np.zeros((len(ts), 10)), np.zeros((len(ts), 3)), [], []
    for i, ph in enumerate(phis):
        fs = {s: gait.foot(s, ph) for s in SIDES}
        tz, txy = gait.hip_z(ph, hip0), com[i] - off
        for _ in range(5):                                    # torso placed so the whole-body CoM is on its path
            tp = np.array([txy[0], txy[1], tz])
            q = [a for s in SIDES for a in ik.leg(s, tp, np.array(fs[s][:3]), fs[s][3], fs[s][4])]
            d.qpos[:3], d.qpos[3:7], d.qpos[7:] = tp, [1, 0, 0, 0], q
            mujoco.mj_kinematics(m, d); mujoco.mj_comPos(m, d)
            err = com[i] - d.subtree_com[1][:2]
            txy = txy + err
            if np.abs(err).max() < 1e-4:
                break
        qref[i], torso[i] = q, tp
        feet.append(fs)
        if stand <= ts[i] <= stand + walk:
            share.append(gait.share(ph))
        else:                                                  # standing: by where the ZMP sits between the feet
            w = min(1.0, max(0.0, (zr[i][1] - fs["right"][1]) / (fs["left"][1] - fs["right"][1])))
            share.append({"left": w, "right": 1 - w})
    return {"t": ts, "phi": phis, "zmp": zr, "com": com, "q": qref, "torso": torso, "feet": feet, "share": share,
            "acc": np.gradient(np.gradient(com, dt, axis=0), dt, axis=0), "dt": dt, "zc": zc}


# ------------------------------------------------------------------------------------------------- simulation
def _rp(q):
    w, x, y, z = q
    return math.atan2(2 * (w * x + y * z), 1 - 2 * (x * x + y * y)), math.asin(max(-1.0, min(1.0, 2 * (w * y - z * x))))


def simulate(p: dict, terrain: dict, loaded: bool, tau_scale: dict | None = None, frames: bool = False) -> dict:
    """One run. tau_scale multiplies the torque limit of the named joints (attribution re-runs)."""
    cfg, gains = p["cfg"], p["cfg"]["gains"]
    W = gait_of(p, loaded)
    load = p["load"] if loaded else None
    G = Ground(terrain, W["stride"])
    m = build(p, G, (-3.0, W["stride"] * (cfg["cycles"] + 1) + 3.0), load)
    r = reference(p, G, W, load)
    d = mujoco.MjData(m)
    d.qpos[:3], d.qpos[3:7], d.qpos[7:] = r["torso"][0], [1, 0, 0, 0], r["q"][0]
    mujoco.mj_forward(m, d)
    lim0 = np.array([p["tau"][j] for _ in SIDES for j in JNAMES])
    lim = lim0 * np.array([(tau_scale or {}).get(j, 1.0) for _ in SIDES for j in JNAMES])
    m.actuator_ctrlrange[:] = np.c_[-lim, lim]              # MuJoCo clamps to the control range too
    sid = lambda kind, n: mujoco.mj_name2id(m, kind, n)                       # noqa: E731
    sole = {s: sid(mujoco.mjtObj.mjOBJ_GEOM, f"sole_{s}") for s in SIDES}
    site = {s: sid(mujoco.mjtObj.mjOBJ_SITE, f"sole_{s}") for s in SIDES}
    foot = {s: sid(mujoco.mjtObj.mjOBJ_BODY, f"foot_{s}") for s in SIDES}
    body = [sid(mujoco.mjtObj.mjOBJ_BODY, b) for b in BODIES]
    ground = sid(mujoco.mjtObj.mjOBJ_GEOM, "ground")
    nsub = int(round(r["dt"] / m.opt.timestep))
    dq_ref = np.gradient(r["q"], r["dt"], axis=0)
    ik, Mtot, jac = IK(p), float(sum(m.body_mass)), np.zeros((3, m.nv))
    om = math.sqrt(G0 / r["zc"])
    xi_ref = r["com"] + np.gradient(r["com"], r["dt"], axis=0) / om
    every = max(1, int(round(1 / cfg["log_hz"] / r["dt"])))
    use, sat, steps = np.zeros(10), np.zeros(10), 0
    tilt, slip, anchor, fall, fz_peak, log = 0.0, {s: 0.0 for s in SIDES}, {s: None for s in SIDES}, None, 0.0, []
    walk_end = cfg["stand_s"] + cfg["cycles"] * p["T"]
    for i in range(len(r["t"])):
        stance = {s: r["feet"][i][s][5] is None for s in SIDES}
        ns = sum(stance.values())
        for _ in range(nsub):
            q, dq = d.qpos[7:], d.qvel[6:]
            qr = r["q"][i].copy()
            Rt = d.xmat[1].reshape(3, 3)
            for k, s in enumerate(SIDES):                     # a swinging foot: steered from the torso as it is
                f = r["feet"][i][s]
                if f[5] is not None:
                    qr[5 * k:5 * k + 5] = ik.leg(s, d.qpos[:3], np.array(f[:3]), f[3], f[4], Rt)
            u = gains["kp"] * (qr - q) + gains["kd"] * (dq_ref[i] - dq) + d.qfrc_bias[6:]
            for s in SIDES:                                   # each stance foot carries its share of the weight
                w = r["share"][i][s]
                if w > 0:
                    pt = d.site_xpos[site[s]] + d.site_xmat[site[s]].reshape(3, 3) @ np.array([r["feet"][i][s][6], 0, 0])
                    mujoco.mj_jac(m, d, jac, None, pt, foot[s])
                    u -= jac[:, 6:].T @ (w * Mtot * np.array([r["acc"][i][0], r["acc"][i][1], G0]))
            roll, pitch = _rp(d.qpos[3:7])
            mujoco.mj_subtreeVel(m, d)
            dp = np.clip(gains["kxi"] * (d.subtree_com[1][:2] + d.subtree_linvel[1][:2] / om - xi_ref[i]), -0.3, 0.3)
            for k, s in enumerate(SIDES):
                if stance[s]:                                 # torso level on the stance hips; capture point on the ankles
                    u[5 * k] += (gains["kt"] * roll + gains["kdt"] * d.qvel[3]) / ns
                    u[5 * k + 1] += (gains["kt"] * pitch + gains["kdt"] * d.qvel[4]) / ns
                    w = r["share"][i][s]
                    u[5 * k + 3] += w * Mtot * G0 * dp[0]
                    u[5 * k + 4] -= w * Mtot * G0 * dp[1]
            d.ctrl[:] = np.clip(u, -lim, lim)
            if fall is None and r["t"][i] <= walk_end + cfg["hold_s"]:
                use = np.maximum(use, np.abs(d.ctrl) / lim0)
                sat += np.abs(u) >= lim
                steps += 1
            mujoco.mj_step(m, d)
        roll, pitch = _rp(d.qpos[3:7])
        if fall is None:
            tilt = max(tilt, abs(roll), abs(pitch))
        F, other = {s: 0.0 for s in SIDES}, False
        for ci in range(d.ncon):
            c = d.contact[ci]
            if ground not in (c.geom1, c.geom2):
                continue
            hit = [s for s in SIDES if sole[s] in (c.geom1, c.geom2)]
            if not hit:
                other = True
                continue
            f6 = np.zeros(6)
            mujoco.mj_contactForce(m, d, ci, f6)
            F[hit[0]] += abs((c.frame.reshape(3, 3).T @ f6[:3])[2])
        if fall is None:
            fz_peak = max(fz_peak, *F.values())
            for s in SIDES:
                pos = d.xpos[foot[s]][:2].copy()
                if stance[s] and F[s] > 0.2 * Mtot * G0:
                    anchor[s] = pos if anchor[s] is None else anchor[s]
                    slip[s] = max(slip[s], float(np.linalg.norm(pos - anchor[s])))
                else:
                    anchor[s] = None
            why = ("non-foot contact" if other else "tilt" if max(abs(roll), abs(pitch)) > math.radians(cfg["fall"]["tilt_deg"])
                   else "drop" if d.qpos[2] < r["torso"][i][2] - cfg["fall"]["drop_m"] else None)
            if why:
                fall = {"t": round(float(r["t"][i]), 2), "why": why}
        if frames and i % every == 0:
            log.append([*(v for b in body for v in (*d.xpos[b], *d.xquat[b])), F["left"], F["right"], roll, pitch])
        if fall and r["t"][i] > fall["t"] + 1.0:
            break
    groups = p["cfg"]["attribution"]["groups"]
    idx = {j: [JNAMES.index(j), 5 + JNAMES.index(j)] for j in JNAMES}
    out = {"walked": fall is None, "fall": fall, "tilt_max_deg": round(math.degrees(tilt), 1),
           "slip_max_m": round(max(slip.values()), 3), "foot_force_peak_kn": round(float(fz_peak) / 1000, 1),
           "weight_kn": round(Mtot * G0 / 1000, 1),
           "torque_use": {g: round(float(max(use[i] for j in js for i in idx[j])), 2) for g, js in groups.items()},
           "at_limit_pct": {g: round(float(100 * max(sat[i] for j in js for i in idx[j]) / max(steps, 1)), 1) for g, js in groups.items()}}
    if frames:
        out["frames"] = log
    return out


def attribute(p: dict, terrain: dict, loaded: bool) -> dict:
    """Why a run fell: re-run with every limit raised by `boost`; if that walks, the single joint group whose raised
    limit alone makes it walk, and the smallest multiplier of its limit that does (bisection)."""
    a = p["cfg"]["attribution"]
    boost, groups = a["boost"], a["groups"]
    scale = lambda g, k: {j: k for j in groups[g]}                    # noqa: E731
    if not simulate(p, terrain, loaded, {j: boost for js in groups.values() for j in js})["walked"]:
        return {"limited_by": "controller", "note": f"falls with every torque limit x{boost}: a limit of the drafted controller, not a finding about CL-05"}
    alone = [g for g in groups if simulate(p, terrain, loaded, scale(g, boost))["walked"]]
    if not alone:
        return {"limited_by": "torque (several joint groups)", "note": f"walks only with more than one joint group's limit raised x{boost}"}
    g = alone[0]
    lo, hi = 1.0, float(boost)
    while hi - lo > a["search_tol"]:
        mid = (lo + hi) / 2
        lo, hi = (lo, mid) if simulate(p, terrain, loaded, scale(g, mid))["walked"] else (mid, hi)
    nm = p["tau"][groups[g][0]]
    return {"limited_by": g, "alone": alone, "multiplier": round(hi, 2), "needed_knm": round(hi * nm / 1000, 1),
            "limit_knm": round(nm / 1000, 1), "note": f"walks with the {g} limit alone raised to x{hi:.2f}"}


def run() -> tuple[dict, dict]:
    p = load_params()
    rows, frames = [], {}
    for loaded in (False, True):
        for t in p["course"]["terrains"]:
            row = {"key": t["key"], "label": t["label"], "mode": "loaded" if loaded else "unloaded"}
            why = skipped(t, gait_of(p, loaded))
            if why:
                rows.append(row | {"skipped": why})
                continue
            res = simulate(p, t, loaded, frames=True)
            frames[f"{row['mode']}/{t['key']}"] = res.pop("frames")
            if not res["walked"]:
                res["attribution"] = attribute(p, t, loaded)
            rows.append(row | res)
            print(f"{row['mode']:8s} {t['key']:8s} {'walked' if res['walked'] else 'fell ' + str(res['fall'])}", flush=True)
    cfg = p["cfg"]
    res = {"about": ABOUT, "mujoco": mujoco.__version__, "id": cfg["id"], "settings": "sim/mujoco/terrain.yaml",
           "cycles": cfg["cycles"], "cycle_s": p["T"], "load_kg": p["load"]["mass_kg"],
           "limits_knm": {"hip": p["tau"]["hip_pitch"] / 1000, "knee": p["tau"]["knee"] / 1000, "ankle": p["tau"]["ankle_pitch"] / 1000},
           "log_hz": cfg["log_hz"], "rows": rows}
    return res, frames


# --------------------------------------------------------------------------------------------------- outputs
def page(res: dict) -> str:
    L = res["limits_knm"]
    out = ["# Level-2 terrain walk\n\n",
           label_table(f"sim/mujoco/terrain.py (MuJoCo {res['mujoco']}), settings {res['settings']}",
                       f"CL-05 walking the sheet 3 terrain course, {res['cycles']} cycles of {res['cycle_s']} s, unloaded and "
                       f"carrying {res['load_kg']} kg (the CAD's margin-peak load)",
                       [("purpose", "how the drafted walk behaves with dynamics, contact and torque limits; not validation against hardware")]),
           "\n## Runs\n\n"
           f"Torque limits: hip {L['hip']:g}, knee {L['knee']:g}, ankle {L['ankle']:g} kN m (sim/spec/walker_l2.yaml). "
           "Torque use is the largest share of its limit a joint group applied; at limit is the share of control steps it "
           "was clipped.\n\n"
           "| Terrain | Load | Outcome | Max tilt (°) | Max slip (m) | Peak contact force, instantaneous (kN) | Torque use hip / knee / ankle | At limit hip / knee / ankle (%) |\n"
           "|---|---|---|---|---|---|---|---|\n"]
    for r in res["rows"]:
        if "skipped" in r:
            out.append(f"| {r['label']} | {r['mode']} | not run: {r['skipped']} | | | | | |\n")
            continue
        oc = "walked" if r["walked"] else f"**fell** at {r['fall']['t']} s ({r['fall']['why']}); {r['attribution']['note']}"
        u, s = r["torque_use"], r["at_limit_pct"]
        out.append(f"| {r['label']} | {r['mode']} | {oc} | {r['tilt_max_deg']} | {r['slip_max_m']} | {r['foot_force_peak_kn']} "
                   f"(weight {r['weight_kn']}) | {u['hip']} / {u['knee']} / {u['ankle']} | {s['hip']} / {s['knee']} / {s['ankle']} |\n")
    lim = [r for r in res["rows"] if not r.get("walked", True) and r["attribution"]["limited_by"] not in ("controller",)]
    ctl = [r for r in res["rows"] if not r.get("walked", True) and r["attribution"]["limited_by"] == "controller"]
    out.append("\n## Findings\n\n")
    for r in lim:
        a = r["attribution"]
        if "needed_knm" in a:
            out.append(f"- **{r['label']}, {r['mode']}**: limited by the {a['limited_by']} torque. It walks with the {a['limited_by']} "
                       f"limit alone at {a['needed_knm']} kN m ({a['multiplier']} x {a['limit_knm']} kN m).\n")
        else:
            out.append(f"- **{r['label']}, {r['mode']}**: {a['note']}.\n")
    for r in ctl:
        out.append(f"- {r['label']}, {r['mode']}: {r['attribution']['note']}.\n")
    if not lim and not ctl:
        out.append("Every run walked.\n")
    out.append("\nThe controller, its gains and the foothold rule are AI drafts (I0); masses and inertias are the CAD's placeholder "
               "values. A torque finding holds for this gait and controller only: a different gait or controller can need more or "
               "less. Findings are for the lead to weigh; nothing here changes a requirement or a hazard.\n")
    return "".join(out)


def mesh_bodies(p: dict) -> tuple[list, list]:
    """Which body each CL-05 standing mesh of sus-m1.js rides on: a leg part (structure, actuator, armour or hose
    beside the hip line, below the pod) goes to the foot below 0.45 m, else to the nearer of thigh and shank; every
    other part rides on the torso. Returns [[mesh id, body index]] and each body's standing origin."""
    text = GEOM.read_text()
    meta = json.loads(re.search(r"meta: (\{.*?\}),\nbin:", text, re.S).group(1))
    raw = base64.b64decode(re.search(r'bin: "([^"]+)"', text).group(1))
    po, pl = meta["layout"]["positions"]
    P = np.frombuffer(raw[po:po + pl], dtype="<i2").reshape(-1, 3) * meta["quantum_m"] + np.array(meta["origin_m"])
    J = p["links"]["joints_m"]

    def seg(c, a, b):
        a, b = np.array(a), np.array(b)
        t = np.clip(np.dot(c - a, b - a) / np.dot(b - a, b - a), 0, 1)
        return float(np.linalg.norm(c - (a + t * (b - a))))
    out = []
    for mid in meta["base"]:
        mm = meta["meshes"][mid]
        vo, vn = mm["v"]
        c = P[vo:vo + vn].mean(0)
        b = 0
        if mm["cls"] in ("structure", "actuator", "armor", "hose") and 0.3 <= abs(c[1]) <= 0.95 and c[0] < 0.7 and c[2] < 2.7:
            side = "left" if c[1] > 0 else "right"
            j = J[side]
            part = "foot" if c[2] < 0.45 else ("thigh" if seg(c, j["hip"], j["knee"]) <= seg(c, j["knee"], j["ankle"]) else "shank")
            b = BODIES.index(f"{part}_{side}")
        out.append([mid, b])
    hip_z = J["left"]["hip"][2]
    origins = [[0, 0, hip_z]] + [J[s][j] for s in SIDES for j in ("hip", "knee", "ankle")]
    return out, origins


def asset(res: dict, frames: dict, p: dict) -> str:
    """Page asset: the run summary, which body each standing mesh rides on, and the frames quantised to int16
    (positions in mm, quaternions x 32767, foot forces in 0.1 kN, tilt in 0.01 degree)."""
    meshes, origins = mesh_bodies(p)
    blob, runs = bytearray(), {}
    for key, fr in frames.items():
        a = np.array(fr, dtype=float)
        nb = len(BODIES)
        q = np.zeros_like(a)
        for b in range(nb):
            q[:, 7 * b:7 * b + 3] = np.round(a[:, 7 * b:7 * b + 3] * 1000)
            q[:, 7 * b + 3:7 * b + 7] = np.round(a[:, 7 * b + 3:7 * b + 7] * 32767)
        q[:, 7 * nb:7 * nb + 2] = np.round(a[:, 7 * nb:7 * nb + 2] / 100)
        q[:, 7 * nb + 2:] = np.round(np.degrees(a[:, 7 * nb + 2:]) * 100)
        b16 = np.clip(q, -32768, 32767).astype("<i2").tobytes()
        runs[key] = {"offset": len(blob), "frames": len(a), "stride": a.shape[1]}
        blob += b16
    x0, x1, yo, ft = foot_box(p)
    meta = {"about": "CL-05 walking the terrain course in the level-2 MuJoCo model (sim/mujoco/terrain.py): synthetic, no "
                     "evidence credit; drafted controller (I0). Frames: body poses from the simulation; each CL-05 standing "
                     "mesh rides rigidly on its body (the carry arms are drawn stowed).",
            "generator": "sim/mujoco/terrain.py", "bodies": BODIES, "origins_m": origins, "meshes": meshes,
            "load": res["load_kg"], "load_box": {"centre_m": p["load"]["centre_m"], "envelope_m": p["load"]["envelope_m"]},
            "foot_box": [x0, x1, yo, ft], "log_hz": res["log_hz"], "runs": runs, "summary": res}
    return ("// GENERATED by sim/mujoco/terrain.py from the level-2 terrain runs; do not edit.\n"
            f"window.SUS_M1_TERRAIN_PHYSICS = {{meta: {json.dumps(meta, separators=(',', ':'))},\n"
            f'bin: "{base64.b64encode(bytes(blob)).decode()}"}};\n')


def compare(new: dict, old: dict) -> list[str]:
    bad = []
    old_rows = {(r["mode"], r["key"]): r for r in old["rows"]}
    for r in new["rows"]:
        o = old_rows.get((r["mode"], r["key"]))
        name = f"{r['mode']}/{r['key']}"
        if o is None:
            bad.append(f"{name}: not in the committed results")
            continue
        if ("skipped" in r) != ("skipped" in o) or r.get("walked") != o.get("walked"):
            bad.append(f"{name}: outcome differs from the committed results")
            continue
        if "skipped" in r:
            continue
        if not r["walked"]:
            a, b = r["attribution"], o["attribution"]
            if a["limited_by"] != b["limited_by"]:
                bad.append(f"{name}: limited by {a['limited_by']} vs committed {b['limited_by']}")
            if "multiplier" in a and abs(a["multiplier"] - b.get("multiplier", 0)) > 0.25:
                bad.append(f"{name}: needed multiplier {a['multiplier']} vs {b.get('multiplier')}")
            if abs(r["fall"]["t"] - o["fall"]["t"]) > 0.3:
                bad.append(f"{name}: fall time {r['fall']['t']} vs {o['fall']['t']}")
        elif abs(r["tilt_max_deg"] - o["tilt_max_deg"]) > 1.5:
            bad.append(f"{name}: max tilt {r['tilt_max_deg']} vs {o['tilt_max_deg']}")
    if len(new["rows"]) != len(old["rows"]):
        bad.append("run list changed; re-run without --compare")
    return bad


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--compare", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    if a.check:
        res = json.loads(OUT_JSON.read_text())
        bad = []
        if OUT_MD.read_text() != decorate(OUT_MD, page(res)):
            bad.append(f"{OUT_MD.relative_to(ROOT)} does not match {OUT_JSON.relative_to(ROOT)}")
        m = re.search(r"meta: (\{.*?\}),\nbin:", OUT_JS.read_text(), re.S)
        if not m or json.loads(m.group(1))["summary"] != res:
            bad.append(f"{OUT_JS.relative_to(ROOT)} does not match {OUT_JSON.relative_to(ROOT)}; run python -m sim.mujoco.terrain")
        for b in bad:
            print(b)
        return 1 if bad else 0
    res, frames = run()
    if a.compare:
        bad = compare(res, json.loads(OUT_JSON.read_text()))
        for b in bad:
            print(b)
        print(f"{len(res['rows'])} runs, {len(bad)} difference(s) from the committed results")
        return 1 if bad else 0
    res = json.loads(dumps(res))
    OUT_JSON.write_text(dumps(res), encoding="utf-8")
    OUT_MD.write_text(decorate(OUT_MD, page(res)), encoding="utf-8")
    OUT_JS.write_text(asset(res, frames, load_params()), encoding="utf-8")
    print(f"wrote {OUT_JSON.relative_to(ROOT)}, {OUT_MD.relative_to(ROOT)} and {OUT_JS.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
