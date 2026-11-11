"""Tests for the PX4 SITL scenario harness (pure parts) and the generated UAV outputs."""
import json
import unittest

from sim.common import ROOT
from sim.figures import uav_scenes
from sim.plant.spec import check as check_spec
from sim.uav import harness
from tools.pdac.load import _read_yaml

SPEC = check_spec(_read_yaml(harness.SPEC))
CFG = _read_yaml(harness.SCENARIOS)


def sc(**over):
    base = {"id": "T", "walker_moved": False, "inject": {"link_loss_at_s": 10}, "params": {}}
    return {**base, **over}


def raw(points, armed=False):
    # points: (t, n, e, alt, mode) -> trace rows with no estimator error
    return {"trace": [[t, n, e, a, m, 0.5] for t, n, e, a, m in points], "final_armed": armed, "texts": [], "params": {}}


class Pure(unittest.TestCase):
    def test_mode_decoding(self):
        self.assertEqual(harness.mode_name((4 << 16) | (5 << 24)), "AUTO.RTL")
        self.assertEqual(harness.mode_name((4 << 16) | (6 << 24)), "AUTO.LAND")
        self.assertEqual(harness.mode_name(3 << 16), "POSCTL")

    def test_latlon_round_trip(self):
        lat, lon = harness.offset_latlon(47.4, 8.5, 40.0, 30.0)
        n, e = harness.latlon_offset(47.4, 8.5, lat, lon)
        self.assertAlmostEqual(n, 40.0, places=3)
        self.assertAlmostEqual(e, 30.0, places=3)

    def test_keepout_breach(self):
        r = harness.score(sc(), SPEC, raw([(0, 40, 30, 25, "AUTO.LOITER"), (12, 40, 30, 25, "AUTO.RTL"), (60, 0.5, 0, 3, "AUTO.RTL"),
                                          (70, 0.2, 0, 0, "AUTO.RTL")]))
        self.assertEqual(r["outcome"], "keepout-breach")
        self.assertEqual(r["first_failsafe"], [12, "AUTO.RTL"])

    def test_stale_home(self):
        r = harness.score(sc(walker_moved=True), SPEC, raw([(0, 40, 30, 25, "AUTO.LOITER"), (12, 40, 30, 25, "AUTO.RTL"),
                                                           (70, 0.1, 0, 0, "AUTO.RTL")]))
        self.assertEqual(r["outcome"], "landed-at-stale-home")
        self.assertAlmostEqual(r["landing_to_dock_m"], SPEC["walker_moved_n_m"] - 0.1, places=1)

    def test_clear_landing(self):
        r = harness.score(sc(), SPEC, raw([(0, 40, 30, 25, "AUTO.LOITER"), (12, 40, 30, 25, "AUTO.LAND"), (40, 40, 30, 0, "AUTO.LAND")]))
        self.assertEqual(r["outcome"], "landed-clear")


class Outputs(unittest.TestCase):
    def test_every_scenario_has_a_result_with_its_hazards(self):
        for s in CFG["scenarios"]:
            r = json.loads((ROOT / f"sim/results/uav/{s['id']}.json").read_text())
            self.assertEqual(r["scenario"]["hazards"], s["hazards"])
            self.assertEqual(r["px4"], harness.PX4_TAG)
            self.assertIn("no evidence credit", r["about"])

    def test_every_outcome_has_a_rule(self):
        outcomes = {"keepout-breach", "landed-at-stale-home", "geofence-overshoot", "landed-clear", "contained", "airborne-at-horizon"}
        self.assertEqual({r["outcome"] for r in CFG["outcome_rules"]}, outcomes)

    def test_rule_hazards_exist(self):
        for r in CFG["outcome_rules"] + CFG["metric_rules"]:
            if r.get("hazard"):
                self.assertTrue((ROOT / f"safety/hazards/{r['hazard']}.yaml").exists(), r["hazard"])
        for s in CFG["scenarios"]:
            for h in s["hazards"]:
                self.assertTrue((ROOT / f"safety/hazards/{h}.yaml").exists(), h)

    def test_generated_outputs_current(self):
        for rel, text in uav_scenes.outputs().items():
            self.assertEqual((ROOT / rel).read_text(encoding="utf-8"), text, f"{rel} stale")


if __name__ == "__main__":
    unittest.main()
