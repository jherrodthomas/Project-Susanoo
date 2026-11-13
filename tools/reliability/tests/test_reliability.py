"""Tests for the reliability engine and generator (tools/reliability)."""
import copy
import json
import math
import shutil
import tempfile
import unittest
from pathlib import Path

import yaml

from tools.reliability import build, engine

ROOT = Path(__file__).resolve().parents[3]


def toy_model() -> engine.Model:
    modes = {
        "PT-1-FM1": {"id": "PT-1-FM1", "kind": "rate", "value": 1e-4, "error_factor": 10, "unit": "per hour", "mode": "a"},
        "PT-2-FM1": {"id": "PT-2-FM1", "kind": "demand", "value": 1e-2, "error_factor": 3, "unit": "per demand", "mode": "b"},
        "PT-2-FM2": {"id": "PT-2-FM2", "kind": "latent", "value": 1e-3, "error_factor": 3, "unit": "per hour", "mode": "c"},
        "PT-3-FM1": {"id": "PT-3-FM1", "kind": "cycle", "value": 1e-3, "error_factor": 3, "unit": "per cycle", "mode": "d"},
    }
    return engine.Model(modes=modes, parts=[], params={"n": {"value": 3}, "test_interval_h": {"value": 10}, "beta": {"value": 0.1}},
                        trees=[], hazards={"HAZ-X": {}}, files={}, item_life={"h_hours": 100.0, "c_cycles": 50.0},
                        bands={"A": 1e-1, "B": 1e-2, "C": 1e-3, "D": 1e-6, "E": 0.0})


TREE = {"id": "FT-T", "hazard": "HAZ-X", "exposure": "h_hours", "title": "t", "top": "top",
        "gates": [{"id": "top", "type": "and", "inputs": ["init", "hold"]},
                  {"id": "hold", "type": "or", "inputs": ["d", "l", "cc"]}],
        "events": [{"id": "init", "mode": "PT-1-FM1"},
                   {"id": "d", "mode": "PT-2-FM1", "count": "n"},
                   {"id": "l", "mode": "PT-2-FM2", "count": "n"},
                   {"id": "cc", "kind": "common_cause", "modes": ["PT-2-FM1", "PT-2-FM2"], "beta": "beta"}]}

MIXED = {"id": "FT-M", "hazard": "HAZ-X", "exposure": "h_hours", "title": "m", "top": "top",
         "gates": [{"id": "top", "type": "or", "inputs": ["sw-path", "person"]},
                   {"id": "sw-path", "type": "and", "inputs": ["sw", "guard"]}],
         "events": [{"id": "sw", "kind": "undeveloped", "nature": "software", "causal_factor": "CF1"},
                    {"id": "guard", "mode": "PT-2-FM2"},
                    {"id": "person", "kind": "undeveloped", "nature": "human", "causal_factor": "CF2"}]}


