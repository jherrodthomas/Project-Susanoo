"""Build the System V cycle page, its wiki page and its still from the records.

    python -m tools.vcycle.build_vcycle                  # write the outputs below
    python -m tools.vcycle.build_vcycle --check          # fail if any of them is stale
    python -m tools.vcycle.build_vcycle --history FILE   # also write FILE: a local copy with the evidence clock

Outputs (all generated; never edit by hand):

- docs/vcycle/index.html            interactive page (page source: tools/vcycle/page.html), data embedded
- docs/wiki/System-V-Cycle.md       wiki page: the still, the system-level blocks and how to open the page
- docs/wiki/images/vcycle-system.svg  still of the system-level V, coloured by record maturity

Reads requirements/, safety/hazards/, safety/software/, safety/events/, architecture/trades/,
architecture/item-definition.yaml, changes/, standards/tailoring/mil-std-882e.yaml (gates) and
framework/lifecycle.md (gate exit evidence).

The evidence clock replays the git history of the records. It is left out of the committed page on purpose: a page
that embeds history is stale after every commit that touches a record, so --check could never pass. --history writes
a copy with it for local viewing; do not commit that copy.

Maturity colours are computed from record status for orientation only. Nothing here reviews, verifies or accepts
anything (rule R13).
"""
from __future__ import annotations

import argparse
import html
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.pdac.load import _read_yaml  # noqa: E402
from tools.terms.terms import decorate, expand, find, label, load as load_terms  # noqa: E402

HERE = Path(__file__).resolve().parent
PAGE = "docs/vcycle/index.html"
WIKI = "docs/wiki/System-V-Cycle.md"
STILL = "docs/wiki/images/vcycle-system.svg"
GEN = "tools/vcycle/build_vcycle.py"

# Record status -> maturity rung (0 not started ... 6 validated). Mirrors stOf in page.html.
STATE = {"open": 1, "draft": 1, "candidate": 1, "in-work": 1, "not-started": 0, "planned": 0, "reviewed": 2,
         "baselined": 3, "verified": 5, "accepted": 5, "closed": 6, "complete": 5}
STATES = ["Not started", "Draft", "Reviewed", "Baselined", "Implemented", "Verified", "Validated"]
LADDER = [("Not started", "No record yet", "Anyone may open a draft"),
          ("Draft", "open, draft, candidate, in-work", "Author or AI (I0)"),
          ("Reviewed", "Review record by a named human", "Human reviewer, I1 or higher"),
          ("Baselined", "Requirement baselined, task approved", "Lead, through a review record (R13)"),
          ("Implemented", "Built or configured item under control", "Design owner, after review"),
          ("Verified", "Evidence accepted; hazard verified", "Named human reviewer in role (R13)"),
          ("Validated", "Meets intended use; risk accepted", "Risk acceptance authority")]


# ---------------------------------------------------------------- record extraction (also used for history)
def ex_req(d: dict) -> dict:
    v = d.get("verification") or {}
    src = d.get("source") or {}
    return {"id": d["id"], "title": d.get("title", ""), "status": d.get("status"), "alloc": d.get("allocated_to") or [],
            "haz": src.get("hazard_ids") or [], "methods": v.get("method") or [], "evidence": len(v.get("evidence_ids") or []),
            "ss": bool(d.get("safety_significant")), "scn": src.get("scenario_ids") or []}


def ex_haz(d: dict) -> dict:
    ir, tr = d.get("initial_risk") or {}, d.get("target_risk") or {}
    return {"id": d["id"], "title": d.get("title", ""), "status": d.get("status"), "subs": d.get("subsystems") or [],
            "rac": ir.get("rac"), "level": ir.get("risk_level"), "target": tr.get("rac"),
            "mit": len(d.get("mitigations") or []),
            "ssf": sorted({x for c in d.get("causal_factors") or [] for x in (c.get("ssf_ids") or [])}),
            "reqids": d.get("requirement_ids") or [],
            "mits": [{"id": m["id"], "d": m.get("description", ""), "reqs": m.get("requirement_ids") or []}
                     for m in d.get("mitigations") or []],
            "cfg": (d.get("applicability") or {}).get("configurations") or []}


def ex_ssf(d: dict) -> dict:
    return {"id": d["id"], "title": d.get("title", ""), "scc": d.get("scc"), "items": d.get("software_items") or [],
            "reqs": d.get("requirement_ids") or [],
            "lor": {k: (v or {}).get("status") for k, v in (d.get("lor") or {}).items()}}


def ex_elements(d: dict) -> list[dict]:
    return [{"id": e["id"], "name": e.get("name") or e.get("title"), "parent": e.get("parent")} for e in d.get("elements") or []]


