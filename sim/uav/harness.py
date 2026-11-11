"""Run the SUS-A1 failsafe scenarios on PX4 SITL (SIH quadrotor, headless) and record the results.

Usage:
  python -m sim.uav.harness --px4 PX4_DIR [--only SU-01] [--compare]

PX4_DIR is a PX4-Autopilot checkout at the pinned tag (sim/uav/fetch_px4.sh) with `make px4_sitl_default` built.
Writes sim/results/uav/SU-xx.json. With --compare it writes nothing and fails if a scenario's outcome class
differs from the committed result (SITL runs are not bit-reproducible, so numbers are compared with tolerances).

Positions are simulator ground truth (HIL_STATE_QUATERNION); the trace also keeps the estimator's
position error. The harness is the ground station: it sends GCS heartbeats, sets parameters, arms, takes off, flies to the
observation point and injects the scenario's fault. It does not implement the integration manager; the
scenarios show what PX4's own failsafes do when no integration manager permit exists (IF-PX4-005/006).
Needs pymavlink (sim/uav/requirements.txt). Results are synthetic, no evidence credit (sim/README.md).
"""
from __future__ import annotations

import argparse
import math
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from sim.common import ABOUT, ROOT, SIM, dumps
from sim.plant.spec import check as check_spec
from tools.pdac.load import _read_yaml

PX4_TAG = "v1.16.2"
SPEC = SIM / "uav" / "spec.yaml"
SCENARIOS = SIM / "uav" / "scenarios.yaml"
OUT = ROOT / "sim" / "results" / "uav"
MAIN = {1: "MANUAL", 2: "ALTCTL", 3: "POSCTL", 4: "AUTO", 5: "ACRO", 6: "OFFBOARD", 7: "STABILIZED"}
AUTO = {1: "READY", 2: "TAKEOFF", 3: "LOITER", 4: "MISSION", 5: "RTL", 6: "LAND", 9: "PRECLAND"}
EARTH_R = 6378137.0
HORIZON_S = 150.0        # simulated seconds after the injection
SETTLE_S = 6.0           # simulated seconds to hold at the observation point before injecting


def mode_name(custom_mode: int) -> str:
    main = (custom_mode >> 16) & 0xFF
    sub = (custom_mode >> 24) & 0xFF
    if main == 4:
        return "AUTO." + AUTO.get(sub, str(sub))
    return MAIN.get(main, str(main))


def offset_latlon(lat: float, lon: float, n: float, e: float) -> tuple[float, float]:
    dlat = n / EARTH_R
    dlon = e / (EARTH_R * math.cos(math.radians(lat)))
    return lat + math.degrees(dlat), lon + math.degrees(dlon)


def latlon_offset(lat0: float, lon0: float, lat: float, lon: float) -> tuple[float, float]:
    n = math.radians(lat - lat0) * EARTH_R
    e = math.radians(lon - lon0) * EARTH_R * math.cos(math.radians(lat0))
    return n, e


class Sitl:
    """One PX4 SITL process in a fresh working directory."""

    def __init__(self, px4: Path, speed: float):
        self.px4, self.speed = px4, speed
        self.dir = Path(tempfile.mkdtemp(prefix="susanoo-px4-"))
        build = px4 / "build" / "px4_sitl_default"
        env = dict(os.environ, PX4_SIM_MODEL="sihsim_quadx", PX4_SIMULATOR="sihsim", HEADLESS="1",
                   PX4_SIM_SPEED_FACTOR=str(speed))
        self.log = open(self.dir / "px4.log", "w")
        self.proc = subprocess.Popen([str(build / "bin" / "px4"), "-d", str(build / "etc")], cwd=self.dir, env=env,
                                     stdout=self.log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL)

    def close(self):
        self.proc.terminate()
        try:
            self.proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.proc.kill()
        self.log.close()
        shutil.rmtree(self.dir, ignore_errors=True)


