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

    def test_starts_in_the_level_1_state(self):
        """Both levels start in the same state (walker.initial_state, DQ-009), with the stance foot at rest."""
        import numpy as np
        from sim.plant.walker import initial_state
        for case in ({"slope_deg": 9.0, "stride_offset_m": 0.28}, {"slope_deg": 13.0, "stride_offset_m": 0.27}):
            sim = l2.L2(case)
            com, vel = sim.com()
            x, z = sim._hv(com - sim.sole_pos("s"))
            x0, v0 = initial_state(sim.case, sim.p, z)
            self.assertAlmostEqual(x, x0, delta=1e-3)
            self.assertAlmostEqual(sim._hv(vel)[0], v0, delta=1e-3)
            self.assertAlmostEqual(sim._hv(vel)[1], 0.0, delta=1e-3)
            jp, jr = np.zeros((3, sim.m.nv)), np.zeros((3, sim.m.nv))
            mujoco.mj_jacBody(sim.m, sim.d, jp, jr, sim.foot_body["s"])
            self.assertLess(float(np.abs(jp @ sim.d.qvel).max() + np.abs(jr @ sim.d.qvel).max()), 1e-9)

    def test_protective_stop_on_a_slope_steps_downhill_and_holds(self):
        """The stop steps towards the horizontal capture point; along the slope a vertical torso reads as uphill of the
        foot, and stepping that way tipped every stop from 8 degrees up."""
        for slope in (8, 16, 20):
            self.assertEqual(l2.simulate({"slope_deg": slope, "stride_offset_m": 0.12, "stop_request_s": 1.0})["outcome"],
                             "safe", slope)

    def test_sizing_proposal_clears_the_envelope_and_matches_sys_016(self):
        from sim.mujoco import sizing
        res = json.loads(sizing.OUT_JSON.read_text())
        pr = res["proposal"]
        self.assertEqual(pr["failures"], 0)
        self.assertAlmostEqual(pr["ankle_ratio"], 1.5, places=2)
        req = _read_yaml(ROOT / "requirements" / "SYS-016.yaml")["statement"]
        self.assertIn("1.5 m g L_foot", req)
        self.assertIn(f"{pr['knee_torque_max_nm'] / 1000:g} kN m", req)

    def test_locked_walker_holds_still_and_ignores_rounding(self):
        """Load holding is a solver constraint: once locked the walker stays put, so the outcome cannot hang on
        rounding (explicit lock springs at omega*dt ~ 1.9 made it rock and tip depending on the CPU)."""
        case = {"fault": "FLT-02", "monitor": True}
        ends = []
        for eps in (0.0, 1e-7, -1e-7):
            sim = l2.L2(case)
            sim.d.qvel[sim.dof["root_x"]] += eps
            r = sim.run()
            self.assertEqual(r["outcome"], "safe")
            after = [row[1] for row in r["trace"] if row[6]]
            self.assertLess(max(after) - min(after), 0.02)
            ends.append(after[-1])
        self.assertLess(max(ends) - min(ends), 1e-3)

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
