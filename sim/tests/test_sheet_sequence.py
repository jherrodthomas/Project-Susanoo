"""The launch and recovery sequence of sheet 2 (sim/scenes3d/sheet_uav.yaml) keeps the dock interlocks the hazard
mitigations name, and build_sheet.sequence() refuses one that breaks them or cites a record that does not exist."""
import copy
import unittest

from sim.common import ROOT
from sim.scenes3d.build_sheet import sequence
from tools.pdac.load import _read_yaml


def steps() -> list:
    return _read_yaml(ROOT / "sim/scenes3d/sheet_uav.yaml")["sequence"]


class SequenceTest(unittest.TestCase):
    def test_committed_sequence_passes(self):
        out, cited = sequence(steps(), {})
        self.assertEqual(len(out), len(steps()))
        self.assertIn("SYS-003", cited)

    def test_refuses_broken_interlocks_and_unknown_records(self):
        idx = {st["title"]: i for i, st in enumerate(steps())}
        cases = [
            ("rotors running while latched", "Captured: the latch closes and cuts propulsion power", {"rotors": "running"}),
            ("charging in flight", "Climb straight up to the keep-out altitude, then away", {"charging": "on"}),
            ("release without a permit", "Latch released, retention confirmed open", {"permit": "none"}),
            ("release with charging on", "Latch released, retention confirmed open", {"charging": "on"}),
            ("off the dock latched", "Arm and lift off clear of the dock", {"latch": "closed"}),
            ("unknown interface", "Docked: latched, charging, rotors inhibited", {"gates": ["IF-PX4-099 nothing"]}),
            ("unknown hazard", "Docked: latched, charging, rotors inhibited", {"gates": ["HAZ-DCK-099 nothing"]}),
        ]
        for name, title, change in cases:
            with self.subTest(name):
                bad = copy.deepcopy(steps())
                bad[idx[title]].update(change)
                with self.assertRaises(ValueError):
                    sequence(bad, {})


if __name__ == "__main__":
    unittest.main()
