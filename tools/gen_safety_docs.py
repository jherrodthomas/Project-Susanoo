#!/usr/bin/env python3
"""Generate the MIL-STD-882E folder READMEs, SVG figures and SysML views from catalog.yaml.

PDaC rule: the folder tree, its figures and its SysML views come from one typed catalog (plus the SysML
models it points at) so they cannot drift apart.

Each folder gets:
  README.md            metadata, purpose, figures, tables; human content below END_MARKER is preserved
  figures/fig-N-*.svg  1 flow position · 2 block · 3 boundary · 4.. SysML views · last inputs/outputs
  <Package>.sysml      generated SysML v2 view (the model of record for the folder)

Usage:
    python3 tools/gen_safety_docs.py           # write files
    python3 tools/gen_safety_docs.py --check   # exit 1 if any file is stale
Needs `npm ci` in tools/figures (pinned ELK layout engine).
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools" / "figures"))
sys.path.insert(0, str(ROOT))
import diagram  # noqa: E402
from tools.sysml import model as sysml_model  # noqa: E402  main's SysML reader (models/sysml/model)
import sysml_parse  # noqa: E402
from layoutkit import MUTED, TONES  # noqa: E402

CATALOG = ROOT / "safety" / "mil-std-882e" / "catalog.yaml"
END_MARKER = "<!-- END GENERATED: content below this line is human-authored and preserved -->"
DEFAULT_TAIL = "\n## Working content\n\n_No analysis content yet. Add authored material below this heading._\n"
GEN = "tools/gen_safety_docs.py"
ITEM_DEF = ROOT / "architecture" / "item-definition.yaml"
REQ_DIR = ROOT / "requirements"
LIBRARY = ROOT / "models" / "sysml" / "model" / "SusanooLibrary.sysml"
ARCH = "models/sysml/model/Architecture.sysml"


# ----------------------------------------------------------------- helpers
def mid(text: str) -> str:
    s = re.sub(r"[^A-Za-z0-9]", "_", text)
    return ("n_" + s) if s[:1].isdigit() else s


def sysml_name(text: str) -> str:
    s = re.sub(r"[^A-Za-z0-9]+", " ", text).title().replace(" ", "")
    return ("_" + s) if s[:1].isdigit() else s


def doc(text: str, indent: str = "") -> str:
    return f"{indent}doc /* {str(text).replace('*/', '* /')} */"


def rel(target: Path, start: Path) -> str:
    return os.path.relpath(target, start).replace(os.sep, "/")


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def edge_leg(label: str, dashed: bool = False, tone: str = "") -> tuple[str, str, str]:
    c = TONES[tone][0] if tone else MUTED
    return ("line:" + c, c + (" dashed" if dashed else ""), label)


class Ctx:
    """Everything the generator reads. System elements, externals and interfaces come from the item-definition
    record; usage paths, requirements and satisfy relations from the SysML model in models/sysml/model. The
    catalog only adds what is specific to the 882E work-product tree."""

    def __init__(self, cat: dict):
        self.cat = cat
        self.elements = {e["n"]: e for e in cat["elements"]}
        self.folders = {f["id"]: f for f in cat["folders"]}
        self.base = ROOT / cat["base"]
        item = yaml.safe_load(ITEM_DEF.read_text())
        self.model = sysml_model.load()
        self.nodes: dict[str, dict] = {}
        root = item["id"]
        self.nodes[root] = {"label": item["title"].removeprefix(f"{root} ").capitalize(), "kind": "system"}
        for e in item["elements"]:
            kind = "safety" if e.get("safety_role") == "protective" else (
                "software" if e.get("kind") == "computing" else "system")
            self.nodes[e["id"]] = {"label": e["name"], "parent": e["parent"], "kind": kind}
        for x in item["externals"]:
            self.nodes[x["id"]] = {"label": x["name"], "kind": "external"}
        for k, n in self.nodes.items():
            me = self.model.elements.get(k)
            if me:
                n["sysml"], n["usage"] = me.type, "context." + me.path
        self.interfaces = item["interfaces"]
        internal = [i for i in self.interfaces
                    if self.nodes.get(i["from"], {}).get("kind") != "external"
                    and self.nodes.get(i["to"], {}).get("kind") != "external"]
        merged: dict[tuple[str, str], list[dict]] = {}
        for i in internal:
            merged.setdefault((i["from"], i["to"]), []).append(i)
        self.links = [(a, b, ifs) for (a, b), ifs in merged.items()]
        self.reqs = {p.stem: yaml.safe_load(p.read_text()) for p in sorted(REQ_DIR.glob("SYS-*.yaml"))}

    def path(self, fid: str) -> Path:
        return self.base / self.folders[fid]["path"]

    def label(self, key: str) -> str:
        n = self.nodes.get(key)
        return f"{key}: {n['label']}" if n else key

    def kind(self, key: str) -> str:
        n = self.nodes.get(key)
        return n.get("kind", "system") if n else "work"

    def children(self, key: str) -> list[str]:
        return [k for k, v in self.nodes.items() if v.get("parent") == key]

    def expand(self, keys: list[str]) -> set[str]:
        out: set[str] = set()
        stack = list(keys)
        while stack:
            k = stack.pop()
            if k not in out:
                out.add(k)
                stack.extend(self.children(k))
        return out

    def interfaces_between(self, a: str, b: str) -> list[str]:
        """IDs of item-definition interfaces joining a and b (either direction, descendants included)."""
        ea, eb = self.expand([a]), self.expand([b])
        return [i["id"] for i in self.interfaces
                if (i["from"] in ea and i["to"] in eb) or (i["from"] in eb and i["to"] in ea)]

    def card(self, key: str, nid: str | None = None, tone: str | None = None) -> dict:
        """A figure node for a registry element or a free-text boundary entry."""
        n = self.nodes.get(key)
        if n:
            return {"id": nid or mid(key), "code": key, "title": n["label"], "tone": tone or n.get("kind", "system")}
        return {"id": nid or mid(key), "title": key, "tone": tone or "work"}


def short_ifs(ids: list[str]) -> str:
    """IF-PX4-005, IF-PX4-006 -> IF-PX4-005/006."""
    if len(ids) == 1:
        return ids[0]
    head = ids[0].rsplit("-", 1)[0]
    if all(i.rsplit("-", 1)[0] == head for i in ids):
        return head + "-" + "/".join(i.rsplit("-", 1)[1] for i in ids)
    return " · ".join(ids)


# ------------------------------------------------------------- figures
def fig_rail(ctx: Ctx, f: dict) -> dict:
    spec = {"kind": "rail", "title": "Position in the MIL-STD-882E flow", "ref": f"catalog.yaml · {f['id']}"}
    el = f.get("element")
    if el and f.get("tasks"):
        spec.update(current=el, tasks=[(t["id"], t["name"]) for t in f["tasks"]],
                    subtitle=f"{f['title']} belongs to element {el} ({ctx.elements[el]['name'].lower()}). "
                             "Everything it finds or decides is recorded in the hazard tracking system.")
    elif el:
        spec.update(current=el, subtitle=f"This folder is element {el} of the iterative system safety process: "
                                         f"{ctx.elements[el]['name'].lower()}.")
    elif f.get("crosscut") == "hts":
        spec.update(hts_current=True, subtitle="The hazard tracking system is the closed loop shared by every element: "
                                               "hazards in, mitigations, evidence and decisions linked, status out.")
        if f["id"] == "ROOT":
            spec.update(chip="Whole program: folders 00–08, hazard tracking and software safety", serves=list(range(1, 9)),
                        hts_current=False,
                        subtitle="The tree is organised by the eight MIL-STD-882E process elements; tasks sit under "
                                 "the element they mainly serve.")
    else:
        served = sorted({ctx.folders[o["ref"]].get("element") for o in f.get("outputs", []) + f.get("inputs", [])
                         if "ref" in o and ctx.folders[o["ref"]].get("element")})
        spec.update(chip=f["title"], serves=served,
                    subtitle=f"{f['title']} is not one element: it serves elements "
                             f"{', '.join(map(str, served))} through the folders it feeds and reads.")
    return spec


def fig_block(ctx: Ctx, f: dict) -> dict:
    scope = ctx.expand(f.get("scope", []))
    root = next(k for k, v in ctx.nodes.items() if not v.get("parent") and v.get("kind") != "external")
    # A sub-assembly below subsystem level (e.g. SUS-M1-PWR) is drawn as one block unless the folder's scope names
    # it or one of its parts explicitly; its internal interfaces are then folded into it.
    named = set(f.get("scope", []))
    collapsed = {k for k, v in ctx.nodes.items()
                 if v.get("parent") not in (None, root) and ctx.children(k) and not (ctx.expand([k]) & named)}
    hidden = set().union(*[ctx.expand(ctx.children(k)) for k in collapsed]) if collapsed else set()

    def shown(k: str) -> str:
        while k in hidden:
            k = ctx.nodes[k]["parent"]
        return k
    nodes = []
    for k, v in ctx.nodes.items():
        if v.get("kind") == "external" or k in hidden:
            continue
        kids = [c for c in ctx.children(k) if c not in hidden]
        if not v.get("parent"):
            nodes.append({"id": mid(k), "banner": f"{k} · {v['label']}", "tone": "work"})
        elif kids:
            inside = bool(ctx.expand([k]) & scope)
            nodes.append({"id": mid(k), "title": f"{k} · {v['label']}", "parent": mid(v["parent"]),
                          "tone": "system" if inside else "muted"})
        else:
            nodes.append({**ctx.card(k, tone=v.get("kind", "system") if k in scope else "muted"),
                          "parent": mid(v["parent"]), "minw": 150, "maxw": 196})
    # Interfaces inside one subsystem are drawn element to element. Interfaces between subsystems are aggregated
    # into one edge between the subsystem panels carrying every IF ID; the N2 view has the element-level detail.

    def top(k: str) -> str:
        while ctx.nodes[k].get("parent") not in (root, None):
            k = ctx.nodes[k]["parent"]
        return k
    inner, cross = [], {}
    for a, b, ifs in ctx.links:
        a, b = shown(a), shown(b)
        if a == b:
            continue                        # folded into a collapsed sub-assembly
        ta, tb = top(a), top(b)
        if ta == tb:
            inner.append((a, b, ifs))
        else:
            key = tuple(sorted((ta, tb)))
            cross.setdefault(key, {"pairs": set(), "ifs": [], "safety": False})
            cross[key]["pairs"].add((ta, tb))
            cross[key]["ifs"] += [i["id"] for i in ifs]
            cross[key]["safety"] |= ctx.kind(a) == "safety"
    edges = [{"src": mid(a), "dst": mid(b), "code": short_ifs([i["id"] for i in ifs]),
              "label": ifs[0]["name"] if len(ifs) == 1 else f"{len(ifs)} interfaces",
              "tone": "safety" if ctx.kind(a) == "safety" else "ink"} for a, b, ifs in inner]
    for (ta, tb), c in cross.items():
        src, dst = sorted(c["pairs"])[0]
        edges.append({"src": mid(src), "dst": mid(dst), "code": f"{len(c['ifs'])} IF",
                      "label": ", ".join(sorted(set(c["ifs"]))) if len(c["ifs"]) <= 2 else
                      f"{sorted(c['ifs'])[0]} …", "arrow": "both" if len(c["pairs"]) > 1 else "end",
                      "tone": "safety" if c["safety"] else "ink", "dash": True})
    in_n = len([k for k in scope if not ctx.children(k)])
    return {"title": "Block diagram", "ref": f"item-definition.yaml · {f['id']}", "direction": "DOWN",
            "hierarchy": "separate",
            "subtitle": (f"SUS-I1 decomposition. The {in_n} coloured blocks are in scope for this folder; hatched blocks "
                         "are not." if scope else "SUS-I1 decomposition. No system element is in scope for this folder "
                         "(all hatched)."),
            "nodes": nodes, "edges": edges,
            "legend": [edge_leg("Interface inside a subsystem (IF-nnn)"), edge_leg("Protective interface", tone="safety"),
                       edge_leg("Interfaces between subsystems (count; see N2 view)", True)]}


def fig_boundary(ctx: Ctx, f: dict) -> dict:
    b = f["boundary"]
    nodes = [{"id": "BND", "banner": f"Boundary · {b['name']}", "tone": "safety", "dashed": True,
              "legend": "Analysis boundary", "direction": "DOWN"}]
    targets = {c for _, c, _ in b["flows"]}
    left = [k for k in b["outside"] if k not in targets]
    right = [k for k in b["outside"] if k in targets]
    nodes = [ctx.card(k, tone="external") for k in left] + nodes
    for k in b["inside"]:
        nodes.append({**ctx.card(k), "parent": "BND"})
    for k in right:
        nodes.append(ctx.card(k, tone="external"))
    edges = [{"src": "BND" if a == "@boundary" else mid(a), "dst": "BND" if c == "@boundary" else mid(c),
              "code": str(i + 1), "label": lab} for i, (a, c, lab) in enumerate(b["flows"])]
    return {"title": "Boundary diagram", "ref": f"catalog.yaml · {f['id']}", "direction": "RIGHT",
            "subtitle": f"{b['name']}: what is inside the dashed boundary, what is outside, and every interaction "
                        "that crosses it, numbered as in the table below.",
            "nodes": nodes, "edges": edges,
            "legend": [("#475569", "none", "1 · numbered crossing (see table)")]}


def fig_io(ctx: Ctx, f: dict) -> dict:
    nodes: list[dict] = []
    edges, seen = [], {}

    def node_for(it: dict) -> str:
        if "ref" in it:
            key, n = it["ref"], {"title": ctx.folders[it["ref"]]["title"], "sub": ctx.folders[it["ref"]]["path"],
                                 "tone": "work"}
        elif "doc" in it:
            key, n = it["doc"], {"title": Path(it["doc"]).name, "sub": str(Path(it["doc"]).parent), "tone": "external"}
        else:
            key, n = it["ext"], {"title": it["ext"], "tone": "external"}
        if key not in seen:
            seen[key] = f"n{len(seen)}"
            nodes.append({"id": seen[key], **n, "maxw": 220})
        return seen[key]
    for it in f.get("inputs", []):
        edges.append({"src": node_for(it), "dst": "THIS", "label": it["item"]})
    nodes.append({"id": "THIS", "code": f["id"], "title": f["title"], "tone": "current", "maxw": 230})
    for it in f.get("outputs", []):
        edges.append({"src": "THIS", "dst": node_for(it), "label": it["item"]})
    return {"title": "Inputs and outputs", "ref": f"catalog.yaml · {f['id']}", "direction": "RIGHT",
            "subtitle": "What this folder consumes (left) and produces (right). White cards are other folders in the "
                        "tree; grey cards are documents or parties outside it.",
            "nodes": nodes, "edges": edges}


# ----------------------------------------------------------- SysML views
def view_bdd(v: dict, pkg: str) -> tuple[dict, str]:
    nodes, edges, s = [], [], []
    stereo = {b["name"]: b.get("stereotype", "part") for b in v["blocks"]}
    label = {"part": "part def", "item": "item def", "attribute": "attribute def", "enum": "enum def"}
    for b in v["blocks"]:
        if b.get("import"):
            # Drawn from the library definition itself; nothing is redefined in this view.
            d = sysml_parse.definition(LIBRARY, b["name"])
            stereo[b["name"]] = d["kind"]
            nodes.append({"id": b["name"], "shape": "class", "title": b["name"], "attrs": d["members"],
                          "stereotype": f"{d['kind']} def · {b['import']}",
                          "tone": "interface" if d["kind"] == "enum" else "external"})
            continue
        st = b.get("stereotype", "part")
        if st == "enum":
            nodes.append({"id": b["name"], "shape": "class", "title": b["name"], "stereotype": "enum def",
                          "attrs": list(b["values"]), "tone": "interface"})
            s.append(f"    enum def {b['name']} {{")
            if b.get("doc"):
                s.append(doc(b["doc"], "        "))
            s += [f"        enum {val};" for val in b["values"]]
            s.append("    }")
            continue
        s.append(f"    {label[st]} {b['name']} {{")
        if b.get("doc"):
            s.append(doc(b["doc"], "        "))
        attrs = []
        for a in b.get("attributes", []):
            name, typ = [x.strip() for x in a.split(":")]
            attrs.append(f"{name} : {typ}")
            s.append(f"        attribute {name} : {typ};")
        for p in b.get("parts", []):
            mult = p.get("mult", "1")
            tst = stereo.get(p["type"], p.get("usage", "item"))
            usage = {"part": "part", "item": "ref item", "attribute": "attribute", "enum": "attribute"}[tst]
            s.append(f"        {usage} {p['name']} : {p['type']}[{mult}];")
            if p["type"] not in stereo and not any(n["id"] == p["type"] for n in nodes):
                nodes.append({"id": p["type"], "shape": "class", "title": p["type"], "tone": "external",
                              "stereotype": "item def · SusanooLibrary"})
            edges.append({"src": b["name"], "dst": p["type"], "label": f"{p['name']} [{mult}]", "arrow": "diamond"})
        s.append("    }")
        nodes.append({"id": b["name"], "shape": "class", "title": b["name"], "stereotype": label[st], "attrs": attrs,
                      "tone": "system"})
    for b in v["blocks"]:
        attrs_of = [m for m in next((n["attrs"] for n in nodes if n["id"] == b["name"]), [])] if b.get("import") \
            else b.get("attributes", [])
        for a in attrs_of:
            if ":" not in a:
                continue
            name, typ = [x.strip() for x in a.split(":")]
            typ = typ.split("[")[0]
            if typ in stereo and typ != b["name"]:
                edges.append({"src": b["name"], "dst": typ, "label": name, "tone": "interface", "dash": True})
    text = "\n".join(s)
    for parent, child in v.get("specializations", []):
        edges.append({"src": child, "dst": parent, "arrow": "triangle"})
        text = re.sub(rf"(def {child}) \{{", rf"\1 :> {parent} {{", text)
    # keep definitions in catalog order with imported types after their owners
    order = {b["name"]: i for i, b in enumerate(v["blocks"])}
    nodes.sort(key=lambda n: order.get(n["id"], 999))
    frag = {"frame": {"kind": "bdd", "type": "package", "name": pkg}, "direction": "RIGHT", "nodes": nodes,
            "edges": edges, "legend": [edge_leg("Composition / reference (diamond at owner)"),
                                       edge_leg("Attribute typed by", True, "interface"),
                                       ("#EEF2FF", "#4F46E5", "Defined in this view"),
                                       ("#F5F3FF", "#7C3AED", "Enumeration"),
                                       ("#F1F5F9", "#64748B", "Imported from SusanooLibrary")]}
    return frag, text


RISK_TONE = {"High": "red", "Medium": "amber", "Low": "ok"}


def view_req(ctx: Ctx, v: dict, pkg: str) -> tuple[dict, str]:
    """Requirements view. Entries with `record: true` (or `records: all`) are requirement records
    (requirements/SYS-*.yaml) owned by models/sysml/model/Requirements.sysml: they are drawn and exposed, never
    redefined, and their satisfy relations come from Satisfaction.sysml. Other entries are local candidate
    requirements defined in this view."""
    entries = list(v.get("requirements", []))
    if v.get("records") == "all":
        entries = [{"id": k, "record": True} for k, r in ctx.reqs.items() if r.get("safety_significant")] + entries
    nodes, edges, s, exposed = [], [], [], []
    ref = {}
    for r in entries:
        rid = mid(r["id"])
        if r.get("record"):
            rec, mr = ctx.reqs[r["id"]], ctx.model.requirements[r["id"]]
            ref[r["id"]] = f"SusanooRequirements::'{r['id']}'"
            exposed.append(ref[r["id"]])
            pills = ([("safety-significant", "red")] if rec.get("safety_significant") else []) + \
                [(m, "system") for m in rec.get("verification", {}).get("method", [])]
            nodes.append({"id": rid, "shape": "requirement", "title": mr.name, "code": r["id"], "text": rec["statement"],
                          "stereotype": f"requirement · {rec.get('status', 'record')}", "tone": "external",
                          "pills": pills})
            continue
        ref[r["id"]] = rid.lower()
        nodes.append({"id": rid, "shape": "requirement", "title": r["name"], "code": r["id"], "text": r["text"],
                      "stereotype": "requirement def · candidate", "tone": "system",
                      "pills": [(r.get("risk", "Medium"), RISK_TONE.get(r.get("risk", "Medium"), "amber")),
                                (r.get("verify", "Test"), "system")]})
        s += [f"    requirement def <'{r['id']}'> {r['name']} {{", doc(r["text"], "        "), "    }",
              f"    requirement {rid.lower()} : {r['name']};"]
    in_view = {r["id"] for r in entries}
    seen = set()

    def element(el: str):
        if el not in seen:
            seen.add(el)
            nodes.append({**ctx.card(el, nid="el_" + mid(el)), "minw": 150})
    for rid, el, *_ in ctx.model.satisfies:
        if rid in in_view and any(e.get("record") and e["id"] == rid for e in entries):
            element(el)
            edges.append({"src": "el_" + mid(el), "dst": mid(rid), "label": "«satisfy»", "dash": True})
    for el, rid in v.get("satisfied_by", []):
        element(el)
        edges.append({"src": "el_" + mid(el), "dst": mid(rid), "label": "«satisfy»", "dash": True})
        s.append(f"    satisfy {ref[rid]} by {ctx.nodes[el]['usage']};")
    verifies: dict[str, list[str]] = {}
    for el, rid in v.get("verified_by", []):
        if el not in seen:
            seen.add(el)
            nodes.append({"id": "el_" + mid(el), "code": el, "title": "Verification case", "tone": "ok"})
        edges.append({"src": "el_" + mid(el), "dst": mid(rid), "label": "«verify»", "dash": True, "tone": "ok"})
        verifies.setdefault(el, []).append(rid)
    for el, rids in verifies.items():
        s += [f"    verification def <'{el}'> {sysml_name(el)} {{", "        objective {",
              *[f"            verify {ref[r]};" for r in rids], "        }", "    }"]
    for a, b in v.get("derives", []):
        edges.append({"src": mid(b), "dst": mid(a), "label": "«deriveReqt»", "dash": True, "tone": "interface"})
        s.append(f"    #derivation connection {{ end #original ::> {ref[a]}; end #derive ::> {ref[b]}; }}")
    if exposed:
        s = [f"    // Requirement records shown here are owned by {'models/sysml/model/Requirements.sysml'} "
             "(generated from requirements/); satisfy relations by Satisfaction.sysml.",
             "    view requirementsInScope {", *[f"        expose {x};" for x in exposed], "    }"] + s
    legend = [edge_leg("«satisfy»", True)]
    if v.get("verified_by"):
        legend.append(edge_leg("«verify»", True, "ok"))
    if v.get("derives"):
        legend.append(edge_leg("«deriveReqt»", True, "interface"))
    if exposed:
        legend.append(("#F1F5F9", "#64748B", "Requirement record (requirements/)"))
    if any(not e.get("record") for e in entries):
        legend.append(("#EEF2FF", "#4F46E5", "Candidate defined in this view"))
    frag = {"frame": {"kind": "req", "type": "package", "name": pkg}, "direction": "RIGHT", "nodes": nodes,
            "edges": edges, "legend": legend}
    return frag, "\n".join(s)


def view_act(v: dict) -> tuple[dict, str]:
    nodes = [{"id": "start", "shape": "initial"}]
    edges = []
    s = [f"    action def {v['name']} {{"]
    if v.get("doc"):
        s.append(doc(v["doc"], "        "))
    for st in v["steps"]:
        nodes.append({"id": st["name"], "shape": "action", "title": st["label"],
                      "tone": "safety" if st.get("safety") else "system"})
        s.append(f"        action {st['name']} {{ {doc(st['label'])} }}")
    nodes.append({"id": "done", "shape": "final"})
    prev = "start"
    for st in v["steps"]:
        edges.append({"src": prev, "dst": st["name"]})
        s.append(f"        first {prev} then {st['name']};")
        prev = st["name"]
    edges.append({"src": prev, "dst": "done"})
    s.append(f"        first {prev} then done;")
    for a, b, lab in v.get("loops", []):
        edges.append({"src": a, "dst": b, "label": lab, "dash": True})
        s.append(f"        // iteration: {a} -> {b} when {lab} (informal; merge node omitted)")
    s.append("    }")
    legend = [edge_leg("Control flow"), edge_leg("Iteration (back to an earlier step)", True)]
    if any(st.get("safety") for st in v["steps"]):
        legend.append(("#FFF7ED", "#C2410C", "Safety-critical step"))
    frag = {"frame": {"kind": "act", "type": "action def", "name": v["name"]},
            "direction": "DOWN" if len(v["steps"]) > 5 else "RIGHT", "nodes": nodes, "edges": edges, "legend": legend}
    return frag, "\n".join(s)


def stm_frag(name: str, states: list[dict], initial: str, transitions: list, final: list[str]) -> dict:
    nodes = [{"id": "init", "shape": "initial"}]
    for st in states:
        nodes.append({"id": st["name"], "shape": "state", "title": st.get("title", st["name"]), "sub": st.get("doc", ""),
                      "code": st.get("id", ""), "tone": st.get("tone", "system")})
    edges = [{"src": "init", "dst": initial}]
    for t in transitions:
        edges.append({"src": t[0], "dst": t[1], "label": t[2] if len(t) > 2 else ""})
    if final:
        nodes.append({"id": "fin", "shape": "final"})
        edges += [{"src": f_, "dst": "fin"} for f_ in final]
    return {"frame": {"kind": "stm", "type": "state def", "name": name},
            "direction": "DOWN" if len(states) > 6 else "RIGHT", "nodes": nodes,
            "edges": edges, "legend": [edge_leg("Transition (trigger)"), ("#0F172A", "#0F172A", "Initial / final")]}


ACRONYMS = {"uav": "UAV", "px4": "PX4", "hmi": "HMI"}


def state_title(name: str) -> str:
    ws = sysml_parse.words(name[:1].upper() + name[1:]).split()
    ws = [ACRONYMS.get(w.lower(), w) for w in ws]
    return " ".join([ws[0][:1].upper() + ws[0][1:], *ws[1:]]) if ws else name


def view_stm(v: dict) -> tuple[dict, str]:
    if v.get("source"):
        sm = sysml_parse.state_machine(ROOT / v["source"], v["state_def"])
        pkg = v["source_package"]
        states = [{"name": st["name"], "id": st["id"], "doc": st["doc"],
                   "title": state_title(st["name"])} for st in sm["states"]]
        frag = stm_frag(f"{pkg}::{v['state_def']}", states, sm["initial"], sm["transitions"], [])
        s = [f"    // Analysed modes are owned by {v['source']} (single source of truth); not redefined here.",
             f"    state {v['usage']} : {pkg}::{v['state_def']} {{", doc(v.get("doc", sm["doc"]), "        "), "    }"]
        return frag, "\n".join(s)
    triggers = sorted({t[2] for t in v["transitions"] if len(t) > 2 and t[2]})
    s = [f"    attribute def {sysml_name(t)};" for t in triggers]
    s.append(f"    state def {v['name']} {{")
    if v.get("doc"):
        s.append(doc(v["doc"], "        "))
    s.append(f"        entry; then {v['initial']};")
    for st in v["states"]:
        s.append(f"        state {st['name']} {{ {doc(st['doc'])} }}" if st.get("doc") else f"        state {st['name']};")
    for i, t in enumerate(v["transitions"]):
        acc = f" accept {sysml_name(t[2])}" if len(t) > 2 and t[2] else ""
        s.append(f"        transition t{i + 1} first {t[0]}{acc} then {t[1]};")
    s.append("    }")
    return stm_frag(v["name"], v["states"], v["initial"], v["transitions"], v.get("final", [])), "\n".join(s)


def view_ibd(v: dict) -> tuple[dict, str]:
    nodes, edges, s = [], [], []
    for p in v["parts"]:
        if p.get("local"):
            s.append(f"    part def {p['type']};")
    s.append(f"    part def {v['name']} {{")
    if v.get("doc"):
        s.append(doc(v["doc"], "        "))
    for p in v["parts"]:
        nodes.append({"id": p["name"], "title": f"{p['name']} : {p['type']}",
                      "tone": "external" if p.get("local") else p.get("kind", "system")})
        s.append(f"        part {p['name']} : {p['type']};")
    for i, (a, b, lab) in enumerate(v["connections"]):
        edges.append({"src": a, "dst": b, "label": lab, "arrow": "none"})
        s.append(f"        connection c{i + 1} connect {a} to {b} {{ {doc(lab)} }}")
    s.append("    }")
    frag = {"frame": {"kind": "ibd", "type": "part def", "name": v["name"]}, "direction": "RIGHT", "nodes": nodes,
            "edges": edges, "legend": [edge_leg("Connector"), ("#F1F5F9", "#64748B", "External part (declared locally)")]}
    return frag, "\n".join(s)


def system_bdd(ctx: Ctx) -> dict:
    nodes, edges = [], []
    for k, v in ctx.nodes.items():
        if v.get("kind") == "external" or not v.get("sysml"):
            continue
        nodes.append({"id": mid(k), "shape": "class", "title": v["sysml"], "stereotype": "part def",
                      "attrs": [f"short name = {k}"], "tone": v.get("kind", "system")})
        if v.get("parent") and ctx.nodes.get(v["parent"], {}).get("sysml"):
            edges.append({"src": mid(v["parent"]), "dst": mid(k), "label": v["usage"].split(".")[-1], "arrow": "diamond"})
    return {"title": "SysML block definition — SUS-I1 system breakdown", "ref": ARCH,
            "subtitle": "Part definitions and composition of context.system in the SysML model, read from "
                        "Architecture.sysml; every folder view imports it.",
            "frame": {"kind": "bdd", "type": "package", "name": "SusanooArchitecture"}, "direction": "RIGHT",
            "nodes": nodes, "edges": edges,
            "legend": [edge_leg("Composition (diamond at owner, label = usage name)"),
                       ("#EEF2FF", "#4F46E5", "System"), ("#F0FDFA", "#0F766E", "Computing"),
                       ("#FFF7ED", "#C2410C", "Protective (safety role)")]}


VIEW_TITLES = {"bdd": "SysML block definition", "req": "SysML requirements", "act": "SysML activity",
               "stm": "SysML state machine", "ibd": "SysML internal block"}


def build_views(ctx: Ctx, f: dict) -> tuple[list[dict], str | None]:
    """(figure specs for the SysML section, generated .sysml text or None)."""
    if f.get("canonical_model"):
        return [system_bdd(ctx)], None
    model = f["model"]
    pkg = model["package"]
    specs, bodies, extra = [], [], set()
    for v in model["views"]:
        k = v["kind"]
        if k == "bdd":
            frag, txt = view_bdd(v, pkg)
        elif k == "req":
            frag, txt = view_req(ctx, v, pkg)
            if v.get("records") or any(r.get("record") for r in v.get("requirements", [])):
                extra.add("SusanooRequirements")
            if v.get("derives"):
                extra.add("RequirementDerivation")
        elif k == "act":
            frag, txt = view_act(v)
        elif k == "stm":
            frag, txt = view_stm(v)
            if v.get("source"):
                extra.add(v["source_package"])
        elif k == "ibd":
            frag, txt = view_ibd(v)
        else:
            raise ValueError(f"{f['id']}: unknown view kind {k}")
        name = v.get("title", v.get("name", pkg))
        specs.append({**frag, "title": f"{VIEW_TITLES[k]} — {name}", "ref": f"{pkg}.sysml",
                      "subtitle": v.get("caption", f"{VIEW_TITLES[k].replace('SysML ', '').capitalize()} view of "
                                                   f"package {pkg}. The .sysml file is the model of record.")})
        bodies.append(txt)
    header = [f"// {pkg} — generated by {GEN} from safety/mil-std-882e/catalog.yaml.",
              "// Do not edit by hand: change the catalog and regenerate.",
              "// Status: planning view only; not evidence of completed analysis or verification.", "",
              f"package {pkg} {{", "    private import ScalarValues::*;", "    private import SusanooLibrary::*;",
              "    private import SusanooArchitecture::*;", *[f"    private import {e}::*;" for e in sorted(extra)], ""]
    return specs, "\n".join(header) + "\n\n".join(bodies) + "\n}\n"


# ------------------------------------------------------------- README
def link_for(ctx: Ctx, here: Path, it: dict) -> str:
    if "ref" in it:
        return f"[{ctx.folders[it['ref']]['title']}]({rel(ctx.path(it['ref']) / 'README.md', here)})"
    if "doc" in it:
        return f"[`{it['doc']}`]({rel(ROOT / it['doc'], here)})"
    return it["ext"]


def img(fig: dict) -> str:
    return f"![Figure {fig['number']} · {fig['title']}](figures/{fig['_file']})\n"


def render(ctx: Ctx, f: dict, figs: dict[str, list[dict]], sysml_text: str | None) -> str:
    here = ctx.path(f["id"])
    cat = ctx.cat
    out = [f"# {f['title']}\n", f"> **Status:** {f.get('status', cat['default_status'])}\n>\n> {cat['disclaimer']}\n"]
    el = ctx.elements.get(f.get("element"))
    rows = []
    if el:
        rows.append(("MIL-STD-882E element", f"{el['n']} — {el['name']}"))
    if f.get("tasks"):
        rows.append(("Tasks", "; ".join(
            f"[Task {t['id']} — {t['name']}]({rel(ROOT / 'docs/wiki' / f'MIL-STD-882E-Task-{t['id']}.md', here)})"
            for t in f["tasks"])))
    for key, label in (("gate", "Lifecycle gate"), ("applicability", "Applicability"), ("role", "Accountable role")):
        if f.get(key):
            rows.append((label, f[key]))
    if f.get("procedure"):
        rows.append(("Procedure", f"[`{f['procedure']}`]({rel(ROOT / f['procedure'], here)})"))
    if f.get("parent"):
        p = f["parent"]
        rows.append(("Parent folder", f"[{ctx.folders[p]['title']}]({rel(ctx.path(p) / 'README.md', here)})"))
    out += ["| Field | Value |", "|---|---|", *[f"| {a} | {b} |" for a, b in rows], ""]
    out.append(f"## Purpose\n\n{f['purpose'].strip()}\n")

    out += ["## Position in the MIL-STD-882E flow\n", img(figs["rail"][0])]
    out += ["## Block diagram\n", img(figs["block"][0]),
            f"Elements and interfaces: [`architecture/item-definition.yaml`]({rel(ITEM_DEF, here)}); SysML: "
            f"[`Architecture.sysml`]({rel(ROOT / ARCH, here)}).\n"]

    b = f["boundary"]
    out += ["## Boundary diagram\n", img(figs["boundary"][0])]
    out.append("| # | From | To | Crossing / interaction | Interface (item definition) |\n|---|---|---|---|---|")
    blabel = lambda k: f"_{b['name']} (boundary)_" if k == "@boundary" else ctx.label(k)  # noqa: E731
    for i, (a, c, lab) in enumerate(b["flows"]):
        ifs = ctx.interfaces_between(a, c) if a in ctx.nodes and c in ctx.nodes else []
        out.append(f"| {i + 1} | {blabel(a)} | {blabel(c)} | {lab} | {', '.join(ifs) or '—'} |")
    out.append("")
    if b.get("excluded"):
        out.append("**Explicitly excluded:** " + "; ".join(b["excluded"]) + "\n")

    out.append("## SysML model\n")
    if f.get("canonical_model"):
        out.append("Project SysML v2 model (model of record for every folder in this tree, validated by the OMG "
                   "pilot in CI): "
                   + ", ".join(f"[`{Path(x).name}`]({rel(ROOT / x, here)})" for x in f["canonical_model"]) + ".\n")
        out.append(img(figs["sysml"][0]))
    else:
        fname = f"{f['model']['package']}.sysml"
        out.append(f"SysML v2 textual view: [`{fname}`]({fname}), generated from the catalog. It imports the project "
                   f"model in [`models/sysml/model`]({rel(ROOT / 'models/sysml/model', here)}): "
                   "`SusanooArchitecture` (elements and usage paths) and `SusanooLibrary` (882E vocabulary). "
                   "The figures are drawn from the same data; the `.sysml` file is the model of record.\n")
        for fig in figs["sysml"]:
            out.append(img(fig))
        out.append("<details><summary>SysML v2 source</summary>\n\n```sysml\n" + sysml_text.rstrip() + "\n```\n\n</details>\n")

    out += ["## Inputs and outputs\n", img(figs["io"][0])]
    if f.get("inputs"):
        out += ["| Input | Source |", "|---|---|", *[f"| {it['item']} | {link_for(ctx, here, it)} |" for it in f["inputs"]], ""]
    if f.get("outputs"):
        out += ["| Output | Destination |", "|---|---|",
                *[f"| {it['item']} | {link_for(ctx, here, it)} |" for it in f["outputs"]], ""]

    out.append("## Folder contents\n")
    out.append("| Item | Description | State |\n|---|---|---|")
    for c in [c for c in cat["folders"] if c.get("parent") == f["id"]]:
        out.append(f"| [`{Path(c['path']).name}/`]({rel(ctx.path(c['id']) / 'README.md', here)}) | {c['title']} | folder |")
    for c in f.get("contents", []):
        exists = (here / c["name"]).exists()
        name = f"[`{c['name']}`]({c['name']})" if exists else f"`{c['name']}`"
        out.append(f"| {name} | {c['desc']} | {'present' if exists else 'planned'} |")
    out.append(f"| [`figures/`](figures/) | Generated SVG figures (do not edit) | generated |")
    if not f.get("canonical_model"):
        out.append(f"| [`{f['model']['package']}.sysml`]({f['model']['package']}.sysml) | Generated SysML v2 view | generated |")
    out.append("")
    if f.get("notes_md"):
        out.append(f["notes_md"].rstrip() + "\n")
    out.append(END_MARKER)
    return "\n".join(out) + "\n"


# ------------------------------------------------------------- validation
# SysML v2 reserved words that catalog names must not use (checked by the OMG pilot in practice).
SYSML_KEYWORDS = {
    "about", "abstract", "accept", "action", "actor", "after", "alias", "all", "allocate", "allocation", "analysis",
    "and", "as", "assert", "assign", "assume", "at", "attribute", "bind", "binding", "by", "calc", "case", "comment",
    "concern", "connect", "connection", "constant", "constraint", "crosses", "decide", "def", "default", "defined",
    "dependency", "derived", "do", "doc", "else", "end", "entry", "enum", "event", "exhibit", "exit", "expose",
    "false", "filter", "first", "flow", "for", "fork", "frame", "from", "hastype", "if", "implies", "import", "in",
    "include", "individual", "inout", "interface", "istype", "item", "join", "language", "library", "locale",
    "loop", "merge", "message", "meta", "metadata", "nonunique", "not", "null", "objective", "occurrence", "of",
    "or", "ordered", "out", "package", "parallel", "part", "perform", "port", "private", "protected", "public",
    "redefines", "ref", "references", "render", "rendering", "rep", "require", "requirement", "return", "satisfy",
    "send", "snapshot", "specializes", "stakeholder", "standard", "state", "subject", "subsets", "succession",
    "terminate", "then", "timeslice", "to", "transition", "true", "until", "use", "variant", "variation",
    "verification", "verify", "via", "view", "viewpoint", "when", "while", "xor"}


def sysml_names(v: dict) -> list[str]:
    names = [st["name"] for st in v.get("steps", [])] + [st["name"] for st in v.get("states", [])]
    names += [p["name"] for p in v.get("parts", [])]
    for b in v.get("blocks", []):
        names.append(b["name"])
        names += [p["name"] for p in b.get("parts", [])]
        names += [a.split(":")[0].strip() for a in b.get("attributes", [])]
    return names


def validate(cat: dict, ctx: "Ctx") -> list[str]:
    """Structural checks on the catalog (PDaC rule 1: IDs unique, references resolve)."""
    errs: list[str] = []
    nodes = ctx.nodes
    ids = [f["id"] for f in cat["folders"]]
    if len(ids) != len(set(ids)):
        errs.append("duplicate folder ids")
    known = set(ids)
    for f in cat["folders"]:
        fid = f["id"]
        if f.get("parent") and f["parent"] not in known:
            errs.append(f"{fid}: unknown parent {f['parent']}")
        for k in f.get("scope", []):
            if k not in nodes:
                errs.append(f"{fid}: scope node {k} not in system registry")
        b = f["boundary"]
        names = set(b["inside"]) | set(b["outside"]) | {"@boundary"}
        for fl in b["flows"]:
            if len(fl) != 3:
                errs.append(f"{fid}: boundary flow must be [from, to, label]: {fl}")
                continue
            for n in fl[:2]:
                if n not in names:
                    errs.append(f"{fid}: flow endpoint '{n}' not declared inside/outside boundary")
        for io in f.get("inputs", []) + f.get("outputs", []):
            if set(io) - {"ref", "doc", "ext", "item"} or "item" not in io:
                errs.append(f"{fid}: malformed input/output {io}")
            if "ref" in io and io["ref"] not in known:
                errs.append(f"{fid}: unknown ref {io['ref']}")
            if "doc" in io and not (ROOT / io["doc"]).exists():
                errs.append(f"{fid}: missing doc {io['doc']}")
        for t in f.get("tasks", []):
            if set(t) - {"id", "name"}:
                errs.append(f"{fid}: malformed task {t}")
        for v in (f.get("model") or {}).get("views", []):
            for name in sysml_names(v):
                if name in SYSML_KEYWORDS:
                    errs.append(f"{fid}: '{name}' is a SysML v2 keyword; rename it")
            for st in v.get("steps", []):
                if set(st) - {"name", "label", "safety"}:
                    errs.append(f"{fid}: malformed step {st}")
            for key in ("transitions", "connections", "loops"):
                for t in v.get(key, []):
                    if len(t) != 3:
                        errs.append(f"{fid}: {key} entry must have 3 items: {t}")
            for r in v.get("requirements", []):
                if set(r) - {"id", "name", "text", "risk", "verify", "record"}:
                    errs.append(f"{fid}: malformed requirement {r}")
                if r.get("record") and (r["id"] not in ctx.reqs or r["id"] not in ctx.model.requirements):
                    errs.append(f"{fid}: requirement record {r['id']} not in requirements/ and the SysML model")
            for el, _ in v.get("satisfied_by", []):
                if not ctx.nodes.get(el, {}).get("usage"):
                    errs.append(f"{fid}: satisfied_by {el} is not an element of the SysML model")
            for b_ in v.get("blocks", []):
                if b_.get("import"):
                    try:
                        sysml_parse.definition(LIBRARY, b_["name"])
                    except Exception as e:  # noqa: BLE001
                        errs.append(f"{fid}: {e}")
            if v.get("source"):
                try:
                    sysml_parse.state_machine(ROOT / v["source"], v["state_def"])
                except Exception as e:  # noqa: BLE001
                    errs.append(f"{fid}: {e}")
        if not f.get("model") and not f.get("canonical_model"):
            errs.append(f"{fid}: needs a SysML model (model or canonical_model)")
    return errs


# ------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="fail if generated files are stale")
    args = ap.parse_args()
    cat = yaml.safe_load(CATALOG.read_text())
    ctx = Ctx(cat)
    errs = validate(cat, ctx)
    if errs:
        print("Catalog errors:\n  " + "\n  ".join(errs))
        return 2
    footer = (f"Generated by {GEN} from safety/mil-std-882e/catalog.yaml. Planning view: not evidence of completed "
              "analysis, verification or risk acceptance.")

    plan = []          # (folder, figs dict, sysml text)
    all_specs = []
    for f in cat["folders"]:
        sysml_specs, sysml_text = build_views(ctx, f)
        figs = {"rail": [fig_rail(ctx, f)], "block": [fig_block(ctx, f)], "boundary": [fig_boundary(ctx, f)],
                "sysml": sysml_specs, "io": [fig_io(ctx, f)]}
        n = 0
        for key in ("rail", "block", "boundary", "sysml", "io"):
            for spec in figs[key]:
                n += 1
                spec["number"] = str(n)
                spec.setdefault("footer", footer)
                spec["_file"] = f"fig-{n}-{slug(spec['title'].split(' — ')[0])}.svg"
                all_specs.append(spec)
        plan.append((f, figs, sysml_text))
    svgs = diagram.render_all(all_specs)
    for spec, s in zip(all_specs, svgs):
        spec["_svg"] = s

    stale: list[str] = []
    for f, figs, sysml_text in plan:
        here = ctx.path(f["id"])
        files: dict[Path, str] = {}
        for group in figs.values():
            for spec in group:
                files[here / "figures" / spec["_file"]] = spec["_svg"]
        if sysml_text:
            files[here / f"{f['model']['package']}.sysml"] = sysml_text
        readme = here / "README.md"
        tail = DEFAULT_TAIL
        if readme.exists() and END_MARKER in readme.read_text():
            tail = readme.read_text().split(END_MARKER, 1)[1]
        files[readme] = render(ctx, f, figs, sysml_text) + "\n" + tail.lstrip("\n")
        # figures no longer produced are stale
        figdir = here / "figures"
        if figdir.exists():
            for old in figdir.glob("*.svg"):
                if old not in files:
                    if args.check:
                        stale.append(str(old.relative_to(ROOT)) + " (orphan)")
                    else:
                        old.unlink()
                        print(f"removed {old.relative_to(ROOT)}")
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
        print(f"Stale generated files (run python3 {GEN}):\n  " + "\n  ".join(stale))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
