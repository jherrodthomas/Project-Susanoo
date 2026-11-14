"""Build the interactive general-arrangement sheets: docs/3d/SUS-M1.html (1), SUS-A1.html (2) and SUS-M1-terrain.html (3).

Usage: python -m sim.scenes3d.build_sheet [--check]

Sheet 2 (sim/scenes3d/sheet_uav.yaml, viewer sheet_uav.js) shows SUS-A1 on the CL-05 dock, with the dock and UAV
figures of cad/params and cad/metrics.json, the UAV hazards and interfaces, and the PX4 SITL results of
sim/results/uav/ replayed in an airspace view with the geofence and pilot keep-out of sim/uav/spec.yaml.

Sheet 3 (sim/scenes3d/terrain.yaml, viewer sheet_terrain.js) walks the CL-05 gait over the terrain course posed by
tools/cad/b3d/cl05_terrain.py, with that export's kinematic findings, the static tip margin of cad/metrics.json on each
slope (frozen posture, and with the gait's lean compensation of sim/spec/walker.yaml) and the SYS-008 slope limit. Its
loaded mode walks the loaded gait carrying the placeholder load (cl05_terrain.py --loaded), with the carry posture's
margin for a load mass the viewer sets (the CAD's margin-peak, 0.30 m flag and tip-over masses marked), SYS-019 and
HAZ-MAN-002. Its physics model replays the level-2 MuJoCo runs of the same walk (sim/mujoco/terrain.py,
docs/3d/assets/sus-m1-terrain-physics.js) with their outcomes, attribution and torque use.

Sheet 1:

One page with a live three.js model of the CL-05 reference layout (docs/3d/assets/sus-m1.js, exported from the
build123d CAD by tools/cad/b3d/cl05_web.py), animated through the layout's postures and walk cycle. The page shows
the concept metrics of cad/metrics.json, the hazard records of safety/hazards/ with callouts on the parts they
concern (sim/scenes3d/sheet.yaml), a static tip-margin check from the same metrics, and the walker scenes of
sim/scenes3d/out/ as plots linked to their own 3D pages. Everything on it is concept geometry or synthetic
simulation output: a design aid with no evidence credit. Viewer code: sim/scenes3d/sheet.js.
"""
from __future__ import annotations

import argparse
import ast
import html
import json
import re
import sys

from sim.common import ABOUT, ROOT, SIM, write_or_check
from sim.scenes3d.export_scene import load as load_scenes
from tools.pdac.load import _read_yaml
from tools.terms.terms import expand, find, label, load as load_terms

CDN = "https://cdn.jsdelivr.net/npm/three@{v}/"
OUT = "docs/3d/SUS-M1.html"
OUT_UAV = "docs/3d/SUS-A1.html"
OUT_TERRAIN = "docs/3d/SUS-M1-terrain.html"
TERRAIN = ROOT / "docs/3d/assets/sus-m1-terrain.js"
TERRAIN_LOADED = ROOT / "docs/3d/assets/sus-m1-terrain-loaded.js"
TERRAIN_PHYSICS = ROOT / "docs/3d/assets/sus-m1-terrain-physics.js"
GEOMETRY = ROOT / "docs/3d/assets/sus-m1.js"


