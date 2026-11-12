"""SUS-M1 reduced-order walker plant (layer 1). Standard library only; deterministic.

A design aid, not evidence (sim/README.md, evidence gate). Stated assumptions:

A1  Sagittal plane only. The body is a point mass on a massless telescopic leg: a linear inverted pendulum
    horizontally (x = CoM offset from the support centre, + downhill), a force-controlled leg vertically (z).
A2  In single support the gait moves the CoM reference as x_ref = stride_offset + slope_lean * z * tan(slope)
    + sway_amplitude * sin(2 pi t / sway_period): the slope_lean fraction of the slope-induced lean is not
    compensated by the gait,
    and the CoM sways over the stance foot as the walker walks.
A3  The balance controller places the centre of pressure p by capture-point feedback. p is limited to
    +/- L * c, where L is the support half-length (foot, or stance after the swing foot is planted) projected
    on the horizontal and c the actuator capacity fraction (supply pressure or bus voltage, 0..1).
A4  Leg force is limited to leg_force_ratio * m * g * c. The structure rests at crouch_height; arriving there
    faster than safe_drop_speed is a hard drop.
A5  Load-holding valves (hydraulic) or brakes (electric) engage after lock_delay once c < lock_threshold, if
    they work. Locked, the body is rigid: it stays if its capture point is inside the geometric support,
    otherwise it rotates about the support edge.
A6  The pilot hears the low-supply alarm (c < low_supply_alarm) and requests a protective stop after
    pilot_reaction_s. The correct (mode-specific) stop plants the swing foot (step_time), then crouches at
    crouch_rate. Stale feedback raises no alarm; the staleness monitor, if fitted, engages the hold. A case may
    also request a stop directly (stop_request_s), as an operator would.
A7  Tipping is irrecoverable beyond tip_offset. Contact, rotation after tipping and terrain compliance are not
    modelled; the run stops at the first mishap.
A8  A case starts in mid-gait on the periodic orbit of the unsaturated balance loop (initial_state): the CoM at the
    gait's mean offset plus the loop's own sway response, not at the reference sway with the reference velocity.
    Starting on the reference put the capture point up to 0.3 m ahead of the CoM, a state the gait never reaches,
    and tipped edge cases with no fault (resolved with the level-2 cross-check, sim/results/l2-crosscheck.md).
"""
from __future__ import annotations

import math

OUTCOMES = ("safe", "tip", "hard-drop")


def default_case() -> dict:
    return {"variant": "hydraulic", "slope_deg": 0.0, "stride_offset_m": 0.1, "fault": None, "fault_onset_s": 1.0,
            "tau_leak_s": 0.3, "pilot_reaction_s": 1.5, "load_holding": "works", "monitor": True}


def capacity(case: dict, p: dict, t: float) -> float:
    f, t0 = case.get("fault"), case["fault_onset_s"]
    if t < t0 or f not in ("FLT-01", "FLT-04"):
        return 1.0
    decay = math.exp(-(t - t0) / max(case["tau_leak_s"], 1e-6))
    if f == "FLT-01":
        return decay
    floor = p["electric_sag_floor"]
    return floor + (1.0 - floor) * decay


def initial_state(case: dict, p: dict, z0: float) -> tuple[float, float]:
    """CoM offset and velocity at t = 0 on the periodic orbit of the unsaturated balance loop (assumption A8).

    With p = xi + k (xi - x_ref) and xi = x + vx / omega, the loop is x'' = -k w0^2 (x - x_ref) - (1 + k) w0 x', so a
    sway reference A sin(w t) is followed as Im(A H e^{jwt}) with H = k w0^2 / (k w0^2 - w^2 + j (1 + k) w0 w).
    Shared with the level-2 model, so both start in the same state.
    """
    th = math.radians(case["slope_deg"])
    w0, k = math.sqrt(p["gravity_mps2"] / z0), p["balance_gain"]
    w, a = 2 * math.pi / p["sway_period_s"], p["sway_amplitude_m"]
    h = k * w0 ** 2 / complex(k * w0 ** 2 - w ** 2, (1 + k) * w0 * w)
    return case["stride_offset_m"] + p["slope_lean"] * z0 * math.tan(th) + a * h.imag, a * w * h.real