class Gcs:
    def __init__(self, speed: float):
        from pymavlink import mavutil
        self.mavutil = mavutil
        self.m = mavutil.mavlink_connection("udpin:127.0.0.1:14550", source_system=255, source_component=190)
        self.speed = speed
        self.link_up = True
        self.last_hb = 0.0
        self.t = 0.0                 # simulated seconds since boot (from time_boot_ms)
        self.pos = None              # (n, e, d)
        self.mode = "?"
        self.armed = False
        self.landed = None
        self.texts: list = []
        self.trace: list = []
        self.home = None
        self.truth = None            # simulator ground truth (lat, lon, alt AMSL) from HIL_STATE_QUATERNION

    def heartbeat(self):
        if self.link_up and time.monotonic() - self.last_hb > 0.2:
            self.m.mav.heartbeat_send(6, 8, 0, 0, 0)    # MAV_TYPE_GCS, MAV_AUTOPILOT_INVALID
            self.last_hb = time.monotonic()

    def pump(self, wall_s: float = 0.05):
        end = time.monotonic() + wall_s
        while time.monotonic() < end:
            self.heartbeat()
            msg = self.m.recv_match(blocking=True, timeout=0.02)
            if msg is None:
                continue
            k = msg.get_type()
            if hasattr(msg, "time_boot_ms"):
                self.t = msg.time_boot_ms / 1000.0
            if k == "HEARTBEAT" and msg.get_srcComponent() == 1:
                self.mode = mode_name(msg.custom_mode)
                self.armed = bool(msg.base_mode & 128)
            elif k == "LOCAL_POSITION_NED":
                self.pos = (msg.x, msg.y, msg.z)
            elif k == "EXTENDED_SYS_STATE":
                self.landed = msg.landed_state
            elif k == "STATUSTEXT":
                self.texts.append([round(self.t, 1), msg.text])
            elif k == "HIL_STATE_QUATERNION":
                self.truth = (msg.lat / 1e7, msg.lon / 1e7, msg.alt / 1000.0)
            elif k == "HOME_POSITION":
                self.home = (msg.latitude / 1e7, msg.longitude / 1e7, msg.altitude / 1000.0)

    def wait(self, cond, sim_timeout: float, what: str):
        t0 = self.t
        wall_end = time.monotonic() + sim_timeout / max(self.speed, 1) * 3 + 30
        while not cond():
            self.pump()
            if self.t - t0 > sim_timeout or time.monotonic() > wall_end:
                raise TimeoutError(f"timed out waiting for {what} (mode {self.mode}, t {self.t:.1f})")

    def _param_value(self, name: str, timeout: float = 1.5):
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            self.heartbeat()
            got = self.m.recv_match(type="PARAM_VALUE", blocking=True, timeout=0.2)
            if got and got.param_id == name:
                return got
        return None

    def param(self, name: str, value: float):
        """Set a parameter with the type PX4 reports for it (PX4 uses the MAVLink bytewise encoding for INT32)."""
        import struct
        ptype = None
        for _ in range(5):
            self.m.mav.param_request_read_send(1, 1, name.encode(), -1)
            got = self._param_value(name)
            if got:
                ptype = got.param_type
                break
        if ptype is None:
            raise RuntimeError(f"parameter {name} not found")
        raw = struct.unpack("<f", struct.pack("<i", int(value)))[0] if ptype == 6 else float(value)
        for _ in range(5):
            self.m.mav.param_set_send(1, 1, name.encode(), raw, ptype)
            got = self._param_value(name)
            if got:
                return
        raise RuntimeError(f"parameter {name} not acknowledged")

    def command(self, cmd: int, *p, tries: int = 1):
        p = list(p) + [0] * (7 - len(p))
        for _ in range(tries):
            self.m.mav.command_long_send(1, 1, cmd, 0, *p)
            ack = self.m.recv_match(type="COMMAND_ACK", blocking=True, timeout=1.5)
            if ack and ack.command == cmd and ack.result == 0:
                return True
            self.pump(0.5)
        return False


