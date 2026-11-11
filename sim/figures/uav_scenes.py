"""Top-down UAV failsafe scenes, results summary and wiki page from the committed PX4 SITL results.

Usage: python -m sim.figures.uav_scenes [--check]

Reads sim/results/uav/SU-*.json (written by sim/uav/harness.py on a PX4 SITL run) and writes:
  docs/wiki/images/sim-su-NN.svg   animated top-down scene: overview (fence, walker, path) + zoom on the dock
  sim/results/uav/summary.md       outcomes, metrics, hazard mapping and findings
  docs/wiki/UAV-Simulation.md      the wiki page
No PX4 needed, so pull-request CI can check these with --check. Synthetic, no evidence credit.
"""
from __future__ import annotations

import argparse
import json
import math
import sys

from sim.common import ABOUT, ROOT, write_or_check
from sim.plant.spec import check as check_spec
from tools.figures import figkit as fk
from tools.pdac.load import _read_yaml

UAV = ROOT / "sim" / "uav"
RES = ROOT / "sim" / "results" / "uav"
W, H = 1000, 560


def load_all():
    spec = check_spec(_read_yaml(UAV / "spec.yaml"))
    cfg = _read_yaml(UAV / "scenarios.yaml")
    results = []
    for sc in cfg["scenarios"]:
        path = RES / f"{sc['id']}.json"
        if not path.exists():
            raise FileNotFoundError(f"{path} missing: run sim/uav/harness.py on PX4 SITL")
        results.append(json.loads(path.read_text()))
    return spec, cfg, results


def mapping(cfg: dict, r: dict) -> list[tuple[str | None, str]]:
    out = []
    rule = next((x for x in cfg["outcome_rules"] if x["outcome"] == r["outcome"]), None)
    if rule is None:
        raise ValueError(f"{r['scenario']['id']}: outcome {r['outcome']} has no rule")
    if rule.get("finding"):
        out.append((rule.get("hazard"), rule["finding"]))
    for m in cfg.get("metric_rules", []):
        v = r.get(m["metric"])
        if v is not None and v > m["above"]:
            out.append((m.get("hazard"), m["finding"] + f" ({m['metric']} = {v})"))
    return out


# ---------------------------------------------------------------- drawing

class View:
    def __init__(self, x, y, w, h, n0, n1, e0, e1):
        s = min(w / (e1 - e0), h / (n1 - n0))
        self.s, self.x, self.y = s, x + (w - s * (e1 - e0)) / 2, y + (h - s * (n1 - n0)) / 2
        self.n1, self.e0 = n1, e0
        self.box = (x, y, w, h)

    def p(self, n, e):
        return self.x + (e - self.e0) * self.s, self.y + (self.n1 - n) * self.s


def walker(v: View, n: float, ghost: bool, spec: dict) -> list[str]:
    """Walker footprint (3 m x 2 m, dock at the rear, pilot station forward)."""
    x0, y0 = v.p(n + 2.6, -1.0)
    x1, y1 = v.p(n - 0.4, 1.0)
    dash = "4 3" if ghost else ""
    out = [fk.rect(x0, y0, x1 - x0, y1 - y0, fill="none" if ghost else fk.HW_BG, stroke=fk.HW, sw=1.4, rx=3, dash=dash)]
    dx, dy = v.p(n, 0)
    out.append(fk.el("rect", None, x=fk.fmt(dx - 4), y=fk.fmt(dy - 4), width="8", height="8", fill="none" if ghost else fk.SAFETY,
                     stroke=fk.SAFETY, stroke_width="1.2", stroke_dasharray=dash))
    px_, py_ = v.p(n + spec["pilot_station_n_m"], spec["pilot_station_e_m"])
    out.append(fk.el("circle", None, cx=fk.fmt(px_), cy=fk.fmt(py_), r="3.5", fill=fk.INK if not ghost else "none", stroke=fk.INK,
                     stroke_dasharray=dash))
    return out


def path_d(v: View, tr: list) -> str:
    pts = [v.p(p[1], p[2]) for p in tr]
    return "M" + " L".join(f"{fk.fmt(x)},{fk.fmt(y)}" for x, y in pts)