def simulate(case: dict, p: dict, trace_every: float = 0.05) -> dict:
    c0 = default_case()
    c0.update(case)
    case = c0
    if case.get("fault") == "FLT-01" and case["variant"] != "hydraulic":
        raise ValueError("FLT-01 applies to the hydraulic variant")
    if case.get("fault") == "FLT-04" and case["variant"] != "electric":
        raise ValueError("FLT-04 applies to the electric variant")
    g, m, dt = p["gravity_mps2"], p["mass_kg"], p["dt_s"]
    th = math.radians(case["slope_deg"])
    foot = p["foot_half_length_m"] * math.cos(th)
    stance = p["stance_half_length_m"] * math.cos(th)
    z0, zc = p["com_height_m"], p["crouch_height_m"]
    fault, t0 = case.get("fault"), case["fault_onset_s"]

    w_s = 2 * math.pi / p["sway_period_s"]

    def x_ref_single(z, t):
        return case["stride_offset_m"] + p["slope_lean"] * z * math.tan(th) + p["sway_amplitude_m"] * math.sin(w_s * t)

    x, vx = initial_state(case, p, z0)
    z, vz = z0, 0.0
    phase, stop_t, lock_t, alarm_t, low_since = "single", None, None, None, None
    frozen = None
    stop_reason = None
    ev = {"alarm_t": None, "stop_t": None, "lock_t": None, "mishap_t": None, "impact_speed": 0.0}
    rho_tip = float("inf")
    outcome = "safe"
    trace, next_trace, t = [], 0.0, 0.0
    steps = int(round(p["horizon_s"] / dt))
    for _ in range(steps + 1):
        c = capacity(case, p, t)
        # ---- monitoring, alarm, pilot, protective stop
        if fault in ("FLT-01", "FLT-04") and alarm_t is None and c < p["low_supply_alarm"]:
            alarm_t = t
            ev["alarm_t"] = round(t, 3)
        if stop_t is None:
            if alarm_t is not None and case["pilot_reaction_s"] is not None and t >= alarm_t + case["pilot_reaction_s"]:
                stop_t, stop_reason = t, "pilot"
            elif case.get("stop_request_s") is not None and fault != "FLT-03" and t >= case["stop_request_s"]:
                stop_t, stop_reason = t, "pilot"
            elif fault == "FLT-03" and t >= t0:
                stop_t, stop_reason = t, "faulty"
            elif fault == "FLT-02" and case["monitor"] and t >= t0 + p["monitor_detect_s"]:
                stop_t, stop_reason = t, "monitor"
            if stop_t is not None:
                ev["stop_t"] = round(t, 3)
                if stop_reason in ("pilot", "monitor"):
                    phase = "stepping"
        if phase == "stepping" and stop_t is not None and t >= stop_t + p["step_time_s"]:
            phase = "double"
        # load holding
        if lock_t is None and case["load_holding"] == "works":
            if c < p["lock_threshold"]:
                low_since = t if low_since is None else low_since
                if t >= low_since + p["lock_delay_s"]:
                    lock_t = t
            elif stop_reason == "monitor":
                lock_t = t   # monitor-commanded hold: balance feedback cannot be trusted
            if lock_t is not None:
                ev["lock_t"] = round(t, 3)
        L_geom = stance if phase == "double" else foot
        omega = math.sqrt(g / max(z, 0.1))
        xi = x + vx / omega
        # ---- horizontal
        if lock_t is not None:
            L_eff = L_geom
            if abs(xi) <= L_geom:
                vx = 0.0
                ax = 0.0
            else:
                ax = omega ** 2 * (x - math.copysign(L_geom, xi))
        else:
            L_eff = L_geom * c
            x_ref = x_ref_single(z, t) if phase == "single" else 0.0
            if fault == "FLT-02" and t >= t0:
                frozen = frozen or (x, vx)
                xm, vxm = frozen
            else:
                xm, vxm = x, vx
            if stop_reason == "faulty":
                pz = 0.0
            else:
                xim = xm + vxm / omega
                pz = xim + p["balance_gain"] * (xim - x_ref)
            pz = max(-L_eff, min(L_eff, pz))
            ax = omega ** 2 * (x - pz)
        rho_tip = min(rho_tip, (L_eff - abs(xi)) / p["foot_half_length_m"])
        # ---- vertical
        if lock_t is not None:
            az, vz = 0.0, 0.0
        else:
            z_ref = z0
            if phase == "double":
                z_ref = max(zc, z0 - p["crouch_rate_mps"] * (t - (stop_t + p["step_time_s"])))
            f_cmd = m * (g + p["height_kp"] * (z_ref - z) - p["height_kd"] * vz)
            f_max = p["leg_force_ratio"] * m * g * c
            force = 0.0 if stop_reason == "faulty" else max(0.0, min(f_cmd, f_max))
            az = force / m - g
        # ---- integrate (semi-implicit Euler)
        vx += ax * dt
        x += vx * dt
        vz += az * dt
        z += vz * dt
        if z <= zc and vz < 0:
            ev["impact_speed"] = max(ev["impact_speed"], round(-vz, 3))
            if -vz > p["safe_drop_speed_mps"] and outcome == "safe":
                outcome, ev["mishap_t"] = "hard-drop", round(t, 3)
            z, vz = zc, 0.0
        if t >= next_trace - 1e-9:
            trace.append([round(t, 3), round(x, 4), round(z, 4), round(c, 4), phase, stop_t is not None, lock_t is not None])
            next_trace += trace_every
        if abs(x) > p["tip_offset_m"] and outcome == "safe":
            outcome, ev["mishap_t"] = "tip", round(t, 3)
        if outcome != "safe":
            trace.append([round(t, 3), round(x, 4), round(z, 4), round(c, 4), phase, stop_t is not None, lock_t is not None])
            break
        t += dt
    rho_drop = (p["safe_drop_speed_mps"] - ev["impact_speed"]) / p["safe_drop_speed_mps"]
    rho = min(rho_tip, rho_drop)
    if outcome == "tip":
        rho = min(rho, -0.01)
    return {"outcome": outcome, "rho": round(rho, 4), "rho_tip": round(rho_tip, 4), "rho_drop": round(rho_drop, 4),
            "stop_active": stop_t is not None, "stop_reason": stop_reason, "events": ev, "trace": trace,
            "case": case}
