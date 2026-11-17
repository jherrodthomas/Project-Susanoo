#!/usr/bin/env python3
"""Render the standards comparison (standards/crosswalk.yaml) to standards/crosswalk.md.

Each column is a level as its own standard defines it; the columns are deliberately not aligned across standards and
no level is equivalent to another. The page has a swimlane of each standard's own process (standards/
crosswalk-swimlane.svg), the side-by-side matrix and worked examples of reading a part's rating against a Susanoo
hazard, software function or requirement.

    python -m tools.crosswalk.build            # write standards/crosswalk.md and crosswalk-swimlane.svg
    python -m tools.crosswalk.build --check    # fail on a malformed record or a stale page

Standard library + PyYAML. Output is deterministic.
"""
from __future__ import annotations

import argparse
import html
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.terms.terms import decorate  # noqa: E402

RECORD = ROOT / "standards" / "crosswalk.yaml"
PAGE = ROOT / "standards" / "crosswalk.md"
SWIM = ROOT / "standards" / "crosswalk-swimlane.svg"
LANE_COLOURS = ["#4F46E5", "#0F766E", "#C2410C", "#7C3AED", "#475569"]
GEN = "tools/crosswalk/build.py"


def load(path: Path = RECORD) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def validate(d: dict) -> list[str]:
    errs = []
    stds = {s["id"]: s for s in d.get("standards") or []}
    if not stds:
        errs.append("no standards")
    for p in d.get("parameters") or []:
        for sid, s in stds.items():
            cells = (p.get("cells") or {}).get(sid)
            if not cells:
                errs.append(f"{p.get('id')}: no cells for {sid}")
                continue
            total = sum(int(c.get("span", 1)) for c in cells)
            if total != len(s["levels"]):
                errs.append(f"{p.get('id')}/{sid}: spans add up to {total}, the standard has {len(s['levels'])} levels")
            for c in cells:
                if not str(c.get("text", "")).strip():
                    errs.append(f"{p.get('id')}/{sid}: empty cell")
                if c.get("verified") and not (c.get("verified_by") and c.get("edition")):
                    errs.append(f"{p.get('id')}/{sid}: a verified cell needs verified_by and edition")
        extra = set((p.get("cells") or {})) - set(stds)
        if extra:
            errs.append(f"{p.get('id')}: cells for unknown standards {sorted(extra)}")
    phases = [ph["id"] for ph in d.get("phases") or []]
    if not phases:
        errs.append("no phases")
    for sid, s in stds.items():
        got = [st.get("phase") for st in s.get("process") or []]
        if got != phases:
            errs.append(f"{sid}: process steps must follow the phases in order, one each ({got} != {phases})")
        for st in s.get("process") or []:
            if not str(st.get("step", "")).strip():
                errs.append(f"{sid}: empty process step")
    for e in d.get("examples") or []:
        for k in ("title", "need", "part", "read_column", "reads", "covers", "leaves_to_us", "decided_by"):
            if not e.get(k):
                errs.append(f"example '{e.get('title')}': missing {k}")
    return errs


