"""Animated 2D side-view hazard scenes from plant runs -> docs/wiki/images/sim-*.svg and docs/wiki/Simulation.md.

Usage: python -m sim.figures.scenes [--check]

Scene conventions (after LionDriver's road-scene kit, side view instead of top-down):
  - one walker; dashed green = what should happen (the intended or mitigated run), solid red = what does
  - both are plant runs from sim/plant/walker.py; nothing is hand-animated
  - the animation loops (SMIL); the static pose, shown where animation does not run, is the end state
  - the scene freezes at the first mishap: contact and rotation after tipping are not modelled
  - a timeline under the scene marks fault onset, alarm, stop, hold and mishap
Every scene names its hazard (or finding), its case and the synthetic label.
"""
from __future__ import annotations

import argparse
import json
import math
import sys

from sim.common import ABOUT, ROOT, write_or_check
from sim.plant import spec, walker
from tools.figures import figkit as fk

W, H = 1000, 540
SCALE = 70.0          # px per metre
ORIGIN = (360, 400)   # px of the support centre on the ground

SCENES = [
    {"id": "SC-01", "hazard": "HAZ-WLK-002", "title": "Slow supply leak on a slope: balance lost before the hold engages",
     "source": "edge case EC-08 (search SF-01)", "edge": ("SF-01", "EC-08")},
    {"id": "SC-02", "hazard": "HAZ-SAF-001", "title": "Protective stop removes leg force instead of crouching",
     "source": "fault FLT-03", "performed": {"fault": "FLT-03"}, "intended": {"stop_request_s": 1.0}},
    {"id": "SC-03", "hazard": "HAZ-WLK-001", "title": "Frozen posture feedback with no staleness monitor",
     "source": "fault FLT-02", "performed": {"fault": "FLT-02", "monitor": False}, "intended": {"fault": "FLT-02", "monitor": True}},
    {"id": "SC-04", "hazard": "HAZ-PIL-002", "title": "Burst supply loss with failed load holding: cockpit drops",
     "source": "edge case EC-01 (search SF-01)", "edge": ("SF-01", "EC-01"), "intended_over": {"load_holding": "works"}},
]


def px(x: float, z: float, slope: float) -> tuple[float, float]:
    """World (x horizontal from support centre, z height above the ground at the support centre) -> pixels."""
    return ORIGIN[0] + x * SCALE, ORIGIN[1] - z * SCALE


def ground_z(x: float, slope: float) -> float:
    return -x * math.tan(math.radians(slope))


def cases(sc: dict) -> tuple[dict, dict]:
    if "edge" in sc:
        fam, ec_id = sc["edge"]
        res = json.loads((ROOT / f"sim/results/search-{fam}.json").read_text())
        ec = next(e for e in res["edge_cases"] if e["id"] == ec_id)
        base = {**res["family"]["base"], **ec["params"]}
        performed = {**base, "fault": res["family"]["fault"]}
        intended = {**performed, **sc["intended_over"]} if "intended_over" in sc else {**base, "fault": None}
        return performed, intended
    return sc["performed"], sc["intended"]


def frames(trace: list, n: int) -> list:
    out = list(trace)
    while len(out) < n:
        out.append(out[-1])
    return out


def walker_svg(fr: list, slope: float, p: dict, color: str, dash: str, dur: float, tag: str) -> list[str]:
    """Body (cockpit box), stance leg and foot, animated over frames fr; base attributes = last frame."""
    keyt = ";".join(f"{i / (len(fr) - 1):.4f}" for i in range(len(fr)))
    foot = p["foot_half_length_m"]
    last = fr[-1]

    def body_tr(f):
        x, z = f[1], f[2]
        gx, gy = px(x, z, slope)
        return f"{fk.fmt(gx)} {fk.fmt(gy)}"

    def hip(f):
        return px(f[1], f[2] - 0.2, slope)

    out = []
    # foot (support) on the ground
    fx0, fy0 = px(-foot, ground_z(-foot, slope), slope)
    fx1, fy1 = px(foot, ground_z(foot, slope), slope)
    out.append(fk.el("line", None, x1=fk.fmt(fx0), y1=fk.fmt(fy0), x2=fk.fmt(fx1), y2=fk.fmt(fy1), stroke=color,
                     stroke_width=5, stroke_linecap="round", stroke_dasharray=dash, opacity="0.9"))
    # leg from foot centre to hip, animated
    hx, hy = hip(last)
    cx, cy = px(0, 0, slope)
    out.append(f'<line x1="{fk.fmt(cx)}" y1="{fk.fmt(cy)}" x2="{fk.fmt(hx)}" y2="{fk.fmt(hy)}" stroke="{color}" '
               f'stroke-width="6" stroke-linecap="round" stroke-dasharray="{dash}">'
               f'<animate attributeName="x2" dur="{dur:.2f}s" repeatCount="indefinite" keyTimes="{keyt}" '
               f'values="{";".join(fk.fmt(hip(f)[0]) for f in fr)}"/>'
               f'<animate attributeName="y2" dur="{dur:.2f}s" repeatCount="indefinite" keyTimes="{keyt}" '
               f'values="{";".join(fk.fmt(hip(f)[1]) for f in fr)}"/></line>')
    # body: cockpit box centred on the CoM, pilot head inside
    bw, bh = 1.3 * SCALE, 1.0 * SCALE
    fill = "none" if dash else fk.RED_BG
    out.append(f'<g transform="translate({body_tr(last)})">'
               f'<animateTransform attributeName="transform" type="translate" dur="{dur:.2f}s" repeatCount="indefinite" '
               f'keyTimes="{keyt}" values="{";".join(body_tr(f) for f in fr)}"/>'
               + fk.rect(-bw / 2, -bh / 2, bw, bh, fill=fill, stroke=color, sw=2.2, rx=10, dash=dash)
               + fk.el("circle", None, cx="0", cy=fk.fmt(-bh / 2 + 22), r="9", fill="none", stroke=color, stroke_width=1.6,
                       stroke_dasharray=dash)
               + fk.text(0, bh / 2 - 10, tag, size=10, fill=color, weight=700, anchor="middle") + "</g>")
    return out