def run_scenario(px4: Path, sc: dict, spec: dict) -> dict:
    speed = spec["sim_speed_factor"]
    sitl = Sitl(px4, speed)
    try:
        g = Gcs(speed)
        g.wait(lambda: g.pos is not None and g.t > 3, 60, "PX4 boot and position")
        g.command(512, 242, tries=3)                    # MAV_CMD_REQUEST_MESSAGE HOME_POSITION
        g.command(511, 115, 100000, tries=3)            # SET_MESSAGE_INTERVAL HIL_STATE_QUATERNION (truth) 10 Hz
        params = {"COM_DL_LOSS_T": spec["link_loss_timeout_s"], "SYS_FAILURE_EN": 1, "COM_RC_IN_MODE": 4,
                  "NAV_RCL_ACT": 0, "GF_MAX_HOR_DIST": spec["geofence_radius_m"], **sc["params"]}
        for k, v in params.items():
            g.param(k, v)
        g.wait(lambda: g.home is not None, 60, "home position")
        g.wait(lambda: g.truth is not None, 30, "simulator ground truth stream")
        # arm (retry until estimator and preflight checks pass), take off, fly to the observation point
        armed_ok = False
        for _ in range(60):
            if g.command(400, 1, tries=1):              # MAV_CMD_COMPONENT_ARM_DISARM
                armed_ok = True
                break
            g.pump(1.0)
        if not armed_ok:
            raise RuntimeError("could not arm: " + "; ".join(t[1] for t in g.texts[-5:]))
        g.command(22, 0, 0, 0, float("nan"), float("nan"), float("nan"), g.home[2] + spec["observe_alt_m"], tries=5)  # NAV_TAKEOFF (AMSL)
        g.wait(lambda: g.pos and -g.pos[2] > spec["observe_alt_m"] - 2, 60, "take-off")
        lat, lon = offset_latlon(g.home[0], g.home[1], spec["observe_n_m"], spec["observe_e_m"])
        g.command(192, -1, 1, 0, float("nan"), lat, lon, g.home[2] + spec["observe_alt_m"], tries=5)   # DO_REPOSITION
        target = (spec["observe_n_m"], spec["observe_e_m"])
        g.wait(lambda: g.pos and math.dist(g.pos[:2], target) < 2.0, 120, "arrival at the observation point")
        t_arrive = g.t
        g.wait(lambda: g.t > t_arrive + SETTLE_S, 30, "settle")
        # inject
        inj = sc["inject"]
        t_inj = g.t
        if "link_loss_at_s" in inj:
            g.link_up = False
        elif "failure" in inj:
            unit = {"gps": 4, "battery": 100}[inj["failure"]["unit"]]
            ftype = {"off": 1}[inj["failure"]["type"]]
            if not g.command(420, unit, ftype, 0, tries=5):     # MAV_CMD_INJECT_FAILURE
                raise RuntimeError("failure injection rejected")
        elif "set_params" in inj:
            for k, v in inj["set_params"].items():
                g.param(k, v)
        elif "reposition_beyond_fence_at_s" in inj:
            r = 1.6 * spec["geofence_radius_m"]
            la, lo = offset_latlon(g.home[0], g.home[1], r, 0.0)
            g.command(192, -1, 1, 0, float("nan"), la, lo, g.home[2] + spec["observe_alt_m"], tries=5)
        # record until landed and disarmed, or the horizon
        t_end = t_inj + HORIZON_S
        last = -1.0
        while g.t < t_end:
            g.pump(0.1)
            if g.truth and g.t - last >= 0.5:
                n, e = latlon_offset(g.home[0], g.home[1], g.truth[0], g.truth[1])
                est = math.dist(g.pos[:2], (n, e)) if g.pos else None
                g.trace.append([round(g.t - t_inj, 1), round(n, 2), round(e, 2), round(g.truth[2] - g.home[2], 2), g.mode,
                                None if est is None else round(est, 2)])
                last = g.t
            if not g.armed and g.t > t_inj + 2:
                break
        return {"trace": g.trace, "texts": [[round(t - t_inj, 1), s] for t, s in g.texts],
                "params": params, "final_armed": g.armed}
    finally:
        sitl.close()


