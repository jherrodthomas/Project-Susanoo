#!/usr/bin/env python3
"""Generate MIL-STD-882E folder READMEs and SysML views from catalog.yaml.

PDaC rule: the folder tree, its diagrams and its SysML views are generated from
one typed catalog so they cannot drift apart.

Each README has a generated part (metadata, flow position, block diagram,
boundary diagram, SysML model, inputs/outputs, contents) followed by the
END_MARKER. Anything after the marker is human-authored and preserved on
regeneration.

Usage:
    python3 tools/gen_safety_docs.py           # write files
    python3 tools/gen_safety_docs.py --check   # exit 1 if any file is stale
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "safety" / "mil-std-882e" / "catalog.yaml"
END_MARKER = "<!-- END GENERATED: content below this line is human-authored and preserved -->"
DEFAULT_TAIL = "\n## Working content\n\n_No analysis content yet. Add authored material below this heading._\n"

CLASSDEFS = [
    "classDef system fill:#dceaf7,stroke:#55758f,color:#17324d",
    "classDef safety fill:#fff0d9,stroke:#b28a3d,color:#513c16",
    "classDef external fill:#e8f1e9,stroke:#63886a,color:#23412c",
    "classDef interface fill:#eae7f5,stroke:#8370a3,color:#30254a",
    "classDef muted fill:#f4f4f4,stroke:#b5b5b5,color:#8a8a8a,stroke-dasharray: 4 3",
    "classDef current fill:#b28a3d,stroke:#513c16,color:#ffffff,stroke-width:2px",
    "classDef work fill:#ffffff,stroke:#55758f,color:#17324d",
]


# ----------------------------------------------------------------- helpers
def mid(text: str) -> str:
    """Mermaid-safe identifier."""
    s = re.sub(r"[^A-Za-z0-9]", "_", text)
    return ("n_" + s) if s[:1].isdigit() else s


def q(text: str) -> str:
    """Mermaid-safe quoted label."""
    return '"' + str(text).replace('"', "'").replace("#", "No.") + '"'


def sysml_name(text: str) -> str:
    s = re.sub(r"[^A-Za-z0-9]+", " ", text).title().replace(" ", "")
    return ("_" + s) if s[:1].isdigit() else s


def doc(text: str, indent: str) -> str:
    return f"{indent}doc /* {str(text).replace('*/', '* /')} */"


def rel(target: Path, start: Path) -> str:
    return os.path.relpath(target, start).replace(os.sep, "/")


class Ctx:
    def __init__(self, cat: dict):
        self.cat = cat
        self.nodes = cat["system"]["nodes"]
        self.links = cat["system"]["links"]
        self.elements = {e["n"]: e for e in cat["elements"]}
        self.folders = {f["id"]: f for f in cat["folders"]}
        self.base = ROOT / cat["base"]

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
            if k in out:
                continue
            out.add(k)
            stack.extend(self.children(k))
        return out

    def sysml_path(self, key: str) -> str | None:
        n = self.nodes.get(key)
        return n.get("usage") if n else None


# ------------------------------------------------------- diagram builders
def flow_position(ctx: Ctx, f: dict) -> str:
    cls: dict[str, str] = {f"E{n}": "work" for n in ctx.elements}
    cls["HTS"] = "work"
    lines = ["flowchart LR"]
    for n, e in ctx.elements.items():
        lines.append(f"  E{n}[{q(f'{n} · ' + e['short'])}]")
    nums = list(ctx.elements)
    lines.append("  " + " --> ".join(f"E{n}" for n in nums))
    lines.append(f"  E{nums[-1]} -. {q('change, deficiency or mishap')} .-> E2")
    lines.append(f"  HTS[({q('Hazard tracking system · Task 106')})]")
    lines.append("  E2 & E3 & E4 & E6 & E7 & E8 -.- HTS")
    cur = f.get("element")
    if cur and f.get("tasks"):
        cls[f"E{cur}"] = "safety"
        for t in f["tasks"]:
            tid = f"T{t['id']}"
            lines.append(f"  {tid}[{q('Task ' + str(t['id']) + ' · ' + t['name'])}]")
            lines.append(f"  E{cur} --- {tid}")
            cls[tid] = "current"
    elif cur:
        cls[f"E{cur}"] = "current"
    if f.get("crosscut") == "hts":
        cls["HTS"] = "current"
    elif f.get("crosscut"):
        lines.append(f"  X[{q(f['title'])}]")
        lines.append("  X -.- E3 & E4 & E5 & E6")
        cls["X"] = "current"
        cls["HTS"] = "safety"
    lines += [f"  class {k} {v}" for k, v in cls.items()]
    lines += ["  " + c for c in CLASSDEFS]
    return "\n".join(lines)


def block_diagram(ctx: Ctx, f: dict) -> str:
    scope = ctx.expand(f.get("scope", []))
    lines = ["flowchart TB"]

    def emit(key: str, indent: str):
        kids = ctx.children(key)
        if kids:
            lines.append(f"{indent}subgraph {mid(key)}[{q(ctx.label(key))}]")
            lines.append(f"{indent}  direction TB")
            for k in kids:
                emit(k, indent + "  ")
            lines.append(f"{indent}end")
        else:
            lines.append(f"{indent}{mid(key)}[{q(ctx.label(key))}]")

    roots = [k for k, v in ctx.nodes.items() if not v.get("parent") and v.get("kind") != "external"]
    for r in roots:
        emit(r, "  ")
    for a, b, lab in ctx.links:
        lines.append(f"  {mid(a)} -->|{q(lab)}| {mid(b)}")
    for k, v in ctx.nodes.items():
        if v.get("kind") == "external" or ctx.children(k):
            continue
        cls = v.get("kind", "system") if k in scope else "muted"
        lines.append(f"  class {mid(k)} {cls}")
    lines += ["  " + c for c in CLASSDEFS]
    return "\n".join(lines)


def bnode(key: str) -> str:
    return "BND" if key == "@boundary" else mid(key)


def boundary_diagram(ctx: Ctx, f: dict) -> str:
    b = f["boundary"]
    lines = ["flowchart LR"]
    lines.append(f"  subgraph BND[{q('Boundary: ' + b['name'])}]")
    lines.append("    direction TB")
    for k in b["inside"]:
        lines.append(f"    {mid(k)}[{q(ctx.label(k))}]")
    lines.append("  end")
    for k in b["outside"]:
        lines.append(f"  {mid(k)}[{q(ctx.label(k))}]")
    for a, c, lab in b["flows"]:
        lines.append(f"  {bnode(a)} -->|{q(lab)}| {bnode(c)}")
    for k in b["inside"]:
        kind = ctx.kind(k)
        lines.append(f"  class {mid(k)} {'system' if kind == 'external' else kind}")
    for k in b["outside"]:
        lines.append(f"  class {mid(k)} external")
    lines.append("  style BND fill:none,stroke:#b28a3d,stroke-width:2px,stroke-dasharray: 6 4")
    lines += ["  " + c for c in CLASSDEFS]
    return "\n".join(lines)


def io_diagram(ctx: Ctx, f: dict) -> str:
    me = mid(f["id"])
    lines = ["flowchart LR", f"  {me}[{q(f['title'])}]"]
    for i, it in enumerate(f.get("inputs", [])):
        src = ctx.folders[it["ref"]]["title"] if "ref" in it else it.get("doc") or it.get("ext")
        lines.append(f"  in{i}[{q(src)}] -->|{q(it['item'])}| {me}")
        lines.append(f"  class in{i} {'work' if 'ref' in it else 'external'}")
    for i, it in enumerate(f.get("outputs", [])):
        dst = ctx.folders[it["ref"]]["title"] if "ref" in it else it.get("doc") or it.get("ext")
        lines.append(f"  {me} -->|{q(it['item'])}| out{i}[{q(dst)}]")
        lines.append(f"  class out{i} {'work' if 'ref' in it else 'external'}")
    lines.append(f"  class {me} current")
    lines += ["  " + c for c in CLASSDEFS]
    return "\n".join(lines)


# ----------------------------------------------------------- SysML views
def view_bdd(v: dict) -> tuple[str, str]:
    m = ["classDiagram"]
    s: list[str] = []
    stereo = {b["name"]: b.get("stereotype", "part") for b in v["blocks"]}
    for b in v["blocks"]:
        st = b.get("stereotype", "part")
        m.append(f"  class {b['name']} {{")
        m.append(f"    <<{'enumeration' if st == 'enum' else st}>>")
        if st == "enum":
            m += [f"    {val}" for val in b["values"]]
            s.append(f"    enum def {b['name']} {{")
            if b.get("doc"):
                s.append(doc(b["doc"], "        "))
            s += [f"        enum {val};" for val in b["values"]]
            s.append("    }")
            m.append("  }")
            continue
        kw = {"part": "part def", "item": "item def", "attribute": "attribute def"}[st]
        s.append(f"    {kw} {b['name']} {{")
        if b.get("doc"):
            s.append(doc(b["doc"], "        "))
        for a in b.get("attributes", []):
            name, typ = [x.strip() for x in a.split(":")]
            m.append(f"    +{typ} {name}")
            s.append(f"        attribute {name} : {typ};")
        for p in b.get("parts", []):
            mult = p.get("mult", "1")
            tst = stereo.get(p["type"], p.get("usage", "part"))
            usage = {"part": "part", "item": "ref item", "attribute": "attribute", "enum": "attribute"}[tst]
            s.append(f"        {usage} {p['name']} : {p['type']}[{mult}];")
        m.append("  }")
        for p in b.get("parts", []):
            arrow = "o--" if stereo.get(p["type"], "part") == "item" and b.get("stereotype") != "part" else "*--"
            m.append(f'  {b["name"]} {arrow} "{p.get("mult", "1")}" {p["type"]} : {p["name"]}')
        s.append("    }")
    for parent, child in v.get("specializations", []):
        m.append(f"  {parent} <|-- {child}")
    # specializations in SysML: rewrite the child header
    text = "\n".join(s)
    for parent, child in v.get("specializations", []):
        text = re.sub(rf"(def {child}) \{{", rf"\1 :> {parent} {{", text)
    return "\n".join(m), text


def view_req(ctx: Ctx, v: dict) -> tuple[str, str]:
    m = ["requirementDiagram"]
    s: list[str] = []
    for r in v["requirements"]:
        rid = mid(r["id"])
        m += [f"  requirement {rid} {{", f"    id: {q(r['id'])}", f"    text: {q(r['text'])}",
              f"    risk: {r.get('risk', 'Medium')}", f"    verifymethod: {r.get('verify', 'Test')}", "  }"]
        if r.get("from"):
            # Reuse the definition owned by another folder's package instead of redefining it.
            s.append(f"    requirement {rid.lower()} : {r['from']}::{r['name']};")
            continue
        s.append(f"    requirement def <'{r['id']}'> {r['name']} {{")
        s.append(doc(r["text"], "        "))
        s.append("    }")
        s.append(f"    requirement {rid.lower()} : {r['name']};")
    elems = {}
    for el, rid in v.get("satisfied_by", []):
        elems[el] = "part"
    for el, rid in v.get("verified_by", []):
        elems[el] = "verification"
    for el, typ in elems.items():
        m += [f"  element {mid(el)} {{", f"    type: {q(typ)}", "  }"]
    for el, rid in v.get("satisfied_by", []):
        m.append(f"  {mid(el)} - satisfies -> {mid(rid)}")
        path = ctx.sysml_path(el)
        target = path if path else el
        s.append(f"    satisfy {mid(rid).lower()} by {target};")
    for el, rid in v.get("verified_by", []):
        m.append(f"  {mid(el)} - verifies -> {mid(rid)}")
        s.append(f"    verification def <'{el}'> {sysml_name(el)} {{")
        s.append(f"        objective {{ verify {mid(rid).lower()}; }}")
        s.append("    }")
    for a, b in v.get("derives", []):
        m.append(f"  {mid(b)} - derives -> {mid(a)}")
        s.append(f"    #derivation connection {{ end #original ::> {mid(a).lower()}; end #derive ::> {mid(b).lower()}; }}")
    return "\n".join(m), "\n".join(s)


def view_act(v: dict) -> tuple[str, str]:
    m = ["flowchart TD", "  start((start))"]
    s = [f"    action def {v['name']} {{"]
    if v.get("doc"):
        s.append(doc(v["doc"], "        "))
    prev = "start"
    for st in v["steps"]:
        n = st["name"]
        m.append(f"  {n}[{q(st['label'])}]")
        s.append(f"        action {n} {{ {doc(st['label'], '').strip()} }}")
    s.append("        first start;")
    for st in v["steps"]:
        m.append(f"  {prev} --> {st['name']}")
        s.append(f"        first {prev} then {st['name']};" if prev != "start" else f"        then {st['name']};")
        prev = st["name"]
    m.append(f"  {prev} --> done((done))")
    s.append(f"        first {prev} then done;")
    for a, b, lab in v.get("loops", []):
        m.append(f"  {a} -. {q(lab)} .-> {b}")
        s.append(f"        // iteration: {a} -> {b} when {lab} (informal; merge node omitted)")
    for st in v["steps"]:
        if st.get("safety"):
            m.append(f"  class {st['name']} safety")
    m += ["  " + c for c in CLASSDEFS]
    s.append("    }")
    return "\n".join(m), "\n".join(s)


def view_stm(v: dict) -> tuple[str, str]:
    m = ["stateDiagram-v2", f"  [*] --> {v['initial']}"]
    triggers = sorted({t[2] for t in v["transitions"] if len(t) > 2 and t[2]})
    s = [f"    attribute def {sysml_name(t)};" for t in triggers]
    s.append(f"    state def {v['name']} {{")
    if v.get("doc"):
        s.append(doc(v["doc"], "        "))
    s.append(f"        entry; then {v['initial']};")
    for st in v["states"]:
        m.append(f"  {st['name']} : {st['name']}")
        if st.get("doc"):
            m[-1] = f"  {st['name']} : {st['name']} - {st['doc']}"
            s.append(f"        state {st['name']} {{ {doc(st['doc'], '').strip()} }}")
        else:
            s.append(f"        state {st['name']};")
    for i, t in enumerate(v["transitions"]):
        a, b = t[0], t[1]
        trig = t[2] if len(t) > 2 else ""
        m.append(f"  {a} --> {b}" + (f" : {trig}" if trig else ""))
        acc = f" accept {sysml_name(trig)}" if trig else ""
        s.append(f"        transition t{i + 1} first {a}{acc} then {b};")
    for fin in v.get("final", []):
        m.append(f"  {fin} --> [*]")
    s.append("    }")
    return "\n".join(m), "\n".join(s)


def view_ibd(ctx: Ctx, v: dict) -> tuple[str, str]:
    m = ["flowchart LR", f"  subgraph CTX[{q(v['name'] + ' : context')}]"]
    s = []
    for p in v["parts"]:
        if p.get("local"):
            s.append(f"    part def {p['type']};")
    s.append(f"    part def {v['name']} {{")
    if v.get("doc"):
        s.append(doc(v["doc"], "        "))
    for p in v["parts"]:
        m.append(f"    {p['name']}[{q(p['name'] + ' : ' + p['type'])}]")
        s.append(f"        part {p['name']} : {p['type']};")
    m.append("  end")
    for i, (a, b, lab) in enumerate(v["connections"]):
        m.append(f"  {a} <-->|{q(lab)}| {b}")
        s.append(f"        connection c{i + 1} connect {a} to {b} {{ {doc(lab, '').strip()} }}")
    for p in v["parts"]:
        m.append(f"  class {p['name']} {'external' if p.get('local') else p.get('kind', 'system')}")
    m.append("  style CTX fill:none,stroke:#55758f,stroke-dasharray: 6 4")
    m += ["  " + c for c in CLASSDEFS]
    s.append("    }")
    return "\n".join(m), "\n".join(s)


def system_bdd(ctx: Ctx) -> str:
    m = ["classDiagram"]
    for k, v in ctx.nodes.items():
        if v.get("kind") == "external":
            continue
        m.append(f"  class {mid(k)}[\"{v['sysml']}\"] {{")
        m.append(f"    <<part def>>")
        m.append(f"    {k}")
        m.append("  }")
    for k, v in ctx.nodes.items():
        if v.get("parent"):
            role = v["usage"].split(".")[-1]
            m.append(f'  {mid(v["parent"])} *-- "1" {mid(k)} : {role}')
    return "\n".join(m)


def build_views(ctx: Ctx, f: dict) -> tuple[list[tuple[str, str]], str | None]:
    model = f.get("model")
    if not model:
        return [], None
    mermaids: list[tuple[str, str]] = []
    bodies: list[str] = []
    for v in model["views"]:
        k = v["kind"]
        if k == "bdd":
            mm, ss = view_bdd(v)
        elif k == "req":
            mm, ss = view_req(ctx, v)
        elif k == "act":
            mm, ss = view_act(v)
        elif k == "stm":
            mm, ss = view_stm(v)
        elif k == "ibd":
            mm, ss = view_ibd(ctx, v)
        else:
            raise ValueError(f"{f['id']}: unknown view kind {k}")
        title = {"bdd": "Block definition (bdd)", "req": "Requirements (req)", "act": "Activity (act)",
                 "stm": "State machine (stm)", "ibd": "Internal block / context (ibd)"}[k]
        mermaids.append((f"{title} — {v.get('title', v.get('name', model['package']))}", mm))
        bodies.append(ss)
    pkg = model["package"]
    extra = sorted({r["from"] for v in model["views"] for r in v.get("requirements", []) if r.get("from")})
    if any(v.get("derives") for v in model["views"]):
        extra.insert(0, "RequirementDerivation")
    header = [
        f"// {pkg} — generated by tools/gen_safety_docs.py from safety/mil-std-882e/catalog.yaml.",
        "// Do not edit by hand: change the catalog and regenerate.",
        "// Status: planning view only; not evidence of completed analysis or verification.",
        "",
        f"package {pkg} {{",
        "    private import ScalarValues::*;",
        "    private import SusanooSystem::*;",
        "    private import SusanooSafety::*;",
        *[f"    private import {e}::*;" for e in extra],
        "",
    ]
    text = "\n".join(header) + "\n\n".join(bodies) + "\n}\n"
    return mermaids, text


# ------------------------------------------------------------- README
def mermaid(block: str) -> str:
    return "```mermaid\n" + block + "\n```\n"


def link_for(ctx: Ctx, here: Path, it: dict) -> str:
    if "ref" in it:
        t = ctx.folders[it["ref"]]
        return f"[{t['title']}]({rel(ctx.path(it['ref']) / 'README.md', here)})"
    if "doc" in it:
        return f"[`{it['doc']}`]({rel(ROOT / it['doc'], here)})"
    return it["ext"]


def render(ctx: Ctx, f: dict, sysml_text: str | None, views: list) -> str:
    here = ctx.path(f["id"])
    cat = ctx.cat
    out: list[str] = []
    out.append(f"# {f['title']}\n")
    out.append(f"> **Status:** {f.get('status', cat['default_status'])}\n>\n> {cat['disclaimer']}\n")

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
    parent = f.get("parent")
    if parent:
        rows.append(("Parent folder", f"[{ctx.folders[parent]['title']}]({rel(ctx.path(parent) / 'README.md', here)})"))
    out.append("| Field | Value |\n|---|---|")
    out += [f"| {a} | {b} |" for a, b in rows]
    out.append("")
    out.append(f"## Purpose\n\n{f['purpose'].strip()}\n")

    out.append("## Position in the MIL-STD-882E flow\n")
    out.append("Highlighted node(s) show where this folder sits in the eight-element iterative flow. "
               "Dotted links are feedback and hazard-tracking-system interactions.\n")
    out.append(mermaid(flow_position(ctx, f)))

    out.append("## Block diagram\n")
    out.append("System elements of SUS-I1 in scope for this folder are coloured "
               "(blue = system, amber = safety function, purple = interface); greyed blocks are out of scope. "
               f"Source of truth: [`SusanooSystem.sysml`]({rel(ctx.base / '00-system-definition/sysml/SusanooSystem.sysml', here)}).\n")
    out.append(mermaid(block_diagram(ctx, f)))

    b = f["boundary"]
    out.append("## Boundary diagram\n")
    out.append(f"Dashed frame = **{b['name']}** boundary. Everything outside it is an external entity or another folder's scope.\n")
    out.append(mermaid(boundary_diagram(ctx, f)))
    out.append("| From | To | Crossing / interaction |\n|---|---|---|")
    blabel = lambda k: f"_{b['name']} (boundary)_" if k == "@boundary" else ctx.label(k)
    out += [f"| {blabel(a)} | {blabel(c)} | {lab} |" for a, c, lab in b["flows"]]
    out.append("")
    if b.get("excluded"):
        out.append("**Explicitly excluded:** " + "; ".join(b["excluded"]) + "\n")

    out.append("## SysML model\n")
    if f.get("canonical_model"):
        files = f["canonical_model"]
        out.append("Canonical SysML v2 textual models (model of record for every folder in this tree): "
                   + ", ".join(f"[`{Path(x).name}`]({rel(ROOT / x, here)})" for x in files) + ".\n")
        out.append("### Block definition (bdd) — SUS-I1 system breakdown\n")
        out.append(mermaid(system_bdd(ctx)))
    else:
        fname = f"{f['model']['package']}.sysml"
        out.append(f"SysML v2 textual view: [`{fname}`]({fname}) (generated from the catalog; imports "
                   f"[`SusanooSystem`]({rel(ctx.base / '00-system-definition/sysml/SusanooSystem.sysml', here)}) and "
                   f"[`SusanooSafety`]({rel(ctx.base / '00-system-definition/sysml/SusanooSafety.sysml', here)})). "
                   "The Mermaid rendering below is a reading aid; the `.sysml` file is the model of record.\n")
        for title, mm in views:
            out.append(f"### {title}\n")
            out.append(mermaid(mm))
        out.append("<details><summary>SysML v2 source</summary>\n\n```sysml\n" + sysml_text.rstrip() + "\n```\n\n</details>\n")

    out.append("## Inputs and outputs\n")
    out.append(mermaid(io_diagram(ctx, f)))
    if f.get("inputs"):
        out.append("| Input | Source |\n|---|---|")
        out += [f"| {it['item']} | {link_for(ctx, here, it)} |" for it in f["inputs"]]
        out.append("")
    if f.get("outputs"):
        out.append("| Output | Destination |\n|---|---|")
        out += [f"| {it['item']} | {link_for(ctx, here, it)} |" for it in f["outputs"]]
        out.append("")

    out.append("## Folder contents\n")
    out.append("| Item | Description | State |\n|---|---|---|")
    kids = [c for c in cat["folders"] if c.get("parent") == f["id"]]
    for c in kids:
        out.append(f"| [`{Path(c['path']).name}/`]({rel(ctx.path(c['id']) / 'README.md', here)}) | {c['title']} | folder |")
    for c in f.get("contents", []):
        p = here / c["name"]
        state = "present" if p.exists() else "planned"
        name = f"[`{c['name']}`]({c['name']})" if p.exists() else f"`{c['name']}`"
        out.append(f"| {name} | {c['desc']} | {state} |")
    if not f.get("canonical_model"):
        out.append(f"| [`{f['model']['package']}.sysml`]({f['model']['package']}.sysml) | Generated SysML v2 view | generated |")
    out.append("")
    if f.get("notes_md"):
        out.append(f["notes_md"].rstrip() + "\n")
    out.append(END_MARKER)
    return "\n".join(out) + "\n"


def validate(cat: dict) -> list[str]:
    """Structural checks on the catalog (PDaC rule 1: IDs unique, references resolve)."""
    errs: list[str] = []
    nodes = cat["system"]["nodes"]
    ids = [f["id"] for f in cat["folders"]]
    if len(ids) != len(set(ids)):
        errs.append("duplicate folder ids")
    known = set(ids)
    for k, v in nodes.items():
        if set(v) - {"label", "parent", "kind", "sysml", "usage"}:
            errs.append(f"node {k}: unexpected keys {sorted(set(v))} (unquoted comma?)")
        if v.get("parent") and v["parent"] not in nodes:
            errs.append(f"node {k}: unknown parent {v['parent']}")
    for a, b, _ in cat["system"]["links"]:
        for n in (a, b):
            if n not in nodes:
                errs.append(f"system link: unknown node {n}")
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
            for st in v.get("steps", []):
                if set(st) - {"name", "label", "safety"}:
                    errs.append(f"{fid}: malformed step {st}")
            for key in ("transitions", "connections", "loops"):
                for t in v.get(key, []):
                    if len(t) != 3:
                        errs.append(f"{fid}: {key} entry must have 3 items: {t}")
            for r in v.get("requirements", []):
                if set(r) - {"id", "name", "text", "risk", "verify", "from"}:
                    errs.append(f"{fid}: malformed requirement {r}")
        if not f.get("model") and not f.get("canonical_model"):
            errs.append(f"{fid}: needs a SysML model (model or canonical_model)")
    return errs


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="fail if generated files are stale")
    args = ap.parse_args()
    cat = yaml.safe_load(CATALOG.read_text())
    errs = validate(cat)
    if errs:
        print("Catalog errors:\n  " + "\n  ".join(errs))
        return 2
    ctx = Ctx(cat)
    stale: list[str] = []
    for f in cat["folders"]:
        here = ctx.path(f["id"])
        views, sysml_text = build_views(ctx, f)
        files: dict[Path, str] = {}
        if sysml_text:
            files[here / f"{f['model']['package']}.sysml"] = sysml_text
        readme = here / "README.md"
        tail = DEFAULT_TAIL
        if readme.exists():
            cur = readme.read_text()
            if END_MARKER in cur:
                tail = cur.split(END_MARKER, 1)[1]
        files[readme] = render(ctx, f, sysml_text, views) + "\n" + tail.lstrip("\n")
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
        print("Stale generated files (run python3 tools/gen_safety_docs.py):\n  " + "\n  ".join(stale))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