def scene(r: dict, spec: dict, cfg: dict) -> str:
    sc, tr = r["scenario"], r["trace"]
    moved = r["dock_m"][0]
    body = fk.header(W, f"{sc['id']} · {sc['title']}", f"PX4 {r['px4']} SITL (SIH quadrotor) · outcome {r['outcome']} · "
                     f"hazards {', '.join(sc['hazards'])}", "synthetic")
    leg, _ = fk.legend(40, 108, [(fk.HW_BG, fk.HW, "walker (dashed: at take-off)"), (fk.SAFETY, fk.SAFETY, "dock"),
                                 ("none", fk.RED, "UAV path after injection (ground truth)"),
                                 (fk.RED_BG, fk.RED + " dashed", f"pilot keep-out {spec['pilot_keepout_m']:g} m")])
    body += leg
    dur = max(6.0, tr[-1][0] / 4.0)
    # overview
    R = spec["geofence_radius_m"]
    ns = [p[1] for p in tr] + [-R, R]
    es = [p[2] for p in tr] + [-R, R]
    ov = View(40, 130, 520, 360, min(ns) - 5, max(ns) + 5, min(es) - 5, max(es) + 5)
    body.append(fk.rect(*ov.box, fill=fk.CHIP, stroke=fk.HAIR, rx=6, sw=1))
    cx, cy = ov.p(0, 0)
    body.append(fk.el("circle", None, cx=fk.fmt(cx), cy=fk.fmt(cy), r=fk.fmt(R * ov.s), fill="none", stroke=fk.AMBER,
                      stroke_width="1.4", stroke_dasharray="6 4"))
    gx, gy = ov.p(R * math.cos(math.radians(225)), R * math.sin(math.radians(225)))
    body.append(fk.text(gx - 4, gy + 14, f"geofence {R:g} m", size=9.5, fill=fk.AMBER, anchor="end"))
    if moved:
        body += walker(ov, 0.0, True, spec)
    body += walker(ov, moved, False, spec)
    ox, oy = ov.p(spec["observe_n_m"], spec["observe_e_m"])
    body.append(fk.el("circle", None, cx=fk.fmt(ox), cy=fk.fmt(oy), r="5", fill="none", stroke=fk.GREEN, stroke_width="1.6"))
    body.append(fk.text(ox + 8, oy - 6, "observation point", size=9.5, fill=fk.GREEN))
    d = path_d(ov, tr)
    body.append(fk.el("path", None, d=d, fill="none", stroke=fk.RED, stroke_width="2"))
    ex, ey = ov.p(tr[-1][1], tr[-1][2])
    body.append(f'<circle r="5" fill="{fk.RED}" cx="0" cy="0" transform="translate({fk.fmt(ex)} {fk.fmt(ey)})">'
                f'<animateMotion dur="{dur:.1f}s" repeatCount="indefinite" path="{_rel(d, ex, ey)}"/></circle>')
    body.append(fk.text(ov.box[0] + 8, ov.box[1] + 16, "overview (north up)", size=10, fill=fk.MUTED, weight=700))
    # zoom on the dock
    zm = View(590, 130, 370, 250, moved - 8, moved + 10, -9, 9)
    body.append(fk.rect(*zm.box, fill=fk.CHIP, stroke=fk.HAIR, rx=6, sw=1))
    px_, py_ = zm.p(moved + spec["pilot_station_n_m"], spec["pilot_station_e_m"])
    body.append(fk.el("circle", None, cx=fk.fmt(px_), cy=fk.fmt(py_), r=fk.fmt(spec["pilot_keepout_m"] * zm.s), fill=fk.RED_BG,
                      stroke=fk.RED, stroke_width="1.2", stroke_dasharray="4 3"))
    body += walker(zm, moved, False, spec)
    low = [p for p in tr if p[3] < spec["keepout_alt_m"] and zm.n1 - 18 <= p[1] <= zm.n1 and -9 <= p[2] <= 9]
    if low:
        body.append(fk.el("path", None, d=path_d(zm, low), fill="none", stroke=fk.RED, stroke_width="2.2"))
        lx, ly = zm.p(low[-1][1], low[-1][2])
        body.append(fk.el("circle", None, cx=fk.fmt(lx), cy=fk.fmt(ly), r="4", fill=fk.RED))
    body.append(fk.text(zm.box[0] + 8, zm.box[1] + 16, f"zoom on the dock: path below {spec['keepout_alt_m']:g} m", size=10,
                        fill=fk.MUTED, weight=700))
    md = r["min_pilot_distance_low_m"]
    lines = [f"closest to the pilot below {spec['keepout_alt_m']:g} m: " + (f"{md} m" if md is not None else "never that low"),
             "landing: " + (f"{r['landing_to_dock_m']} m from the dock" if r["landing_to_dock_m"] is not None else "did not land")]
    for i, ln in enumerate(lines):
        bad = (i == 0 and md is not None and md < spec["pilot_keepout_m"]) or (i == 1 and r["outcome"] == "landed-at-stale-home")
        body.append(fk.text(zm.box[0] + 8, zm.box[1] + zm.box[3] - 26 + i * 14, ln, size=10, fill=fk.RED if bad else fk.INK))
    # altitude and modes timeline
    tx0, tx1, ty0, ty1 = 600, 960, 400, 480
    tmax = max(tr[-1][0], 1.0)
    amax = max(max(p[3] for p in tr), spec["keepout_alt_m"]) + 2
    pts = " L".join(f"{fk.fmt(tx0 + (tx1 - tx0) * p[0] / tmax)},{fk.fmt(ty1 - (ty1 - ty0) * max(p[3], 0) / amax)}" for p in tr)
    body.append(fk.rect(tx0, ty0, tx1 - tx0, ty1 - ty0, fill="#FFFFFF", stroke=fk.HAIR, rx=3, sw=1))
    yk = ty1 - (ty1 - ty0) * spec["keepout_alt_m"] / amax
    body.append(fk.line(tx0, yk, tx1, yk, stroke=fk.RED, sw=1, dash="3 3"))
    body.append(fk.el("path", None, d="M" + pts, fill="none", stroke=fk.INK, stroke_width="1.4"))
    body.append(fk.text(tx0, ty0 - 6, "altitude above the dock vs time after injection; modes below", size=9.5, fill=fk.MUTED))
    for t, mode in r["mode_changes"]:
        x = tx0 + (tx1 - tx0) * t / tmax
        body.append(fk.line(x, ty1, x, ty1 + 8, stroke=fk.SW, sw=1.5))
        near_end = x > tx1 - 40
        body.append(fk.text(x - 2 if near_end else x + 2, ty1 + 18, mode.replace("AUTO.", ""), size=9, fill=fk.SW,
                            anchor="end" if near_end else ""))
    body += fk.footer(W, H, f"Synthetic, no evidence credit · ground truth from PX4 SIH · injection at t = 0 · generated by "
                            f"sim/figures/uav_scenes.py from sim/results/uav/{sc['id']}.json")
    desc = (f"{sc['id']}: {sc['title']}. Outcome {r['outcome']}; first failsafe {r['first_failsafe']}; minimum distance to the pilot "
            f"station below {spec['keepout_alt_m']:g} m: {r['min_pilot_distance_low_m']} m; landing to dock {r['landing_to_dock_m']} m.")
    return fk.svg(W, H, f"{sc['id']} {sc['title']}", desc, body)