class TestEngine(unittest.TestCase):
    def test_single_mode_kinds(self):
        m = toy_model()
        self.assertAlmostEqual(engine.single(m.modes["PT-1-FM1"], 1e-4, 10, 100), 1 - math.exp(-1e-2))
        self.assertAlmostEqual(engine.single(m.modes["PT-2-FM2"], 1e-3, 10, 100), 5e-3)   # lambda * tau / 2
        self.assertAlmostEqual(engine.single(m.modes["PT-2-FM1"], 1e-2, 10, 100), 1e-2)
        self.assertAlmostEqual(engine.single(m.modes["PT-3-FM1"], 1e-3, 10, 50), 1 - (1 - 1e-3) ** 50)

    def test_gate_arithmetic(self):
        m = toy_model()
        p = engine.tree_p(m, TREE, engine.nominal_values(m), 10)
        init = 1 - math.exp(-1e-2)
        d = 1 - (1 - 1e-2) ** 3
        lat = 1 - (1 - 5e-3) ** 3
        cc = 0.1 * (1e-2 + 5e-3)
        self.assertAlmostEqual(p["top"], init * (1 - (1 - d) * (1 - lat) * (1 - cc)))

    def test_counted_gate(self):
        m = toy_model()
        t = copy.deepcopy(TREE)
        t["gates"][0]["count"] = "n"
        p1 = engine.tree_p(m, TREE, engine.nominal_values(m), 10)["top"]
        self.assertAlmostEqual(engine.tree_p(m, t, engine.nominal_values(m), 10)["top"], 1 - (1 - p1) ** 3)

    def test_minimal_cut_sets(self):
        m = toy_model()
        sets = {frozenset(s) for s, _ in engine.cut_sets(m, TREE)}
        self.assertEqual(sets, {frozenset({"init", "d"}), frozenset({"init", "l"}), frozenset({"init", "cc"})})
        t = copy.deepcopy(TREE)       # a superset is not minimal
        t["gates"].append({"id": "x", "type": "and", "inputs": ["init", "d"]})
        t["gates"][0] = {"id": "top", "type": "or", "inputs": ["x", "init"]}
        self.assertEqual([s for s, _ in engine.cut_sets(m, t)], [frozenset({"init"})])

    def test_undeveloped_events_are_never_quantified(self):
        m = toy_model()
        r = engine.analyse(m, MIXED, n_mc=50)
        self.assertEqual(r["top"], 0.0)
        self.assertFalse(r["quantified"])
        self.assertIsNone(r["band"])
        kinds = {tuple(c["events"]): c for c in r["cut_sets"]}
        self.assertEqual(kinds[("person",)]["kind"], "unquantified")
        self.assertEqual(r["single_points"], ["person"])
        mixed = kinds[("guard", "sw")]
        self.assertEqual(mixed["kind"], "mixed")
        self.assertAlmostEqual(mixed["defence_p"], 5e-3)    # the hardware defence behind the software cause

    def test_bands(self):
        b = engine.parse_bands({"A": ">= 1e-1", "B": "< 1e-1 and >= 1e-2", "C": "< 1e-2 and >= 1e-3",
                                "D": "< 1e-3 and >= 1e-6", "E": "< 1e-6"})
        self.assertEqual([engine.band_of(p, b) for p in (0.5, 0.05, 5e-3, 5e-5, 5e-7)], list("ABCDE"))
        self.assertEqual(engine.band_of(1e-6, b), "D")   # the boundary belongs to the more likely band

    def test_reach_target_band(self):
        m = toy_model()
        r = engine.analyse(m, TREE, n_mc=50)
        rc = r["reach_e"]
        v = engine.nominal_values(m)
        v[rc["mode"]] = rc["value"]
        self.assertLess(engine.tree_p(m, TREE, v, 10)["top"], m.bands["D"])
        v[rc["mode"]] = rc["value"] * 1.01
        self.assertGreaterEqual(engine.tree_p(m, TREE, v, 10)["top"], m.bands["D"])

    def test_monte_carlo_is_seeded(self):
        m = toy_model()
        a = engine.analyse(m, TREE, n_mc=300, seed=7)
        self.assertEqual(a["mc"], engine.analyse(m, TREE, n_mc=300, seed=7)["mc"])
        self.assertLess(a["mc"]["p05"], a["mc"]["p50"])
        self.assertLess(a["mc"]["p50"], a["mc"]["p95"])


class TestRecords(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = engine.load(ROOT)
        cls.outs = build.outputs()

    def test_every_hazard_has_a_tree(self):
        hazards = {p.stem for p in (ROOT / "safety/hazards").glob("HAZ-*.yaml")}
        self.assertEqual(hazards, {t["hazard"] for t in self.m.trees})

    def test_pil_002_alternatives(self):
        self.assertEqual({t.get("alternative") for t in self.m.trees if t["hazard"] == "HAZ-PIL-002"}, {"A", "B-EHA", "B-EMA"})

    def test_parts_name_real_elements(self):
        idf = yaml.safe_load((ROOT / "architecture/item-definition.yaml").read_text())
        ids = {e["id"] for e in idf["elements"]}
        for part in self.m.parts:
            self.assertIn(part["element"], ids, part["id"])

    def test_assumed_inputs_make_the_results_illustrative(self):
        data = json.loads(self.outs[build.JSON_OUT])
        self.assertEqual(data["illustrative"], bool(self.m.assumed))
        if self.m.assumed:
            self.assertIn("**Illustrative.**", self.outs[build.PAGE])

    def test_outputs_are_deterministic(self):
        self.assertEqual(self.outs, build.outputs())

    def test_never_touches_a_hazard_record(self):
        self.assertFalse([k for k in self.outs if k.startswith("safety/hazards/")])

    def test_unknown_node_keys_are_errors(self):
        bad = copy.deepcopy(MIXED)
        bad["gates"][1]["the rest of a title"] = None    # what an unquoted comma in a flow mapping produces
        errors = engine._check_tree({**bad}, toy_model().modes, {}, {"h_hours": 1.0}, set(), {"CF1", "CF2"}, set())
        self.assertTrue(any("unknown keys" in e for e in errors))

    def test_uncovered_causal_factor_is_an_error(self):
        tmp = Path(tempfile.mkdtemp())
        try:
            for d in ("reliability", "safety/hazards", "safety/software", "standards/tailoring"):
                shutil.copytree(ROOT / d, tmp / d)
            f = tmp / "reliability/HAZ-PIL-002.yaml"
            doc = yaml.safe_load(f.read_text())
            doc.pop("not_modelled")
            f.write_text(yaml.safe_dump(doc))
            with self.assertRaisesRegex(engine.ModelError, "CF2 of HAZ-PIL-002"):
                engine.load(tmp)
        finally:
            shutil.rmtree(tmp)


if __name__ == "__main__":
    unittest.main()
