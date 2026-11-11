"""Tests for the generated item-definition figures."""
import copy
import re
import unittest

from tools.figures import fig_item as f
from tools.figures.figkit import FigureError, wrap
from tools.pdac.load import _read_yaml

ITEM = _read_yaml(f.ROOT / f.ITEM)
LAYOUT = _read_yaml(f.ROOT / f.LAYOUT)


def texts(svg: str) -> str:
    return " ".join(re.findall(r">([^<]*)</text>", svg))


class Current(unittest.TestCase):
    def test_committed_figures_are_current(self):
        for rel, text in f.build().items():
            self.assertEqual((f.ROOT / rel).read_text(encoding="utf-8"), text, f"{rel} stale; run fig_item")

    def test_every_element_external_and_interface_drawn(self):
        svg = texts(f.build_view("boundary", ITEM, LAYOUT, "x"))
        for kind in ("elements", "externals", "interfaces"):
            for rec in ITEM[kind]:
                self.assertIn(rec["id"], svg, f"{rec['id']} missing from the boundary figure")

    def test_context_hides_interfaces_inside_one_top_level_element(self):
        svg = texts(f.build_view("context", ITEM, LAYOUT, "x"))
        self.assertNotIn("IF-017", svg)   # PIL -> CTL, both inside SUS-M1
        self.assertIn("IF-006", svg)      # SUS-M1 dock <-> SUS-A1

    def test_description_lists_connectors(self):
        svg = f.build_view("boundary", ITEM, LAYOUT, "x")
        desc = re.search(r"<desc>(.*)</desc>", svg).group(1)
        self.assertIn("IF-PX4-005", desc)


class LayoutErrors(unittest.TestCase):
    def build(self, mutate):
        lay = copy.deepcopy(LAYOUT)
        mutate(lay)
        return f.build_view("boundary", ITEM, lay, "x")

    def test_missing_box(self):
        with self.assertRaisesRegex(FigureError, "no box for"):
            self.build(lambda l: l["boundary"]["boxes"].pop("SUS-M1-MAN"))

    def test_unknown_box(self):
        with self.assertRaisesRegex(FigureError, "unknown id"):
            self.build(lambda l: l["boundary"]["boxes"].update({"SUS-M1-XXX": [10, 900, 20, 20]}))

    def test_child_outside_parent(self):
        with self.assertRaisesRegex(FigureError, "not inside its parent"):
            self.build(lambda l: l["boundary"]["boxes"].update({"SUS-A1-FC": [700, 820, 100, 40]}))

    def test_external_inside_boundary(self):
        with self.assertRaisesRegex(FigureError, "overlaps the system boundary"):
            self.build(lambda l: l["boundary"]["boxes"].update({"EXT-WEATHER": [1200, 800, 100, 40]}))

    def test_crossing_connector(self):
        with self.assertRaisesRegex(FigureError, "crosses"):
            self.build(lambda l: l["boundary"]["routes"].pop("SUS-A1-FC|SUS-A1-PROP"))

    def test_route_for_unknown_connector(self):
        with self.assertRaisesRegex(FigureError, "unknown connector"):
            self.build(lambda l: l["boundary"]["routes"].update({"EXT-PILOT|SUS-A1": {"via": []}}))


class Kit(unittest.TestCase):
    def test_wrap_cuts_with_ellipsis(self):
        lines = wrap("one two three four five six seven eight nine ten", 60, 11, 2)
        self.assertEqual(len(lines), 2)
        self.assertTrue(lines[-1].endswith("…"))


if __name__ == "__main__":
    unittest.main()