def _glob(pattern: str) -> list[dict]:
    return [_read_yaml(p) for p in sorted(ROOT.glob(pattern))]


def gates() -> tuple[list[dict], str]:
    t = _read_yaml(ROOT / "standards/tailoring/mil-std-882e.yaml")
    exits = {}
    for line in (ROOT / "framework/lifecycle.md").read_text(encoding="utf-8").splitlines():
        m = re.match(r"\|\s*(G\d)\s*\|[^|]*\|\s*(.+?)\s*\|\s*$", line)
        if m:
            exits[m.group(1)] = m.group(2)
    out = [{"id": g, "title": v["title"], "phase": v["phase"], "exit": exits.get(g, "")} for g, v in t["gates"].items()]
    return out, t["current_gate"]


def records() -> dict:
    idf = _read_yaml(ROOT / "architecture/item-definition.yaml")
    g, cur = gates()
    return {
        "elements": ex_elements(idf),
        "reqs": [ex_req(d) for d in _glob("requirements/SYS-*.yaml")],
        "haz": [ex_haz(d) for d in _glob("safety/hazards/HAZ-*.yaml")],
        "ssf": [ex_ssf(d) for d in _glob("safety/software/SSF-*.yaml")],
        "events": [{"id": d["id"], "title": d.get("title", ""), "status": d.get("status"), "subs": d.get("subsystems") or []}
                   for d in _glob("safety/events/EVT-*.yaml")],
        "trades": [{"id": d["id"], "title": d.get("title", ""), "status": d.get("status"), "reqs": d.get("requirement_ids") or []}
                   for d in _glob("architecture/trades/TS-*.yaml")],
        "changes": [{"id": d["id"], "title": d.get("title", ""), "kind": d.get("kind"), "status": d.get("status"),
                     "affects": d.get("affects") or []} for d in _glob("changes/CR-*.yaml")],
        "gates": g, "current_gate": cur,
    }


# ---------------------------------------------------------------- system-level blocks (for the still and wiki)
def system_blocks(data: dict) -> list[dict]:
    """The eleven blocks of the top-level V, as page.html computes them for SUS-I1."""
    st = lambda s: STATE.get(s, 1)  # noqa: E731
    lor = lambda s, k: STATE.get(s["lor"].get(k), 0)  # noqa: E731
    top = [e for e in data["elements"] if e["parent"] == "SUS-I1"]
    kids_reqs = lambda eid: sum(1 for r in data["reqs"] if any(a == eid or a.startswith(eid + "-") for a in r["alloc"]))  # noqa: E731
    scn = sorted({s for r in data["reqs"] for s in r["scn"]})
    impl = [(s["id"], 1 if "pinned" in it else 0) for s in data["ssf"] for it in s["items"]]
    B = [
        ("L1", "Stakeholder needs & hazards", "What must not go wrong", [st(h["status"]) for h in data["haz"]], "hazards"),
        ("L2", "System requirements", "What the system shall do", [st(r["status"]) for r in data["reqs"]], "requirements"),
        ("L3", "Architecture", "Item definition and trade studies", [st(t["status"]) for t in data["trades"]] + [1] * len(top),
         "trade studies and top-level elements"),
        ("L4", "Subsystem requirements", "Derived at the next level", [0] * len(top),
         "top-level elements, " + ", ".join(f"{e['id']} {kids_reqs(e['id'])}" for e in top) + " requirements allocated, none derived"),
        ("L5", "Detailed design", "Component and software design", [lor(s, "design_analysis") for s in data["ssf"]], "SSF design analyses"),
        ("B", "Implementation", "Build, code, configure", [x[1] for x in impl], "SSF software items"),
        ("R5", "Unit test", "Software code analysis", [lor(s, "code_analysis") for s in data["ssf"]], "SSF code analyses"),
        ("R4", "Subsystem verification", "Safety-specific testing", [lor(s, "safety_specific_testing") for s in data["ssf"]],
         "SSF safety-specific testing"),
        ("R3", "Integration test", "Interfaces and integrated events", [STATE.get(e["status"], 0) for e in data["events"]], "events"),
        ("R2", "System verification", "Requirement met, with evidence", [2 if r["evidence"] else 0 for r in data["reqs"]],
         f"requirements, {sum(1 for r in data['reqs'] if r['evidence'])} with evidence"),
        ("R1", "Operational validation", "Right system for the CONOPS", [0] * len(scn), "CONOPS scenarios"),
    ]
    exit_gate = {"L1": 0, "L2": 1, "L3": 2, "L4": 2, "L5": 3, "B": 4, "R5": 4, "R4": 5, "R3": 5, "R2": 5, "R1": 6}
    return [{"k": k, "title": t, "sub": s, "states": xs, "state": min(xs) if xs else 0, "what": w,
             "gate": data["gates"][exit_gate[k]]["id"] if len(data["gates"]) > exit_gate[k] else ""}
            for k, t, s, xs, w in B]


