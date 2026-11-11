"""Generate the SUS-I1 context and boundary figures from architecture/item-definition.yaml.

Usage: python -m tools.figures.fig_item [--check]

Every box label comes from the item-definition record; positions come from architecture/layout.yaml, which is
checked against the record (missing or unknown IDs, children outside parents, externals inside the boundary,
connectors crossing unrelated boxes all raise FigureError). --check exits 1 when a committed SVG is stale.
"""
from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

from tools.pdac.load import ROOT, _read_yaml
from tools.figures import figkit as fk
from tools.figures.figkit import FigureError

ITEM = "architecture/item-definition.yaml"
LAYOUT = "architecture/layout.yaml"
OUT = {
    "context": "docs/wiki/images/sus-i1-context.svg",
    "boundary": "docs/wiki/images/sus-i1-boundary.svg",
}
ROOT_ID = "SUS-I1"


# ---------------------------------------------------------------- model

def index(item: dict) -> tuple[dict, dict, list]:
    els = {e["id"]: e for e in item["elements"]}
    exts = {e["id"]: e for e in item["externals"]}
    return els, exts, item["interfaces"]


def chain(els: dict, eid: str) -> list[str]:
    out = []
    while eid in els:
        eid = els[eid]["parent"]
        out.append(eid)
    return out


def top(els: dict, eid: str) -> str:
    if eid not in els:
        return eid
    c = [eid] + chain(els, eid)
    return c[c.index(ROOT_ID) - 1]


def style(e: dict | None) -> tuple[str, str]:
    """(fill, stroke) for an element; None = external."""
    if e is None:
        return fk.EXT_BG, fk.EXT
    if e["safety_role"] == "protective":
        return fk.SAFETY_BG, fk.SAFETY
    if e["kind"] == "computing":
        return fk.SW_BG, fk.SW
    return fk.HW_BG, fk.HW


# ---------------------------------------------------------------- layout checks

def inside(inner, outer) -> bool:
    return (inner[0] >= outer[0] and inner[1] >= outer[1] and inner[0] + inner[2] <= outer[0] + outer[2]
            and inner[1] + inner[3] <= outer[1] + outer[3])


def overlap(a, b) -> bool:
    return not (a[0] + a[2] <= b[0] or b[0] + b[2] <= a[0] or a[1] + a[3] <= b[1] or b[1] + b[3] <= a[1])


def seg_hits_rect(x1, y1, x2, y2, r, pad=3.0) -> bool:
    """Liang-Barsky: does segment (x1,y1)-(x2,y2) pass through rect r shrunk by pad?"""
    rx0, ry0, rx1, ry1 = r[0] + pad, r[1] + pad, r[0] + r[2] - pad, r[1] + r[3] - pad
    dx, dy = x2 - x1, y2 - y1
    t0, t1 = 0.0, 1.0
    for p, q in ((-dx, x1 - rx0), (dx, rx1 - x1), (-dy, y1 - ry0), (dy, ry1 - y1)):
        if p == 0:
            if q < 0:
                return False
            continue
        t = q / p
        if p < 0:
            t0 = max(t0, t)
        else:
            t1 = min(t1, t)
        if t0 > t1:
            return False
    return True


def check_layout(view: str, spec: dict, expected: set, els: dict) -> dict:
    boxes = {k: tuple(v) for k, v in (spec.get("boxes") or {}).items()}
    missing, unknown = expected - set(boxes), set(boxes) - expected
    if missing:
        raise FigureError(f"{view}: no box for {sorted(missing)}")
    if unknown:
        raise FigureError(f"{view}: box for unknown id {sorted(unknown)}")
    for k, b in boxes.items():
        if len(b) != 4 or b[2] <= 0 or b[3] <= 0:
            raise FigureError(f"{view}: bad box for {k}: {b}")
        if b[0] < 0 or b[1] < 90 or b[0] + b[2] > spec["width"] or b[1] + b[3] > spec["height"] - 40:
            raise FigureError(f"{view}: box {k} leaves the drawing area")
        if k == ROOT_ID:
            continue
        if k in els:
            parent = els[k]["parent"]
            if parent in boxes and not inside(b, boxes[parent]):
                raise FigureError(f"{view}: {k} is not inside its parent {parent}")
        elif overlap(b, boxes[ROOT_ID]):
            raise FigureError(f"{view}: external {k} overlaps the system boundary")
    ids = sorted(k for k in boxes if k != ROOT_ID)
    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            related = a in chain(els, b) or b in chain(els, a)
            if not related and overlap(boxes[a], boxes[b]):
                raise FigureError(f"{view}: boxes {a} and {b} overlap")
    return boxes