def swimlane(d: dict) -> str:
    """One lane per standard, its own steps in order, under shared phase columns; evidence from the other standards
    goes to a sourcing review that feeds Susanoo's own verification step."""
    sys.path.insert(0, str(ROOT / "tools" / "figures"))
    import layoutkit as fk
    from layoutkit import INK, MUTED, FAINT, HAIR, TONES
    phases, stds = d["phases"], d["standards"]
    W, M, LW, RW, gap, lh = 1560, 40, 170, 210, 10, 96
    cw = (W - 2 * M - LW - RW - 30) / len(phases)
    out, yl = fk.header(W, "1", "Where each standard sets its level and produces its evidence",
                        "One lane per standard, its own steps in order. Phase columns show where in each process a step "
                        "happens, not that the steps or levels are equal. Evidence from a part's standard comes into "
                        "Susanoo through the sourcing review.", "standards/crosswalk.yaml")
    y0, x0 = yl + 24, M + LW
    for i, ph in enumerate(phases):
        out.append(fk.rect(x0 + i * cw + 2, y0, cw - 4, 30, fill="#F8FAFC", stroke=HAIR, rx=6))
        out.append(fk.text(x0 + i * cw + cw / 2, y0 + 19, f"{i + 1} · {ph['title']}", size=10.5, weight=700,
                           anchor="middle"))
    rxc = x0 + len(phases) * cw + 30
    s_col, s_fill = TONES["safety"]
    out.append(fk.rect(rxc, y0, RW, 30, fill=s_fill, stroke=s_col, rx=6))
    out.append(fk.text(rxc + RW / 2, y0 + 19, "Into Susanoo", size=10.5, weight=700, anchor="middle", fill=s_col))
    ly, boxes = y0 + 42, {}
    for li, s in enumerate(stds):
        col = LANE_COLOURS[li % len(LANE_COLOURS)]
        y = ly + li * (lh + gap)
        name = s["title"].split(" (")[0] + (" (Susanoo)" if li == 0 else "")
        out.append(fk.rect(M, y, W - 2 * M - RW - 30, lh, fill="#EEF2FF" if li == 0 else "#FBFCFE", stroke=HAIR, rx=10))
        out.append(fk.rect(M, y, 6, lh, fill=col, stroke="none", rx=3, sw=0))
        for k, ln in enumerate(fk.wrap(name, LW - 24, 12.5, bold=True)):
            out.append(fk.text(M + 16, y + 28 + 16 * k, ln, size=12.5, weight=700, fill=col))
        for i, st in enumerate(s["process"]):
            bx, by, bw, bh = x0 + i * cw + 6, y + 12, cw - 12, lh - 24
            out.append(fk.rect(bx, by, bw, bh, fill="#FFFFFF", stroke=col, rx=8, sw=1.2))
            for k, ln in enumerate(fk.wrap(st["step"], bw - 14, 10.5, max_lines=3)):
                out.append(fk.text(bx + 7, by + 17 + 13 * k, ln, size=10.5, fill=INK, weight=600 if k == 0 else ""))
            out.append(fk.text(bx + 7, by + bh - 8, st.get("source", ""), size=9, fill=MUTED))
            if i:
                out.append(fk.path(f"M{fk.fmt(bx - 12)} {by + bh / 2} L{fk.fmt(bx - 2)} {by + bh / 2}", stroke=col,
                                   sw=1.3, marker_end="url(#arr-ink)"))
            boxes[(li, i)] = (bx, by, bw, bh)
    last = len(phases) - 1
    ytop, ybot = ly + (lh + gap) + 12, ly + (len(stds) - 1) * (lh + gap) + lh - 12
    out.append(fk.rect(rxc, ytop, RW, ybot - ytop, fill=s_fill, stroke=s_col, rx=10, sw=1.4))
    lines = ["Sourcing review", "", "Read the part's rating in", "its own column of the", "comparison; list what it",
             "covers and what it leaves", "to us (the four-step", "examples below).", "", "Accepting supplier evidence",
             "as Susanoo evidence is a", "lead decision."]
    for k, ln in enumerate(lines):
        out.append(fk.text(rxc + 12, ytop + 26 + 15 * k, ln, size=11 if k else 12.5, weight=700 if k == 0 else "",
                           fill=INK if k else s_col))
    for li in range(1, len(stds)):
        bx, by, bw, bh = boxes[(li, last)]
        out.append(fk.path(f"M{fk.fmt(bx + bw)} {by + bh / 2} L{fk.fmt(rxc - 3)} {by + bh / 2}", stroke=s_col, sw=1.2,
                           dash="5 3", marker_end="url(#arr-safety)"))
    vx, vy, vw, vh = boxes[(0, last - 1)]                    # Susanoo's verify-and-review step
    out.append(fk.path(fk.rounded_path([(rxc + RW / 2, ytop - 2), (rxc + RW / 2, ly - 6), (vx + vw / 2, ly - 6),
                                        (vx + vw / 2, vy - 3)]), stroke=s_col, sw=1.6, marker_end="url(#arr-safety)"))
    out.append(fk.text(rxc + RW / 2 + 8, ytop - 40, "feeds Susanoo", size=10, fill=s_col, weight=700))
    out.append(fk.text(rxc + RW / 2 + 8, ytop - 27, "verification", size=10, fill=s_col, weight=700))
    yb = ly + len(stds) * (lh + gap) + 18
    leg, yb = fk.legend(M, yb, [("#EEF2FF", LANE_COLOURS[0], "Susanoo's own process (MIL-STD-882E)"),
                                ("#FFFFFF", "#475569", "A step of another standard"),
                                ("line:" + s_col, s_col + " dashed", "Supplier evidence handed to the sourcing review")],
                       W - M)
    out += leg
    out.append(fk.text(M, yb + 14, f"Generated by {GEN} from standards/crosswalk.yaml. Steps and clauses are drafts until "
                       "checked against each standard's text.", size=10.5, fill=FAINT))
    return fk.svg(W, yb + 34, "Figure 1 · Where each standard sets its level and produces its evidence",
                  "Swimlane of each standard's own process", out)


