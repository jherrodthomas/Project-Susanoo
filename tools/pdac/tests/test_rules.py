"""Rule tests: each rule must fire on a seeded violation and stay quiet on the committed records."""
import copy
import unittest

from tools.pdac import rules
from tools.pdac.load import load
from tools.pdac.report import build
from tools.terms.terms import decorate

BASE = load()


def fresh():
    repo = copy.copy(BASE)
    repo.objects = copy.deepcopy(BASE.objects)
    repo.tailoring = copy.deepcopy(BASE.tailoring)
    repo.product = copy.deepcopy(BASE.product)
    repo.paths = dict(BASE.paths)
    repo.item = copy.deepcopy(BASE.item)
    repo.decisions = copy.deepcopy(BASE.decisions)
    return repo


def errors(repo, rule):
    return [f for f in rules.run_all(repo) if f.rule == rule and f.level == "error"]


def accept(aid, level, role, basis="target", concur=True):
    a = {"id": aid, "risk_level": level, "basis": basis, "authority_role": role, "date": "2026-11-11",
         "record": "records/acceptance.pdf", "simulated": True}
    if concur:
        a["user_concurrence"] = {"role": "ROLE-UR", "date": "2026-11-11", "record": "records/concur.pdf"}
    return a


class Baseline(unittest.TestCase):
    def test_committed_records_have_no_errors(self):
        errs = [str(f) for f in rules.run_all(BASE) if f.level == "error"]
        self.assertEqual(errs, [])

    def test_generated_files_current(self):
        for rel, text in build(BASE).items():
            self.assertEqual((BASE.root / rel).read_text(encoding="utf-8"), decorate(rel, text), f"{rel} stale; run report")

    def test_table_v_examples(self):
        self.assertEqual(BASE.model["sscm"][1][2], 1)
        self.assertEqual(BASE.model["sscm"][3][1], 2)
        self.assertEqual(BASE.model["rac_matrix"]["D"][1], "Serious")
        self.assertEqual(BASE.model["rac_matrix"]["E"][4], "Low")


class Rules(unittest.TestCase):
    def test_r01_wrong_level(self):
        r = fresh()
        r.objects["hazard"]["HAZ-PIL-001"]["initial_risk"]["risk_level"] = "Serious"
        self.assertTrue(errors(r, "R01"))

    def test_r01_target_above_initial(self):
        r = fresh()
        h = r.objects["hazard"]["HAZ-DCK-002"]
        h["target_risk"].update(severity=2, probability="A", rac="2A", risk_level="High")
        self.assertTrue(any("higher than initial" in f.message for f in errors(r, "R01")))

    def test_r02_f_without_elimination(self):
        r = fresh()
        h = r.objects["hazard"]["HAZ-PIL-001"]
        h["target_risk"].update(probability="F", rac="1F", risk_level="Eliminated")
        self.assertTrue(errors(r, "R02"))
        h["mitigations"].append({"id": "M9", "description": "x", "precedence": "a", "state": "selected",
                                 "verification": {"method": ["analysis"]}})
        self.assertFalse(errors(r, "R02"))

    def test_r03_procedures_only_for_catastrophic(self):
        r = fresh()
        h = r.objects["hazard"]["HAZ-PWR-001"]
        for m in h["mitigations"]:
            m["state"] = "selected" if m["precedence"] == "e" else "rejected"
            m.setdefault("rejection_rationale", "test")
        h["status"] = "in-mitigation"
        self.assertTrue(any("only on signage" in f.message for f in errors(r, "R03")))

    def test_r04_verified_without_evidence(self):
        r = fresh()
        h = r.objects["hazard"]["HAZ-PWR-001"]
        h["mitigations"][1]["state"] = "implemented"
        h["status"] = "verified"
        self.assertTrue(any("no verification evidence" in f.message for f in errors(r, "R04")))

    def test_r05_authority_and_concurrence(self):
        r = fresh()
        h = r.objects["hazard"]["HAZ-PWR-001"]   # no SSFs, so Table VI does not interfere
        h["acceptances"] = [accept("ACC-1", "Serious", "ROLE-SL", concur=False)]
        msgs = [f.message for f in errors(r, "R05")]
        self.assertTrue(any("requires ROLE-PL" in m for m in msgs))
        self.assertTrue(any("user representative" in m for m in msgs))
        h["acceptances"] = [accept("ACC-1", "Medium", "ROLE-CE", concur=False)]
        self.assertFalse(errors(r, "R05"))

    def test_r05_table_vi_covers_acceptance(self):
        r = fresh()
        h = r.objects["hazard"]["HAZ-INT-001"]  # SSF-006 SwCI 1, LOR incomplete -> High
        h["acceptances"] = [accept("ACC-1", "Medium", "ROLE-CE", concur=False)]
        self.assertTrue(any("Table VI" in f.message for f in errors(r, "R05")))

    def test_r06_exposure_requires_acceptance(self):
        r = fresh()
        r.objects["event"]["EVT-BENCH-001"]["status"] = "authorized"
        self.assertTrue(errors(r, "R06"))
        r.objects["event"]["EVT-SIM-001"]["status"] = "authorized"
        self.assertFalse(any(f.obj == "EVT-SIM-001" for f in errors(r, "R06")))

    def test_r07_swci_mismatch_and_lor_decision(self):
        r = fresh()
        r.objects["ssf"]["SSF-003"]["swci"] = 4
        self.assertTrue(any("Table V gives SwCI 2" in f.message for f in errors(r, "R07")))
        r = fresh()
        h = r.objects["hazard"]["HAZ-DCK-001"]
        h["status"] = "verified"
        self.assertTrue(any("PM decision" in f.message for f in errors(r, "R07")))

    def test_r07_software_cause_needs_ssf(self):
        r = fresh()
        r.objects["hazard"]["HAZ-PIL-001"]["causal_factors"][0]["ssf_ids"] = []
        self.assertTrue(any("not linked to an SSF" in f.message for f in errors(r, "R07")))

    def test_r08_missing_definitions(self):
        r = fresh()
        del r.objects["hazard"]["HAZ-PIL-001"]["target_risk"]["definitions"]
        self.assertTrue(errors(r, "R08"))

    def test_r09_empty_element(self):
        r = fresh()
        r.objects["hazard"]["HAZ-PIL-001"]["modes"] = []
        self.assertTrue(any("106.2f" in f.message for f in errors(r, "R09")))

    def test_r10_change_reopens_hazard(self):
        r = fresh()
        r.objects["change"]["CR-001"] = {"schema": "susanoo/change-request/v0.1", "id": "CR-001", "title": "t",
                                         "kind": "ecp", "status": "approved", "affects": ["SYS-001"]}
        r.paths[("change", "CR-001")] = "changes/CR-001.yaml"
        self.assertTrue(any("HAZ-PIL-001" in f.message for f in errors(r, "R10")))
        r.objects["hazard"]["HAZ-PIL-001"]["reassessments"] = [
            {"change_request": "CR-001", "date": "2026-11-11", "outcome": "no-change"}]
        self.assertFalse(errors(r, "R10"))

    def test_r11_record_for_unselected_task(self):
        r = fresh()
        r.objects["task"][103] = dict(r.objects["task"][102], task_id=103)
        r.paths[("task", 103)] = "safety/mil-std-882e/tasks/T103.yaml"
        self.assertTrue(any("not-selected" in f.message for f in errors(r, "R11")))

    def test_r12_simulated_outside_demo_profile(self):
        r = fresh()
        r.objects["hazard"]["HAZ-PWR-001"]["acceptances"] = [accept("ACC-1", "Medium", "ROLE-CE")]
        r.product["release"]["profile"] = "field-release"
        self.assertTrue(errors(r, "R12"))


