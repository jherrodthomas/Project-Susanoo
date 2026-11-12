#!/usr/bin/env python3
"""Render figure specs to SVG in the Susanoo house style.

A spec is a plain dict:

    {"number": "3", "title": "...", "subtitle": "...", "ref": "...", "footer": "...",
     "direction": "RIGHT" | "DOWN",
     "frame": {"kind": "stm", "type": "state def", "name": "OperatingModes"},   # optional SysML diagram frame
     "nodes": [{"id", "title", "sub", "tone", "shape", "code", "parent", "banner", "dashed",
                "stereotype", "attrs", "text", "pills"}],
     "edges": [{"src", "dst", "label", "code", "tone", "dash", "arrow"}],
     "legend": [(fill, stroke, label)],                                         # optional extra legend rows
     "legend_only": True}                                                       # optional: no tone legend rows

Shapes: card (default), class, requirement, state, action, initial, final, actor, usecase.
A node that is another node's `parent` is drawn as a container. Layout is computed by the pinned ELK engine
(elk_layout.js) in one batch for all figures; rendering is pure Python. Output is deterministic.

`rail(spec)` draws the fixed eight-element MIL-STD-882E process rail without ELK.
"""
from __future__ import annotations

import copy
import json
import subprocess
from pathlib import Path

import layoutkit as fk
from layoutkit import INK, MUTED, FAINT, LINE, HAIR, CHIP, GREY_BG, TONES

HERE = Path(__file__).resolve().parent
M = 40
PAD = 12


# ================================================================ node measurement
def _tone(n):
    return TONES.get(n.get("tone", "system"), TONES["system"])


def measure(n: dict) -> None:
    """Size a leaf node and store the text lines it will draw."""
    shape = n.get("shape", "card")
    title = n.get("title", "")
    if shape == "initial":
        n["_w"] = n["_h"] = 18
    elif shape == "final":
        n["_w"] = n["_h"] = 24
    elif shape == "actor":
        n["_lines"] = fk.wrap(title, 110, 11.5, True)
        n["_w"] = max(64, max(fk.text_w(x, 11.5, True) for x in n["_lines"]) + 12)
        n["_h"] = 58 + 15 * len(n["_lines"])
    elif shape == "usecase":
        n["_lines"] = fk.wrap(title, 150, 12, True)
        code_h = 20 if n.get("code") else 0
        n["_w"] = 196
        n["_h"] = 30 + code_h + 16 * len(n["_lines"])
    elif shape == "action":
        n["_lines"] = fk.wrap(title, 168, 12, True)
        n["_w"] = max(120, max(fk.text_w(x, 12, True) for x in n["_lines"]) + 36)
        n["_h"] = 24 + 16 * len(n["_lines"])
    elif shape in ("class", "requirement"):
        st = n.get("stereotype", "block")
        name_lines = fk.wrap(title, 230, 13, True)
        rows: list[tuple[str, str]] = []           # (kind, text)
        if shape == "requirement":
            rows.append(("mono", f"id = {n.get('code', '')}"))
            rows += [("txt", ln) for ln in fk.wrap(n.get("text", ""), 236, 10.5)]
        else:
            rows += [("mono", a) for a in n.get("attrs", [])]
        pills = n.get("pills", [])
        widths = [fk.text_w(f"«{st}»", 10), *(fk.text_w(x, 13, True) for x in name_lines)]
        widths += [fk.text_w(t, 10.5, mono=(k == "mono")) for k, t in rows]
        widths.append(sum(fk.pill_w(p[0]) + 6 for p in pills))
        n["_w"] = max(150, max(widths) + 28)
        n["_name"], n["_rows"] = name_lines, rows
        h = 26 + 16 * len(name_lines) + 8
        if rows:
            h += 10 + 15 * len(rows)
        if pills:
            h += 26
        n["_h"] = h + 4
    elif shape == "state":
        n["_title"] = fk.wrap(title, 170, 12.5, True)
        n["_sub"] = fk.wrap(n.get("sub", ""), 180, 10.5) if n.get("sub") else []
        code_h = 22 if n.get("code") else 0
        widths = [fk.text_w(x, 12.5, True) for x in n["_title"]] + [fk.text_w(x, 10.5) for x in n["_sub"]]
        widths.append(fk.pill_w(n.get("code", "")) if n.get("code") else 0)
        n["_w"] = max(128, max(widths) + 2 * PAD + 4)
        n["_h"] = PAD + code_h + 16 * len(n["_title"]) + (4 + 14 * len(n["_sub"]) if n["_sub"] else 0) + PAD
    else:  # card
        maxw = n.get("maxw", 212)
        n["_title"] = fk.wrap(title, maxw - 2 * PAD, 12.5, True)
        n["_sub"] = fk.wrap(n["sub"], maxw - 2 * PAD, 10.5, max_lines=4) if n.get("sub") else []
        code_h = 22 if n.get("code") else 0
        widths = [fk.text_w(x, 12.5, True) for x in n["_title"]] + [fk.text_w(x, 10.5) for x in n["_sub"]]
        widths.append(fk.pill_w(n["code"]) if n.get("code") else 0)
        n["_w"] = max(n.get("minw", 136), max(widths) + 2 * PAD)
        n["_h"] = PAD + code_h + 16 * len(n["_title"]) + (2 + 14 * len(n["_sub"]) if n["_sub"] else 0) + PAD - 2


