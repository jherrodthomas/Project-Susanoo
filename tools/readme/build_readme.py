#!/usr/bin/env python3
"""Build the repository README's figures and data tables from the records.

Every number on the front page is read from a record, so the README cannot drift from the project:

  docs/readme/banner.svg        hero banner with headline counts
  docs/readme/at-a-glance.svg   status tiles: hazards, requirements, 882E tasks, interfaces, decisions, simulation
  docs/readme/risk-matrix.svg   hazards on the MIL-STD-882E Table III matrix, initial -> target
  docs/readme/simulation.svg    synthetic walker failure search and PX4 SITL failsafe outcomes
  README.md                     the blocks between <!-- readme:NAME:start --> and <!-- readme:NAME:end -->

    python -m tools.readme.build_readme            # write
    python -m tools.readme.build_readme --check    # fail if anything is stale

Standard library + PyYAML; output is deterministic.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "figures"))
import layoutkit as fk  # noqa: E402
from layoutkit import INK, MUTED, FAINT, LINE, HAIR, CHIP, GREY_BG, TONES  # noqa: E402

OUT = ROOT / "docs" / "readme"
README = ROOT / "README.md"
GEN = "tools/readme/build_readme.py"

LEVEL_TONE = {  # fill, stroke/text
    "High": ("#FEE2E2", "#B91C1C"), "Serious": ("#FFEDD5", "#C2410C"), "Medium": ("#FEF3C7", "#B45309"),
    "Low": ("#DCFCE7", "#15803D"), "Eliminated": ("#F1F5F9", "#64748B")}
OUTCOME_TONE = {"keepout-breach": "red", "landed-at-stale-home": "amber", "landed-clear": "ok", "contained": "ok"}


# ================================================================ records
def load() -> dict:
    y = lambda p: yaml.safe_load((ROOT / p).read_text())  # noqa: E731
    d = {
        "hazards": [yaml.safe_load(p.read_text()) for p in sorted((ROOT / "safety/hazards").glob("HAZ-*.yaml"))],
        "reqs": [yaml.safe_load(p.read_text()) for p in sorted((ROOT / "requirements").glob("SYS-*.yaml"))],
        "ssf": sorted((ROOT / "safety/software").glob("SSF-*.yaml")),
        "item": y("architecture/item-definition.yaml"),
        "std": y("standards/mil-std-882e/model.yaml"),
        "tailor": y("standards/tailoring/mil-std-882e.yaml"),
        "decisions": y("decisions/register.yaml")["decisions"],
        "search": json.loads((ROOT / "sim/results/search-SF-01.json").read_text()),
        "uav": [json.loads(p.read_text()) | {"id": p.stem}
                for p in sorted((ROOT / "sim/results/uav").glob("SU-*.json"))],
        "sysml": sorted((ROOT / "models/sysml/model").glob("*.sysml")),
        "doc_sysml": sorted([*(ROOT / "safety/mil-std-882e").rglob("*.sysml"), *(ROOT / "concept").glob("*.sysml"),
                             *(ROOT / "integrations/px4").glob("*.sysml")]),
        "folders": len(list((ROOT / "safety/mil-std-882e").rglob("README.md"))),
    }
    uav_md = (ROOT / "sim/results/uav/summary.md").read_text()
    d["uav_findings"] = re.findall(r"^- \*\*(FND-UAV-\d+)\*\*", uav_md, re.M)
    return d


def stats(d: dict) -> dict:
    hz = d["hazards"]
    tasks = Counter(v["disposition"] for v in d["tailor"]["tasks"].values())
    dec = Counter(x["status"] for x in d["decisions"])
    mc = d["search"]["monte_carlo"]
    return {
        "hazards": len(hz), "hazards_open": sum(h["status"] == "open" for h in hz),
        "initial": Counter(h["initial_risk"]["risk_level"] for h in hz),
        "target": Counter(h["target_risk"]["risk_level"] for h in hz),
        "mitigations": sum(len(h.get("mitigations", [])) for h in hz),
        "reqs": len(d["reqs"]), "req_status": Counter(r["status"] for r in d["reqs"]),
        "req_open": sum(r["verification"]["disposition"] == "open" for r in d["reqs"]),
        "ssf": len(d["ssf"]),
        "elements": len(d["item"]["elements"]), "externals": len(d["item"]["externals"]),
        "interfaces": len(d["item"]["interfaces"]), "functions": len(d["item"]["functions"]),
        "tasks": tasks, "tasks_total": sum(tasks.values()), "gate": d["tailor"]["current_gate"],
        "decisions": len(d["decisions"]), "dec": dec,
        "dec_lead_open": sum(x["status"] == "open" and x.get("decider") == "lead" for x in d["decisions"]),
        "mc_n": mc["n"], "mc": mc["by_outcome"], "mc_split": mc["split"],
        "uav": len(d["uav"]), "uav_findings": len(d["uav_findings"]),
        "sysml": len(d["sysml"]) + len(d["doc_sysml"]), "folders": d["folders"],
    }


# ================================================================ banner
def banner(s: dict) -> str:
    W, H = 1280, 420
    out = ['<defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">'
           '<stop offset="0" stop-color="#0B1220"/><stop offset="1" stop-color="#1E293B"/></linearGradient>'
           '<linearGradient id="glass" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#5EEAD4" '
           'stop-opacity=".55"/><stop offset="1" stop-color="#0F766E" stop-opacity=".25"/></linearGradient>'
           '<radialGradient id="glow" cx=".72" cy=".42" r=".55"><stop offset="0" stop-color="#4F46E5" '
           'stop-opacity=".35"/><stop offset="1" stop-color="#4F46E5" stop-opacity="0"/></radialGradient>'
           '<pattern id="grid" width="32" height="32" patternUnits="userSpaceOnUse"><path d="M32 0H0V32" '
           'fill="none" stroke="#FFFFFF" stroke-opacity=".045" stroke-width="1"/></pattern></defs>',
           fk.rect(0, 0, W, H, fill="url(#bg)", stroke="none", rx=18, sw=0),
           fk.rect(0, 0, W, H, fill="url(#grid)", stroke="none", rx=18, sw=0),
           fk.rect(0, 0, W, H, fill="url(#glow)", stroke="none", rx=18, sw=0)]
    # --- copy
    x = 64
    out.append(fk.text(x, 92, "PROJECT SUSANOO  ·  SUS-I1", size=13, fill="#5EEAD4", weight=700))
    out.append(fk.text(x, 158, "Susanoo", size=64, fill="#FFFFFF", weight=800))
    for i, ln in enumerate(["A human-piloted mechanized walker and a dockable", "observation UAV, engineered as code against",
                            "MIL-STD-882E: every claim traced, checked and drawn."]):
        out.append(fk.text(x, 200 + 26 * i, ln, size=19, fill="#CBD5E1"))
    chips = [(f"{s['hazards']}", "hazards tracked"), (f"{s['interfaces']}", "interfaces"),
             (f"{s['reqs']}", "safety requirements"), (f"{s['sysml']}", "SysML files validated")]
    cx = x
    for num, lab in chips:
        w = fk.text_w(num, 22, True) + fk.text_w(lab, 12.5) + 40
        out.append(fk.rect(cx, 300, w, 46, fill="#FFFFFF", stroke="#FFFFFF", rx=12, sw=0, opacity="0.06"))
        out.append(fk.rect(cx, 300, w, 46, fill="none", stroke="#334155", rx=12, sw=1))
        out.append(fk.text(cx + 14, 330, num, size=22, fill="#FFFFFF", weight=800))
        out.append(fk.text(cx + 22 + fk.text_w(num, 22, True), 329, lab, size=12.5, fill="#94A3B8"))
        cx += w + 10
    out.append(fk.text(x, 384, "Simulation-first  ·  Unarmed  ·  Nothing certified, accepted or flight-qualified",
                       size=12.5, fill="#64748B"))
    out += walker_art()
    return fk.svg(W, H, "Project Susanoo", "Human-piloted mechanized walker and dockable observation UAV, "
                  "engineered as code against MIL-STD-882E.", out).replace(fk.rect(0, 0, W, H, fill="#FFFFFF", stroke="none", rx=0, sw=0), "")


def walker_art() -> list[str]:
    """Original line-art of the SUS-M1 walker with SUS-A1 returning to its dock (concept illustration)."""
    o: list[str] = []
    st, acc, uav, safe = "#CBD5E1", "#818CF8", "#5EEAD4", "#FB923C"
    gy = 372
    o.append(fk.line(760, gy, 1236, gy, stroke="#334155", sw=1.5))
    for i in range(0, 470, 26):
        o.append(fk.line(770 + i, gy + 6, 760 + i, gy + 16, stroke="#1F2A3D", sw=1.2))
    # exclusion zone
    o.append(fk.el("ellipse", cx="985", cy=str(gy), rx="205", ry="16", fill="none", stroke=safe, stroke_width="1.2",
                   stroke_dasharray="6 6", opacity="0.6"))
    # back leg (darker)
    for hip, knee, ank, toe, c in [((945, 268), (888, 312), (925, 360), (958, 368), "#475569"),
                                   ((1010, 268), (1068, 314), (1030, 360), (1066, 368), st)]:
        o.append(fk.path(f"M{hip[0]} {hip[1]} L{knee[0]} {knee[1]} L{ank[0]} {ank[1]}", stroke=c, sw=9, fill="none"))
        o.append(fk.path(f"M{ank[0] - 22} {gy} L{toe[0] + 6} {gy}", stroke=c, sw=7))
        for p in (hip, knee, ank):
            o.append(fk.circle(p[0], p[1], 6.5, fill="#0B1220", stroke=acc, sw=2.2))
    # hips / chassis
    o.append(fk.rect(915, 246, 130, 34, fill="#1E293B", stroke=st, rx=10, sw=2))
    # pilot pod: protected cockpit
    pod = "M905 246 L905 168 Q905 136 936 128 L1028 128 Q1062 136 1066 168 L1066 246 Z"
    o.append(fk.path(pod, stroke=st, sw=2.4, fill="#162033"))
    o.append(fk.path("M922 220 L922 172 Q924 150 946 146 L1018 146 Q1044 152 1048 176 L1048 220 Z",
                     stroke=uav, sw=1.6, fill="url(#glass)"))
    # pilot silhouette
    o.append(fk.path("M958 220 Q958 198 985 196 Q1012 198 1012 220 Z", stroke=st, sw=1.6, fill="#0B1220"))
    o.append(fk.circle(985, 176, 13, fill="#0B1220", stroke=st, sw=1.6))
    o.append(fk.path("M974 174 Q985 168 996 174 L996 180 Q985 184 974 180 Z", stroke="none", sw=0, fill=uav))
    o.append(fk.line(962, 214, 1008, 214, stroke=safe, sw=2))
    # protective-stop / safety monitor badge
    o.append(fk.circle(1052, 236, 8, fill=safe, stroke="none", sw=0))
    o.append(fk.text(1052, 240, "!", size=11, fill="#0B1220", weight=800, anchor="middle"))
    # manipulator arm
    o.append(fk.path("M1066 196 L1112 224 L1104 268", stroke=st, sw=7, fill="none"))
    for p in ((1066, 196), (1112, 224)):
        o.append(fk.circle(p[0], p[1], 5.5, fill="#0B1220", stroke=acc, sw=2))
    o.append(fk.path("M1096 268 L1104 284 L1112 268", stroke=st, sw=3, fill="none"))
    # dock on the back of the pod
    o.append(fk.rect(912, 112, 76, 10, fill="#1E293B", stroke=acc, rx=4, sw=1.8))
    o.append(fk.line(950, 112, 950, 104, stroke=acc, sw=2))
    # UAV returning: dashed approach path into the dock
    o.append(fk.path("M1170 82 C 1120 70, 990 60, 950 100", stroke=uav, sw=1.6, dash="5 6", fill="none"))
    ux, uy = 1182, 78
    for dx, dy in ((-26, -14), (26, -14), (-26, 14), (26, 14)):
        o.append(fk.line(ux, uy, ux + dx, uy + dy, stroke=uav, sw=2.4))
        o.append(fk.el("ellipse", cx=fk.fmt(ux + dx), cy=fk.fmt(uy + dy), rx="15", ry="4.5", fill="none",
                       stroke=uav, stroke_width="1.6", opacity="0.9"))
    o.append(fk.rect(ux - 11, uy - 7, 22, 14, fill="#0B1220", stroke=uav, rx=4, sw=2))
    # observation cone
    o.append(fk.path(f"M{ux} {uy + 8} L{ux - 70} {gy - 4} L{ux + 40} {gy - 4} Z", stroke="none", sw=0,
                     fill="#5EEAD4").replace('fill="#5EEAD4"', 'fill="#5EEAD4" fill-opacity="0.06"'))
    o.append(fk.text(1236, 402, "Concept illustration · SUS-M1 walker, SUS-A1 returning to its dock",
                     size=10.5, fill="#475569", anchor="end"))
    return o


# ================================================================ at a glance
def bar(x, y, w, parts: list[tuple[int, str]], h=10) -> list[str]:
    total = sum(n for n, _ in parts) or 1
    out, cx = [fk.rect(x, y, w, h, fill=GREY_BG, stroke="none", rx=h / 2, sw=0)], x
    segs = [(n, c) for n, c in parts if n]
    for i, (n, c) in enumerate(segs):
        sw = w * n / total
        out.append(fk.rect(cx, y, sw - (2 if i < len(segs) - 1 else 0), h, fill=c, stroke="none", rx=h / 2, sw=0))
        cx += sw
    return out


def glance(s: dict) -> str:
    W, M = 1120, 40
    head, y0 = fk.header(W, "1", "Project at a glance",
                         "Read from the records on every build. Risk levels are preliminary qualitative judgements; "
                         "simulation is synthetic with no evidence credit.", "safety/ · requirements/ · standards/ · sim/")
    out = list(head)
    lv = ["High", "Serious", "Medium", "Low"]
    t = s["tasks"]
    tiles = [
        ("HAZARDS", s["hazards"], f"{s['hazards_open']} open · {s['mitigations']} mitigations",
         [(s["initial"][k], LEVEL_TONE[k][1]) for k in lv],
         "Initial risk: " + ", ".join(f"{s['initial'][k]} {k}" for k in lv if s["initial"][k])),
        ("TARGET RISK", s["hazards"], "after planned mitigation",
         [(s["target"][k], LEVEL_TONE[k][1]) for k in lv],
         "Target: " + ", ".join(f"{s['target'][k]} {k}" for k in lv if s["target"][k]) + " · none accepted"),
        ("SAFETY REQUIREMENTS", s["reqs"], f"{s['req_status']['candidate']} candidate · {s['ssf']} software functions",
         [(s["reqs"] - s["req_open"], TONES["ok"][0]), (s["req_open"], TONES["amber"][0])],
         f"Verification: {s['req_open']} open, {s['reqs'] - s['req_open']} closed"),
        ("MIL-STD-882E TASKS", s["tasks_total"], f"tailored · current gate {s['gate']}",
         [(t["selected"], TONES["system"][0]), (t["conditional"], TONES["amber"][0]),
          (t["not-selected"], FAINT), (t["not-applicable"], LINE)],
         f"{t['selected']} selected, {t['conditional']} conditional, {t['not-selected']} not selected, "
         f"{t['not-applicable']} n/a"),
        ("ARCHITECTURE", s["interfaces"], f"interfaces · {s['elements']} elements · {s['externals']} externals",
         [(s["elements"], TONES["system"][0]), (s["externals"], TONES["external"][0])],
         f"{s['functions']} functions · {s['sysml']} SysML files pass the OMG pilot"),
        ("SIMULATION", s["mc_n"] + s["uav"], f"runs · {s['uav_findings']} findings for review",
         [(s["mc"]["safe"], TONES["ok"][0]), (s["mc"]["tip"], TONES["amber"][0]),
          (s["mc"]["hard-drop"], TONES["red"][0])],
         f"SF-01: {s['mc']['safe']} safe, {s['mc']['tip']} tip, {s['mc']['hard-drop']} hard-drop · "
         f"{s['uav']} PX4 SITL"),
    ]
    tw, th, gap = (W - 2 * M - 2 * 16) / 3, 150, 16
    for i, (label, num, sub, parts, note) in enumerate(tiles):
        x, y = M + (i % 3) * (tw + gap), y0 + 24 + (i // 3) * (th + gap)
        out.append(fk.rect(x, y, tw, th, fill="#FFFFFF", stroke=HAIR, rx=14, sw=1.2))
        out.append(fk.text(x + 20, y + 30, label, size=11, fill=MUTED, weight=700))
        out.append(fk.text(x + 20, y + 76, str(num), size=40, fill=INK, weight=800))
        out.append(fk.text(x + 32 + fk.text_w(str(num), 40, True) * 1.12, y + 74, sub, size=12, fill=MUTED))
        out += bar(x + 20, y + 96, tw - 40, parts)
        out.append(fk.text(x + 20, y + 130, note, size=11, fill=MUTED))
    y = y0 + 24 + 2 * th + gap + 34
    out.append(fk.text(M, y, f"Generated by {GEN} from the records; regenerated and diffed in CI.", size=10.5, fill=FAINT))
    return fk.svg(W, y + 18, "Figure 1 · Project at a glance", "Counts from the Susanoo records", out)


# ================================================================ risk matrix
def risk_matrix(d: dict) -> str:
    std, hz = d["std"], d["hazards"]
    W, M = 1120, 40
    head, y0 = fk.header(W, "2", "Where the hazards sit on the risk matrix",
                         "Each hazard's initial risk (dashed) and its target after planned mitigation (solid) on the "
                         "MIL-STD-882E Table III matrix. Arrows show the planned reduction; none is verified or accepted.",
                         "safety/hazards · standards/mil-std-882e/model.yaml")
    out = list(head)
    matrix = {str(p): {str(k): v for k, v in row.items()} for p, row in std["rac_matrix"].items()}
    sev = sorted(matrix["A"].keys())
    prob = list(matrix.keys())
    sev_name = {str(x["category"]): x["name"] for x in std["severity"]}
    prob_name = {x["level"]: x["name"] for x in std["probability"]}
    gx, gy, cw, ch = M + 150, y0 + 64, 146, 70
    for j, sv in enumerate(sev):
        out.append(fk.text(gx + j * cw + cw / 2, gy - 26, f"{sv} · {sev_name.get(sv, sv)}", size=12, weight=700,
                           anchor="middle"))
    out.append(fk.text(gx + 2 * cw, gy - 46, "SEVERITY", size=10.5, fill=MUTED, weight=700, anchor="middle"))
    cells: dict[tuple[str, str], tuple[float, float]] = {}
    for i, p in enumerate(prob):
        out.append(fk.text(gx - 14, gy + i * ch + ch / 2 + 4, f"{p} · {prob_name.get(p, p)}", size=12, weight=700,
                           anchor="end"))
        for j, sv in enumerate(sev):
            lvl = matrix[p][sv]
            f, c = LEVEL_TONE[lvl]
            x, y = gx + j * cw, gy + i * ch
            out.append(fk.rect(x + 2, y + 2, cw - 4, ch - 4, fill=f, stroke="#FFFFFF", rx=8, sw=0))
            out.append(fk.text(x + cw - 10, y + 18, lvl.upper(), size=9, fill=c, weight=700, anchor="end"))
            cells[(p, sv)] = (x, y)
    out.append(fk.text(M + 6, gy + 3 * ch, "PROBABILITY", size=10.5, fill=MUTED, weight=700, anchor="middle")
               .replace("<text", f'<text transform="rotate(-90 {fk.fmt(M + 6)} {fk.fmt(gy + 3 * ch)})"', 1))
    # chips per cell
    def rac(r):
        return r["rac"][1], r["rac"][0]
    by_cell_i: dict = {}
    by_cell_t: dict = {}
    for h in hz:
        by_cell_i.setdefault(rac(h["initial_risk"]), []).append(h["id"])
        by_cell_t.setdefault(rac(h["target_risk"]), []).append(h["id"])
    moves = Counter((rac(h["initial_risk"]), rac(h["target_risk"])) for h in hz)
    chip_w = cw - 58                      # chips sit left; arrows run in a lane on the right of the column
    for cell, ids in by_cell_i.items():
        x, y = cells[cell]
        out.append(fk.rect(x + 10, y + 30, chip_w, 22, fill="#FFFFFF", stroke=INK, rx=11, sw=1, dash="3 2"))
        out.append(fk.text(x + 10 + chip_w / 2, y + 45, f"{len(ids)} initial", size=10.5, weight=700, anchor="middle"))
    for cell, ids in by_cell_t.items():
        x, y = cells[cell]
        out.append(fk.rect(x + 10, y + 30, chip_w, 22, fill=INK, stroke=INK, rx=11, sw=1))
        out.append(fk.text(x + 10 + chip_w / 2, y + 45, f"{len(ids)} target", size=10.5, weight=700, fill="#FFFFFF",
                           anchor="middle"))
    lane: Counter = Counter()
    for (a, b), n in sorted(moves.items(), key=lambda t: (t[0][0][1], t[0][0][0])):
        (ax, ay), (bx, by) = cells[a], cells[b]
        k = lane[a[1]]
        lane[a[1]] += 1
        lx_ = ax + cw - 34 + k * 16
        y1, y2 = ay + 41, by + 30
        out.append(fk.path(f"M{fk.fmt(ax + 10 + chip_w)} {fk.fmt(y1)} L{fk.fmt(lx_)} {fk.fmt(y1)} "
                           f"L{fk.fmt(lx_)} {fk.fmt(y2 + 11)} L{fk.fmt(bx + 10 + chip_w + 2)} {fk.fmt(y2 + 11)}",
                           stroke=INK, sw=1.5, marker_end="url(#arr-current)"))
        p, _ = fk.pill(lx_ - 8, (y1 + y2) / 2 - 4, str(n), INK)
        out += p
    # hazard list on the right
    lx, ly = gx + len(sev) * cw + 36, gy - 30
    out.append(fk.text(lx, ly, "HAZARDS", size=10.5, fill=MUTED, weight=700))
    for k, h in enumerate(hz):
        y = ly + 22 + k * 40
        i_l, t_l = h["initial_risk"], h["target_risk"]
        p, pw = fk.pill(lx, y - 12, h["id"], INK)
        out += p
        for m, (rr, dash) in enumerate(((i_l, "3 2"), (t_l, ""))):
            f, c = LEVEL_TONE[rr["risk_level"]]
            bx = lx + pw + 8 + m * 50
            out.append(fk.rect(bx, y - 12, 40, 16, fill=f, stroke=c, rx=8, sw=1, dash=dash))
            out.append(fk.text(bx + 20, y, rr["rac"], size=9.5, fill=c, weight=700, anchor="middle"))
        out.append(fk.text(lx + pw + 8 + 44, y, "→", size=10, fill=MUTED, anchor="middle"))
        out.append(fk.text(lx, y + 17, fk.wrap(h["title"], W - lx - M, 10.5, max_lines=1)[0], size=10.5, fill=MUTED))
    yb = gy + len(prob) * ch + 30
    leg, yb = fk.legend(M, yb, [("#FFFFFF", INK + " dashed", "Initial risk (count)"), (INK, INK, "Target risk (count)"),
                                *[(LEVEL_TONE[k][0], LEVEL_TONE[k][1], k) for k in ["High", "Serious", "Medium", "Low"]]],
                        W - M)
    out += leg
    out.append(fk.text(M, yb + 16, f"Generated by {GEN}. Preliminary judgements on a concept with no selected hardware; "
                       "a hazard is accepted only by a recorded human review (rule R13).", size=10.5, fill=FAINT))
    return fk.svg(W, yb + 36, "Figure 2 · Where the hazards sit on the risk matrix", "Hazards initial and target RAC", out)


# ================================================================ simulation
def simulation(d: dict, s: dict) -> str:
    W, M = 1120, 40
    head, y0 = fk.header(W, "3", "What the simulations found",
                         "Walker failure search SF-01 (hydraulic supply loss mid-stride on a slope) and six PX4 SITL "
                         "failsafe scenarios for the UAV. Design aids that feed the hazard records; not evidence.",
                         "sim/results")
    out = list(head)
    # stamp
    stamp = "SYNTHETIC · NO EVIDENCE CREDIT"
    sw_ = fk.text_w(stamp, 10.5, True) + 24
    out.append(fk.rect(W - M - sw_, y0 + 18, sw_, 24, fill=TONES["amber"][1], stroke=TONES["amber"][0], rx=12, sw=1.2))
    out.append(fk.text(W - M - sw_ / 2, y0 + 34, stamp, size=10.5, fill=TONES["amber"][0], weight=700, anchor="middle"))
    # left: SF-01
    x, y = M, y0 + 40
    colw = (W - 2 * M - 40) / 2
    out.append(fk.text(x, y, "WALKER · SF-01 MONTE CARLO", size=11, fill=MUTED, weight=700))
    out.append(fk.text(x, y + 22, f"{s['mc_n']} seeded samples over slope, leak rate, pilot reaction, stride offset",
                       size=11.5, fill=MUTED))
    mc = s["mc"]
    rows = [("All samples", [(mc["safe"], TONES["ok"][0]), (mc["tip"], TONES["amber"][0]),
                             (mc["hard-drop"], TONES["red"][0])], s["mc_n"])]
    for k, v in sorted(s["mc_split"].items()):
        rows.append((k.replace("load_holding=", "Load holding ").replace("works", "works").replace("fails", "fails"),
                     [(v["n"] - v["failures"], TONES["ok"][0]), (v["failures"], TONES["red"][0])], v["n"]))
    for i, (lab, parts, n) in enumerate(rows):
        yy = y + 56 + i * 64
        fail = n - parts[0][0]
        out.append(fk.text(x, yy, lab, size=12.5, weight=700))
        out.append(fk.text(x + colw, yy, f"{fail / n:.0%} fail", size=12.5, weight=700,
                           fill=TONES["red"][0] if fail / n > 0.5 else INK, anchor="end"))
        out += bar(x, yy + 10, colw, parts, h=16)
    yl = y + 56 + len(rows) * 64
    leg, _ = fk.legend(x, yl, [(TONES["ok"][0], TONES["ok"][0], "safe stop"), (TONES["amber"][0], TONES["amber"][0], "tip"),
                               (TONES["red"][0], TONES["red"][0], "hard drop / failure")], x + colw)
    out += leg
    out.append(fk.text(x, yl + 26, "Every sample with failed load holding ends in a failure: drives HAZ-WLK-002 CF4.",
                       size=11.5, fill=INK))
    # right: UAV SITL
    rx = M + colw + 40
    out.append(fk.text(rx, y, "UAV · PX4 SITL FAILSAFE SCENARIOS", size=11, fill=MUTED, weight=700))
    out.append(fk.text(rx, y + 22, "PX4 v1.16.2 SIH, headless; minimum distance to the pilot below keep-out altitude",
                       size=11.5, fill=MUTED))
    dists = [u.get("min_pilot_distance_low_m") for u in d["uav"]]
    mx = max(v for v in dists if v is not None)
    for i, u in enumerate(d["uav"]):
        yy = y + 50 + i * 40
        tone = OUTCOME_TONE.get(u["outcome"], "amber")
        p, pw = fk.pill(rx, yy, u["id"], INK)
        out += p
        v = u.get("min_pilot_distance_low_m")
        bx, bw = rx + 64, colw - 64 - 200
        out.append(fk.rect(bx, yy + 3, bw, 10, fill=GREY_BG, stroke="none", rx=5, sw=0))
        if v is not None:
            out.append(fk.rect(bx, yy + 3, max(6, bw * v / mx), 10, fill=TONES[tone][0], stroke="none", rx=5, sw=0))
            out.append(fk.text(bx + bw + 8, yy + 12, f"{v:.1f} m", size=11, fill=INK, weight=700))
        else:
            out.append(fk.text(bx + bw + 8, yy + 12, "n/a", size=11, fill=FAINT))
        lab = u["outcome"].replace("-", " ")
        pw2 = fk.pill_w(lab)
        p, _ = fk.pill(rx + colw - pw2, yy, lab, TONES[tone][0])
        out += p
        out.append(fk.text(rx, yy + 30, fk.wrap(u["scenario"]["title"], colw, 10.5, max_lines=1)[0],
                           size=10.5, fill=MUTED))
    yb = max(yl + 50, y + 50 + len(d["uav"]) * 40 + 30)
    out.append(fk.text(rx, yb - 14, f"{s['uav_findings']} findings (FND-UAV-01..) recorded against HAZ-INT-001 for review.",
                       size=11.5, fill=INK))
    out.append(fk.text(M, yb + 14, f"Generated by {GEN} from sim/results. Plant and SITL outputs are labelled synthetic "
                       "until a fidelity case is approved (sim/README.md, evidence gate).", size=10.5, fill=FAINT))
    return fk.svg(W, yb + 34, "Figure 3 · What the simulations found", "Synthetic simulation results", out)


# ================================================================ README blocks
def blocks(d: dict, s: dict) -> dict[str, str]:
    lv = lambda c: ", ".join(f"{c[k]} {k}" for k in ["High", "Serious", "Medium", "Low"] if c[k])  # noqa: E731
    t = s["tasks"]
    numbers = "\n".join([
        "| What | Count | Source |",
        "|---|---|---|",
        f"| Hazards tracked (Task 106) | **{s['hazards']}** ({s['hazards_open']} open) · initial {lv(s['initial'])} → "
        f"target {lv(s['target'])} | [`safety/hazards/`](safety/hazards/) |",
        f"| Mitigations planned | **{s['mitigations']}** | hazard records |",
        f"| Safety requirements | **{s['reqs']}** ({s['req_status']['candidate']} candidate, {s['req_open']} with "
        f"verification open) | [`requirements/`](requirements/) |",
        f"| Safety-significant software functions | **{s['ssf']}** | [`safety/software/`](safety/software/) |",
        f"| Architecture | **{s['elements']}** elements, **{s['externals']}** externals, **{s['interfaces']}** interfaces, "
        f"**{s['functions']}** functions | [`architecture/item-definition.yaml`](architecture/item-definition.yaml) |",
        f"| MIL-STD-882E tasks | **{s['tasks_total']}** tailored: {t['selected']} selected, {t['conditional']} "
        f"conditional, {t['not-selected']} not selected, {t['not-applicable']} n/a · gate **{s['gate']}** | "
        f"[`standards/tailoring/`](standards/tailoring/mil-std-882e.yaml) |",
        f"| SysML v2 files passing the OMG pilot | **{s['sysml']}** | [`models/sysml/`](models/sysml/model/) |",
        f"| Work-product folders with generated figures | **{s['folders']}** | [`safety/mil-std-882e/`](safety/mil-std-882e/README.md) |",
        f"| Decisions for the lead | **{s['dec_lead_open']}** open of {s['decisions']} | "
        f"[`decisions/register.yaml`](decisions/register.yaml) |",
        f"| Simulation runs (synthetic) | **{s['mc_n']}** walker Monte Carlo + **{s['uav']}** PX4 SITL · "
        f"**{s['uav_findings']}** findings | [`sim/results/`](sim/results/) |",
    ])
    hz_rows = ["| Hazard | What could go wrong | Initial | Target | Mitigations |", "|---|---|---|---|---|"]
    for h in d["hazards"]:
        i_l, t_l = h["initial_risk"], h["target_risk"]
        hz_rows.append(f"| [`{h['id']}`](safety/hazards/{h['id']}.yaml) | {h['title']} | {i_l['rac']} {i_l['risk_level']} | "
                       f"{t_l['rac']} {t_l['risk_level']} | {len(h.get('mitigations', []))} |")
    return {"numbers": numbers, "hazards": "\n".join(hz_rows)}


def apply_blocks(text: str, bl: dict[str, str]) -> str:
    for name, body in bl.items():
        start, end = f"<!-- readme:{name}:start (generated by {GEN}; do not edit) -->", f"<!-- readme:{name}:end -->"
        pat = re.compile(re.escape(start) + r".*?" + re.escape(end), re.S)
        if not pat.search(text):
            raise SystemExit(f"README.md has no block {name}")
        text = pat.sub(lambda _m: f"{start}\n{body}\n{end}", text)
    return text


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    d = load()
    s = stats(d)
    files = {OUT / "banner.svg": banner(s), OUT / "at-a-glance.svg": glance(s),
             OUT / "risk-matrix.svg": risk_matrix(d), OUT / "simulation.svg": simulation(d, s),
             README: apply_blocks(README.read_text(), blocks(d, s))}
    stale = []
    for p, content in files.items():
        if p.exists() and p.read_text() == content:
            continue
        if args.check:
            stale.append(str(p.relative_to(ROOT)))
        else:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content)
            print(f"wrote {p.relative_to(ROOT)}")
    if stale:
        print(f"Stale (run python -m tools.readme.build_readme):\n  " + "\n  ".join(stale))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
