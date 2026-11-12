"""Architecture (item definition), review-record and decision-register rules.

A01-A04 keep architecture/item-definition.yaml consistent with itself and with the safety records.
R13 enforces that only a recorded human review accepts anything (ported from LionDriver's V6 rule).
D01 enforces the decision register lifecycle (ported from LionDriver's check_decisions.py).
"""
from __future__ import annotations

from jsonschema import Draft202012Validator, FormatChecker

from .rules import Finding

ROOT_ID = "SUS-I1"
ACCEPTING = {"accepted", "accepted-with-actions"}
MAX_OPEN = 10


# ---------------------------------------------------------------- item definition helpers

def item_index(repo) -> dict:
    item = repo.item or {}
    return {
        "elements": {e["id"]: e for e in item.get("elements") or []},
        "externals": {e["id"]: e for e in item.get("externals") or []},
        "interfaces": {i["id"]: i for i in item.get("interfaces") or []},
        "functions": {f["id"]: f for f in item.get("functions") or []},
    }


def ancestors(elements: dict, eid: str) -> list[str]:
    out, seen = [], set()
    while eid in elements and eid not in seen:
        seen.add(eid)
        eid = elements[eid]["parent"]
        out.append(eid)
    return out


def top_level(elements: dict, eid: str) -> str:
    """The child of the root that contains eid (eid itself if it is top level); externals map to themselves."""
    if eid not in elements:
        return eid
    chain = [eid] + ancestors(elements, eid)
    return chain[chain.index(ROOT_ID) - 1] if ROOT_ID in chain else eid


def check_item_schema(repo):
    if not repo.item:
        yield Finding("A01", "error", "architecture", "architecture/item-definition.yaml is missing")
        return
    v = Draft202012Validator(repo.schemas["item"], format_checker=FormatChecker())
    for err in sorted(v.iter_errors(repo.item), key=lambda e: list(e.path)):
        where = "/".join(str(p) for p in err.path) or "(root)"
        yield Finding("A01", "error", "item-definition", f"{where}: {err.message}")
    seen = {}
    for kind in ("functions", "elements", "externals", "interfaces"):
        for rec in repo.item.get(kind) or []:
            rid = rec.get("id")
            if rid in seen:
                yield Finding("A01", "error", str(rid), f"duplicate id (also in {seen[rid]})")
            seen[rid] = kind
    idx = item_index(repo)
    decisions = {d["id"] for d in (repo.decisions or {}).get("decisions") or []}
    for eid, e in idx["elements"].items():
        if e["parent"] != ROOT_ID and e["parent"] not in idx["elements"]:
            yield Finding("A01", "error", eid, f"parent {e['parent']} is not an element")
        if eid in ancestors(idx["elements"], eid):
            yield Finding("A01", "error", eid, "parent chain is cyclic")
        if e.get("status") == "candidate" and not e.get("decision"):
            yield Finding("A01", "error", eid, "candidate element must name the decision it depends on")
    for rec in list(idx["elements"].values()) + list(idx["interfaces"].values()):
        if rec.get("decision") and rec["decision"] not in decisions:
            yield Finding("A01", "error", rec["id"], f"decision {rec['decision']} is not in the decision register")


def check_interfaces(repo):
    idx = item_index(repo)
    ends = set(idx["elements"]) | set(idx["externals"]) | {ROOT_ID}
    hazards = repo.objects["hazard"]
    for iid, i in idx["interfaces"].items():
        for side in ("from", "to"):
            if i[side] not in ends:
                yield Finding("A02", "error", iid, f"{side} endpoint {i[side]} is not an element or external")
        if i["from"] == i["to"]:
            yield Finding("A02", "error", iid, "interface connects an element to itself")
        if i["from"] in idx["externals"] and i["to"] in idx["externals"]:
            yield Finding("A02", "error", iid, "interface lies wholly outside the boundary")
        for h in i.get("hazard_ids") or []:
            if h not in hazards:
                yield Finding("A02", "error", iid, f"unresolved hazard reference '{h}'")