def _rel(d: str, ex: float, ey: float) -> str:
    """The path relative to the end point, so the marker's static position is the end state."""
    out = []
    for tok in d[1:].split(" L"):
        x, y = (float(v) for v in tok.split(","))
        out.append(f"{fk.fmt(x - ex)},{fk.fmt(y - ey)}")
    return "M" + " L".join(out)


# ---------------------------------------------------------------- pages

def summary(spec, cfg, results) -> tuple[str, list]:
    findings: dict = {}
    rows = []
    for r in results:
        sc = r["scenario"]
        maps = mapping(cfg, r)
        for hz, f in maps:
            findings.setdefault(f, {"hazard": hz, "scenarios": []})["scenarios"].append(sc["id"])
        fs = f"{r['first_failsafe'][1]} at {r['first_failsafe'][0]} s" if r["first_failsafe"] else "—"
        rows.append(f"| {sc['id']} | {sc['title']} | `{', '.join(f'{k}={v}' for k, v in sc['params'].items()) or 'defaults'}` | "
                    f"{fs} | **{r['outcome']}** | {r['min_pilot_distance_low_m']} | {r['landing_to_dock_m']} | "
                    f"{r['max_distance_from_home_m']} | {r['max_estimate_error_m']} |")
    flist = [{"id": f"FND-UAV-{i:02d}", "text": t, **v} for i, (t, v) in enumerate(findings.items(), 1)]
    page = ["# UAV failsafe scenarios (PX4 SITL)\n\n", f"> {ABOUT}\n\n",
            f"PX4 {results[0]['px4']}, SIH quadrotor, headless, speed factor {results[0]['speed_factor']:g}. Positions are simulator "
            "ground truth. The harness acts as the ground station; there is no integration manager, so these runs show what PX4's own "
            "failsafes do when no recovery permit exists. Parameters are candidate configurations, not decisions.\n\n",
            "| ID | Scenario | PX4 parameters | First failsafe | Outcome | Min distance to pilot below keep-out altitude (m) | "
            "Landing to dock (m) | Max distance from home (m) | Max estimate error (m) |\n|---|---|---|---|---|---|---|---|---|\n",
            "\n".join(rows), "\n\n## Findings for review\n\n"]
    page += [f"- **{f['id']}** ({', '.join(f['scenarios'])}; {f['hazard'] or 'no hazard'}): {f['text']}\n" for f in flist]
    page.append("\nFindings are drafts for the safety lead (CLAUDE.md). Scenario notes: " +
                "; ".join(f"{s['id']}: {s['note']}" for s in cfg["scenarios"] if s.get("note")) + ".\n")
    return "".join(page), flist


def wiki(summary_md: str, results) -> str:
    out = ["<!-- GENERATED by sim/figures/uav_scenes.py from sim/results/uav. Do not edit by hand. -->\n\n",
           summary_md.replace("# UAV failsafe scenarios (PX4 SITL)", "# UAV Simulation (PX4 SITL)"), "\n## Scenes\n\n"]
    for r in results:
        sid = r["scenario"]["id"]
        out.append(f"### {sid} · {r['scenario']['title']}\n\n![{sid}](images/sim-{sid.lower()}.svg)\n\n")
    return "".join(out)


def outputs() -> dict:
    spec, cfg, results = load_all()
    outs = {f"docs/wiki/images/sim-{r['scenario']['id'].lower()}.svg": scene(r, spec, cfg) for r in results}
    md, _ = summary(spec, cfg, results)
    outs["sim/results/uav/summary.md"] = md
    outs["docs/wiki/UAV-Simulation.md"] = wiki(md, results)
    return outs


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    return write_or_check(outputs(), a.check, "python -m sim.figures.uav_scenes")


if __name__ == "__main__":
    sys.exit(main())