def review(rid, scope, reviewers, outcome="accepted"):
    return {"schema": "susanoo/review/v0.1", "id": rid, "title": "t", "date": "2026-11-11", "type": "risk-acceptance",
            "scope": scope, "baseline": "abc123", "reviewers": reviewers, "outcome": outcome}


def human(role, person="A. Person"):
    return {"role": role, "person": person, "human": True, "independence": "I1"}


class Architecture(unittest.TestCase):
    def test_a02_unknown_endpoint(self):
        r = fresh()
        r.item["interfaces"][0]["to"] = "SUS-M1-NOPE"
        self.assertTrue(errors(r, "A02"))

    def test_a03_hazard_subsystem_must_be_element(self):
        r = fresh()
        r.objects["hazard"]["HAZ-PIL-001"]["subsystems"].append("SUS-M1-NOPE")
        self.assertTrue(any("SUS-M1-NOPE" in f.message for f in errors(r, "A03")))

    def test_a04_element_without_interface(self):
        r = fresh()
        r.item["elements"].append({"id": "SUS-M1-LGT", "parent": "SUS-M1", "name": "Lights", "kind": "electrical",
                                   "safety_role": "none", "status": "concept"})
        self.assertTrue(any(f.obj == "SUS-M1-LGT" for f in errors(r, "A04")))

    def test_a01_candidate_needs_known_decision(self):
        r = fresh()
        r.item["elements"][8]["decision"] = "DQ-999"
        self.assertTrue(any("DQ-999" in f.message for f in errors(r, "A01")))