def check_item_references(repo):
    idx = item_index(repo)
    elements = set(idx["elements"]) | {ROOT_ID}
    for hid, h in repo.objects["hazard"].items():
        for s in h.get("subsystems") or []:
            if s not in elements:
                yield Finding("A03", "error", hid, f"subsystem {s} is not an element of the item definition")
        for i in (h.get("source") or {}).get("interface_ids") or []:
            if i not in idx["interfaces"]:
                yield Finding("A03", "error", hid, f"interface {i} is not in the item definition")
    for eid, ev in repo.objects["event"].items():
        for s in ev.get("subsystems") or []:
            if s not in elements:
                yield Finding("A03", "error", eid, f"subsystem {s} is not an element of the item definition")
        for s in ev.get("hardware") or []:
            if s not in elements:
                yield Finding("A03", "error", eid, f"hardware {s} is not an element of the item definition")
    for rid, r in repo.objects["requirement"].items():
        for s in r.get("allocated_to") or []:
            if s not in elements:
                yield Finding("A03", "error", rid, f"allocated to {s}, which is not an element of the item definition")


def check_item_completeness(repo):
    idx = item_index(repo)
    els = idx["elements"]
    touched = set()
    for i in idx["interfaces"].values():
        for side in (i["from"], i["to"]):
            touched.add(side)
            touched.update(ancestors(els, side))
    for eid in list(els) + list(idx["externals"]):
        if eid not in touched:
            yield Finding("A04", "error", eid, "has no interface (4.3.2: interfaces, including human, must be identified)")
    performed = set()
    for fid, f in idx["functions"].items():
        for p in f["performed_by"]:
            if p not in els:
                yield Finding("A04", "error", fid, f"performer {p} is not an element")
            performed.add(p)
            performed.update(ancestors(els, p))
    parents = {e["parent"] for e in els.values()}
    direct = {p for f in idx["functions"].values() for p in f["performed_by"]}
    for eid in els:
        if eid not in parents and eid not in performed and not set(ancestors(els, eid)) & direct:
            yield Finding("A04", "warning", eid, "leaf element performs no function")


# ---------------------------------------------------------------- R13: acceptance only through human review

def _accepting_review(repo, rev_id, scope_id, need_role=None):
    """(ok, reason) for whether REV rev_id accepts scope_id with a human reviewer (in need_role, if given)."""
    rev = repo.objects["review"].get(rev_id)
    if not rev_id:
        return False, "no review_id"
    if rev is None:
        return False, f"review {rev_id} does not exist"
    if rev.get("outcome") not in ACCEPTING:
        return False, f"review {rev_id} outcome is {rev.get('outcome')}"
    if scope_id not in rev.get("scope", []):
        return False, f"review {rev_id} does not list {scope_id} in its scope"
    humans = [r for r in rev.get("reviewers", []) if r.get("human") and r.get("person")]
    if need_role and not any(r.get("role") == need_role for r in humans):
        return False, f"review {rev_id} has no named human reviewer in role {need_role}"
    if not humans:
        return False, f"review {rev_id} has no named human reviewer"
    return True, ""