# ---------------------------------------------------------------- edges

def edge_groups(interfaces: list, mapper) -> dict:
    """{(a, b) sorted: [interfaces]} after mapping endpoints; interfaces collapsing onto one box are dropped."""
    groups: dict = {}
    for i in interfaces:
        a, b = mapper(i["from"]), mapper(i["to"])
        if a == b:
            continue
        groups.setdefault(tuple(sorted((a, b))), []).append(i)
    return dict(sorted(groups.items()))


def polyline(boxes, a, b, waypoints) -> list[tuple[float, float]]:
    ba, bb = boxes[a], boxes[b]
    pts = [tuple(p) for p in waypoints]
    if not pts:
        x1, y1, x2, y2 = fk.connect(ba, bb)
        return [(x1, y1), (x2, y2)]
    first = fk.border_point(ba, *pts[0])
    last = fk.border_point(bb, *pts[-1])
    return [first, *pts, last]


def draw_edges(view: str, boxes: dict, groups: dict, routes: dict, els: dict, mapper) -> tuple[list, list]:
    lines, labels, crossings = [], [], []
    known = {f"{a}|{b}" for a, b in groups}
    unknown = set(routes) - known
    if unknown:
        raise FigureError(f"{view}: route for unknown connector {sorted(unknown)}")
    for (a, b), ifs in groups.items():
        route = routes.get(f"{a}|{b}") or {}
        if isinstance(route, list):
            route = {"via": route}
        pts = polyline(boxes, a, b, route.get("via") or [])
        exempt = {a, b, *chain(els, a), *chain(els, b), ROOT_ID}
        exempt |= {k for k in boxes if a in chain(els, k) or b in chain(els, k)}
        for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
            for k, r in boxes.items():
                if k not in exempt and seg_hits_rect(x1, y1, x2, y2, r):
                    crossings.append(f"{a}|{b} crosses {k}")
        dirs = set()
        for i in ifs:
            if i["direction"] == "bi":
                dirs.update({"start", "end"})
            else:
                dirs.add("end" if mapper(i["from"]) == a else "start")
        dash = "5 4" if all(i.get("status") == "candidate" for i in ifs) else ""
        for j, ((x1, y1), (x2, y2)) in enumerate(zip(pts, pts[1:])):
            start = "url(#arr)" if "start" in dirs and j == 0 else ""
            end = "url(#arr)" if "end" in dirs and j == len(pts) - 2 else ""
            lines.append(fk.line(x1, y1, x2, y2, stroke=fk.MUTED, sw=1.3, dash=dash, start=start, end=end))
        # label at the midpoint of the longest segment
        if route.get("label"):
            mx, my = route["label"]
        else:
            seg = max(zip(pts, pts[1:]), key=lambda s: (s[1][0] - s[0][0]) ** 2 + (s[1][1] - s[0][1]) ** 2)
            mx, my = (seg[0][0] + seg[1][0]) / 2, (seg[0][1] + seg[1][1]) / 2
        ids = [i["id"] for i in ifs]
        n = len(ids)
        for k, iid in enumerate(ids):
            labels += fk.pill(mx, my + (k - (n - 1) / 2) * 15, iid, size=8.5)
    if crossings:
        raise FigureError(f"{view}: connectors cross unrelated boxes (add waypoints under routes): "
                          + "; ".join(sorted(set(crossings))))
    return lines, labels


# ---------------------------------------------------------------- boxes

def draw_box(bid: str, box, e: dict | None, ext: dict | None, container: bool, children: list | None = None) -> list[str]:
    x, y, w, h = box
    fill, stroke = style(e)
    dash = "6 4" if (e and e.get("status") == "candidate") else ""
    out = []
    if container:
        out.append(fk.rect(x, y, w, h, fill="#FFFFFF", stroke=stroke, sw=1.4, rx=12, dash=dash))
        out.append(fk.text(x + 12, y + 20, bid, size=11, fill=stroke, weight=700))
        off = fk.text_w(bid, 11, True) + 22
        out.append(fk.text(x + 12 + off, y + 20, fk.wrap(e["name"], w - 24 - off, 11, 1)[0], size=11, fill=fk.MUTED))
        return out
    name = (e or ext)["name"]
    out.append(fk.rect(x, y, w, h, fill=fill, stroke=stroke, sw=1.3, rx=8, dash=dash))
    out.append(fk.text(x + 10, y + 18, bid, size=10, fill=stroke, weight=700))
    name_lines = fk.wrap(name, w - 20, 10.5, 2)
    for k, ln in enumerate(name_lines):
        out.append(fk.text(x + 10, y + 35 + k * 14, ln, size=10.5, fill=fk.INK))
    if e and e.get("decision"):
        out.append(fk.text(x + w - 8, y + h - 8, f"candidate · {e['decision']}", size=8.5, fill=fk.MUTED, anchor="end"))
    if children:
        cy = y + 35 + len(name_lines) * 14 + 8
        for c in children:
            if cy > y + h - 8:
                break
            out.append(fk.text(x + 14, cy, fk.wrap(f"{c['id']} · {c['name']}", w - 28, 9.5, 1)[0], size=9.5, fill=fk.MUTED))
            cy += 13
    return out