def class_colours() -> dict:
    """Part class -> [colour, opacity] from the CLASSES table of tools/cad/build_concepts.py (read, not imported:
    that module needs FreeCAD)."""
    tree = ast.parse((ROOT / "tools/cad/build_concepts.py").read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(getattr(t, "id", None) == "CLASSES" for t in node.targets):
            return {k: [v[0], v[1]] for k, v in ast.literal_eval(node.value).items()}
    raise ValueError("CLASSES not found in tools/cad/build_concepts.py")


def cad_constant(name: str):
    """A module-level literal of tools/cad/build_concepts.py (read, not imported: that module needs FreeCAD)."""
    tree = ast.parse((ROOT / "tools/cad/build_concepts.py").read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(getattr(t, "id", None) == name for t in node.targets):
            return ast.literal_eval(node.value)
    raise ValueError(f"{name} not found in tools/cad/build_concepts.py")


def cad_revision() -> str:
    m = re.search(r"\*\*Revision:\*\*\s*([^\s·]+)", (ROOT / "cad/README.md").read_text(encoding="utf-8"))
    return m.group(1) if m else "draft"


METRIC_KEYS = ["envelope_m", "height_m", "hip_height_m", "cockpit_floor_m", "pilot_eye_m", "placeholder_mass_kg", "cg_m",
               "support_polygon_m", "static_margin_m", "static_tip_angle_deg", "rotor_to_pilot_m", "egress_sill_m",
               "arm_ground_clearance_m"]


def metrics(layout: str) -> dict:
    """Standing metrics and each analysed posture of the layout, as cad/metrics.json gives them."""
    m = json.loads((ROOT / "cad/metrics.json").read_text())["concepts"][layout]
    out = {"standing": {k: m[k] for k in METRIC_KEYS if k in m}}
    for name, pm in (m.get("postures") or {}).items():
        out[name] = {k: pm[k] for k in METRIC_KEYS if k in pm}
    return {"title": m["title"], "postures": out}


def hazards() -> list[dict]:
    out = []
    for path in sorted((ROOT / "safety/hazards").glob("HAZ-*.yaml")):
        h = _read_yaml(path)
        ir = h.get("initial_risk") or {}
        out.append({"id": h["id"], "title": h["title"], "status": h["status"], "rac": ir.get("rac"),
                    "level": ir.get("risk_level"), "subsystems": h.get("subsystems") or []})
    return out


def replay(ids: list[str]) -> list[dict]:
    out = []
    for sid in ids:
        a = json.loads((ROOT / f"sim/scenes3d/out/{sid}.json").read_text())
        if a["kind"] != "walker":
            raise ValueError(f"{sid} is not a walker scene")
        out.append({k: a[k] for k in ("id", "title", "hazards", "reference", "slope_deg", "spec", "source")} |
                   {"performed": a["performed"], "intended": {k: a["intended"][k] for k in ("frames", "outcome")}})
    return out


def terms_line(data: dict, extra: list[str] | None = None) -> str:
    shown = [data["sheet"]["document"], data["sheet"]["id"], "SUS-M1 SUS-A1 CAD CG UAV RAC I0 SYS-017",
             *(h["id"] for h in data["hazards"]), *(r["id"] + " " + r.get("reference", "") for r in data["replay"]), *(extra or [])]
    keys = expand(find(" ".join(shown))[0])
    defs, _ = load_terms()
    return "Terms: " + " · ".join(f"{html.escape(label(k))} = {html.escape(defs[k])}"
                                  for k in sorted(keys, key=lambda q: label(q).lower()))


PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<!-- GENERATED by sim/scenes3d/build_sheet.py from sim/scenes3d/sheet.yaml, cad/metrics.json, safety/hazards and
     sim/scenes3d/out. Do not edit by hand. -->
<title>{title}</title>
<style>
{css}
</style>
<script type="importmap">{{"imports":{{"three":"{cdn}build/three.module.min.js","three/addons/":"{cdn}examples/jsm/"}}}}</script>
</head><body>
{body}
<div id="terms">{terms}</div>
<script>window.SHEET = {data};</script>
<script src="assets/sus-m1.js"></script>
<script type="module">
{viewer}
</script>
</body></html>
"""


def uav_data(cfg: dict, layout: str) -> dict:
    """Sheet 2: SUS-A1 elements and interfaces, the docked quadrotor's placeholder geometry, dock clearances, the
    SITL spec and results, and the findings the scenario rules attach to each outcome."""
    item = _read_yaml(ROOT / "architecture/item-definition.yaml")
    elements = [{"id": e["id"], "name": e["name"]} for e in item["elements"] if e["id"] == "SUS-A1" or e.get("parent") == "SUS-A1"]
    a1 = {e["id"] for e in elements} | {"SUS-M1-DCK"}
    uavh = set(cfg["anchors"])
    ifs = [{k: f.get(k) for k in ("id", "name", "from", "to", "exchange", "hazard_ids")} for f in item["interfaces"]
           if (f["from"] in a1 or f["to"] in a1 or set(f.get("hazard_ids") or []) & uavh) and (f["from"] in a1 or f["to"] in a1)]
    common = _read_yaml(ROOT / "cad/params/common.yaml")
    m = json.loads((ROOT / "cad/metrics.json").read_text())["concepts"][layout]
    spec = _read_yaml(SIM / "uav" / "spec.yaml")
    rules = _read_yaml(SIM / "uav" / "scenarios.yaml")
    runs = []
    for sid in cfg["replay"]:
        r = json.loads((ROOT / f"sim/results/uav/{sid}.json").read_text())
        finding = next((x for x in rules["outcome_rules"] if x["outcome"] == r["outcome"]), {})
        metric = [x for x in rules.get("metric_rules") or [] if (r.get(x["metric"]) or 0) > x["above"]]
        runs.append({"id": sid, "title": r["scenario"]["title"], "hazards": r["scenario"]["hazards"], "inject": r["scenario"]["inject"],
                     "contract": r["scenario"]["contract"], "walker_moved": r["scenario"]["walker_moved"], "params": r["params_set"],
                     "dock_m": r["dock_m"], "pilot_m": r["pilot_m"], "outcome": r["outcome"], "first_failsafe": r["first_failsafe"],
                     "landing_point_m": r["landing_point_m"], "landing_to_pilot_m": r["landing_to_pilot_m"],
                     "min_pilot_distance_low_m": r["min_pilot_distance_low_m"], "max_estimate_error_m": r["max_estimate_error_m"],
                     "mode_changes": r["mode_changes"], "trace": [t[:6] for t in r["trace"]], "px4": r["px4"], "simulator": r["simulator"],
                     "finding": finding.get("finding"), "metric_findings": [x["finding"] for x in metric]})
    return {"elements": elements, "interfaces": ifs, "uav": common["uav"],
            "dock": {k: m[k] for k in ("rotor_to_pilot_m", "rotor_to_structure_m")},
            "spec": {k: {"value": v["value"], "unit": v["unit"], "source": v["source"]} for k, v in spec["params"].items()},
            "spec_id": spec["id"], "runs": runs}


def outputs() -> dict:
    return {**sheet1(), **sheet2(), **sheet3()}


def _inside(pt, poly) -> bool:
    c = False
    for i in range(len(poly)):
        (xi, yi), (xj, yj) = poly[i], poly[i - 1]
        if (yi > pt[1]) != (yj > pt[1]) and pt[0] < (xj - xi) * (pt[1] - yi) / (yj - yi) + xi:
            c = not c
    return c


def _edge(pt, poly) -> float:
    d = 1e9
    for i in range(len(poly)):
        (ax, ay), (bx, by) = poly[i - 1], poly[i]
        dx, dy = bx - ax, by - ay
        t = max(0.0, min(1.0, ((pt[0] - ax) * dx + (pt[1] - ay) * dy) / (dx * dx + dy * dy)))
        d = min(d, ((pt[0] - ax - t * dx) ** 2 + (pt[1] - ay - t * dy) ** 2) ** 0.5)
    return d


def static_margin(m: dict, pitch: float, roll: float, lean: float = 1.0) -> float:
    """Signed distance (m) from the support polygon's edge to the centre of gravity projected along gravity, for the
    standing CL-05 on ground pitched `pitch` (uphill +) and rolled `roll` (right side down +) degrees; `lean` is the
    share of the slope-induced shift left uncompensated. Inside > 0. Same geometry as cad/metrics.json."""
    import math
    cx, cy, cz = m["cg_m"]
    pt = (cx - lean * cz * math.tan(math.radians(pitch)), cy + lean * cz * math.tan(math.radians(roll)))
    d = _edge(pt, m["support_polygon_m"])
    return d if _inside(pt, m["support_polygon_m"]) else -d


def tip_angle(m: dict, sp: float, sr: float, lean: float = 1.0) -> float:
    """Slope angle (degrees) in the direction (sp, sr) at which the static margin reaches zero."""
    lo, hi = 0.0, 89.0
    for _ in range(60):
        mid = (lo + hi) / 2
        if static_margin(m, sp * mid, sr * mid, lean) > 0:
            lo = mid
        else:
            hi = mid
    return lo


def sheet3() -> dict:
    """Sheet 3: the CL-05 walk posed on the terrain course (sim/scenes3d/terrain.yaml, docs/3d/assets/sus-m1-terrain.js)."""
    import math
    course = _read_yaml(SIM / "scenes3d" / "terrain.yaml")
    mt = metrics("CL-05")["postures"]["standing"]
    walker = _read_yaml(SIM / "spec" / "walker.yaml")["params"]
    lean = walker["slope_lean"]
    req = _read_yaml(ROOT / "requirements/SYS-008.yaml")
    req19 = _read_yaml(ROOT / "requirements/SYS-019.yaml")
    allh = hazards()
    haz = next(h for h in allh if h["id"] == "HAZ-WLK-002")
    haz_load = next(h for h in allh if h["id"] == "HAZ-MAN-002")
    cm = json.loads((ROOT / "cad/metrics.json").read_text())["concepts"]["CL-05"]["postures"]["carry"]
    mc = metrics("CL-05")["postures"]["carry"]
    carry = {"cg_m": mc["cg_m"], "support_polygon_m": mc["support_polygon_m"], "mass_kg": cm["placeholder_mass_kg"],
             "load_centre_m": cm["carry_load_centre_m"], "load_envelope_m": cm["carry_load_envelope_m"],
             "peak": cm["carry_margin_peak"], "flag_kg": cm["carry_load_at_margin_flag_kg"], "tipover_kg": cm["carry_load_at_tipover_kg"],
             "flag_margin_m": cad_constant("FLAG_MARGIN")}

    def with_load(kg: float) -> dict:   # the carry posture's centre of gravity with a load of kg at the load centre
        M = carry["mass_kg"]
        return dict(mc, cg_m=[(M * c + kg * l) / (M + kg) for c, l in zip(mc["cg_m"], carry["load_centre_m"])])
    # reference values the page must reproduce (sheet_check.mjs): level ground with the CAD's margin-peak load
    carry["check"] = {"mass_kg": carry["peak"]["load_kg"], "level_margin_m": round(static_margin(with_load(carry["peak"]["load_kg"]), 0, 0), 4),
                      "up20_lean_margin_m": round(static_margin(with_load(carry["peak"]["load_kg"]), 20, 0, lean["value"]), 4)}
    rows = []
    for t in course["terrains"]:
        r = {k: t[k] for k in ("key", "label", "kind")} | {k: t[k] for k in ("note", "pitch_deg", "roll_deg", "run_m", "rise_m", "amp_m") if k in t}
        if t["kind"] == "plane":
            pitch, roll = t.get("pitch_deg", 0), t.get("roll_deg", 0)
            slope = math.hypot(pitch, roll)
            sp, sr = (pitch / slope, roll / slope) if slope else (1.0, 0.0)
            r["slope_deg"] = round(slope, 1)
            r["frozen_margin_m"] = round(static_margin(mt, pitch, roll), 3)
            r["frozen_tip_deg"] = round(tip_angle(mt, sp, sr), 1)
            r["lean_margin_m"] = round(static_margin(mt, pitch, roll, lean["value"]), 3)
            r["lean_tip_deg"] = round(tip_angle(mt, sp, sr, lean["value"]), 1)
        elif t["kind"] == "ledges":
            r["slope_deg"] = round(math.degrees(math.atan2(t["rise_m"], t["run_m"])), 1)   # average incline of the flight
        rows.append(r)
    data = {
        "sheet": {"id": course["id"], "document": "SUS-CAD-001-CL-05 · " + course["id"], "layout": "CL-05",
                  "title": "Terrain course, interactive", "sheet": "3 of 3", "revision": cad_revision()},
        "about": ABOUT, "classes": class_colours(), "terrains": rows, "standing": mt,
        "lean": {"value": lean["value"], "source": lean["source"]},
        "sys008": {"id": req["id"], "title": req["title"], "status": req["status"], "statement": " ".join(req["statement"].split()), "limit_deg": 20},
        "sys019": {"id": req19["id"], "title": req19["title"], "status": req19["status"], "statement": " ".join(req19["statement"].split()),
                   "tbd": req19.get("tbd") or []},
        "hazard": haz, "hazard_load": haz_load, "carry": carry, "replay": [], "hazards": [haz, haz_load],
    }
    extra = ["SYS-008 SYS-019 HAZ-WLK-002 HAZ-MAN-002 CG TBD MuJoCo", course["id"]]
    return {OUT_TERRAIN: page_html(data, "SUS-M1 terrain course", "sheet_terrain.body.html", "sheet_terrain.js",
                                   terms_line(data, extra)).replace('<script src="assets/sus-m1.js"></script>',
                                                                   '<script src="assets/sus-m1.js"></script>\n<script src="assets/sus-m1-terrain.js"></script>\n'
                                                                   '<script src="assets/sus-m1-terrain-loaded.js"></script>\n'
                                                                   '<script src="assets/sus-m1-terrain-physics.js"></script>')}


def page_html(data: dict, title: str, body: str, viewer: str, terms: str) -> str:
    version = load_scenes()["three"]["version"]
    d = SIM / "scenes3d"
    blob = json.dumps(data, sort_keys=True, separators=(",", ":")).replace("</", "<\\/")
    return PAGE.format(title=html.escape(title), css=(d / "sheet.css").read_text(encoding="utf-8").rstrip(), cdn=CDN.format(v=version),
                       body=(d / body).read_text(encoding="utf-8").rstrip(), terms=terms, data=blob,
                       viewer=(d / viewer).read_text(encoding="utf-8").rstrip())


SEQ_UAV = {"docked", "hover", "keepalt", "away"}


def sequence(steps: list[dict], data: dict) -> tuple[list[dict], dict]:
    """The launch and recovery sequence of sheet_uav.yaml, checked: every record it cites exists, and the states keep the
    interlocks the dock mitigations name. Returns the steps and the titles of the requirements they cite."""
    item = _read_yaml(ROOT / "architecture/item-definition.yaml")
    ifs = {f["id"] for f in item["interfaces"]}
    haz = {h["id"] for h in hazards()}
    reqs = {}
    for path in sorted((ROOT / "requirements").glob("SYS-*.yaml")):
        r = _read_yaml(path)
        reqs[r["id"]] = r["title"]
    conops = (ROOT / "concept/CONOPS.md").read_text(encoding="utf-8")
    cited = {}
    prev = None
    for i, st in enumerate(steps, 1):
        where = f"sheet_uav.yaml sequence step {i} ({st['title']})"
        if st["uav"] not in SEQ_UAV:
            raise ValueError(f"{where}: uav must be one of {sorted(SEQ_UAV)}")
        text = " ".join(st["gates"]) + " " + st["mode"]
        for tok in re.findall(r"\b(IF-PX4-\d{3}|IF-\d{3})\b", text):
            if tok not in ifs:
                raise ValueError(f"{where}: unknown interface {tok}")
        for tok in re.findall(r"\b(HAZ-[A-Z]{3}-\d{3})\b", text):
            if tok not in haz:
                raise ValueError(f"{where}: unknown hazard {tok}")
        for tok in re.findall(r"\b(SYS-\d{3})\b", text):
            if tok not in reqs:
                raise ValueError(f"{where}: unknown requirement {tok}")
            cited[tok] = reqs[tok]
        for tok in re.findall(r"\b((?:SCN|MOD)-\d{2,3})\b", text):
            if tok not in conops:
                raise ValueError(f"{where}: {tok} is not in concept/CONOPS.md")
        # interlocks named by the mitigations (HAZ-DCK-001 M1/M2, HAZ-DCK-004 M1/M3, IF-PX4-005)
        if st["rotors"] == "running" and st["latch"] != "open":
            raise ValueError(f"{where}: rotors running while latched (HAZ-DCK-001 M1, SYS-003)")
        if st["charging"] == "on" and (st["latch"] != "closed" or st["rotors"] != "inhibited"):
            raise ValueError(f"{where}: charging while not latched with rotors inhibited (HAZ-DCK-004 M3)")
        if st["uav"] != "docked" and (st["latch"] != "open" or st["rotors"] != "running"):
            raise ValueError(f"{where}: off the dock without the latch open and rotors running")
        if prev and prev["latch"] == "closed" and st["latch"] == "open" and (st["permit"] != "launch" or st["charging"] != "off"):
            raise ValueError(f"{where}: latch released without a launch permit and charging off (IF-PX4-005, HAZ-DCK-004 M1)")
        if prev and prev["rotors"] == "inhibited" and st["rotors"] == "running" and st["latch"] != "open":
            raise ValueError(f"{where}: rotors started while latched (HAZ-DCK-001 M2)")
        prev = st
    return steps, cited


def sheet2() -> dict:
    cfg = _read_yaml(SIM / "scenes3d" / "sheet_uav.yaml")
    allh = hazards()
    if set(cfg["anchors"]) - {h["id"] for h in allh}:
        raise ValueError(f"sheet_uav.yaml anchors name unknown hazards: {sorted(set(cfg['anchors']) - {h['id'] for h in allh})}")
    hz = [h for h in allh if "SUS-A1" in h["subsystems"] or h["id"] in cfg["anchors"]]
    data = {
        "sheet": {k: cfg[k] for k in ("id", "document", "layout", "title", "sheet")} | {"revision": cad_revision()},
        "about": ABOUT, "anchors": cfg["anchors"], "uav_scale_air": cfg["uav_scale_air"],
        "classes": class_colours(), "hazards": hz, **uav_data(cfg, cfg["layout"]),
    }
    data["replay"] = [{"id": r["id"]} for r in data["runs"]]
    data["sequence"], data["seq_requirements"] = sequence(cfg.get("sequence") or [], data)
    modes = sorted({m.replace("AUTO.", "") for r in data["runs"] for _, m in r["mode_changes"]})
    extra = ["PX4 SITL SIH NED GNSS RF ESC SCN-004 SCN-005 MOD-06 MOD-07 MOD-08", *data["seq_requirements"], data["spec_id"], *modes, *(e["id"] for e in data["elements"]),
             *(f["id"] for f in data["interfaces"]), *(f["from"] + " " + f["to"] for f in data["interfaces"])]
    return {OUT_UAV: page_html(data, "SUS-A1 on dock and in airspace", "sheet_uav.body.html", "sheet_uav.js", terms_line(data, extra))}


def sheet1() -> dict:
    cfg = _read_yaml(SIM / "scenes3d" / "sheet.yaml")
    data = {
        "sheet": {k: cfg[k] for k in ("id", "document", "layout", "title", "sheet")} | {"revision": cad_revision()},
        "about": ABOUT,
        "postures": cfg["postures"],
        "anchors": cfg["anchors"],
        "metrics": metrics(cfg["layout"]),
        "classes": class_colours(),
        "hazards": hazards(),
        "replay": replay(cfg["replay"]),
    }
    known = {h["id"] for h in data["hazards"]}
    if set(cfg["anchors"]) - known:
        raise ValueError(f"sheet.yaml anchors name unknown hazards: {sorted(set(cfg['anchors']) - known)}")
    return {OUT: page_html(data, "SUS-M1 general arrangement", "sheet.body.html", "sheet.js", terms_line(data))}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    if not GEOMETRY.exists() or not TERRAIN.exists() or not TERRAIN_LOADED.exists() or not TERRAIN_PHYSICS.exists():
        print("missing docs/3d/assets/sus-m1.js, sus-m1-terrain[-loaded].js or sus-m1-terrain-physics.js: run tools/cad/b3d/cl05_web.py and "
              "cl05_terrain.py [--loaded] (build123d environment), and python -m sim.mujoco.terrain", file=sys.stderr)
        return 1
    return write_or_check(outputs(), a.check, "python -m sim.scenes3d.build_sheet")


if __name__ == "__main__":
    sys.exit(main())