def container_pad(n: dict) -> tuple[int, int]:
    """(top padding, minimum width) for a container."""
    if n.get("banner"):
        return 50, fk.text_w(n["banner"].upper(), 10, True) + 60
    top = 40 + (16 if n.get("sub") else 0)
    return top, max(fk.text_w(n.get("title", ""), 13, True), fk.text_w(n.get("sub", ""), 10.5)) + 40


# ================================================================ ELK graph
ROOT_OPTS = {
    "elk.algorithm": "layered",
    "elk.edgeRouting": "ORTHOGONAL",
    "elk.hierarchyHandling": "INCLUDE_CHILDREN",
    "elk.layered.spacing.nodeNodeBetweenLayers": "64",
    "elk.spacing.nodeNode": "26",
    "elk.spacing.edgeNode": "20",
    "elk.spacing.edgeEdge": "14",
    "elk.layered.spacing.edgeNodeBetweenLayers": "22",
    "elk.layered.spacing.edgeEdgeBetweenLayers": "12",
    "elk.spacing.edgeLabel": "4",
    "elk.layered.considerModelOrder.strategy": "NODES_AND_EDGES",
    "elk.layered.nodePlacement.strategy": "NETWORK_SIMPLEX",
    "elk.layered.cycleBreaking.strategy": "MODEL_ORDER",
    "elk.padding": "[top=6,left=6,bottom=6,right=6]",
}


def label_size(e: dict) -> tuple[float, float]:
    lbl = e.get("label", "")
    w = fk.text_w(lbl, 10.5) + (10 if lbl else 0)
    if e.get("code"):
        w += fk.pill_w(e["code"]) + (4 if lbl else 0)
    return max(w, 1), 18


def to_elk(spec: dict) -> dict:
    nodes = {n["id"]: n for n in spec["nodes"]}
    kids: dict[str | None, list[str]] = {}
    for n in spec["nodes"]:
        kids.setdefault(n.get("parent"), []).append(n["id"])

    def build(nid: str) -> dict:
        n = nodes[nid]
        if nid in kids:
            n["_container"] = True
            top, minw = container_pad(n)
            return {"id": nid, "children": [build(c) for c in kids[nid]],
                    "layoutOptions": {"elk.padding": f"[top={top},left=18,bottom=18,right=18]",
                                      "elk.nodeSize.constraints": "[MINIMUM_SIZE]",
                                      "elk.nodeSize.minimum": f"({fk.fmt(minw)}, 60)",
                                      "elk.direction": n.get("direction", spec.get("direction", "RIGHT")),
                                      **({"elk.hierarchyHandling": "SEPARATE_CHILDREN"}
                                         if spec.get("hierarchy") == "separate" else {}),
                                      **n.get("elk", {})}}
        measure(n)
        return {"id": nid, "width": round(n["_w"], 1), "height": round(n["_h"], 1)}

    separate = spec.get("hierarchy") == "separate"
    parent = {n["id"]: n.get("parent") for n in spec["nodes"]}

    def chain(nid):
        out = []
        while nid is not None:
            out.append(nid)
            nid = parent.get(nid)
        return out

    def lca(a: str, b: str) -> str:
        ca = chain(parent.get(a))
        cb = set(chain(parent.get(b)))
        return next((x for x in ca if x in cb), "root")
    owned: dict[str, list[dict]] = {}
    for i, e in enumerate(spec.get("edges", [])):
        d = {"id": f"e{i}", "sources": [e["src"]], "targets": [e["dst"]]}
        if e.get("label") or e.get("code"):
            w, h = label_size(e)
            d["labels"] = [{"id": f"e{i}l", "text": e.get("label", ""), "width": round(w, 1), "height": h}]
        owned.setdefault(lca(e["src"], e["dst"]) if separate else "root", []).append(d)
    opts = dict(ROOT_OPTS, **{"elk.direction": spec.get("direction", "RIGHT")}, **spec.get("elk", {}))
    if separate:
        # Each container is laid out on its own; every edge lives in the lowest container holding both ends.
        opts["elk.hierarchyHandling"] = "SEPARATE_CHILDREN"
    children = [build(c) for c in kids.get(None, [])]

    def attach(g: dict):
        if g["id"] in owned and g["id"] != "root":
            g["edges"] = owned[g["id"]]
        for c in g.get("children", []):
            attach(c)
    for c in children:
        attach(c)
    return {"id": "root", "layoutOptions": opts, "children": children, "edges": owned.get("root", [])}