def score(sc: dict, spec: dict, raw: dict) -> dict:
    moved = spec["walker_moved_n_m"] if sc["walker_moved"] else 0.0
    dock = (moved, 0.0)
    pilot = (spec["pilot_station_n_m"] + moved, spec["pilot_station_e_m"])
    tr = raw["trace"]
    low = [p for p in tr if p[3] < spec["keepout_alt_m"]]
    min_pilot = min((math.dist(p[1:3], pilot) for p in low), default=None)
    end = tr[-1] if tr else None
    modes, first_fs = [], None
    for p in tr:
        if not modes or modes[-1][1] != p[4]:
            modes.append([p[0], p[4]])
            if first_fs is None and p[0] > 0 and p[4] != "AUTO.LOITER":
                first_fs = [p[0], p[4]]
    max_r = max((math.hypot(p[1], p[2]) for p in tr), default=0.0)
    landed = end is not None and not raw["final_armed"]   # PX4 auto-disarms after land detection
    if min_pilot is not None and min_pilot < spec["pilot_keepout_m"]:
        outcome = "keepout-breach"
    elif landed and math.dist(end[1:3], dock) > 5.0 and sc["walker_moved"]:
        outcome = "landed-at-stale-home"
    elif max_r > spec["geofence_radius_m"] + 2.0:
        outcome = "geofence-overshoot"
    elif landed:
        outcome = "landed-clear"
    elif "reposition_beyond_fence_at_s" in sc["inject"]:
        outcome = "contained"
    else:
        outcome = "airborne-at-horizon"
    return {"outcome": outcome, "first_failsafe": first_fs, "mode_changes": modes,
            "min_pilot_distance_low_m": None if min_pilot is None else round(min_pilot, 2),
            "landing_point_m": None if not landed else [end[1], end[2]],
            "landing_to_dock_m": None if not landed else round(math.dist(end[1:3], dock), 2),
            "landing_to_pilot_m": None if not landed else round(math.dist(end[1:3], pilot), 2),
            "max_distance_from_home_m": round(max_r, 2), "dock_m": list(dock), "pilot_m": list(pilot),
            "max_estimate_error_m": max((p[5] for p in tr if p[5] is not None), default=None)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--px4", required=True, type=Path)
    ap.add_argument("--only")
    ap.add_argument("--compare", action="store_true")
    a = ap.parse_args(argv)
    spec = check_spec(_read_yaml(SPEC))
    tag = subprocess.run(["git", "describe", "--tags", "--always"], cwd=a.px4, capture_output=True, text=True).stdout.strip()
    if tag != PX4_TAG:
        print(f"PX4 checkout is {tag!r}; the harness is pinned to {PX4_TAG}")
        return 1
    OUT.mkdir(parents=True, exist_ok=True)
    bad = 0
    for sc in _read_yaml(SCENARIOS)["scenarios"]:
        if a.only and sc["id"] != a.only:
            continue
        t0 = time.monotonic()
        raw = run_scenario(a.px4, sc, spec)
        res = {"about": ABOUT, "scenario": sc, "px4": PX4_TAG, "simulator": "PX4 SITL SIH sihsim_quadx (headless, lockstep)",
               "speed_factor": spec["sim_speed_factor"], **score(sc, spec, raw), "trace": raw["trace"], "statustext": raw["texts"],
               "params_set": raw["params"]}
        path = OUT / f"{sc['id']}.json"
        print(f"{sc['id']}: {res['outcome']} (first failsafe {res['first_failsafe']}, min pilot distance "
              f"{res['min_pilot_distance_low_m']}) in {time.monotonic() - t0:.0f} s")
        if a.compare:
            old = _read_json(path)
            if old is None or old["outcome"] != res["outcome"]:
                print(f"  DIFFERS from committed outcome {old and old['outcome']}")
                bad += 1
        else:
            path.write_text(dumps(res), encoding="utf-8")
    return 1 if bad else 0


def _read_json(path: Path):
    import json
    return json.loads(path.read_text()) if path.exists() else None


if __name__ == "__main__":
    sys.exit(main())
