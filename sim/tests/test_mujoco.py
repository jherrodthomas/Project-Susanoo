"""Tests for the level-2 MuJoCo model and the level-1/level-2 cross-check."""
import json
import unittest

from sim.common import ROOT
from sim.plant.spec import SpecError, check
from tools.pdac.load import _read_yaml

try:
    import mujoco  # noqa: F401
    from sim.mujoco import crosscheck, l2
    from sim.mujoco.model import L2_SPEC, load_params
    HAVE = True
except ImportError:          # the MuJoCo tests run in the CI job that installs sim/mujoco/requirements.txt
    HAVE = False


@unittest.skipUnless(HAVE, "mujoco not installed")
class Model(unittest.TestCase):
    def test_l2_spec_refuses_unsourced_values(self):
        s = _read_yaml(L2_SPEC)
        s["params"]["knee_torque_max_nm"]["source"] = ""
        with self.assertRaises(SpecError):
            check(s)

    def test_mass_and_height_match_level_1(self):
        p = load_params()
        sim = l2.L2({}, p)
        self.assertAlmostEqual(sim.mass, p["mass_kg"], places=3)
        com, _ = sim.com()
        self.assertAlmostEqual(com[2], p["com_height_m"], delta=0.25)

    def test_no_fault_stands_and_is_deterministic(self):
        a, b = l2.simulate({"slope_deg": 8}), l2.simulate({"slope_deg": 8})
        self.assertEqual(a["outcome"], "safe")
        self.assertEqual(json.dumps(a["trace"], default=float), json.dumps(b["trace"], default=float))

    def test_faulty_stop_drops_and_correct_stop_holds(self):
        self.assertEqual(l2.simulate({"fault": "FLT-03"})["outcome"], "hard-drop")
        self.assertEqual(l2.simulate({"stop_request_s": 1.0})["outcome"], "safe")

    def test_monitor_hold_does_not_fake_double_support(self):
        r = l2.simulate({"fault": "FLT-02", "monitor": True})
        self.assertEqual(r["outcome"], "safe")
        self.assertNotIn("double", {f[4] for f in r["trace"]})


@unittest.skipUnless(HAVE, "mujoco not installed")
class CrossCheck(unittest.TestCase):
    def test_committed_results_reproduce(self):
        res = crosscheck.run()
        self.assertEqual(crosscheck.compare(res, json.loads(crosscheck.OUT_JSON.read_text())), [])

    def test_every_disagreement_is_explained(self):
        res = json.loads(crosscheck.OUT_JSON.read_text())
        self.assertEqual(res["unexplained"], [])

    def test_every_search_edge_case_is_cross_checked(self):
        res = json.loads(crosscheck.OUT_JSON.read_text())
        ids = {r["id"] for r in res["rows"]}
        for p in (ROOT / "sim" / "results").glob("search-*.json"):
            s = json.loads(p.read_text())
            for e in s["edge_cases"]:
                self.assertIn(f"{s['family']['id']}/{e['id']}", ids)


if __name__ == "__main__":
    unittest.main()