def matrix(d: dict) -> str:
    stds = d["standards"]
    esc = html.escape
    out = ["<table>", "<thead>", "<tr><th rowspan=\"2\">Parameter</th>"]
    out += [f"<th colspan=\"{len(s['levels'])}\">{esc(s['title'])}</th>" for s in stds]
    out += ["</tr>", "<tr>"]
    out += [f"<th>{esc(lv)}</th>" for s in stds for lv in s["levels"]]
    out += ["</tr>", "</thead>", "<tbody>"]
    for p in d["parameters"]:
        row = [f"<tr><th>{esc(p['title'])}</th>"]
        for s in stds:
            for c in p["cells"][s["id"]]:
                mark = " ✓" if c.get("verified") else ""
                src = f"<br><sub>{esc(c['source'])}{mark}</sub>" if c.get("source") else (f"<br><sub>{mark.strip()}</sub>"
                                                                                             if mark else "")
                text = esc(c["text"])
                if text.startswith(("Not defined", "No ", "—")):
                    text = f"<i>{text}</i>"
                span = f" colspan=\"{c['span']}\"" if int(c.get("span", 1)) > 1 else ""
                row.append(f"<td{span}>{text}{src}</td>")
        out.append("".join(row) + "</tr>")
    out += ["</tbody>", "</table>"]
    return "\n".join(out)


def examples(d: dict) -> str:
    out = []
    for i, e in enumerate(d["examples"], 1):
        out += [f"### Example {i} · {e['title']}", "",
                "**1 · What we need** (from the Susanoo records)", ""]
        out += [f"- **{n['ref']}**: {n['what']}" for n in e["need"]]
        out += ["", f"**2 · The part's rating:** {e['part']}. Read the column **{e['read_column']}**:", ""]
        out += [f"- {r}" for r in e["reads"]]
        out += ["", f"**3 · What it covers:** {e['covers']}", "", "**4 · What it leaves to us**", ""]
        out += [f"- {r}" for r in e["leaves_to_us"]]
        out += ["", f"*{e['decided_by']}*", ""]
    return "\n".join(out)


def page(d: dict) -> str:
    cells = [c for p in d["parameters"] for s in d["standards"] for c in p["cells"][s["id"]]]
    done = sum(1 for c in cells if c.get("verified"))
    names = ", ".join(s["title"].split(" (")[0] for s in d["standards"])
    return "\n".join([
        f"<!-- GENERATED by {GEN} from standards/crosswalk.yaml. Do not edit; edit the record and re-run. -->", "",
        "# Standards comparison", "",
        f"**{d['id']}** · status {d['status']} · **{done} of {len(cells)} cells verified** against the text of their "
        "standard.", "",
        d["purpose"], "",
        f"> **Not an equivalence table.** Each column is a level of one standard ({names}), described only in that "
        "standard's own terms. Read a part's rating in its own column; never read across the columns as if they lined "
        "up. Cells are drafts until verified: " + d["verification"]["note"], "",
        "## How to read it", "",
        "- **Columns** are the levels of each standard, grouped under the standard. Their order follows each "
        "standard's own scale, lowest to highest integrity; nothing is implied between standards.",
        "- **Rows** are the parameters that set or qualify a level. A cell spanning several levels means the parameter "
        "is the same for all of them. *Not defined* means that standard has no such parameter: nothing is borrowed "
        "from another standard.",
        "- **Sources** under each cell name the clause or table. ✓ marks a cell checked against the standard's text.", "",
        "## Where each standard sets its level", "",
        "Each lane is one standard's own process, step by step. The phase columns show where in that process a step "
        "happens, not that steps or levels are equal. A part's evidence (safety manual, certificate, information for "
        "use, accomplishment summary) comes into Susanoo only through the sourcing review.", "",
        f"![Figure 1 · Where each standard sets its level and produces its evidence]({SWIM.name})", "",
        "## The matrix", "",
        matrix(d), "",
        "## How to use it", "",
        "Start from what the Susanoo records require, read the candidate part's rating in its own column, and list what "
        "the rating covers and what it leaves to us. The judgement stays in Susanoo's own terms. The parts below are "
        "generic illustrations, not selections.", "",
        examples(d),
        "## Checking a cell", "",
        "To mark a cell checked, compare it with the controlled text of its standard and add `verified: true`, "
        "`verified_by` and `edition` to it in [`crosswalk.yaml`](crosswalk.yaml), then run "
        "`python -m tools.crosswalk.build`. A check is a review, not an acceptance: it says the cell matches the "
        "standard, not that any part is suitable.", "",
    ])


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    d = load()
    errs = validate(d)
    if errs:
        print("standards/crosswalk.yaml has errors:")
        for e in errs:
            print(f"  {e}")
        return 1
    stale = []
    for path, text in ((PAGE, page(d)), (SWIM, swimlane(d))):
        text = decorate(path.relative_to(ROOT).as_posix(), text)
        if path.exists() and path.read_text(encoding="utf-8") == text:
            continue
        if a.check:
            stale.append(path.relative_to(ROOT).as_posix())
        else:
            path.write_text(text, encoding="utf-8")
            print(f"wrote {path.relative_to(ROOT).as_posix()}")
    if stale:
        print("Out of date; run: python -m tools.crosswalk.build")
        for s in stale:
            print(f"  {s}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
