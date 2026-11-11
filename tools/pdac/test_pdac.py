# SPDX-License-Identifier: Apache-2.0
"""Tests of the PDaC checks: the real records pass, and each check fires on a record broken on purpose."""
from __future__ import annotations

import copy
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import generate  # noqa: E402
import pdaclib  # noqa: E402

SCHEMA = pdaclib.load_schema()
MODEL = pdaclib.load()


def fresh() -> pdaclib.Model:
    return copy.deepcopy(MODEL)


def item(model: pdaclib.Model, iid: str) -> dict:
    return next(it for _, it in model.items if it.get("id") == iid)


def checks_of(findings) -> set[str]:
    return {f.check for f in findings}


class RealRecords(unittest.TestCase):
    def test_records_pass_every_check(self):
        findings = pdaclib.validate(MODEL, SCHEMA)
        self.assertEqual([], [str(f) for f in findings])

    def test_generated_views_are_current(self):
        for rel, text in generate.render(MODEL).items():
            self.assertEqual((MODEL.root / rel).read_text(encoding="utf-8"), text, f"{rel} is stale")


class RiskMatrix(unittest.TestCase):
    def test_matrix_corners(self):
        self.assertEqual("high", pdaclib.risk_level("catastrophic", "frequent"))
        self.assertEqual("low", pdaclib.risk_level("negligible", "improbable"))
        self.assertEqual("serious", pdaclib.risk_level("catastrophic", "remote"))
        self.assertEqual("medium", pdaclib.risk_level("catastrophic", "improbable"))
        self.assertEqual("eliminated", pdaclib.risk_level("catastrophic", "eliminated"))


class BrokenRecords(unittest.TestCase):
    def assertFires(self, check: str, model: pdaclib.Model, fn=None):
        findings = fn(model) if fn else pdaclib.validate(model, SCHEMA)
        self.assertIn(check, checks_of(findings), [str(f) for f in findings])

    def test_p1_unknown_field(self):
        m = fresh()
        item(m, "HAZ-001")["asil"] = "D"
        self.assertFires("P1", m)

    def test_p1_882e_rating_on_failure_condition_is_rejected(self):
        m = fresh()
        m.items.append(("pdac/items/x.yaml", {
            "id": "FC-001", "kind": "failure-condition", "title": "Loss of flight control", "status": "proposed",
            "applicability": ["SUS-A1"], "source": "SUS-CONOPS-001", "function": "fly", "phase": "cruise",
            "effect": "fly-away", "classification": "hazardous",
            "risk": {"initial": {"severity": "critical", "probability": "remote", "level": "medium"}}}))
        self.assertFires("P1", m, lambda mm: pdaclib.check_schema(mm, SCHEMA))

    def test_p1_unknown_kind(self):
        m = fresh()
        m.items.append(("pdac/items/x.yaml", {"id": "X-1", "kind": "widget"}))
        self.assertFires("P1", m, lambda mm: pdaclib.check_schema(mm, SCHEMA))

    def test_p2_duplicate_id(self):
        m = fresh()
        m.items.append(("pdac/items/x.yaml", copy.deepcopy(item(m, "SYS-001"))))
        self.assertFires("P2", m, pdaclib.check_unique)

    def test_p3_unresolved_reference(self):
        m = fresh()
        item(m, "HAZ-001")["scenarios"].append("SCN-999")
        self.assertFires("P3", m, pdaclib.check_references)

    def test_p3_wrong_kind(self):
        m = fresh()
        item(m, "SYS-001")["allocated_to"] = ["ACT-PILOT"]
        self.assertFires("P3", m, pdaclib.check_references)

    def test_p3_layout_option_must_be_an_alternative(self):
        m = fresh()
        item(m, "CL-01")["options"]["TS-003"] = "wheeled"
        self.assertFires("P3", m, pdaclib.check_references)

    def test_p4_one_sided_mitigation(self):
        m = fresh()
        item(m, "HAZ-019")["mitigated_by"].append("SYS-001")
        self.assertFires("P4", m, pdaclib.check_bidirectional)

    def test_p5_level_disagrees_with_matrix(self):
        m = fresh()
        item(m, "HAZ-001")["risk"]["initial"]["level"] = "medium"
        self.assertFires("P5", m, pdaclib.check_risk)

    def test_p5_failure_condition_must_apply_to_uav(self):
        m = fresh()
        m.items.append(("pdac/items/x.yaml", {"id": "FC-001", "kind": "failure-condition", "applicability": ["SUS-M1"]}))
        self.assertFires("P5", m, pdaclib.check_risk)

    def test_p6_closed_hazard_needs_human_acceptance(self):
        m = fresh()
        item(m, "HAZ-019")["status"] = "closed"
        self.assertFires("P6", m, pdaclib.check_acceptance)

    def test_p6_closed_hazard_with_recorded_acceptance_passes(self):
        m = fresh()
        hz = item(m, "HAZ-019")
        hz.update(status="closed", acceptance_ref="APR-001")
        hz["risk"].update(rating_status="reviewed", residual={"severity": "marginal", "probability": "remote", "level": "medium"})
        m.items.append(("pdac/items/approvals.yaml", {
            "id": "APR-001", "kind": "approval", "title": "t", "status": "recorded", "applicability": ["SUS-M1"],
            "authority": "test", "authority_type": "simulated", "decision": "accept-risk", "date": "2026-11-11",
            "objects": ["HAZ-019"]}))
        self.assertEqual([], [str(f) for f in pdaclib.check_acceptance(m)])

    def test_p6_baselined_requirement_needs_approval(self):
        m = fresh()
        item(m, "SYS-001")["status"] = "baselined"
        self.assertFires("P6", m, pdaclib.check_acceptance)

    def test_p6_release_needs_real_approval(self):
        m = fresh()
        m.product["release"]["status"] = "released"
        self.assertFires("P6", m, pdaclib.check_acceptance)

    def test_p7_allocation_without_shared_variant(self):
        m = fresh()
        item(m, "SYS-003")["allocated_to"] = ["SUS-M1-WLK"]
        item(m, "SYS-003")["applicability"] = ["SUS-A1"]
        self.assertFires("P7", m, pdaclib.check_applicability)

    def test_p9_scenario_without_hazard(self):
        m = fresh()
        for hz in m.of_kind("hazard"):
            if "SCN-107" in hz["scenarios"]:
                hz["scenarios"].remove("SCN-107")
        self.assertFires("P9", m, pdaclib.check_coverage)

    def test_p9_serious_hazard_without_mitigation(self):
        m = fresh()
        item(m, "HAZ-014")["mitigated_by"] = []
        self.assertFires("P9", m, pdaclib.check_coverage)