def check_reviews(repo):
    roles = set(repo.tailoring["roles"])
    t = repo.tailoring
    for rid, rev in repo.objects["review"].items():
        for r in rev.get("reviewers", []):
            if r.get("role") not in roles:
                yield Finding("R13", "error", rid, f"reviewer role {r.get('role')} is not a tailoring role")
            if not r.get("human") and r.get("independence") != "I0":
                yield Finding("R13", "error", rid, "an AI reviewer is independence I0")
        if rev.get("outcome") in ACCEPTING and not any(r.get("human") and r.get("person") for r in rev.get("reviewers", [])):
            yield Finding("R13", "error", rid, "accepting review has no named human reviewer; CI, tests or an AI review never accept")
    for hid, h in repo.objects["hazard"].items():
        for a in h.get("acceptances") or []:
            ok, why = _accepting_review(repo, a.get("review_id"), hid, a.get("authority_role"))
            if not ok:
                yield Finding("R13", "error", hid, f"acceptance {a.get('id')}: {why}")
            elif a.get("user_concurrence"):
                ok, why = _accepting_review(repo, a.get("review_id"), hid, a["user_concurrence"].get("role"))
                if not ok:
                    yield Finding("R13", "error", hid, f"acceptance {a.get('id')} user concurrence: {why}")
    for tid, rec in repo.objects["task"].items():
        if rec.get("status") == "approved":
            ok, why = _accepting_review(repo, rec.get("review_id"), f"T{tid}")
            if not ok:
                yield Finding("R13", "error", f"T{tid}", f"approved task record: {why}")
    for qid, r in repo.objects["requirement"].items():
        if r.get("status") == "baselined":
            ok, why = _accepting_review(repo, r.get("review_id"), qid)
            if not ok:
                yield Finding("R13", "error", qid, f"baselined requirement: {why}")
    for label, block, scope_id in (("tailoring", t.get("approval") or {}, "tailoring"),
                                   ("risk definitions", (t.get("risk_definitions") or {}).get("approval") or {},
                                    (t.get("risk_definitions") or {}).get("id"))):
        if block.get("status") == "approved":
            ok, why = _accepting_review(repo, block.get("record"), scope_id, block.get("authority_role"))
            if not ok:
                yield Finding("R13", "error", label, f"approved {label}: {why}")
    if (repo.item or {}).get("status") == "approved":
        ok, why = _accepting_review(repo, repo.item.get("review_id"), repo.item.get("id"))
        if not ok:
            yield Finding("R13", "error", "item-definition", f"approved item definition: {why}")


# ---------------------------------------------------------------- D01: decision register

def check_decisions(repo):
    reg = repo.decisions or {}
    if not reg:
        yield Finding("D01", "error", "decisions", "decisions/register.yaml is missing")
        return
    v = Draft202012Validator(repo.schemas["decisions"], format_checker=FormatChecker())
    for err in sorted(v.iter_errors(reg), key=lambda e: list(e.path)):
        where = "/".join(str(p) for p in err.path) or "(root)"
        yield Finding("D01", "error", "decisions", f"{where}: {err.message}")
    seen = set()
    open_count = 0
    for d in reg.get("decisions") or []:
        did = d.get("id")
        if did in seen:
            yield Finding("D01", "error", str(did), "duplicate decision id")
        seen.add(did)
        keys = [o.get("key") for o in d.get("options") or []]
        if len(set(keys)) != len(keys):
            yield Finding("D01", "error", did, "option keys must be unique")
        if keys and d.get("recommendation") != keys[0]:
            yield Finding("D01", "error", did, "the recommended option must be listed first")
        st = d.get("status")
        ans = d.get("answer")
        if st in ("answered", "applied"):
            if not ans:
                yield Finding("D01", "error", did, f"status {st} needs an answer")
            elif ans.get("choice") not in keys:
                yield Finding("D01", "error", did, f"answer choice {ans.get('choice')} is not an option")
            elif d.get("decider") == "lead" and ans.get("by") == "claude":
                yield Finding("D01", "error", did, "a lead decision cannot be answered by claude")
        elif ans:
            yield Finding("D01", "error", did, f"status {st} must not carry an answer")
        if st == "applied":
            if not d.get("applied_in"):
                yield Finding("D01", "error", did, "applied decision must say where it was applied (applied_in)")
            for p in d.get("applied_in") or []:
                if not (repo.root / p.split("#")[0]).exists():
                    yield Finding("D01", "error", did, f"applied_in path {p} does not exist")
        if st == "open":
            open_count += 1
            if d.get("decider") == "claude":
                yield Finding("D01", "error", did, "a claude decision is never open for the lead; decide, apply and record it")
            if not d.get("asked"):
                yield Finding("D01", "error", did, "open decision needs the date it was asked")
    if open_count > MAX_OPEN:
        yield Finding("D01", "warning", "decisions", f"{open_count} decisions open; keep about {MAX_OPEN} (batches of ten)")


# ---------------------------------------------------------------- T01: trade studies

