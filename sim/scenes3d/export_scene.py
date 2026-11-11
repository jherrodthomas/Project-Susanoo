"""Export the analysis of every 3D scene to sim/scenes3d/out/<id>.json.

Usage: python -m sim.scenes3d.export_scene [--check]

Reads only each scene's `motion` block (and its id, hazards and title) plus the records it names: plant runs from
sim/plant/walker.py, search edge cases from sim/results/search-*.json, SITL results from sim/results/uav/*.json.
It never reads `look` or `variants` (rule: the look never changes the analysis; checked by test_scenes3d.py).
Frames are downsampled to 10 Hz. Synthetic, no evidence credit.
"""
from __future__ import annotations

import argparse
import json
import sys

from sim.common import ABOUT, ROOT, SIM, dumps, write_or_check
from sim.figures.scenes import cases as plant_cases
from sim.plant import spec as plant_spec
from sim.plant import walker
from sim.plant.spec import check as check_spec
from tools.pdac.load import _read_yaml

SCENES = SIM / "scenes3d" / "scenes.yaml"
ANALYSIS_KEYS = ("id", "hazards", "title", "motion")


class SceneError(Exception):
    pass


def analysis_view(sc: dict) -> dict:
    """The only part of a scene the exporter may read."""
    return {k: sc[k] for k in ANALYSIS_KEYS}


def walker_frames(trace: list, step: float = 0.1) -> list:
    out, nxt = [], 0.0
    for f in trace:
        if f[0] >= nxt - 1e-9 or f is trace[-1]:
            out.append([f[0], f[1], f[2], f[4], f[5], f[6]])     # t, x, z, phase, stop, hold
            nxt = f[0] + step
    return out


def export(sc: dict) -> dict:
    a = analysis_view(sc)
    m = a["motion"]
    base = {"about": ABOUT, "id": a["id"], "hazards": a["hazards"], "title": a["title"], "source": m["source"]}
    if m["source"] in ("plant", "edge"):
        p = plant_spec.load()
        if m["source"] == "edge":
            perf_case, int_case = plant_cases({"edge": (m["family"], m["edge_case"]), **({"intended_over": m["intended_over"]}
                                                                                          if "intended_over" in m else {})})
            ref = f"{m['family']} {m['edge_case']}"
        else:
            perf_case, int_case = m["performed"], m["intended"]
            ref = f"fault {m['performed'].get('fault')}"
        perf, intd = walker.simulate(perf_case, p), walker.simulate(int_case, p)
        keys = ("com_height_m", "crouch_height_m", "foot_half_length_m", "stance_half_length_m", "tip_offset_m", "safe_drop_speed_mps")
        return {**base, "kind": "walker", "reference": ref, "slope_deg": perf["case"]["slope_deg"],
                "spec": {k: p[k] for k in keys}, "spec_digest": plant_spec.digest(),
                "performed": {"case": perf["case"], "outcome": perf["outcome"], "events": perf["events"],
                              "frames": walker_frames(perf["trace"])},
                "intended": {"case": intd["case"], "outcome": intd["outcome"], "events": intd["events"],
                             "frames": walker_frames(intd["trace"])}}
    if m["source"] == "sitl":
        path = ROOT / "sim" / "results" / "uav" / f"{m['scenario']}.json"
        if not path.exists():
            raise SceneError(f"{a['id']}: {path} missing")
        r = json.loads(path.read_text())
        s = check_spec(_read_yaml(SIM / "uav" / "spec.yaml"))
        return {**base, "kind": "uav", "reference": m["scenario"], "px4": r["px4"], "outcome": r["outcome"],
                "dock_m": r["dock_m"], "pilot_m": r["pilot_m"], "walker_moved": r["scenario"]["walker_moved"],
                "keepout_m": s["pilot_keepout_m"], "keepout_alt_m": s["keepout_alt_m"], "geofence_m": s["geofence_radius_m"],
                "observe_m": [s["observe_n_m"], s["observe_e_m"], s["observe_alt_m"]],
                "min_pilot_distance_low_m": r["min_pilot_distance_low_m"], "landing_to_dock_m": r["landing_to_dock_m"],
                "mode_changes": r["mode_changes"], "frames": [p[:5] for p in r["trace"]]}
    raise SceneError(f"{a['id']}: unknown motion source {m['source']!r}")


def load() -> dict:
    return _read_yaml(SCENES)


def outputs(cfg: dict | None = None) -> dict:
    cfg = cfg or load()
    seen = set()
    outs = {}
    for sc in cfg["scenes"]:
        ids = [sc["id"]] + [v["id"] for v in sc.get("variants") or []]
        for i in ids:
            if i in seen:
                raise SceneError(f"duplicate scene id {i}")
            seen.add(i)
        outs[f"sim/scenes3d/out/{sc['id']}.json"] = dumps(export(sc))
    return outs


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    return write_or_check(outputs(), a.check, "python -m sim.scenes3d.export_scene")


if __name__ == "__main__":
    sys.exit(main())