def scene_svg(sc: dict, p: dict) -> tuple[str, dict]:
    perf_case, int_case = cases(sc)
    perf = walker.simulate(perf_case, p)
    intd = walker.simulate(int_case, p)
    slope = perf["case"]["slope_deg"]
    n = max(len(perf["trace"]), len(intd["trace"])) + 20      # hold the end state for 20 frames
    fp, fi = frames(perf["trace"], n), frames(intd["trace"], n)
    dur = n * 0.05
    body = fk.header(W, f"{sc['id']} · {sc['title']}", f"{sc['hazard']} · {sc['source']} · slope {slope:g}° · "
                     f"performed: {perf['outcome']}, intended: {intd['outcome']}", "synthetic")
    leg, _ = fk.legend(40, 108, [("none", fk.GREEN + " dashed", "intended / mitigated run"),
                                 (fk.RED_BG, fk.RED, "performed run (fault)")])
    body += leg
    # ground
    gx0, gy0 = px(-4.6, ground_z(-4.6, slope), slope)
    gx1, gy1 = px(8.6, ground_z(8.6, slope), slope)
    gb = H - 44
    body.append(fk.el("path", None, d=f"M{fk.fmt(gx0)},{fk.fmt(min(gy0, gb))} L{fk.fmt(gx1)},{fk.fmt(min(gy1, gb))} "
                      f"L{fk.fmt(gx1)},{gb} L{fk.fmt(gx0)},{gb} Z", fill=fk.GREY_BG, stroke=fk.MUTED, stroke_width=1.2))
    # crouch height and tip limit guides
    _, yc = px(0, p["crouch_height_m"], slope)
    body.append(fk.line(ORIGIN[0] - 220, yc, ORIGIN[0] + 330, yc, stroke=fk.FAINT, sw=1, dash="2 4"))
    body.append(fk.text(ORIGIN[0] + 335, yc + 4, "crouch / rest height", size=9.5, fill=fk.MUTED))
    xt, _ = px(p["tip_offset_m"], 0, slope)
    body.append(fk.line(xt, 150, xt, ORIGIN[1] - 10, stroke=fk.FAINT, sw=1, dash="2 4"))
    body.append(fk.text(xt + 4, ORIGIN[1] - 40, "tip limit", size=9.5, fill=fk.MUTED))
    body += walker_svg(fi, slope, p, fk.GREEN, "6 4", dur, "")
    body += walker_svg(fp, slope, p, fk.RED, "", dur, "")
    # mishap marker on the end state
    ev = perf["events"]
    if perf["outcome"] != "safe":
        lx, ly = px(fp[-1][1], fp[-1][2], slope)
        label = "TIP" if perf["outcome"] == "tip" else f"HARD DROP {ev['impact_speed']:.1f} m/s"
        body += fk.pill(lx, ly - 62, f"{label} at {ev['mishap_t']} s", fill=fk.RED, color="#FFFFFF", stroke=fk.RED, size=10)
    # timeline
    tx0, tx1, ty = 600, 960, 150
    tmax = dur
    body.append(fk.line(tx0, ty, tx1, ty, stroke=fk.LINE, sw=3))
    marks = [("fault", perf["case"].get("fault_onset_s") if perf["case"].get("fault") else None), ("alarm", ev["alarm_t"]),
             ("stop", ev["stop_t"]), ("hold", ev["lock_t"]), ("mishap", ev["mishap_t"])]
    row_end: list = []
    for name, tm in marks:
        if tm is None:
            continue
        x = tx0 + (tx1 - tx0) * tm / tmax
        col = fk.RED if name == "mishap" else fk.INK
        lbl = f"{name} {tm:g}s"
        half = fk.text_w(lbl, 9) / 2 + 4
        row = next((i for i, e in enumerate(row_end) if x - half > e), len(row_end))
        if row == len(row_end):
            row_end.append(0.0)
        row_end[row] = x + half
        body.append(fk.line(x, ty - 7, x, ty + 7, stroke=col, sw=2))
        body.append(fk.text(x, ty + 20 + row * 12, lbl, size=9, fill=col, anchor="middle"))
    body.append(f'<line x1="{tx0}" y1="{ty - 9}" x2="{tx0}" y2="{ty + 9}" stroke="{fk.SW}" stroke-width="2">'
                f'<animate attributeName="x1" dur="{dur:.2f}s" repeatCount="indefinite" values="{tx0};{tx1}"/>'
                f'<animate attributeName="x2" dur="{dur:.2f}s" repeatCount="indefinite" values="{tx0};{tx1}"/></line>')
    body.append(fk.text(tx0, ty - 14, "timeline (performed run)", size=9.5, fill=fk.MUTED))
    body += fk.footer(W, H, f"Synthetic, no evidence credit · sim/plant/walker.py, spec digest {spec.digest()} · contact not "
                            "modelled; the run stops at the first mishap · generated by sim/figures/scenes.py")
    desc = (f"{sc['id']} {sc['hazard']}: {sc['title']}. Performed run ({fmt_case(perf['case'])}) ends {perf['outcome']}"
            f"{' at ' + str(ev['mishap_t']) + ' s' if ev['mishap_t'] else ''}; intended run ends {intd['outcome']}.")
    meta = {"id": sc["id"], "hazard": sc["hazard"], "title": sc["title"], "source": sc["source"], "performed": perf["outcome"],
            "intended": intd["outcome"], "mishap_t": ev["mishap_t"], "case": fmt_case(perf["case"])}
    return fk.svg(W, H, f"{sc['id']} {sc['title']}", desc, body), meta