# ---------------------------------------------------------------- the still (SVG)
FILL = ["#eef1f5", "#ffffff", "#86b6ea", "#2a55a8", "#8a5cd1", "#e8833a", "#47a866"]
INK, MUTED, LINE, DECOMP, VERIF = "#152033", "#566275", "#cfd7e2", "#2a55a8", "#2d7a4c"


def _geo(k: str) -> tuple[float, float, float, float]:
    W, LH, BH, BW, X0, STEP, Y0 = 1000, 86, 64, 300, 24, 40, 60
    if k == "B":
        return 380, Y0 + 5 * LH, 240, BH
    lvl = int(k[1]) - 1
    y = Y0 + lvl * LH
    return (X0 + lvl * STEP, y, BW, BH) if k[0] == "L" else (W - X0 - lvl * STEP - BW, y, BW, BH)


def still(data: dict) -> str:
    blocks = system_blocks(data)
    H, SK = 640, 16
    e = html.escape
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 {H}" width="1000" height="{H}" '
         f'font-family="Inter, Segoe UI, Helvetica, Arial, sans-serif">',
         f'<rect width="1000" height="{H}" fill="#ffffff"/>',
         f'<text x="24" y="28" font-size="20" font-weight="700" fill="{INK}">SUS-I1 System V cycle</text>',
         f'<text x="976" y="28" font-size="12" fill="{MUTED}" text-anchor="end">Maturity computed from record status; '
         f'current gate {e(data["current_gate"])}</text>',
         f'<text x="24" y="50" font-size="11" font-weight="700" letter-spacing="1" fill="{DECOMP}">Decomposition · define</text>',
         f'<text x="976" y="50" font-size="11" font-weight="700" letter-spacing="1" fill="{VERIF}" text-anchor="end">'
         f'Verification · prove</text>']
    for n in "12345":
        x, y, w, h = _geo("L" + n)
        rx, _, _, _ = _geo("R" + n)
        if rx - (x + w) > 30:
            o.append(f'<line x1="{x + w}" y1="{y + h / 2}" x2="{rx + 8}" y2="{y + h / 2}" stroke="{LINE}" stroke-dasharray="4 5"/>')
    for b in blocks:
        x, y, w, h = _geo(b["k"])
        side = "L" if b["k"] in ("B",) or b["k"][0] == "L" else "R"
        col = "#8a5cd1" if b["k"] == "B" else DECOMP if side == "L" else VERIF
        pts = (f"{x + SK},{y} {x + w},{y} {x + w - SK},{y + h} {x},{y + h}" if side == "L"
               else f"{x},{y} {x + w - SK},{y} {x + w},{y + h} {x + SK},{y + h}")
        fill = "#f4f6f9" if b["state"] == 0 else "#ffffff"
        dash = ' stroke-dasharray="5 4"' if b["state"] == 0 else ""
        o.append(f'<polygon points="{pts}" fill="{fill}" stroke="{col}" stroke-width="1.5"{dash}/>')
        o.append(f'<circle cx="{x + SK + 16}" cy="{y + 19}" r="6.5" fill="{FILL[b["state"]]}" stroke="#7b8798" stroke-width="1.2"/>')
        o.append(f'<text x="{x + SK + 29}" y="{y + 24}" font-size="15" font-weight="700" fill="{INK}">{e(b["title"])}</text>')
        o.append(f'<text x="{x + SK + 29}" y="{y + 40}" font-size="11.5" fill="{MUTED}">{e(b["sub"])} · exit {e(b["gate"])}</text>')
        o.append(f'<text x="{x + w - SK - 10}" y="{y + 23}" font-size="12" fill="{MUTED}" text-anchor="end">{len(b["states"])}</text>')
        bx, bw, by = x + SK + 12, w - 2 * SK - 24, y + h - 13
        if b["states"]:
            acc = 0.0
            for s in range(7):
                c = b["states"].count(s)
                if c:
                    ww = bw * c / len(b["states"])
                    o.append(f'<rect x="{bx + acc:.1f}" y="{by}" width="{max(ww - 1, 1):.1f}" height="5" fill="{FILL[s]}" '
                             f'stroke="#7b8798" stroke-width=".6"/>')
                    acc += ww
        else:
            o.append(f'<rect x="{bx}" y="{by}" width="{bw}" height="5" fill="none" stroke="#b9c3d1" stroke-dasharray="3 3"/>')
    ly = H - 34
    lx = 24
    for i, n in enumerate(STATES):
        o.append(f'<circle cx="{lx + 6}" cy="{ly}" r="6" fill="{FILL[i]}" stroke="#7b8798" stroke-width="1.2"/>'
                 f'<text x="{lx + 17}" y="{ly + 4}" font-size="12" fill="{MUTED}">{n}</text>')
        lx += 22 + len(n) * 7.2
    o.append(f'<text x="976" y="{ly + 4}" font-size="12" fill="{MUTED}" text-anchor="end">Dashed block: nothing started. '
             f'Strip: mix of record maturity.</text>')
    o.append("</svg>")
    return "\n".join(o) + "\n"