def check_trades(repo):
    """A trade study is AI-draftable; its weights are confirmed and its alternative selected only by the lead."""
    decisions = {d["id"]: d for d in (repo.decisions or {}).get("decisions") or []}
    elements = set(item_index(repo)["elements"])
    hazards, reqs = repo.objects.get("hazard", {}), repo.objects.get("requirement", {})
    for tid, t in (repo.objects.get("trade") or {}).items():
        alts = {a["id"] for a in t.get("alternatives") or []}
        crit = {c["id"]: c for c in t.get("criteria") or []}
        evid = {e["id"]: e for e in t.get("evidence") or []}
        total = sum(c["weight"] for c in crit.values())
        if abs(total - 100) > 1e-9:
            yield Finding("T01", "error", tid, f"criteria weights sum to {total:g}, not 100")
        for did in t.get("decision_ids") or []:
            if did not in decisions:
                yield Finding("T01", "error", tid, f"decision {did} is not in decisions/register.yaml")
        for a in t.get("alternatives") or []:
            for e in a.get("elements") or []:
                if e not in elements:
                    yield Finding("T01", "error", tid, f"alternative {a['id']}: element {e} is not in the item definition")
            for h in a.get("hazard_ids") or []:
                if h not in hazards:
                    yield Finding("T01", "error", tid, f"alternative {a['id']}: hazard {h} does not exist")
        for r in t.get("requirement_ids") or []:
            if r not in reqs:
                yield Finding("T01", "error", tid, f"requirement {r} does not exist")
        for e in evid.values():
            for c in e["criteria"]:
                if c not in crit:
                    yield Finding("T01", "error", tid, f"evidence {e['id']}: unknown criterion {c}")
            if e["status"] != "planned":
                src = e.get("source")
                if not src:
                    yield Finding("T01", "error", tid, f"evidence {e['id']} is {e['status']} but names no source")
                elif not (repo.root / src.split("#")[0]).exists():
                    yield Finding("T01", "error", tid, f"evidence {e['id']}: source {src} does not exist")
        seen = set()
        for s in t.get("scores") or []:
            key = (s["alternative"], s["criterion"])
            if key in seen:
                yield Finding("T01", "error", tid, f"score {key} given twice")
            seen.add(key)
            if s["alternative"] not in alts or s["criterion"] not in crit:
                yield Finding("T01", "error", tid, f"score {key} names an unknown alternative or criterion")
            for b in s["basis"]:
                if b not in evid:
                    yield Finding("T01", "error", tid, f"score {key}: unknown evidence {b}")
                elif s["score"] is not None and evid[b]["status"] == "planned":
                    yield Finding("T01", "error", tid, f"score {key} rests on planned evidence {b}")
            if s["score"] is not None and not s["basis"]:
                yield Finding("T01", "error", tid, f"score {key} has no evidence basis")
        wd = decisions.get(t.get("weights_decision_id"))
        if t.get("weights_decision_id") and not wd:
            yield Finding("T01", "error", tid, f"weights decision {t['weights_decision_id']} is not in the register")
        if t.get("weights_status") == "confirmed" and not (wd and wd.get("decider") == "lead" and wd.get("status") == "applied"):
            yield Finding("T01", "error", tid, "weights are confirmed only by an applied lead decision (weights_decision_id)")
        sel = t.get("selection")
        if t.get("status") == "selected" or sel:
            if not sel or sel.get("alternative") not in alts:
                yield Finding("T01", "error", tid, "status selected needs selection.alternative from the alternatives")
            else:
                d = decisions.get(sel.get("decision_id"))
                if not d or d.get("decider") != "lead" or d.get("status") != "applied":
                    yield Finding("T01", "error", tid, "a selection needs an applied lead decision (selection.decision_id)")
                ok, why = _accepting_review(repo, t.get("review_id"), tid)
                if not ok:
                    yield Finding("R13", "error", tid, f"selected trade study: {why}")


EXT_CHECKS = [check_item_schema, check_interfaces, check_item_references, check_item_completeness,
              check_reviews, check_decisions, check_trades]