def build_view(view: str, item: dict, layout: dict, digest: str) -> str:
    els, exts, ifs = index(item)
    spec = layout[view]
    if view == "context":
        shown = {k for k, e in els.items() if e["parent"] == ROOT_ID}
        mapper = lambda x: top(els, x)  # noqa: E731
        title = "SUS-I1 system context"
        sub = "Top-level elements inside the boundary and the external elements they interface with"
    else:
        shown = set(els)
        mapper = lambda x: x  # noqa: E731
        title = "SUS-I1 boundary and interfaces"
        sub = "Every element of the item definition, its parent, the external elements and every interface (IDs on the connectors)"
    expected = shown | set(exts) | {ROOT_ID}
    boxes = check_layout(view, spec, expected, els)
    groups = edge_groups(ifs, mapper)
    lines, labels = draw_edges(view, boxes, groups, spec.get("routes") or {}, els, mapper)
    W, H = spec["width"], spec["height"]
    body = fk.header(W, title, sub, f"{item['id']} item definition · rev {item['revision']} ({item['status']})")
    legend, _ = fk.legend(40, 108, [(fk.HW_BG, fk.HW, "hardware / mixed"), (fk.SW_BG, fk.SW, "computing"),
                                     (fk.SAFETY_BG, fk.SAFETY, "protective function"),
                                     (fk.EXT_BG, fk.EXT, "outside the boundary"),
                                     ("#FFFFFF", fk.MUTED + " dashed", "candidate (open decision)")])
    body += legend
    rx, ry, rw, rh = boxes[ROOT_ID]
    body.append(fk.rect(rx, ry, rw, rh, fill=fk.CHIP, stroke=fk.INK, sw=1.6, rx=14, dash="8 5"))
    body.append(fk.text(rx + 14, ry + rh - 12, f"{ROOT_ID} boundary · {item['title']}", size=11, fill=fk.INK, weight=700))
    parents = {e["parent"] for e in els.values()}
    order = sorted(shown, key=lambda k: (len(chain(els, k)), k))
    for k in order:
        kids = [els[c] for c in sorted(els) if els[c]["parent"] == k] if view == "context" else None
        body += draw_box(k, boxes[k], els[k], None, container=(view == "boundary" and k in parents), children=kids)
    body += lines
    for k in sorted(exts):
        body += draw_box(k, boxes[k], None, exts[k], container=False)
    body += labels
    n_if = sum(len(v) for v in groups.values())
    body += fk.footer(W, H, f"Generated by tools/figures/fig_item.py from {ITEM} and {LAYOUT} · digest {digest} · "
                            f"{n_if} interfaces shown · concept, not reviewed")
    desc = (f"{title}. Inside the boundary: " + ", ".join(f"{k} {els[k]['name']}" for k in order) +
            ". Outside: " + ", ".join(f"{k} {exts[k]['name']}" for k in sorted(exts)) +
            ". Connectors: " + "; ".join(f"{a}–{b}: {', '.join(i['id'] for i in v)}" for (a, b), v in groups.items()) + ".")
    return fk.svg(W, H, title, desc, body)


def build(root: Path = ROOT) -> dict[str, str]:
    item = _read_yaml(root / ITEM)
    layout = _read_yaml(root / LAYOUT)
    digest = hashlib.sha256((root / ITEM).read_bytes() + (root / LAYOUT).read_bytes()).hexdigest()[:12]
    return {OUT[v]: build_view(v, item, layout, digest) for v in OUT}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args(argv)
    try:
        outputs = build()
    except FigureError as exc:
        print(f"FigureError: {exc}")
        return 1
    stale = []
    for rel, text in outputs.items():
        path = ROOT / rel
        if path.exists() and path.read_text(encoding="utf-8") == text:
            continue
        if args.check:
            stale.append(rel)
        else:
            path.write_text(text, encoding="utf-8")
            print(f"wrote {rel}")
    if stale:
        print("Stale figures; run: python -m tools.figures.fig_item")
        for s in stale:
            print(f"  {s}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
