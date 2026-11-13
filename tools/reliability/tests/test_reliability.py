"""Tests for the reliability engine and generator (tools/reliability)."""
import copy
import json
import math
import unittest
from pathlib import Path

from tools.reliability import build, engine

ROOT = Path(__file__).resolve().parents[3]


def toy_model(**over) -> engine.Model:
    modes = {
        "PT-1-FM1": {"id": "PT-1-FM1", "kind": "rate", "value": 1e-4, "error_factor": 10, "unit": "per hour", "mode": "a"},
        "PT-2-FM1": {"id": "PT-2-FM1", "kind": "demand", "value": 1e-2, "error_factor": 3, "unit": "per demand", "mode": "b"},
        "PT-2-FM2": {"id": "PT-2-FM2", "kind": "latent", "value": 1e-3, "error_factor": 3, "unit": "per hour", "mode": "c"},
    }
    m = engine.Model(modes=modes, parts=[], params={"n": {"value": 3}, "test_interval_h": {"value": 10}, "beta": {"value": 0.1}},
                     trees=[], hazard="HAZ-X", causal_factor="CF1", exposure_key="h", exposure_h=100.0,
                     bands={"A": 1e-1, "B": 1e-2, "C": 1e-3, "D": 1e-6, "E": 0.0})
    for k, v in over.items():
        setattr(m, k, v)
    return m


TREE = {"id": "FT-T", "alternative": "X", "title": "t", "top": "top",
        "gates": [{"id": "top", "type": "and", "inputs": ["init", "hold"]},
                  {"id": "hold", "type": "or", "inputs": ["d", "l", "cc"]}],
        "events": [{"id": "init", "mode": "PT-1-FM1"},
                   {"id": "d", "mode": "PT-2-FM1", "count": "n"},
                   {"id": "l", "mode": "PT-2-FM2", "count": "n"},
                   {"id": "cc", "kind": "common_cause", "modes": ["PT-2-FM1", "PT-2-FM2"], "beta": "beta"}]}


class TestEngine(unittest.TestCase):
    def test_single_mode_kinds(self):
        m = toy_model()
        self.assertAlmostEqual(engine.single(m.modes["PT-1-FM1"], 1e-4, 10, 100), 1 - math.exp(-1e-2))
        self.assertAlmostEqual(engine.single(m.modes["PT-2-FM2"], 1e-3, 10, 100), 5e-3)   # lambda * tau / 2
        self.assertAlmostEqual(engine.single(m.modes["PT-2-FM1"], 1e-2, 10, 100), 1e-2)

    def test_gate_arithmetic(self):
        m = toy_model()
        p = engine.tree_p(m, TREE, engine.nominal_values(m), 10)
        init = 1 - math.exp(-1e-2)
        d = 1 - (1 - 1e-2) ** 3
        lat = 1 - (1 - 5e-3) ** 3
        cc = 0.1 * (1e-2 + 5e-3)
        hold = 1 - (1 - d) * (1 - lat) * (1 - cc)
        self.assertAlmostEqual(p["hold"], hold)
        self.assertAlmostEqual(p["top"], init * hold)

    def test_counted_gate(self):
        m = toy_model()
        t = copy.deepcopy(TREE)
        t["gates"][0]["count"] = "n"
        p1 = engine.tree_p(m, TREE, engine.nominal_values(m), 10)["top"]
        p3 = engine.tree_p(m, t, engine.nominal_values(m), 10)["top"]
        self.assertAlmostEqual(p3, 1 - (1 - p1) ** 3)

    def test_minimal_cut_sets(self):
        m = toy_model()
        sets = {frozenset(s): mult for s, mult in engine.cut_sets(m, TREE)}
        self.assertEqual(set(sets), {frozenset({"init", "d"}), frozenset({"init", "l"}), frozenset({"init", "cc"})})
        t = copy.deepcopy(TREE)       # a superset is not minimal
        t["gates"].append({"id": "x", "type": "and", "inputs": ["init", "d"]})
        t["gates"][0] = {"id": "top", "type": "or", "inputs": ["x", "init"]}
        self.assertEqual([s for s, _ in engine.cut_sets(m, t)], [frozenset({"init"})])

    def test_bands(self):
        b = engine.parse_bands({"A": ">= 1e-1", "B": "< 1e-1 and >= 1e-2", "C": "< 1e-2 and >= 1e-3",
                                "D": "< 1e-3 and >= 1e-6", "E": "< 1e-6"})
        self.assertEqual([engine.band_of(p, b) for p in (0.5, 0.05, 5e-3, 5e-5, 5e-7)], list("ABCDE"))
        self.assertEqual(engine.band_of(1e-6, b), "D")   # the boundary belongs to the more likely band

    def test_reach_target_band(self):
        m = toy_model()
        r = engine.analyse(m, TREE, n_mc=50)
        rc = r["reach_e"]
        self.assertEqual(rc["mode"], r["drivers"][0]["mode"])
        v = engine.nominal_values(m)
        v[rc["mode"]] = rc["value"]
        tau = m.param("test_interval_h")
        self.assertLess(engine.tree_p(m, TREE, v, tau)["top"], m.bands["D"])
        v[rc["mode"]] = rc["value"] * 1.01
        self.assertGreaterEqual(engine.tree_p(m, TREE, v, tau)["top"], m.bands["D"])

    def test_monte_carlo_is_seeded(self):
        m = toy_model()
        a = engine.analyse(m, TREE, n_mc=300, seed=7)
        b = engine.analyse(m, TREE, n_mc=300, seed=7)
        self.assertEqual(a["mc"], b["mc"])
        self.assertLess(a["mc"]["p05"], a["mc"]["p50"])
        self.assertLess(a["mc"]["p50"], a["mc"]["p95"])


class TestRecords(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = engine.load(ROOT)
        cls.outs = build.outputs()

    def test_records_load(self):
        self.assertEqual(self.m.hazard, "HAZ-PIL-002")
        self.assertTrue((ROOT / f"safety/hazards/{self.m.hazard}.yaml").exists())
        self.assertEqual({t["alternative"] for t in self.m.trees}, {"A", "B-EHA", "B-EMA"})

    def test_parts_name_real_elements(self):
        import yaml
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

    def test_bad_reference_is_reported(self):
        m = toy_model()
        bad = copy.deepcopy(TREE)
        bad["events"][0]["mode"] = "PT-9-FM9"
        with self.assertRaises(KeyError):
            engine.tree_p(m, bad, engine.nominal_values(m), 10)


if __name__ == "__main__":
    unittest.main()
