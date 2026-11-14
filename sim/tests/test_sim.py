"""Tests for the simulation track: spec checks, fault traceability, plant behaviour, search mapping, outputs current."""
import copy
import re
import unittest

from sim.common import ROOT
from sim.figures import scenes
from sim.plant import report, spec, walker
from sim.search import search
from tools.pdac.load import _read_yaml
from tools.terms.terms import decorate

P = spec.load()


class ReferenceLayout(unittest.TestCase):
    """The simulated walker is the reference layout (CL-05, DQ-014): mass, centre of mass and heights come from the
    CAD metrics (DQ-023), so a change to the layout that the simulation has not followed fails here."""

    def test_spec_matches_cl05_metrics(self):
        import json
        from sim.mujoco.model import L2_SPEC
        m = json.loads((ROOT / "cad" / "metrics.json").read_text())["concepts"]["CL-05"]
        p = spec.load()
        l2 = _read_yaml(L2_SPEC)["params"]
        self.assertAlmostEqual(p["mass_kg"], m["placeholder_mass_kg"], delta=5)
        self.assertAlmostEqual(p["com_height_m"], m["cg_m"][2], delta=0.01)
        self.assertAlmostEqual(p["crouch_height_m"], m["postures"]["kneel"]["cg_m"][2], delta=0.01)
        self.assertAlmostEqual(l2["hip_height_m"]["value"], m["hip_height_m"], delta=0.01)
        legs = sum(l2[f"{s}_mass_kg"]["value"] for s in ("thigh", "shank", "foot"))
        self.assertAlmostEqual(l2["torso_mass_kg"]["value"] + 2 * legs, p["mass_kg"], delta=1)

    def test_l2_spec_matches_cl05_links(self):
        """The level-2 masses, centres of mass and pitch inertias are the CL-05 link mass properties."""
        import json
        from sim.mujoco.model import L2_SPEC
        cad = json.loads((ROOT / "cad" / "links.json").read_text())
        links, l2 = cad["links"], _read_yaml(L2_SPEC)["params"]
        for seg in ("thigh", "shank", "foot"):
            for side in ("left", "right"):
                link = links[f"{seg}_{side}"]
                self.assertAlmostEqual(l2[f"{seg}_mass_kg"]["value"], link["mass_kg"], delta=0.1, msg=f"{seg}_{side}")
                self.assertAlmostEqual(l2[f"{seg}_pitch_inertia_kgm2"]["value"], link["inertia_kgm2"][1][1], delta=1)
                if seg != "foot":
                    self.assertAlmostEqual(l2[f"{seg}_com_fraction"]["value"], link["along_segment"], delta=0.002)
        self.assertAlmostEqual(l2["foot_com_above_sole_m"]["value"], links["foot_left"]["com_m"][2], delta=0.002)
        torso, hip = links["torso"], cad["joints_m"]["left"]["hip"][2]
        self.assertAlmostEqual(l2["torso_mass_kg"]["value"], torso["mass_kg"], delta=5)
        self.assertAlmostEqual(l2["torso_pitch_inertia_kgm2"]["value"], torso["inertia_kgm2"][1][1], delta=1)
        self.assertAlmostEqual(l2["torso_com_above_hip_m"]["value"], torso["com_m"][2] - hip, delta=0.002)
        m = json.loads((ROOT / "cad" / "metrics.json").read_text())["concepts"]["CL-05"]
        self.assertAlmostEqual(cad["total"]["mass_kg"], m["placeholder_mass_kg"], delta=5)
        self.assertEqual(cad["total"]["com_m"][2], m["cg_m"][2])

    def test_link_densities_match_build_concepts(self):
        """tools/cad/b3d/cl05_links.py weighs each part class as tools/cad/build_concepts.py does."""
        import ast

        def density_class(path):
            for node in ast.walk(ast.parse((ROOT / path).read_text())):
                if isinstance(node, ast.Assign) and any(getattr(t, "id", "") == "DENSITY_CLASS" for t in node.targets):
                    return ast.literal_eval(node.value)
        self.assertEqual(density_class("tools/cad/b3d/cl05_links.py"), density_class("tools/cad/build_concepts.py"))


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

    def test_case_starts_on_the_gait_periodic_orbit(self):
        """A8: the start state is the balance loop's own periodic orbit, so a no-fault run returns to it one sway
        period later; starting on the sway reference put the capture point at the foot edge (DQ-009)."""
        p = spec.load()
        case = {"slope_deg": 9.0, "stride_offset_m": 0.28}
        x0, v0 = walker.initial_state(dict(walker.default_case(), **case), p, p["com_height_m"])
        q = dict(p, horizon_s=p["sway_period_s"])
        tr = walker.simulate(case, q, trace_every=p["dt_s"])["trace"]
        self.assertAlmostEqual(tr[0][1], x0, delta=0.001)          # first sample is after one step
        self.assertAlmostEqual(tr[-1][1], x0, delta=0.002)
        omega = (p["gravity_mps2"] / p["com_height_m"]) ** 0.5
        self.assertLess(x0 + v0 / omega, p["foot_half_length_m"])

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
                self.assertEqual((ROOT / rel).read_text(encoding="utf-8"), decorate(rel, text), f"{rel} stale")

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
