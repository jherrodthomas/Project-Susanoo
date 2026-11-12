"""Executable checks traced to MIL-STD-882E (11 May 2012) clauses and PDaC rules.

Every finding names the rule and the clause it enforces. Rules check data, links and
logic only: they never judge technical adequacy and never accept risk.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from jsonschema import Draft202012Validator, FormatChecker

from .load import Repo

RULES = {
    "S00": ("Schema, ID convention and file naming", "PDaC"),
    "L00": ("All references resolve", "PDaC rule 1"),
    "R01": ("RAC and risk level match Table III; target not worse than initial", "4.3.3, Table III"),
    "R02": ("Probability F only through hazard elimination by design", "4.3.3b, 4.3.4a"),
    "R03": ("Design order of precedence applied", "4.3.4"),
    "R04": ("Selected mitigations verified before hazard is verified/accepted/closed", "4.3.6"),
    "R05": ("Acceptance by the appropriate authority with user concurrence for Serious/High", "4.3.1c, 4.3.7"),
    "R06": ("Risk accepted before people, equipment or environment are exposed", "4.3.7, Task 303"),
    "R07": ("Software contribution: SCC, SwCI, LOR and Table VI", "4.4"),
    "R08": ("Risk definitions documented and approved", "4.3.3d, 4.3.3e"),
    "R09": ("HTS minimum data elements present", "4.3.1d, Task 106.2"),
    "R10": ("Changes reopen affected hazards; increased risk re-accepted", "4.3.8, Task 304"),
    "R11": ("Task tailoring consistent with Table A-I and task records", "5.2, Appendix A"),
    "R12": ("Simulated approvals confined to the demonstrator release profile", "Project rule"),
    "R13": ("Acceptance only through a recorded human review; AI review is I0 and never accepts", "4.3.7; project rule"),
    "A01": ("Item definition valid: unique IDs, parents, decisions resolve", "4.3.2; PDaC"),
    "A02": ("Interface endpoints and hazard links resolve", "4.3.2"),
    "A03": ("Hazards, events and requirements name real elements and interfaces", "4.3.2, Task 106.2c"),
    "A04": ("Every element and external has an interface; functions have performers", "4.3.2"),
    "D01": ("Decision register lifecycle", "Project rule"),
}

LEVEL_RANK = {"Eliminated": 0, "Low": 1, "Medium": 2, "Serious": 3, "High": 4}
ACTIVE_MITIGATION = {"selected", "implemented"}
STATUS_ORDER = ["open", "in-mitigation", "verified", "accepted", "closed"]
DEMO_PROFILE = "simulation-and-assurance-demonstrator"


@dataclass(frozen=True)
class Finding:
    rule: str
    level: str  # error | warning
    obj: str
    message: str

    @property
    def clause(self) -> str:
        return RULES[self.rule][1]

    def __str__(self) -> str:
        return f"{self.level.upper():7} {self.rule} [{self.clause}] {self.obj}: {self.message}"


# ---------------------------------------------------------------- helpers

def status_at_least(hazard: dict, status: str) -> bool:
    s = hazard.get("status")
    if s not in STATUS_ORDER:  # "monitor" or invalid (schema rule reports invalid values)
        return False
    return STATUS_ORDER.index(s) >= STATUS_ORDER.index(status)


def matrix_level(model: dict, severity: int, probability: str) -> str:
    return model["rac_matrix"][probability][severity]


def required_authority(tailoring: dict, level: str) -> str | None:
    return tailoring["acceptance_authority"].get(level)


def authority_ok(tailoring: dict, role: str, level: str) -> bool:
    rank = tailoring["authority_rank"]
    need = required_authority(tailoring, level)
    if need is None or role not in rank:
        return False
    return rank.index(role) <= rank.index(need)


def risk_entries(hazard: dict):
    yield "initial_risk", hazard.get("initial_risk")
    yield "target_risk", hazard.get("target_risk")
    for i, ev in enumerate(hazard.get("event_risks") or []):
        yield f"event_risks[{i}]", ev


def hazard_ssf_ids(hazard: dict) -> set:
    ids = set()
    for cf in hazard.get("causal_factors") or []:
        ids.update(cf.get("ssf_ids") or [])
    for m in hazard.get("mitigations") or []:
        ids.update(m.get("ssf_ids") or [])
    return ids


def software_analysis(repo: Repo) -> dict:
    """Per SSF: severity (worst linked hazard), SwCI (Table V), required/incomplete LOR, Table VI level."""
    model = repo.model
    out = {}
    hazards = repo.objects["hazard"]
    for sid, ssf in repo.objects["ssf"].items():
        linked = sorted(h for h, rec in hazards.items() if sid in hazard_ssf_ids(rec))
        severities = [hazards[h]["initial_risk"]["severity"] for h in linked
                      if isinstance(hazards[h].get("initial_risk"), dict) and hazards[h]["initial_risk"].get("severity") in (1, 2, 3, 4)]
        severity = min(severities) if severities else None
        swci = model["sscm"][ssf["scc"]][severity] if severity else None
        required = model["lor_tasks"][swci] if swci else []
        lor = ssf.get("lor") or {}
        incomplete = [t for t in required if (lor.get(t) or {}).get("status") != "complete"]
        table_vi = model["incomplete_lor_risk"][swci] if (swci and incomplete) else None
        out[sid] = {
            "hazards": linked, "severity": severity, "swci": swci, "required": required,
            "incomplete": incomplete, "table_vi_level": table_vi,
        }
    return out


def software_contribution_level(repo: Repo, hazard: dict, analysis: dict) -> str | None:
    """Highest Table VI risk level among SSFs linked to this hazard with incomplete LOR."""
    best = None
    for sid in hazard_ssf_ids(hazard):
        lvl = (analysis.get(sid) or {}).get("table_vi_level")
        if lvl and (best is None or LEVEL_RANK[lvl] > LEVEL_RANK[best]):
            best = lvl
    return best


def event_applies(event: dict, hazard: dict) -> bool:
    if event["configuration"] not in hazard["applicability"]["configurations"]:
        return False
    if not set(event.get("modes") or []) & set(hazard.get("modes") or []):
        return False
    subs = set(event.get("subsystems") or [])
    return not subs or bool(subs & set(hazard.get("subsystems") or []))


# ---------------------------------------------------------------- rules

def check_schema(repo: Repo):
    for path, msg in repo.load_errors:
        yield Finding("S00", "error", path, msg)
    patterns = repo.tailoring.get("id_patterns", {})
    pattern_for = {"hazard": "hazard", "ssf": "ssf", "requirement": "requirement",
                   "event": "event", "change": "change", "verification": "verification", "review": "review"}
    for kind, recs in repo.objects.items():
        validator = Draft202012Validator(repo.schemas[kind], format_checker=FormatChecker())
        for oid, rec in recs.items():
            for err in sorted(validator.iter_errors(rec), key=lambda e: list(e.path)):
                where = "/".join(str(p) for p in err.path) or "(root)"
                yield Finding("S00", "error", str(oid), f"{where}: {err.message}")
            pat = patterns.get(pattern_for.get(kind, ""))
            if pat and not re.match(pat, str(oid)):
                yield Finding("S00", "error", str(oid), f"id does not match convention {pat}")
            path = repo.paths.get((kind, oid), "")
            expected = f"T{oid}.yaml" if kind == "task" else f"{oid}.yaml"
            if not path.endswith("/" + expected):
                yield Finding("S00", "error", str(oid), f"file {path} should be named {expected}")


def check_links(repo: Repo):
    o = repo.objects
    roles = set(repo.tailoring["roles"])
    reqs, ssfs, vers, evts, hzs = o["requirement"], o["ssf"], o["verification"], o["event"], o["hazard"]
    tasks = {t["id"] for t in repo.model["tasks"]}
    mitigation_ids = {f"{h}:{m['id']}" for h, rec in hzs.items() for m in rec.get("mitigations") or []}

    def need(obj, ref, pool, what):
        if ref not in pool:
            yield Finding("L00", "error", obj, f"unresolved {what} reference '{ref}'")

    for hid, h in hzs.items():
        for r in h.get("requirement_ids") or []:
            yield from need(hid, r, reqs, "requirement")
        for cf in h.get("causal_factors") or []:
            for s in cf.get("ssf_ids") or []:
                yield from need(hid, s, ssfs, "SSF")
        for m in h.get("mitigations") or []:
            for r in m.get("requirement_ids") or []:
                yield from need(hid, r, reqs, "requirement")
            for s in m.get("ssf_ids") or []:
                yield from need(hid, s, ssfs, "SSF")
            for e in (m.get("verification") or {}).get("evidence_ids") or []:
                yield from need(hid, e, vers, "verification")
        for ev in h.get("event_risks") or []:
            yield from need(hid, ev.get("event_id"), evts, "event")
        for a in h.get("acceptances") or []:
            yield from need(hid, a.get("authority_role"), roles, "role")
            if a.get("basis") != "target":
                yield from need(hid, a.get("basis"), evts, "event (acceptance basis)")
            if a.get("user_concurrence"):
                yield from need(hid, a["user_concurrence"].get("role"), roles, "role")
        yield from need(hid, (h.get("owner") or {}).get("role"), roles, "role")
        if (h.get("source") or {}).get("task") not in tasks:
            yield Finding("L00", "error", hid, f"source task {h.get('source', {}).get('task')} is not a MIL-STD-882E task")
        for c in [x["change_request"] for x in h.get("reassessments") or []]:
            yield from need(hid, c, o["change"], "change request")
    for sid, s in ssfs.items():
        for r in s.get("requirement_ids") or []:
            yield from need(sid, r, reqs, "requirement")
        yield from need(sid, s.get("owner"), roles, "role")
    for rid, r in reqs.items():
        for h in (r.get("source") or {}).get("hazard_ids") or []:
            yield from need(rid, h, hzs, "hazard")
        for d in r.get("derived_from") or []:
            yield from need(rid, d, reqs, "parent requirement (derived_from)")
            if d == rid:
                yield Finding("L00", "error", rid, "requirement is derived from itself")
        for e in (r.get("verification") or {}).get("evidence_ids") or []:
            yield from need(rid, e, vers, "verification")
    pool = repo.all_ids() | mitigation_ids
    configs = {repo.product.get("configuration", {}).get("id")}
    for cid, c in o["change"].items():
        for a in c.get("affects") or []:
            if a not in pool and a not in configs:
                yield Finding("L00", "error", cid, f"unresolved affected item '{a}'")
    for tid, t in o["task"].items():
        for hz in t.get("hazard_ids") or []:
            yield from need(f"T{tid}", hz, hzs, "hazard")
        yield from need(f"T{tid}", t.get("owner"), roles, "role")


def check_rac(repo: Repo):
    for hid, h in repo.objects["hazard"].items():
        for where, r in risk_entries(h):
            if not isinstance(r, dict) or r.get("severity") not in (1, 2, 3, 4) or r.get("probability") not in tuple("ABCDEF"):
                continue
            rac = f"{r['severity']}{r['probability']}"
            if r.get("rac") != rac:
                yield Finding("R01", "error", hid, f"{where}.rac is {r.get('rac')}, expected {rac}")
            expected = matrix_level(repo.model, r["severity"], r["probability"])
            if r.get("risk_level") != expected:
                yield Finding("R01", "error", hid, f"{where}.risk_level is {r.get('risk_level')}, Table III gives {expected} for {rac}")
        ini, tgt = h.get("initial_risk") or {}, h.get("target_risk") or {}
        if ini.get("risk_level") in LEVEL_RANK and tgt.get("risk_level") in LEVEL_RANK:
            if LEVEL_RANK[tgt["risk_level"]] > LEVEL_RANK[ini["risk_level"]]:
                yield Finding("R01", "error", hid, "target risk is higher than initial risk")


def check_eliminated(repo: Repo):
    for hid, h in repo.objects["hazard"].items():
        has_a = any(m.get("precedence") == "a" and m.get("state") in ACTIVE_MITIGATION for m in h.get("mitigations") or [])
        for where, r in risk_entries(h):
            if where == "initial_risk" or not isinstance(r, dict):
                continue
            if r.get("probability") == "F" and not has_a:
                yield Finding("R02", "error", hid,
                              f"{where} claims probability F without a selected precedence-a (eliminate by design) mitigation; "
                              "doctrine, training, warnings, caution or PPE cannot reach F")


def check_precedence(repo: Repo):
    for hid, h in repo.objects["hazard"].items():
        active = [m for m in h.get("mitigations") or [] if m.get("state") in ACTIVE_MITIGATION]
        for m in h.get("mitigations") or []:
            if m.get("state") == "rejected" and not m.get("rejection_rationale"):
                yield Finding("R03", "error", hid, f"mitigation {m.get('id')} rejected without rationale")
        if status_at_least(h, "in-mitigation") and not active:
            yield Finding("R03", "error", hid, f"status {h['status']} but no mitigation is selected")
        if not active:
            continue
        sev = (h.get("initial_risk") or {}).get("severity")
        best = min(m["precedence"] for m in active)
        if sev in (1, 2) and best == "e":
            yield Finding("R03", "error", hid,
                          "Catastrophic/Critical hazard relies only on signage, procedures, training or PPE")
        elif best in ("d", "e") and not h.get("precedence_rationale"):
            yield Finding("R03", "warning", hid,
                          f"best selected mitigation is precedence {best}; record precedence_rationale for why a-c are not feasible")


def check_verification(repo: Repo):
    vers = repo.objects["verification"]
    for hid, h in repo.objects["hazard"].items():
        if not status_at_least(h, "verified"):
            continue
        for m in h.get("mitigations") or []:
            if m.get("state") not in ACTIVE_MITIGATION:
                continue
            if m.get("state") != "implemented":
                yield Finding("R04", "error", hid, f"mitigation {m['id']} is not implemented")
            ev = (m.get("verification") or {}).get("evidence_ids") or []
            if not ev:
                yield Finding("R04", "error", hid, f"mitigation {m['id']} has no verification evidence")
            for e in ev:
                rec = vers.get(e)
                if rec and rec.get("result") != "passed":
                    yield Finding("R04", "error", hid, f"mitigation {m['id']} evidence {e} result is {rec.get('result')}")
                if rec and rec.get("method") not in (m.get("verification") or {}).get("method", []):
                    yield Finding("R04", "warning", hid, f"evidence {e} method {rec.get('method')} not among planned methods for {m['id']}")
    for rid, r in repo.objects["requirement"].items():
        if r.get("status") == "baselined" and "TBD" in (r.get("verification") or {}).get("method", ["TBD"]):
            yield Finding("R04", "error", rid, "baselined requirement has no verification method (PDaC rule 2)")


def _accepted_level_ok(repo, hid, acc, level, what):
    if LEVEL_RANK[acc["risk_level"]] < LEVEL_RANK[level]:
        yield Finding("R05", "error", hid, f"acceptance {acc['id']} accepts {acc['risk_level']} but {what} is {level}")


def check_acceptance(repo: Repo, analysis: dict | None = None):
    t = repo.tailoring
    analysis = analysis if analysis is not None else software_analysis(repo)
    for hid, h in repo.objects["hazard"].items():
        events = {e.get("event_id"): e for e in h.get("event_risks") or []}
        sw_level = software_contribution_level(repo, h, analysis)
        for acc in h.get("acceptances") or []:
            lvl = acc.get("risk_level")
            if lvl not in LEVEL_RANK:
                continue
            if not authority_ok(t, acc.get("authority_role"), lvl):
                yield Finding("R05", "error", hid,
                              f"acceptance {acc['id']} of {lvl} risk by {acc.get('authority_role')}; requires {required_authority(t, lvl)} or higher")
            if lvl in t["user_concurrence_required_for"]:
                uc = acc.get("user_concurrence")
                if not uc or uc.get("role") != t["user_representative"]:
                    yield Finding("R05", "error", hid, f"acceptance {acc['id']} of {lvl} risk lacks user representative concurrence")
            basis = acc.get("basis")
            if basis == "target":
                yield from _accepted_level_ok(repo, hid, acc, (h.get("target_risk") or {}).get("risk_level", "Low"), "target risk")
            elif basis in events:
                yield from _accepted_level_ok(repo, hid, acc, events[basis].get("risk_level", "Low"), f"event risk for {basis}")
            else:
                yield Finding("R05", "error", hid, f"acceptance {acc['id']} basis '{basis}' has no matching event risk")
            if sw_level:
                yield from _accepted_level_ok(repo, hid, acc, sw_level, "Table VI software contribution")
        if status_at_least(h, "accepted") and not any(a.get("basis") == "target" for a in h.get("acceptances") or []):
            yield Finding("R05", "error", hid, f"status {h['status']} requires an acceptance with basis 'target'")


def check_exposure(repo: Repo):
    for eid, ev in repo.objects["event"].items():
        exp = ev.get("exposure") or {}
        if not (exp.get("people") or exp.get("equipment") or exp.get("environment")):
            continue
        level = "error" if ev.get("status") in ("authorized", "conducted") else "warning"
        for hid, h in sorted(repo.objects["hazard"].items()):
            if not event_applies(ev, h):
                continue
            if not any(e.get("event_id") == eid for e in h.get("event_risks") or []):
                yield Finding("R06", level, eid, f"{hid} applies but has no event risk assessment for this event")
            elif not any(a.get("basis") == eid for a in h.get("acceptances") or []):
                yield Finding("R06", level, eid, f"{hid} event risk not accepted before exposure")


def check_software(repo: Repo, analysis: dict | None = None):
    analysis = analysis if analysis is not None else software_analysis(repo)
    for sid, a in analysis.items():
        ssf = repo.objects["ssf"][sid]
        if not a["hazards"]:
            yield Finding("R07", "error", sid, "SSF is not linked to any hazard; SwCI cannot be derived")
            continue
        if ssf.get("swci") is not None and ssf["swci"] != a["swci"]:
            yield Finding("R07", "error", sid, f"declared SwCI {ssf['swci']} but Table V gives SwCI {a['swci']} (SCC {ssf['scc']}, severity {a['severity']})")
        if a["incomplete"]:
            hazards = repo.objects["hazard"]
            advanced = [h for h in a["hazards"] if status_at_least(hazards[h], "verified")]
            if advanced and not ssf.get("lor_decision"):
                yield Finding("R07", "error", sid,
                              f"LOR incomplete ({', '.join(a['incomplete'])}) for SwCI {a['swci']} while {', '.join(advanced)} "
                              f"progressed; Table VI requires a documented PM decision at {a['table_vi_level']}")
    for hid, h in repo.objects["hazard"].items():
        sw = [cf for cf in h.get("causal_factors") or [] if cf.get("type") == "software"]
        for cf in sw:
            if not cf.get("ssf_ids"):
                yield Finding("R07", "error", hid, f"software causal factor {cf.get('id')} not linked to an SSF")


def check_definitions(repo: Repo):
    rd = repo.tailoring.get("risk_definitions") or {}
    rid = rd.get("id")
    if not rid:
        yield Finding("R08", "error", "tailoring", "no risk definitions documented (4.3.3e)")
        return
    sev = (rd.get("severity") or {}).get("monetary_min_usd") or {}
    vals = [sev.get(k) for k in (1, 2, 3, 4)]
    if None in vals or not all(vals[i] > vals[i + 1] for i in range(2)) or vals[3] != 0:
        yield Finding("R08", "error", "tailoring", "tailored severity thresholds must keep four ordered Table I categories")
    if not (rd.get("probability") or {}).get("basis"):
        yield Finding("R08", "error", "tailoring", "probability exposure basis not documented")
    if (rd.get("approval") or {}).get("status") != "approved":
        yield Finding("R08", "warning", "tailoring", f"{rid} is not approved; tailored definitions need formal approval (4.3.3d)")
    for hid, h in repo.objects["hazard"].items():
        for where, r in risk_entries(h):
            if isinstance(r, dict) and r.get("definitions") != rid:
                yield Finding("R08", "error", hid, f"{where} does not cite risk definitions {rid}")


def check_hts(repo: Repo):
    required_nonempty = {"a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "m", "n", "p", "s"}
    for hid, h in repo.objects["hazard"].items():
        for el in repo.model["hts_elements"]:
            if el["id"] not in required_nonempty:
                continue
            key = el["path"].split("[")[0].split(".")[0]
            if h.get(key) in (None, "", [], {}):
                yield Finding("R09", "error", hid, f"HTS element 106.2{el['id']} ({el['element']}) is empty")
        if status_at_least(h, "accepted") and not h.get("acceptances"):
            yield Finding("R09", "error", hid, "HTS element 106.2q: no record of risk acceptance")


def impacted_hazards(repo: Repo, affects: list) -> set:
    out = set()
    aff = set(affects)
    for hid, h in repo.objects["hazard"].items():
        links = {hid} | set(h.get("requirement_ids") or []) | hazard_ssf_ids(h) | set(h["applicability"]["configurations"])
        for m in h.get("mitigations") or []:
            links.add(f"{hid}:{m['id']}")
            links.update(m.get("requirement_ids") or [])
        if links & aff:
            out.add(hid)
    return out


def check_changes(repo: Repo):
    for cid, c in repo.objects["change"].items():
        if c.get("status") not in ("approved", "implemented"):
            continue
        for hid in sorted(impacted_hazards(repo, c.get("affects") or [])):
            h = repo.objects["hazard"][hid]
            ra = [r for r in h.get("reassessments") or [] if r.get("change_request") == cid]
            if not ra:
                yield Finding("R10", "error", cid, f"{hid} is affected but has no reassessment for this change")
                continue
            accs = h.get("acceptances") or []
            for r in ra:
                # 4.3.8: a previously accepted risk that increases must be formally re-accepted.
                if r["outcome"] == "risk-increased" and accs:
                    later = [a for a in accs if str(a.get("date")) >= str(r["date"])]
                    if not later:
                        yield Finding("R10", "error", hid, f"risk increased by {cid}; needs a new acceptance dated on or after {r['date']}")


def check_tailoring(repo: Repo):
    t = repo.tailoring
    gates = list(t["gates"])
    current = t["current_gate"]
    a1 = {x["id"]: x for x in repo.model["tasks"]}
    records = repo.objects["task"]
    for tid, task in a1.items():
        dec = t["tasks"].get(tid)
        if dec is None:
            yield Finding("R11", "error", f"T{tid}", "no tailoring decision recorded")
            continue
        if not dec.get("rationale"):
            yield Finding("R11", "error", f"T{tid}", "tailoring decision without rationale")
        if dec["disposition"] == "selected":
            if dec.get("gate") not in gates:
                yield Finding("R11", "error", f"T{tid}", "selected task has no valid gate")
            elif gates.index(dec["gate"]) <= gates.index(current) and tid not in records:
                yield Finding("R11", "warning", f"T{tid}", f"selected for {dec['gate']} (current {current}) but no task record exists")
            if dec.get("did") and dec["did"] not in {d["id"] for d in repo.model["dids"]}:
                yield Finding("R11", "error", f"T{tid}", f"DID {dec['did']} is not listed in 6.3")
        else:
            if tid in records:
                yield Finding("R11", "error", f"T{tid}", f"task record exists but task is {dec['disposition']}")
            if dec["disposition"] == "conditional" and not dec.get("trigger"):
                yield Finding("R11", "error", f"T{tid}", "conditional task needs a trigger")
    for tid in records:
        if tid not in a1:
            yield Finding("R11", "error", f"T{tid}", "task record for unknown task")


def check_simulated(repo: Repo):
    profile = (repo.product.get("release") or {}).get("profile")
    if profile == DEMO_PROFILE:
        return
    for hid, h in repo.objects["hazard"].items():
        for a in h.get("acceptances") or []:
            if a.get("simulated"):
                yield Finding("R12", "error", hid, f"simulated acceptance {a['id']} used with release profile '{profile}'")


def run_all(repo: Repo) -> list[Finding]:
    analysis = software_analysis(repo)
    checks = [check_schema, check_links, check_rac, check_eliminated, check_precedence, check_verification,
              lambda r: check_acceptance(r, analysis), check_exposure, lambda r: check_software(r, analysis),
              check_definitions, check_hts, check_changes, check_tailoring, check_simulated]
    from .rules_ext import EXT_CHECKS  # local import: rules_ext imports Finding from this module
    checks += EXT_CHECKS
    findings = []
    for check in checks:
        findings.extend(check(repo))
    return findings