def run_elk(graphs: list[dict]) -> list[dict]:
    if not graphs:
        return []
    if not (HERE / "node_modules" / "elkjs").exists():
        raise fk.FigureError("elkjs not installed: run `npm ci` in tools/figures")
    r = subprocess.run(["node", str(HERE / "elk_layout.js")], input=json.dumps(graphs), capture_output=True,
                       text=True, check=False)
    if r.returncode != 0:
        raise fk.FigureError("ELK layout failed:\n" + r.stderr[-2000:])
    return json.loads(r.stdout)


# ================================================================ drawing nodes
def draw_leaf(n: dict, x: float, y: float) -> list[str]:
    shape = n.get("shape", "card")
    stroke, fill = _tone(n)
    w, h = n["_w"], n["_h"]
    tone = n.get("tone", "system")
    ink = "#FFFFFF" if tone == "current" else (FAINT if tone == "muted" else INK)
    sub_ink = "#CBD5E1" if tone == "current" else (FAINT if tone == "muted" else MUTED)
    dash = "4 3" if tone == "muted" or n.get("dashed") else ""
    out: list[str] = []
    if shape == "initial":
        return [fk.circle(x + 9, y + 9, 8, fill=INK, stroke=INK)]
    if shape == "final":
        return [fk.circle(x + 12, y + 12, 11, fill="#FFFFFF", stroke=INK, sw=1.6), fk.circle(x + 12, y + 12, 6.5, fill=INK, stroke=INK)]
    if shape == "actor":
        cx = x + w / 2
        c = stroke
        out += [fk.circle(cx, y + 9, 7, fill="#FFFFFF", stroke=c, sw=1.6),
                fk.line(cx, y + 16, cx, y + 34, stroke=c, sw=1.6), fk.line(cx - 13, y + 23, cx + 13, y + 23, stroke=c, sw=1.6),
                fk.line(cx, y + 34, cx - 10, y + 48, stroke=c, sw=1.6), fk.line(cx, y + 34, cx + 10, y + 48, stroke=c, sw=1.6)]
        for i, ln in enumerate(n["_lines"]):
            out.append(fk.text(cx, y + 66 + 15 * i, ln, size=11.5, weight=700, anchor="middle"))
        return out
    if shape == "usecase":
        out.append(fk.el("ellipse", cx=fk.fmt(x + w / 2), cy=fk.fmt(y + h / 2), rx=fk.fmt(w / 2), ry=fk.fmt(h / 2),
                         fill=fill, stroke=stroke, stroke_width=1.3))
        ty = y + h / 2 - (16 * len(n["_lines"]) + (20 if n.get("code") else 0)) / 2 + 12
        if n.get("code"):
            pw = fk.pill_w(n["code"])
            p, _ = fk.pill(x + w / 2 - pw / 2, ty - 11, n["code"], stroke)
            out += p
            ty += 20
        for i, ln in enumerate(n["_lines"]):
            out.append(fk.text(x + w / 2, ty + 16 * i, ln, size=12, weight=700, anchor="middle"))
        return out
    if shape == "action":
        out.append(fk.rect(x, y, w, h, fill=fill, stroke=stroke, rx=min(h / 2, 18), sw=1.3, dash=dash))
        for i, ln in enumerate(n["_lines"]):
            out.append(fk.text(x + w / 2, y + 17 + 16 * i, ln, size=12, weight=700, anchor="middle", fill=ink))
        return out
    if shape in ("class", "requirement"):
        out.append(fk.rect(x, y, w, h, fill="#FFFFFF", stroke=stroke, rx=4, sw=1.3, dash=dash))
        hh = 26 + 16 * len(n["_name"]) + 4
        out.append(fk.rect(x, y, w, hh, fill=fill, stroke="none", rx=4, sw=0))
        out.append(fk.line(x, y + hh, x + w, y + hh, stroke=stroke, sw=1.1))
        out.append(fk.text(x + w / 2, y + 17, f"«{n.get('stereotype', 'block')}»", size=10, fill=MUTED, anchor="middle"))
        for i, ln in enumerate(n["_name"]):
            out.append(fk.text(x + w / 2, y + 34 + 16 * i, ln, size=13, weight=700, anchor="middle", fill=ink))
        ry = y + hh + 18
        for kind, t in n["_rows"]:
            out.append(fk.text(x + 12, ry, t, size=10.5, mono=(kind == "mono"), fill=INK if kind == "mono" else MUTED))
            ry += 15
        px = x + 12
        for label, ptone in n.get("pills", []):
            p, pw = fk.pill(px, y + h - 24, label, TONES[ptone][0])
            out += p
            px += pw + 6
        return out
    # card and state
    rx = 14 if shape == "state" else 8
    sw = 2 if tone == "current" else 1.3
    out.append(fk.rect(x, y, w, h, fill=fill, stroke=stroke, rx=rx, sw=sw, dash=dash))
    ty = y + PAD
    if n.get("code"):
        p, _ = fk.pill(x + PAD, ty, n["code"], "#FFFFFF" if tone == "current" else stroke,
                       color=INK if tone == "current" else "#FFFFFF")
        out += p
        ty += 22
    for ln in n["_title"]:
        out.append(fk.text(x + PAD, ty + 12, ln, size=12.5, weight=700, fill=ink))
        ty += 16
    if n["_sub"]:
        ty += 2
        for ln in n["_sub"]:
            out.append(fk.text(x + PAD, ty + 11, ln, size=10.5, fill=sub_ink))
            ty += 14
    return out