# ---------------------------------------------------------------- the wiki page
def wiki(data: dict) -> str:
    blocks = system_blocks(data)
    side = lambda k: "bottom" if k == "B" else "left (define)" if k[0] == "L" else "right (prove)"  # noqa: E731
    rows = "".join(f"| {b['title']} | {side(b['k'])} | {b['gate']} | {len(b['states'])} {b['what']} | {STATES[b['state']]} |\n"
                   for b in blocks)
    ev = sum(1 for r in data["reqs"] if r["evidence"])
    return (
        f"<!-- GENERATED by {GEN} from the records. Do not edit by hand. -->\n\n"
        "# System V Cycle\n\n"
        "The System V cycle of SUS-I1, built from the records: the left side defines (hazards, requirements, architecture, "
        "design), the bottom builds, and the right side proves (code analysis, testing, integration, verification, "
        "validation). Each block lists the records that sit in it and takes the colour of the least mature one. "
        "Maturity is computed from record status for orientation only; nothing on this page reviews, verifies or "
        "accepts anything (rule R13).\n\n"
        f"![System V cycle of SUS-I1](images/vcycle-system.svg)\n\n"
        f"**Now:** {len(data['reqs'])} requirements, {len(data['haz'])} hazards and {len(data['ssf'])} SSFs; "
        f"{ev} of {len(data['reqs'])} requirements have verification evidence. Current gate {data['current_gate']}.\n\n"
        "## Open the interactive page\n\n"
        "GitHub does not run scripts in wiki pages or repository files, so this page shows a still. For the interactive "
        "page, open `docs/vcycle/index.html` from a local checkout in a browser. It has five views:\n\n"
        "- **Maturity.** Click any block for its records. Open an element to see its own V, down to a single SSF, where "
        "the blocks become the MIL-STD-882E level-of-rigor tasks.\n"
        "- **Gate scrubber.** Pick a gate; blocks due by then are marked met or gap. The rule used (left side baselined, "
        "right side verified by the exit gate) is a placeholder for real exit criteria.\n"
        "- **Trace a requirement.** One requirement drawn across the cycle: hazard, requirement, element, SSF, "
        "verification method, evidence, scenario.\n"
        "- **Change ripple.** Pick a change request and see which hazards it reopens (the same links as validator rule "
        "R10) and what needs rework and re-verification. Records in `changes/` come first; the rest are examples.\n"
        "- **Evidence clock.** Replays the git history of the records. Not in the committed page; build a local copy "
        "with `python -m tools.vcycle.build_vcycle --history <file.html>`.\n\n"
        "## Blocks at system level\n\n"
        "| Block | Side | Exit gate | Records | Lowest maturity |\n|---|---|---|---|---|\n" + rows + "\n"
        "## Maturity ladder\n\n| Rung | What it means | Who may move a record to it |\n|---|---|---|\n"
        + "".join(f"| {a} | {b} | {c} |\n" for a, b, c in LADDER) + "\n"
        f"Generated by `{GEN}` from `requirements/`, `safety/hazards/`, `safety/software/`, `safety/events/`, "
        "`architecture/`, `changes/`, `standards/tailoring/mil-std-882e.yaml` and `framework/lifecycle.md`.\n")


# ---------------------------------------------------------------- the interactive page
def terms_html(data: dict) -> str:
    shown = " ".join([e["id"] for e in data["elements"]] + [r["id"] for r in data["reqs"]] + [h["id"] for h in data["haz"]]
                     + [s["id"] for s in data["ssf"]] + [x["id"] for x in data["events"] + data["trades"] + data["changes"]]
                     + [g["id"] for g in data["gates"]] + [g["phase"] for g in data["gates"]]
                     + ["SUS-I1 MIL-STD-882E LOR SCC RAC CONOPS PX4 SITL AI I0 I1 R10 R13 CR- SCN- ECP"])
    keys = expand(find(shown)[0])
    defs, _ = load_terms()
    rows = "".join(f"<tr><td>{html.escape(label(k))}</td><td>{html.escape(defs[k])}</td></tr>"
                   for k in sorted(keys, key=lambda q: label(q).lower()))
    return f"<table>{rows}</table>"


