"""Check the SysML model against the records. Usage: python -m tools.sysml.check

Rule families (after LionDriver's check_model.py, adapted to MIL-STD-882E):
  M1  every item-definition element is a part inside SUS-I1, with the same parent, name, kind, role, status, decision
  M2  every external element is a part of the context outside SUS-I1, with the same name and assumption
  M4  every interface is a connection with the same endpoints, direction, kinds, exchange, hazards, status
  M9  every function is an action, performed by exactly the item-definition performers
  R1  generated Requirements.sysml / Satisfaction.sysml match the requirement records
  R2  every satisfy ends on an element inside SUS-I1, and matches the record's allocated_to
  R3  every safety-significant requirement names at least one hazard, and every named hazard exists
Exit 1 on any finding. Hand-written files are checked; generated files are regenerated and compared.
"""
from __future__ import annotations

import sys

from tools.pdac.load import ROOT, _read_yaml
from tools.sysml import gen_requirements
from tools.sysml.model import SYSTEM_ID, Model, ModelError, load

KIND = {"humanInterface": "human-interface"}


def _item():
    return _read_yaml(ROOT / "architecture/item-definition.yaml")


def check(m: Model, item: dict, reqs: list[dict], hazards: set) -> list[str]:
    out = []
    els = {e["id"]: e for e in item["elements"]}
    exts = {e["id"]: e for e in item["externals"]}
    inside = {k: e for k, e in m.elements.items() if not e.external and k != SYSTEM_ID}
    outside = {k: e for k, e in m.elements.items() if e.external}

    # M1 elements
    for k in sorted(set(els) - set(inside)):
        out.append(f"M1 {k}: in the item definition but not a part of SUS-I1 in Architecture.sysml")
    for k in sorted(set(inside) - set(els)):
        out.append(f"M1 {k}: part of SUS-I1 in the model but not in the item definition")
    for k in sorted(set(els) & set(inside)):
        rec, el = els[k], inside[k]
        md = el.meta.get("ItemElement")
        if md is None:
            out.append(f"M1 {k}: part has no @ItemElement metadata")
            continue
        got = {"parent": el.parent or SYSTEM_ID, "name": _type_doc(m, el), "kind": KIND.get(md.get("kind"), md.get("kind")),
               "safety_role": md.get("safetyRole"), "status": md.get("status"), "decision": md.get("decision")}
        for f, v in got.items():
            if rec.get(f) != v:
                out.append(f"M1 {k}: {f} is {v!r} in the model, {rec.get(f)!r} in the item definition")

    # M2 externals
    for k in sorted(set(exts) ^ set(outside)):
        where = "item definition" if k in exts else "model"
        out.append(f"M2 {k}: external element only in the {where}")
    for k in sorted(set(exts) & set(outside)):
        el, rec = outside[k], exts[k]
        if "ExternalElement" not in el.meta:
            out.append(f"M2 {k}: part has no @ExternalElement metadata")
        if _type_doc(m, el) != rec["name"]:
            out.append(f"M2 {k}: name {_type_doc(m, el)!r} vs {rec['name']!r}")
        if el.doc != rec["assumption"]:
            out.append(f"M2 {k}: assumption {el.doc!r} vs {rec['assumption']!r}")

    # M4 interfaces
    ifs = {i["id"]: i for i in item["interfaces"]}
    for k in sorted(set(ifs) ^ set(m.connections)):
        where = "item definition" if k in ifs else "model"
        out.append(f"M4 {k}: interface only in the {where}")
    for k in sorted(set(ifs) & set(m.connections)):
        c, rec = m.connections[k], ifs[k]
        spec = c.meta.get("InterfaceSpec")
        if spec is None:
            out.append(f"M4 {k}: connection has no @InterfaceSpec metadata")
            continue
        got = {"from": c.ends[0], "to": c.ends[1], "name": c.doc, "direction": spec.get("direction"),
               "kind": _list(spec.get("kinds")), "exchange": spec.get("exchange"), "hazard_ids": _list(spec.get("hazards")),
               "status": spec.get("status"), "decision": spec.get("decision")}
        for f, v in got.items():
            if rec.get(f) != v:
                out.append(f"M4 {k}: {f} is {v!r} in the model, {rec.get(f)!r} in the item definition")

    # M9 functions
    fns = {f["id"]: f for f in item["functions"]}
    for k in sorted(set(fns) ^ set(m.functions)):
        where = "item definition" if k in fns else "model"
        out.append(f"M9 {k}: function only in the {where}")
    performers: dict = {}
    for el in m.elements.values():
        for fid in el.performs:
            performers.setdefault(fid, set()).add(el.id)
    for k in sorted(set(fns) & set(m.functions)):
        if m.functions[k].doc != fns[k]["name"]:
            out.append(f"M9 {k}: name {m.functions[k].doc!r} vs {fns[k]['name']!r}")
        if performers.get(k, set()) != set(fns[k]["performed_by"]):
            out.append(f"M9 {k}: performed by {sorted(performers.get(k, set()))} in the model, "
                       f"{sorted(fns[k]['performed_by'])} in the item definition")

    # R1 generated files current
    try:
        for path, text in gen_requirements.build().items():
            if not path.exists() or path.read_text(encoding="utf-8") != text:
                out.append(f"R1 {path.name}: out of date with requirements/; run python -m tools.sysml.gen_requirements")
    except ModelError as exc:
        out.append(f"R1 {exc}")

    # R2 satisfy
    sat: dict = {}
    for rid, eid, f, line in m.satisfies:
        el = m.elements[eid]
        if el.external:
            out.append(f"R2 {f}:{line}: {rid} satisfied by {eid}, which is outside the SUS-I1 boundary")
        sat.setdefault(rid, set()).add(eid)
    for q in reqs:
        if set(q.get("allocated_to") or []) != sat.get(q["id"], set()):
            out.append(f"R2 {q['id']}: satisfied by {sorted(sat.get(q['id'], set()))}, allocated to {sorted(q.get('allocated_to') or [])}")

    # R3 hazards
    for q in reqs:
        r = m.requirements.get(q["id"])
        ids = _list((r.meta.get("HazardRef") or {}).get("ids")) if r else []
        if q.get("safety_significant") and not ids:
            out.append(f"R3 {q['id']}: safety-significant requirement names no hazard")
        for h in ids:
            if h not in hazards:
                out.append(f"R3 {q['id']}: hazard {h} does not exist in safety/hazards/")
    return out


def _list(v) -> list:
    if v is None:
        return []
    return v if isinstance(v, list) else [v]


def _type_doc(m: Model, el) -> str:
    d = m.defs.get((el.type or "").split("::")[-1])
    return d.doc if d else ""


def main() -> int:
    try:
        m = load()
    except ModelError as exc:
        print(f"ModelError: {exc}")
        return 1
    reqs = [_read_yaml(p) for p in sorted((ROOT / "requirements").glob("SYS-*.yaml"))]
    hazards = {p.stem for p in (ROOT / "safety/hazards").glob("HAZ-*.yaml")}
    findings = check(m, _item(), reqs, hazards)
    print(f"SysML model: {len(m.elements)} parts, {len(m.connections)} connections, {len(m.functions)} functions, "
          f"{len(m.requirements)} requirements, {len(m.satisfies)} satisfy relations")
    for f in findings:
        print(f"ERROR {f}")
    print(f"{len(findings)} finding(s). Conformance to SysML v2 is checked separately by tools/sysml/pilot/validate.sh.")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