def draw_container(n: dict, x: float, y: float, w: float, h: float) -> list[str]:
    stroke, fill = _tone(n)
    tone = n.get("tone", "system")
    dash = "7 5" if n.get("dashed") else ("4 3" if tone == "muted" else "")
    bg = "none" if n.get("dashed") else ("url(#hatch)" if tone == "muted" else fill)
    out = [fk.rect(x, y, w, h, fill=bg, stroke=stroke, rx=12, sw=1.8 if n.get("dashed") else 1.3, dash=dash)]
    return out


def draw_banner(n: dict, x: float, y: float, w: float) -> list[str]:
    """Container banner or title, painted above edges so connectors pass beneath it."""
    stroke, _ = _tone(n)
    tone = n.get("tone", "system")
    out: list[str] = []
    if n.get("banner"):
        label = n["banner"].upper()
        bw = min(w - 24, fk.text_w(label, 10, True) + 40)
        out.append(fk.rect(x + 12, y + 12, bw, 22, fill=stroke, stroke="none", rx=11, sw=0))
        out.append(fk.text(x + 12 + bw / 2, y + 27, label, size=10, weight=700, fill="#FFFFFF", anchor="middle"))
    else:
        out.append(fk.text(x + 16, y + 26, n.get("title", ""), size=13, weight=700,
                           fill=FAINT if tone == "muted" else INK))
        if n.get("sub"):
            out.append(fk.text(x + 16, y + 42, n["sub"], size=10.5, fill=MUTED))
    return out