def fmt_case(c: dict) -> str:
    keys = ["variant", "fault", "slope_deg", "tau_leak_s", "pilot_reaction_s", "stride_offset_m", "load_holding", "monitor"]
    return ", ".join(f"{k}={c[k]}" for k in keys if c.get(k) is not None)


def page(metas: list) -> str:
    plant = json.loads((ROOT / "sim/results/plant-results.json").read_text())
    nominal = "; ".join(f"{n['slope_deg']}° {n['outcome']}" for n in plant["nominal"])
    out = ["<!-- GENERATED by sim/figures/scenes.py from the simulation results. Do not edit by hand. -->\n\n",
           "# Simulation\n\n",
           f"> {ABOUT} Results rank risks and guide analysis and tests; they are not verification evidence.\n\n",
           "Layer 1 plant (`sim/plant/walker.py`): a reduced-order sagittal walker with stated assumptions A1–A7, parameters in "
           "`sim/spec/walker.yaml` (each with a range, status and source), faults in `sim/faults.yaml` traced to hazard causal "
           "factors. Layer 4 failure search (`sim/search`): seeded Monte Carlo and cross-entropy falsification; worst cases "
           "are re-run without the fault and under assumption probes, then mapped to hazards or raised as findings.\n\n",
           f"No-fault capability by slope: {nominal}.\n\n",
           "Results: [plant results](https://github.com/jherrodthomas/Project-Susanoo/blob/main/sim/results/plant-results.md) · "
           "[search SF-01](https://github.com/jherrodthomas/Project-Susanoo/blob/main/sim/results/search-SF-01.md) · "
           "[edge cases](https://github.com/jherrodthomas/Project-Susanoo/blob/main/sim/results/edge-cases.md)\n\n## Scenes\n\n"]
    for m in metas:
        out.append(f"### {m['id']} · {m['title']}\n\n{m['hazard']} · {m['source']} · performed **{m['performed']}**"
                   f"{' at ' + str(m['mishap_t']) + ' s' if m['mishap_t'] else ''}, intended {m['intended']}.\n\n"
                   f"![{m['id']} {m['title']}](images/sim-{m['id'].lower()}.svg)\n\nCase: `{m['case']}`\n\n")
    return "".join(out)


def outputs() -> dict:
    p = spec.load()
    outs, metas = {}, []
    for sc in SCENES:
        svg, meta = scene_svg(sc, p)
        outs[f"docs/wiki/images/sim-{sc['id'].lower()}.svg"] = svg
        metas.append(meta)
    outs["docs/wiki/Simulation.md"] = page(metas)
    return outs


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    return write_or_check(outputs(), a.check, "python -m sim.figures.scenes")


if __name__ == "__main__":
    sys.exit(main())
