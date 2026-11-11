"""Tests for the simulation track: spec checks, fault traceability, plant behaviour, search mapping, outputs current."""
import copy
import re
import unittest

from sim.common import ROOT
from sim.figures import scenes
from sim.plant import report, spec, walker
from sim.search import search
from tools.pdac.load import _read_yaml

P = spec.load()


class Spec(unittest.TestCase):
    def raw(self):
        return _read_yaml(spec.SPEC)

    def test_unsourced_value_refused(self):
        s = self.raw()
        s["params"]["mass_kg"]["source"] = ""
        with self.assertRaisesRegex(spec.SpecError, "mass_kg: missing source"):
            spec.check(s)

    def test_out_of_range_refused(self):
        s = self.raw()
        s["params"]["com_height_m"]["value"] = 9.0
        with self.assertRaisesRegex(spec.SpecError, "outside range"):
            spec.check(s)

    def test_bad_status_refused(self):
        s = self.raw()
        s["params"]["dt_s"]["status"] = "guessed"
        with self.assertRaises(spec.SpecError):
            spec.check(s)


class Faults(unittest.TestCase):
    def test_every_cause_exists(self):
        report.check_faults(_read_yaml(report.FAULTS))

    def test_unknown_causal_factor_refused(self):
        f = copy.deepcopy(_read_yaml(report.FAULTS))
        f["faults"][0]["causes"] = ["HAZ-SAF-001:CF9"]
        with self.assertRaisesRegex(report.CatalogueError, "no causal factor CF9"):
            report.check_faults(f)


class Plant(unittest.TestCase):
    def test_nominal_flat_is_safe(self):
        self.assertEqual(walker.simulate({}, P)["outcome"], "safe")

    def test_correct_stop_safe_faulty_stop_drops(self):
        self.assertEqual(walker.simulate({"stop_request_s": 1.0}, P)["outcome"], "safe")
        r = walker.simulate({"fault": "FLT-03"}, P)
        self.assertEqual(r["outcome"], "hard-drop")
        self.assertGreater(r["events"]["impact_speed"], P["safe_drop_speed_mps"])

    def test_staleness_monitor_prevents_runaway(self):
        self.assertEqual(walker.simulate({"fault": "FLT-02", "monitor": True}, P)["outcome"], "safe")
        self.assertEqual(walker.simulate({"fault": "FLT-02", "monitor": False}, P)["outcome"], "tip")

    def test_load_holding_prevents_drop_on_burst(self):
        base = {"fault": "FLT-01", "tau_leak_s": 0.05}
        self.assertEqual(walker.simulate({**base, "load_holding": "works"}, P)["outcome"], "safe")
        self.assertEqual(walker.simulate({**base, "load_holding": "fails"}, P)["outcome"], "hard-drop")

    def test_fault_variant_mismatch_refused(self):
        with self.assertRaises(ValueError):
            walker.simulate({"fault": "FLT-04"}, P)

    def test_deterministic(self):
        c = {"fault": "FLT-01", "slope_deg": 9, "tau_leak_s": 1.8}
        self.assertEqual(walker.simulate(c, P), walker.simulate(c, P))


class Search(unittest.TestCase):
    FAM = _read_yaml(search.FAMILIES)["families"][0]

    def test_first_matching_rule_wins(self):
        m = search.map_case(self.FAM, {"outcome": "tip", "stop_active": False, "nofault_outcome": "tip"})
        self.assertIsNone(m["hazard"])
        self.assertIn("outside the nominal gait capability", m["new"])
        m = search.map_case(self.FAM, {"outcome": "tip", "stop_active": False, "nofault_outcome": "safe"})
        self.assertEqual(m["hazard"], "HAZ-WLK-002")

    def test_cause_gap_is_reported(self):
        # with a fault catalogue that does not trace FLT-01 to HAZ-WLK-002, a tip mapped to HAZ-WLK-002 is a cause gap
        real = search.fault_causes
        search.fault_causes = lambda: {"FLT-01": ["HAZ-SAF-001:CF2"]}
        try:
            res = search.run_family(self.FAM, P)
        finally:
            search.fault_causes = real
        gaps = [e for e in res["edge_cases"] if e["cause_gap"]]
        self.assertTrue(gaps)
        self.assertTrue(all(e["hazard"] not in ("HAZ-SAF-001",) for e in gaps))

    def test_committed_catalogue_has_no_cause_gap(self):
        import json
        res = json.loads((ROOT / "sim/results/search-SF-01.json").read_text())
        self.assertEqual([e["id"] for e in res["edge_cases"] if e["cause_gap"]], [])

    def test_rounding(self):
        self.assertEqual(search.rounded({"a": 1.234}, {"a": 0.5}), {"a": 1.0})


class Outputs(unittest.TestCase):
    def test_all_outputs_current(self):
        for mod in (report, search, scenes):
            for rel, text in mod.outputs().items():
                self.assertEqual((ROOT / rel).read_text(encoding="utf-8"), text, f"{rel} stale")

    def test_scene_static_pose_is_end_state(self):
        for rel, svg in scenes.outputs().items():
            if not rel.endswith(".svg"):
                continue
            for m in re.finditer(r'<g transform="translate\(([^)]*)\)"><animateTransform[^>]*values="([^"]*)"', svg):
                self.assertEqual(m.group(1), m.group(2).split(";")[-1], f"{rel}: static pose is not the end state")

    def test_scenes_name_their_hazard_and_label(self):
        for sc in scenes.SCENES:
            svg = (ROOT / f"docs/wiki/images/sim-{sc['id'].lower()}.svg").read_text()
            self.assertIn(sc["hazard"], svg)
            self.assertIn("no evidence credit", svg)


if __name__ == "__main__":
    unittest.main()