# ================================================================ drawing edges
def orthogonal(pts: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """Replace any diagonal step (ELK hierarchy junctions) with a Z-jog that continues the previous direction."""
    out = [pts[0]]
    for b in pts[1:]:
        a = out[-1]
        # snap sub-pixel misalignment so corner rounding does not turn it into a hook
        if abs(b[0] - a[0]) <= 1.0:
            b = (a[0], b[1]) if b is not pts[-1] else b
        if abs(b[1] - a[1]) <= 1.0:
            b = (b[0], a[1]) if b is not pts[-1] else b
        dx, dy = b[0] - a[0], b[1] - a[1]
        if abs(dx) <= 1.0 or abs(dy) <= 1.0:
            out.append(b)
            continue
        if abs(dx) > 0.5 and abs(dy) > 0.5:
            prev_vertical = len(out) > 1 and abs(out[-2][0] - a[0]) < 0.5
            if prev_vertical or (len(out) == 1 and abs(dy) >= abs(dx)):
                my = a[1] + dy / 2
                out += [(a[0], my), (b[0], my)]
            else:
                mx = a[0] + dx / 2
                out += [(mx, a[1]), (mx, b[1])]
        out.append(b)
    return out


def _marker(kind: str, tone: str) -> str:
    return f"url(#{kind}-{tone})"


def draw_edge(e: dict, le: dict, off: tuple[float, float]) -> tuple[list[str], list[str]]:
    """Returns (edge svg, label svg) so labels can be painted last."""
    tone = e.get("tone", "ink")
    colour = MUTED if tone == "ink" else TONES[tone][0]
    out, labels = [], []
    for sec in le.get("sections", []):
        pts = [sec["startPoint"], *sec.get("bendPoints", []), sec["endPoint"]]
        pts = orthogonal([(p["x"] + off[0], p["y"] + off[1]) for p in pts])
        arrow = e.get("arrow", "end")
        mk = "tri" if arrow == "triangle" else "arr"
        m_end = _marker(mk, tone) if arrow in ("end", "both", "triangle") else ""
        m_start = _marker("arr", tone) if arrow == "both" else (_marker("dia", tone) if arrow == "diamond" else "")
        out.append(fk.path(fk.rounded_path(pts), stroke=colour, sw=1.5, dash="5 4" if e.get("dash") else "",
                           marker_end=m_end, marker_start=m_start))
    for lab in le.get("labels", []):
        lx, ly = lab["x"] + off[0], lab["y"] + off[1]
        labels.append(fk.rect(lx - 2, ly, lab["width"] + 4, lab["height"], fill="#FFFFFF", stroke="none",
                              rx=4, sw=0, opacity="0.92"))
        tx = lx + 3
        if e.get("code"):
            p, pw = fk.pill(lx + 1, ly + 1, e["code"], colour)
            labels += p
            tx = lx + pw + 5
        if e.get("label"):
            labels.append(fk.text(tx, ly + 13, e["label"], size=10.5, fill=MUTED))
    return out, labels


# ================================================================ figure assembly
def _legend_entries(spec: dict) -> list[tuple[str, str, str]]:
    if spec.get("frame") or spec.get("legend_only"):
        return list(spec.get("legend", []))
    seen, out = [], []
    for n in spec["nodes"]:
        t = n.get("tone", "system")
        if n.get("shape") in ("initial", "final") or t in seen or n.get("_container") and not n.get("dashed"):
            continue
        if n.get("_container") and n.get("dashed"):
            out.append(("none", TONES[t][0] + " dashed", n.get("legend", "Boundary")))
            seen.append(t + "-frame")
            continue
        seen.append(t)
        s, f = TONES[t]
        out.append((f if t != "muted" else GREY_BG, s + (" dashed" if t == "muted" else ""), fk.LEGEND_LABELS[t]))
    return out + list(spec.get("legend", []))


def assemble(spec: dict, body_w: float, body_h: float, body: list[str], min_w: float = 760) -> str:
    frame = spec.get("frame")
    fw, fh = body_w, body_h
    inner_off = (0.0, 0.0)
    if frame:
        inner_off = (16.0, 40.0)
        fw, fh = body_w + 32, body_h + 56
    width = max(fw + 2 * M, min_w)
    head, y_line = fk.header(width, spec["number"], spec["title"], spec.get("subtitle", ""), spec.get("ref", ""))
    top = y_line + 24
    out = list(head)
    if frame:
        out.append(fk.rect(M, top, fw, fh, fill="none", stroke=INK, rx=2, sw=1.2))
        tab = f"{frame['kind']} [{frame['type']}] {frame['name']}"
        tw = fk.text_w(tab, 11.5, True) + 26
        out.append(fk.path(f"M{M} {top} L{fk.fmt(M + tw)} {top} L{fk.fmt(M + tw)} {top + 14} "
                           f"L{fk.fmt(M + tw - 10)} {top + 24} L{M} {top + 24} Z", stroke=INK, sw=1.2, fill=CHIP))
        out.append(fk.text(M + 10, top + 17, tab, size=11.5, weight=700))
    out.append(f'<g transform="translate({fk.fmt(M + inner_off[0])} {fk.fmt(top + inner_off[1])})">')
    out += body
    out.append("</g>")
    y = top + fh + 30
    leg, y = fk.legend(M, y, _legend_entries(spec), width - M)
    out += leg
    y += 10
    for ln in fk.wrap(spec.get("footer", ""), width - 2 * M, 10.5):
        out.append(fk.text(M, y + 4, ln, size=10.5, fill=FAINT))
        y += 15
    return fk.svg(width, y + 18, f"Figure {spec['number']} · {spec['title']}", spec.get("subtitle", ""), out)


def render_graph(spec: dict, laid: dict) -> str:
    nodes = {n["id"]: n for n in spec["nodes"]}
    absol: dict[str, tuple[float, float]] = {"root": (0.0, 0.0)}
    containers, leaves = [], []

    def walk(g: dict, ox: float, oy: float, depth: int):
        for c in g.get("children", []):
            x, y = ox + c["x"], oy + c["y"]
            absol[c["id"]] = (x, y)
            if c.get("children"):
                containers.append((depth, c["id"], x, y, c["width"], c["height"]))
                walk(c, x, y, depth + 1)
            else:
                leaves.append((c["id"], x, y))
    walk(laid, 0, 0, 0)

    # ELK can leave an empty band at the bottom of a container for hierarchy ports; trim it when no edge bends
    # or labels sit in the band (straight edges still pass through the border).
    bend_pts: list[tuple[float, float]] = []      # bends and label corners (absolute)
    ends: list[tuple[dict, float, float]] = []    # (point dict, abs x, abs y) for section start/end points

    def collect(g: dict):
        for le in g.get("edges", []):
            ox, oy = absol.get(le.get("container", g["id"]), (0.0, 0.0))
            for sec in le.get("sections", []):
                bend_pts.extend((p["x"] + ox, p["y"] + oy) for p in sec.get("bendPoints", []))
                for key in ("startPoint", "endPoint"):
                    p = sec[key]
                    ends.append((p, p["x"] + ox, p["y"] + oy))
            for lab in le.get("labels", []):
                bend_pts.append((lab["x"] + ox, lab["y"] + oy))
                bend_pts.append((lab["x"] + ox, lab["y"] + oy + lab["height"]))
        for c in g.get("children", []):
            collect(c)
    collect(laid)
    sizes: dict[str, tuple[float, float]] = {}

    def sizes_of(g: dict):
        for c in g.get("children", []):
            sizes[c["id"]] = (c["width"], c["height"])
            sizes_of(c)
    sizes_of(laid)
    parent_of = {n["id"]: n.get("parent") for n in spec["nodes"]}
    kids_of: dict[str, list[str]] = {}
    for cid_, p in parent_of.items():
        if p:
            kids_of.setdefault(p, []).append(cid_)
    # ELK can leave an empty band at the bottom of a container for hierarchy ports. Trim it when nothing but
    # straight edge exits sits in the band; those exits move up with the border. Deepest containers first, so a
    # parent sees its children's trimmed heights.
    trimmed = []
    for depth, cid, x, y, w, h in sorted(containers, key=lambda t: -t[0]):
        content = max((absol[k][1] + sizes[k][1] for k in kids_of.get(cid, []) if k in absol), default=y + h - 18) + 18
        inside = lambda px, py: x - 1 <= px <= x + w + 1 and content < py <= y + h + 1  # noqa: E731
        movable = [(p, px, py) for p, px, py in ends if inside(px, py)]
        if (content < y + h - 4 and not any(inside(px, py) for px, py in bend_pts)
                and all(abs(py - (y + h)) <= 1 for _, _, py in movable)):
            for p, _, _ in movable:
                p["y"] -= (y + h) - content
            h = content - y
            sizes[cid] = (sizes[cid][0], h)
        trimmed.append((depth, cid, x, y, w, h))
    containers = trimmed

    body: list[str] = []
    for _, cid, x, y, w, h in sorted(containers, key=lambda t: t[0]):
        body += draw_container(nodes[cid], x, y, w, h)
    banners = []
    for _, cid, x, y, w, h in sorted(containers, key=lambda t: t[0]):
        banners += draw_banner(nodes[cid], x, y, w)
    edge_svg, label_svg = [], []
    by_id = {f"e{i}": e for i, e in enumerate(spec.get("edges", []))}

    def edges_of(g: dict):
        for le in g.get("edges", []):
            yield le, g["id"]
        for c in g.get("children", []):
            yield from edges_of(c)
    for le, owner in edges_of(laid):
        off = absol.get(le.get("container", owner), (0.0, 0.0))
        es, ls = draw_edge(by_id[le["id"]], le, off)
        edge_svg += es
        label_svg += ls
    body += edge_svg
    body += banners
    for nid, x, y in leaves:
        body += draw_leaf(nodes[nid], x, y)
    body += label_svg
    return assemble(spec, laid["width"], laid["height"], body)


# ================================================================ the 882E process rail (fixed layout)
ELEMENTS = ["Document approach", "Identify hazards", "Assess risk", "Identify mitigations", "Reduce risk",
            "Verify risk reduction", "Accept risk", "Manage life-cycle risk"]
HTS_LINKS = [2, 3, 4, 6, 7, 8]


def rail(spec: dict) -> str:
    """spec: number, title, subtitle, ref, footer, current (element no.), tasks [(id, name)],
    hts_current (bool), chip (label for a folder without an element), serves [element numbers]."""
    width = 1000
    inner = width - 2 * M
    gap = 20
    cw = (inner - 7 * gap) / 8
    ch = 86
    head, y_line = fk.header(width, spec["number"], spec["title"], spec.get("subtitle", ""), spec.get("ref", ""))
    out = list(head)
    top = y_line + 64
    xs = [M + i * (cw + gap) for i in range(8)]
    cur = spec.get("current")
    serves = set(spec.get("serves", []))

    # feedback loop 8 -> 2
    fy = top - 26
    x8, x2 = xs[7] + cw / 2, xs[1] + cw / 2
    out.append(fk.path(fk.rounded_path([(x8, top), (x8, fy), (x2, fy), (x2, top - 2)], r=10), stroke=FAINT, sw=1.5,
                       dash="5 4", marker_end="url(#arr-muted)"))
    out.append(fk.text((x2 + x8) / 2, fy - 7, "Change, deficiency, mishap or new hazard → re-identify and re-assess",
                       size=10.5, fill=MUTED, anchor="middle", halo=True))
    # arrows between cards
    for i in range(7):
        out.append(fk.path(f"M{fk.fmt(xs[i] + cw + 3)} {fk.fmt(top + ch / 2)} L{fk.fmt(xs[i + 1] - 4)} {fk.fmt(top + ch / 2)}",
                           stroke=MUTED, sw=1.5, marker_end="url(#arr-ink)"))
    # hazard tracking bar (drawn before cards' ticks end on it)
    by = top + ch + 30
    bx0, bx1 = xs[1], xs[7] + cw
    hts_cur = spec.get("hts_current")
    for k in HTS_LINKS:
        cx = xs[k - 1] + cw / 2
        out.append(fk.line(cx, top + ch, cx, by, stroke=INK if hts_cur else LINE, sw=1.3, dash="3 3"))
    # task / chip connectors (behind the bar)
    chip_y = by + 58
    if cur and spec.get("tasks"):
        cx = xs[cur - 1] + cw / 2
        out.append(fk.line(cx, top + ch, cx, chip_y, stroke=TONES["safety"][0], sw=1.8))
    elif spec.get("chip") and serves:
        for k in sorted(serves):
            cx = xs[k - 1] + cw / 2
            out.append(fk.line(cx, top + ch, cx, chip_y, stroke=INK, sw=1.4, dash="2 3"))
    out.append(fk.rect(bx0, by, bx1 - bx0, 30, fill=INK if hts_cur else GREY_BG, stroke=INK if hts_cur else LINE,
                       rx=15, sw=1.2))
    out.append(fk.text((bx0 + bx1) / 2, by + 19.5, "Hazard tracking system · Task 106 — hazards, mitigations, evidence and decisions",
                       size=11.5, weight=700, fill="#FFFFFF" if hts_cur else MUTED, anchor="middle"))
    # cards
    for i, name in enumerate(ELEMENTS):
        n = i + 1
        x = xs[i]
        is_cur = n == cur and not spec.get("tasks")
        is_parent = n == cur and spec.get("tasks")
        served = n in serves
        stroke, fill = (INK, INK) if is_cur else TONES["safety"] if is_parent else (INK, "#FFFFFF") if served else (LINE, "#FFFFFF")
        out.append(fk.rect(x, top, cw, ch, fill=fill, stroke=stroke, rx=10, sw=2 if (is_cur or is_parent or served) else 1.2))
        num_fill = "#FFFFFF" if is_cur else stroke if (is_parent or served) else MUTED
        out.append(fk.circle(x + 20, top + 20, 11, fill=num_fill, stroke="none", sw=0))
        out.append(fk.text(x + 20, top + 24.5, str(n), size=12, weight=700, anchor="middle",
                           fill=INK if is_cur else "#FFFFFF"))
        for j, ln in enumerate(fk.wrap(name, cw - 20, 11.5, True)):
            out.append(fk.text(x + 10, top + 50 + 15 * j, ln, size=11.5, weight=700, fill="#FFFFFF" if is_cur else INK))
    # task pills / folder chip
    y_end = by + 30
    if cur and spec.get("tasks"):
        cx = xs[cur - 1] + cw / 2
        px = cx
        rows = []
        for tid, tname in spec["tasks"]:
            label = f"Task {tid} · {tname}"
            w = fk.text_w(label, 12, True) + 28
            rows.append((label, w))
        total = sum(w for _, w in rows) + 8 * (len(rows) - 1)
        px = min(max(M, cx - total / 2), width - M - total)
        for label, w in rows:
            out.append(fk.rect(px, chip_y, w, 30, fill=INK, stroke=INK, rx=8, sw=1))
            out.append(fk.text(px + w / 2, chip_y + 19.5, label, size=12, weight=700, fill="#FFFFFF", anchor="middle"))
            px += w + 8
        p, _ = fk.pill(min(max(M, cx - total / 2), width - M - total), chip_y - 22, "THIS FOLDER", TONES["safety"][0])
        out += p
        y_end = chip_y + 30
    elif spec.get("chip"):
        ks = sorted(serves) or [1, 8]
        x0, x1 = xs[ks[0] - 1], xs[ks[-1] - 1] + cw
        if x1 - x0 < 260:
            mid = (x0 + x1) / 2
            x0, x1 = max(M, mid - 130), min(width - M, mid + 130)
        out.append(fk.rect(x0, chip_y, x1 - x0, 30, fill=INK, stroke=INK, rx=8, sw=1))
        out.append(fk.text((x0 + x1) / 2, chip_y + 19.5, spec["chip"], size=12, weight=700, fill="#FFFFFF", anchor="middle"))
        p, _ = fk.pill(x0, chip_y - 22, "THIS FOLDER", INK)
        out += p
        y_end = chip_y + 30
    y = y_end + 34
    entries = [(INK, INK, "This folder"), (TONES["safety"][1], TONES["safety"][0], "Element it belongs to"),
               ("#FFFFFF", INK, "Element it serves"), ("line:" + FAINT, FAINT + " dashed", "Iteration / feedback")]
    leg, y = fk.legend(M, y, entries, width - M)
    out += leg
    y += 10
    for ln in fk.wrap(spec.get("footer", ""), width - 2 * M, 10.5):
        out.append(fk.text(M, y + 4, ln, size=10.5, fill=FAINT))
        y += 15
    return fk.svg(width, y + 18, f"Figure {spec['number']} · {spec['title']}", spec.get("subtitle", ""), out)


# ================================================================ batch API
MAX_W, MAX_H = 1040, 1600       # content box that still reads at GitHub page width


def _flip(spec: dict) -> dict:
    alt = copy.deepcopy(spec)
    alt["direction"] = "DOWN" if spec.get("direction", "RIGHT") == "RIGHT" else "RIGHT"
    for n in alt["nodes"]:
        n.pop("direction", None)
    return alt


def render_all(specs: list[dict]) -> list[str]:
    """Render specs in order; graph specs share one ELK run.

    Unless a spec sets orient: fixed, it is laid out in its preferred direction and the flipped one; the preferred
    layout is kept when it fits MAX_W, otherwise the layout with the smaller overflow wins."""
    jobs = []                                   # (spec index, candidate spec)
    for i, s in enumerate(specs):
        if s.get("kind", "graph") != "graph":
            continue
        jobs.append((i, s))
        if s.get("orient") != "fixed":
            jobs.append((i, _flip(s)))
    laid = run_elk([to_elk(c) for _, c in jobs])
    best: dict[int, tuple[float, dict, dict]] = {}
    for rank, ((i, cand), g) in enumerate(zip(jobs, laid)):
        preferred = cand is specs[i]
        over = max(g["width"] / MAX_W, g["height"] / MAX_H)
        score = 0.0 if preferred and g["width"] <= MAX_W else over + (0 if preferred else 0.05)
        if i not in best or score < best[i][0]:
            best[i] = (score, cand, g)
    out: list[str] = [""] * len(specs)
    for i, (_, cand, g) in best.items():
        out[i] = render_graph(cand, g)
    for i, s in enumerate(specs):
        if s.get("kind") == "rail":
            out[i] = rail(s)
    return out