class Documents(unittest.TestCase):
    """P8 reads files, so it runs on a temporary copy of the repository's documents."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        for rel in ("pdac", "concept", "framework", "safety", "docs", "README.md", "CLAUDE.md",
                    "cad/params", "cad/metrics.json", "cad/README.md"):
            src = pdaclib.ROOT / rel
            (self.tmp / rel).parent.mkdir(parents=True, exist_ok=True)
            (shutil.copytree if src.is_dir() else shutil.copy)(src, self.tmp / rel)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_copy_passes(self):
        self.assertEqual([], [str(f) for f in pdaclib.check_documents(pdaclib.load(self.tmp))])

    def test_revision_mismatch(self):
        path = self.tmp / "concept/CONOPS.md"
        rev = item(pdaclib.load(self.tmp), "SUS-CONOPS-001")["revision"]
        path.write_text(path.read_text().replace(f"**Revision:** {rev}", "**Revision:** 9.9-draft"))
        self.assertIn("P8", checks_of(pdaclib.check_documents(pdaclib.load(self.tmp))))

    def test_stale_id_in_markdown(self):
        path = self.tmp / "framework/lifecycle.md"
        path.write_text(path.read_text() + "\nSee SYS-999.\n")
        self.assertIn("P8", checks_of(pdaclib.check_documents(pdaclib.load(self.tmp))))

    def test_layout_without_metrics(self):
        (self.tmp / "cad/metrics.json").write_text('{"concepts": {}}')
        self.assertIn("P8", checks_of(pdaclib.check_documents(pdaclib.load(self.tmp))))

    def test_layout_without_params(self):
        (self.tmp / "cad/params/CL-02.yaml").unlink()
        self.assertIn("P8", checks_of(pdaclib.check_documents(pdaclib.load(self.tmp))))

    def test_scenario_missing_from_conops(self):
        path = self.tmp / "concept/CONOPS.md"
        path.write_text(path.read_text().replace("SCN-107", "SCN-1O7"))
        self.assertIn("P8", checks_of(pdaclib.check_documents(pdaclib.load(self.tmp))))


if __name__ == "__main__":
    unittest.main()