def page(data: dict, hist: list) -> str:
    payload = {**data, "terms": terms_html(data),
               "footer": f"Generated by {GEN} from the records. Maturity colours are computed from record status for "
                         "orientation only; nothing here is reviewed, verified or accepted."}
    dump = lambda o: json.dumps(o, sort_keys=True, separators=(",", ":"), default=str).replace("</", "<\\/")  # noqa: E731
    src = (HERE / "page.html").read_text(encoding="utf-8")
    return src.replace("__DATA__", dump(payload)).replace("__HIST__", dump(hist))


def outputs() -> dict[str, str]:
    data = records()
    return {PAGE: page(data, []), WIKI: wiki(data), STILL: still(data)}


# ---------------------------------------------------------------- git history (local only)
HIST_PATHS = ["requirements", "safety/hazards", "safety/software", "architecture/item-definition.yaml",
              "architecture/trades", "safety/events", "decisions/register.yaml"]


def history() -> list[dict]:
    """One entry per commit that changed a record's extracted fields, oldest first."""
    git = lambda *a: subprocess.run(["git", "-C", str(ROOT), *a], capture_output=True, text=True)  # noqa: E731
    log = git("log", "--no-merges", "--reverse", "--date-order", "--format=@@%h|%cI|%s", "--name-only", "--", *HIST_PATHS).stdout
    last: dict = {}
    out = []
    for blk in log.split("@@")[1:]:
        lines = blk.strip().split("\n")
        h, t, s = lines[0].split("|", 2)
        changes = []
        for f in (x for x in lines[1:] if x.strip()):
            kind = ("req" if re.match(r"requirements/SYS-\d+\.yaml$", f) else "haz" if re.match(r"safety/hazards/HAZ-.*\.yaml$", f)
                    else "ssf" if re.match(r"safety/software/SSF-\d+\.yaml$", f)
                    else "other" if re.match(r"(architecture/trades/TS-|safety/events/EVT-).*\.yaml$", f)
                    else "idf" if f == "architecture/item-definition.yaml" else "dec" if f == "decisions/register.yaml" else None)
            if not kind:
                continue
            shown = git("show", f"{h}:{f}")
            if shown.returncode:
                rid = Path(f).stem
                if (kind, rid) in last:
                    changes.append({"k": kind, "del": f})
                    last.pop((kind, rid))
                continue
            try:
                import yaml
                d = yaml.safe_load(shown.stdout)
            except Exception:  # an intermediate commit may hold invalid YAML
                continue
            if not isinstance(d, dict):
                continue
            recs = ([ex_req(d)] if kind == "req" else [ex_haz(d)] if kind == "haz" else [ex_ssf(d)] if kind == "ssf"
                    else [{"id": d.get("id"), "title": d.get("title", ""), "status": d.get("status")}] if kind == "other"
                    else [{"id": "ITEMDEF", "status": d.get("status"), "rev": d.get("revision"), "elements": ex_elements(d)}]
                    if kind == "idf" else [{"id": e["id"], "q": e.get("question", ""), "status": e.get("status"),
                                            "decider": e.get("decider")} for e in d.get("decisions") or []])
            for r in recs:
                if last.get((kind, r["id"])) != r:
                    changes.append({"k": kind, "r": r})
                    last[(kind, r["id"])] = r
        if changes:
            out.append({"h": h, "t": t, "s": s[:120], "c": changes})
    return out


# ---------------------------------------------------------------- CLI
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="fail if an output is stale")
    ap.add_argument("--history", metavar="FILE", help="also write a local page with the evidence clock (do not commit)")
    a = ap.parse_args(argv)
    stale = []
    for rel, text in outputs().items():
        text = decorate(rel, text)  # terms block (.md) / line (.svg)
        p = ROOT / rel
        if p.exists() and p.read_text(encoding="utf-8") == text:
            continue
        if a.check:
            stale.append(rel)
        else:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding="utf-8")
            print(f"wrote {rel}")
    if a.history:
        Path(a.history).write_text(page(records(), history()), encoding="utf-8")
        print(f"wrote {a.history} (local copy with the evidence clock; do not commit)")
    if stale:
        print("System V cycle outputs are out of date; run: python -m tools.vcycle.build_vcycle")
        for s in stale:
            print(f"  {s}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