class HumanReviewAccepts(unittest.TestCase):
    def setup_acceptance(self, reviewers, role="ROLE-CE"):
        r = fresh()
        a = accept("ACC-1", "Medium", role, concur=False)
        a["review_id"] = "REV-2026-001"
        r.objects["hazard"]["HAZ-PWR-001"]["acceptances"] = [a]
        r.objects["review"]["REV-2026-001"] = review("REV-2026-001", ["HAZ-PWR-001"], reviewers)
        r.paths[("review", "REV-2026-001")] = "reviews/REV-2026-001.yaml"
        return r

    def test_acceptance_without_review_fails(self):
        r = fresh()
        r.objects["hazard"]["HAZ-PWR-001"]["acceptances"] = [accept("ACC-1", "Medium", "ROLE-CE", concur=False)]
        self.assertTrue(any("no review_id" in f.message for f in errors(r, "R13")))

    def test_acceptance_with_human_review_in_role_passes(self):
        self.assertFalse(errors(self.setup_acceptance([human("ROLE-CE")]), "R13"))

    def test_review_by_wrong_role_fails(self):
        self.assertTrue(errors(self.setup_acceptance([human("ROLE-SL")]), "R13"))

    def test_ai_review_never_accepts(self):
        ai = {"role": "ROLE-CE", "person": None, "human": False, "independence": "I0"}
        msgs = [f.message for f in errors(self.setup_acceptance([ai]), "R13")]
        self.assertTrue(any("never accept" in m for m in msgs))

    def test_approved_task_record_needs_review(self):
        r = fresh()
        r.objects["task"][102]["status"] = "approved"
        self.assertTrue(any(f.obj == "T102" for f in errors(r, "R13")))


class Decisions(unittest.TestCase):
    def dq(self, r, did):
        return next(d for d in r.decisions["decisions"] if d["id"] == did)

    def test_committed_register_clean(self):
        self.assertFalse(errors(fresh(), "D01"))

    def test_recommendation_first(self):
        r = fresh()
        self.dq(r, "DQ-002")["recommendation"] = "table-i"
        self.assertTrue(any("listed first" in f.message for f in errors(r, "D01")))

    def test_applied_needs_applied_in(self):
        r = fresh()
        self.dq(r, "DQ-001")["applied_in"] = []
        self.assertTrue(errors(r, "D01"))

    def test_claude_decision_never_open(self):
        r = fresh()
        d = self.dq(r, "DQ-007")
        d["status"], d["asked"] = "open", "2026-11-11"
        self.assertTrue(any("never open" in f.message for f in errors(r, "D01")))

    def test_lead_decision_not_answered_by_claude(self):
        r = fresh()
        d = self.dq(r, "DQ-002")
        d["status"] = "answered"
        d["answer"] = {"choice": "scale-100", "by": "claude", "at": "2026-11-11", "via": "chat"}
        self.assertTrue(any("cannot be answered by claude" in f.message for f in errors(r, "D01")))


if __name__ == "__main__":
    unittest.main()


class TradeStudies(unittest.TestCase):
    """T01: a trade study is AI-draftable; weights are confirmed and an alternative selected only by the lead."""

    def ts(self, r):
        return r.objects["trade"]["TS-001"]

    def test_committed_trade_study_is_clean(self):
        self.assertFalse(errors(BASE, "T01"))

    def test_weights_must_sum_to_100(self):
        r = fresh()
        self.ts(r)["criteria"][0]["weight"] += 5
        self.assertTrue(any("sum to" in f.message for f in errors(r, "T01")))

    def test_weights_confirmed_only_by_applied_lead_decision(self):
        r = fresh()
        self.ts(r)["weights_status"] = "confirmed"
        self.assertTrue(any("weights are confirmed" in f.message for f in errors(r, "T01")))

    def test_score_cannot_rest_on_planned_evidence(self):
        r = fresh()
        planned = next(e["id"] for e in self.ts(r)["evidence"] if e["status"] == "planned")
        self.ts(r)["scores"][0]["basis"] = [planned]
        self.assertTrue(any("planned evidence" in f.message for f in errors(r, "T01")))

    def test_selection_needs_lead_decision_and_human_review(self):
        r = fresh()
        t = self.ts(r)
        t["status"], t["selection"] = "selected", {"alternative": "A", "decision_id": "DQ-016"}
        self.assertTrue(any("applied lead decision" in f.message for f in errors(r, "T01")))
        self.assertTrue(any(f.obj == "TS-001" for f in errors(r, "R13")))

    def test_selection_with_lead_decision_and_human_review_passes(self):
        r = fresh()
        t = self.ts(r)
        d = next(d for d in r.decisions["decisions"] if d["id"] == "DQ-016")
        d["status"], d["answer"], d["applied_in"] = "applied", {"choice": "draft", "by": "lead", "at": "2026-11-12", "via": "chat"}, ["architecture/trades/TS-001.yaml"]
        t["status"], t["selection"], t["review_id"] = "selected", {"alternative": "A", "decision_id": "DQ-016"}, "REV-2026-009"
        r.objects["review"]["REV-2026-009"] = review("REV-2026-009", ["TS-001"], [human("ROLE-SL")])
        r.paths[("review", "REV-2026-009")] = "reviews/REV-2026-009.yaml"
        self.assertFalse(errors(r, "T01"))
        self.assertFalse([f for f in errors(r, "R13") if f.obj == "TS-001"])
