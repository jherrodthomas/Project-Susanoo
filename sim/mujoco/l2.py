"""SUS-M1 level-2 plant: the same cases as sim/plant/walker.py, simulated in MuJoCo.

What is physics here and an assumption in level 1:
  - the centre of pressure is limited by the foot's contact with the ground, not by an assumed +/- L * c;
  - leg support, balance and torso pitch come from joint torques limited by actuator capacity;
  - load holding locks the joints mechanically (a solver-enforced joint constraint at the current angle);
  - the protective stop really steps the swing foot back to the ground before crouching.
What is unchanged from level 1 (so outcomes are comparable): the case dictionary, the faults and capacity curve,
alarm, pilot reaction, monitor and lock logic, and the outcome definitions (tip beyond tip_offset from the support
centre; hard drop when the CoM reaches crouch height faster than safe_drop_speed). Contact after a mishap is not
analysed; the run stops at the first mishap, as in level 1. Deterministic for a given MuJoCo version.

Controller (virtual model control): the wanted force on the CoM is F = m (omega^2 (x - p_cmd), g + kp dz - kd vz),
with the level-1 capture-point law for p_cmd; stance-leg torques are J_rel^T F, where J_rel is the CoM Jacobian
relative to the stance sole. A PD on the stance hip keeps the torso upright; the swing leg follows a PD with gravity
compensation. Every torque is clipped to the actuator limit times capacity.
"""
from __future__ import annotations

import math

import mujoco
import numpy as np

from sim.mujoco.model import JOINTS, load_params, mjcf
from sim.plant.walker import capacity, default_case

LIMIT = {"hip": "hip_torque_max_nm", "knee": "knee_torque_max_nm", "ankle": "ankle_torque_max_nm"}
STANCE0 = {"hip_s": -0.15, "knee_s": 0.3, "ankle_s": -0.15}
SWING0 = {"hip_w": -0.6, "knee_w": 1.2, "ankle_w": -0.6}


class L2:
    def __init__(self, case: dict, p: dict | None = None):
        c0 = default_case()
        c0.update(case)
        self.case, self.p = c0, p or load_params()
        self.m = mujoco.MjModel.from_xml_string(mjcf(self.p, self.case["slope_deg"]))
        self.d = mujoco.MjData(self.m)
        m = self.m
        self.jid = {n: mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, n) for n in JOINTS + ["root_x", "root_z", "root_pitch"]}
        self.dof = {n: m.jnt_dofadr[j] for n, j in self.jid.items()}
        self.qadr = {n: m.jnt_qposadr[j] for n, j in self.jid.items()}
        self.eq = {n: mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_EQUALITY, f"lock_{n}") for n in JOINTS}
        self.torso = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, "torso")
        self.sole = {s: mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_SITE, f"sole_{s}") for s in ("s", "w")}
        self.foot_body = {s: mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, f"foot_{s}") for s in ("s", "w")}
        self.mass = float(sum(m.body_mass))
        self._initial_pose()

    # ------------------------------------------------------------ helpers
    def com(self):
        mujoco.mj_subtreeVel(self.m, self.d)          # subtree_linvel is only filled on request
        return self.d.subtree_com[self.torso].copy(), self.d.subtree_linvel[self.torso].copy()

    def sole_pos(self, s):
        return self.d.site_xpos[self.sole[s]].copy()

    def _initial_pose(self):
        """Stand upright on the slope (torso vertical, stance sole flat on the ground), as the level-1 plant assumes."""
        d, m = self.d, self.m
        self.pitch_ref = -math.radians(self.case["slope_deg"])      # torso vertical: lean uphill by the slope angle
        for n, v in {**STANCE0, **SWING0}.items():
            d.qpos[self.qadr[n]] = v
        d.qpos[self.qadr["root_pitch"]] = self.pitch_ref
        d.qpos[self.qadr["ankle_s"]] = -(self.pitch_ref + STANCE0["hip_s"] + STANCE0["knee_s"])
        mujoco.mj_kinematics(m, d)
        mujoco.mj_comPos(m, d)
        sole = self.sole_pos("s")
        d.qpos[self.qadr["root_z"]] -= sole[2]
        mujoco.mj_forward(m, d)
        w = 2 * math.pi / self.p["sway_period_s"]
        d.qvel[self.dof["root_x"]] = self.p["sway_amplitude_m"] * w
        mujoco.mj_forward(m, d)

    def x_ref_single(self, z, t):
        p, c = self.p, self.case
        th = math.radians(c["slope_deg"])
        return (c["stride_offset_m"] + p["slope_lean"] * z * math.tan(th)
                + p["sway_amplitude_m"] * math.sin(2 * math.pi * t / p["sway_period_s"]))

    def jac_rel(self, s):
        """CoM Jacobian relative to sole s, x and z rows (3 x nv -> 2 x nv)."""
        m, d = self.m, self.d
        jc = np.zeros((3, m.nv))
        mujoco.mj_jacSubtreeCom(m, d, jc, self.torso)
        jp = np.zeros((3, m.nv))
        mujoco.mj_jacSite(m, d, jp, None, self.sole[s])
        jr = (jc - jp)[[0, 2], :]
        # with the sole flat on the ground the foot, not the torso, is fixed: joint i also rotates everything above it,
        # so its foot-fixed column is its torso-fixed column minus the whole-body rotation column (planar chain)
        jr_foot = jr.copy()
        pitch = self.dof["root_pitch"]
        for j in ("hip", "knee", "ankle"):
            k = self.dof[f"{j}_{s}"]
            jr_foot[:, k] = jr[:, k] - jr[:, pitch]
        return jr_foot

    def lock(self):
        """Load holding: hold each leg joint at its current angle (hydraulic lock or brakes).

        A joint-equality constraint enforced by the solver. Stiff joint springs were used first, but they are
        integrated explicitly and put the light feet at the stability limit (omega*dt ~ 1.9), which pumped energy
        into the "locked" walker and made the outcome depend on rounding.
        """
        for n in JOINTS:
            e = self.eq[n]
            self.m.eq_data[e, :] = 0.0
            self.m.eq_data[e, 0] = self.d.qpos[self.qadr[n]]
            self.d.eq_active[e] = 1

    def swing_target(self, foot_x):
        """Joint angles that put the swing sole flat on the ground at foot_x (2-link IK in the leg plane)."""
        p, d = self.p, self.d
        hip = d.xpos[mujoco.mj_name2id(self.m, mujoco.mjtObj.mjOBJ_BODY, "thigh_w")]
        pitch = d.qpos[self.qadr["root_pitch"]]
        dx, dz = foot_x - hip[0], (p["ankle_height_m"]) - hip[2]
        lt, ls = p["thigh_length_m"], p["shank_length_m"]
        r = min(math.hypot(dx, dz), lt + ls - 1e-3)
        knee = math.pi - math.acos(max(-1.0, min(1.0, (lt * lt + ls * ls - r * r) / (2 * lt * ls))))
        # absolute thigh angle from vertical-down, positive = tip backwards (-x)
        to_target = math.atan2(-dx, -dz)          # direction hip->ankle, measured like the joints
        inner = math.asin(max(-1.0, min(1.0, ls * math.sin(knee) / r)))
        thigh_abs = to_target - inner
        hip_q = thigh_abs - pitch
        ankle_q = -(pitch + hip_q + knee)
        return {"hip_w": hip_q, "knee_w": knee, "ankle_w": ankle_q}

    # ------------------------------------------------------------ run
    def run(self, trace_every: float = 0.05) -> dict:
        p, c, m, d = self.p, self.case, self.m, self.d
        g = p["gravity_mps2"]
        fault, t0 = c.get("fault"), c["fault_onset_s"]
        th = math.radians(c["slope_deg"])
        ch, sh = math.cos(th), math.sin(th)

        def hv(v):          # slope-frame (x along slope downhill, z normal) -> (horizontal downhill, vertical up)
            return v[0] * ch + v[2] * sh, -v[0] * sh + v[2] * ch

        z0 = hv(self.com()[0] - self.sole_pos("s"))[1]
        zc = p["crouch_height_m"] + (z0 - p["com_height_m"])        # crouch height in this model's CoM frame
        phase, stop_t, stop_reason, lock_t, alarm_t, low_since, frozen = "single", None, None, None, None, None, None
        ev = {"alarm_t": None, "stop_t": None, "lock_t": None, "mishap_t": None, "impact_speed": 0.0}
        outcome, rho_tip, trace, nxt = "safe", float("inf"), [], 0.0
        swing_goal, double_t = None, None
        steps = int(round(p["horizon_s"] / m.opt.timestep))
        for _ in range(steps + 1):
            t = d.time
            cap = capacity(c, p, t)
            com, vel = self.com()
            # ---- alarm, stop, lock (as level 1)
            if fault in ("FLT-01", "FLT-04") and alarm_t is None and cap < p["low_supply_alarm"]:
                alarm_t = t
                ev["alarm_t"] = round(t, 3)
            if stop_t is None:
                if alarm_t is not None and c["pilot_reaction_s"] is not None and t >= alarm_t + c["pilot_reaction_s"]:
                    stop_t, stop_reason = t, "pilot"
                elif c.get("stop_request_s") is not None and fault != "FLT-03" and t >= c["stop_request_s"]:
                    stop_t, stop_reason = t, "pilot"
                elif fault == "FLT-03" and t >= t0:
                    stop_t, stop_reason = t, "faulty"
                elif fault == "FLT-02" and c["monitor"] and t >= t0 + p["monitor_detect_s"]:
                    stop_t, stop_reason = t, "monitor"
                if stop_t is not None:
                    ev["stop_t"] = round(t, 3)
                    if stop_reason in ("pilot", "monitor"):
                        phase = "stepping"
                        swing_goal = self.sole_pos("s")[0] - 1.2
            if lock_t is None and c["load_holding"] == "works":
                if cap < p["lock_threshold"]:
                    low_since = t if low_since is None else low_since
                    if t >= low_since + p["lock_delay_s"]:
                        lock_t = t
                elif stop_reason == "monitor":
                    lock_t = t
                if lock_t is not None:
                    ev["lock_t"] = round(t, 3)
                    self.lock()
            if phase == "stepping" and stop_t is not None and t >= stop_t + p["step_time_s"] \
                    and self.sole_pos("w")[2] < 0.02:
                phase, double_t = "double", t                 # only once the swing sole is really on the ground
            # ---- support
            ss = self.sole_pos("s")
            if phase == "double":
                sw = self.sole_pos("w")
                centre_s, half = (ss + sw) / 2, abs(ss[0] - sw[0]) / 2 + p["foot_half_length_m"]
            else:
                centre_s, half = ss, p["foot_half_length_m"]
            half_h = half * ch                       # support half-length projected on the horizontal
            x, z = hv(com - centre_s)
            vx, vz = hv(vel)
            omega = math.sqrt(g / max(z, 0.1))
            xi = x + vx / omega
            l_eff = half_h if lock_t is not None else half_h * cap
            rho_tip = min(rho_tip, (l_eff - abs(xi)) / p["foot_half_length_m"])
            # ---- control torques
            tau = np.zeros(m.nv)
            if lock_t is None and stop_reason != "faulty":
                if fault == "FLT-02" and t >= t0:
                    frozen = frozen or (x, vx)
                    xm, vxm = frozen
                else:
                    xm, vxm = x, vx
                x_ref = self.x_ref_single(z, t) if phase == "single" else 0.0
                xim = xm + vxm / omega
                p_cmd = xim + p["balance_gain"] * (xim - x_ref)
                p_cmd = max(-0.9 * half_h, min(0.9 * half_h, p_cmd))   # the controller knows its own support
                z_ref = z0
                if phase == "double" and double_t is not None:
                    z_ref = max(zc + 0.05, z0 - p["crouch_rate_mps"] * (t - double_t))
                fh = self.mass * omega ** 2 * (xm - p_cmd)
                fv = self.mass * (g + p["height_kp"] * (z_ref - z) - p["height_kd"] * vz)
                fx, fz = fh * ch - fv * sh, fh * sh + fv * ch            # back to the slope frame
                legs = ("s", "w") if phase == "double" else ("s",)
                for s in legs:
                    jr = self.jac_rel(s)
                    share = 1.0 / len(legs)
                    tq = jr.T @ np.array([fx * share, fz * share])
                    for j in ("hip", "knee", "ankle"):
                        tau[self.dof[f"{j}_{s}"]] += tq[self.dof[f"{j}_{s}"]]
                pitch, wp = d.qpos[self.qadr["root_pitch"]], d.qvel[self.dof["root_pitch"]]
                for s in legs:
                    tau[self.dof[f"hip_{s}"]] += (8e4 * (pitch - self.pitch_ref) + 2e4 * wp) / len(legs)
                if phase != "double":
                    goal = SWING0 if swing_goal is None else self.swing_target(swing_goal)
                    for n, q in goal.items():
                        k = self.dof[n]
                        tau[k] += d.qfrc_bias[k] + 2e4 * (q - d.qpos[self.qadr[n]]) - 4e3 * d.qvel[k]
            for i, n in enumerate(JOINTS):
                lim = p[LIMIT[n.split("_")[0]]] * cap
                d.ctrl[i] = float(np.clip(tau[self.dof[n]], -lim, lim))
            mujoco.mj_step(m, d)
            # ---- outcome
            com, vel = self.com()
            xh, zv = hv(com - centre_s)
            xs, _ = hv(com - self.sole_pos("s"))
            _, vzv = hv(vel)
            if t >= nxt - 1e-9:
                trace.append([round(t, 3), round(float(xs), 4), round(float(zv), 4), round(cap, 4), phase,
                              stop_t is not None, lock_t is not None])
                nxt += trace_every
            if zv <= zc and vzv < 0 and outcome == "safe":
                ev["impact_speed"] = round(-float(vzv), 3)
                if -vzv > p["safe_drop_speed_mps"]:
                    outcome, ev["mishap_t"] = "hard-drop", round(t, 3)
            if abs(xh) > p["tip_offset_m"] + (half_h - p["foot_half_length_m"] * ch) and outcome == "safe":
                outcome, ev["mishap_t"] = "tip", round(t, 3)
            if abs(d.qpos[self.qadr["root_pitch"]]) > 0.7 and outcome == "safe":
                outcome, ev["mishap_t"] = "tip", round(t, 3)
            if outcome != "safe":
                break
        rho_drop = (p["safe_drop_speed_mps"] - ev["impact_speed"]) / p["safe_drop_speed_mps"]
        rho = min(rho_tip, rho_drop)
        if outcome == "tip":
            rho = min(rho, -0.01)
        return {"outcome": outcome, "rho": round(rho, 4), "stop_active": stop_t is not None, "stop_reason": stop_reason,
                "events": ev, "trace": trace, "case": c, "model": "mujoco " + mujoco.__version__}


def simulate(case: dict, p: dict | None = None) -> dict:
    return L2(case, p).run()
