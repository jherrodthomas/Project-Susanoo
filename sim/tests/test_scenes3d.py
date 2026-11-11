"""Tests for the 3D scenes: coverage of hazards, the look never changes the analysis, pages current and pinned."""
import copy
import json
import re
import unittest

from sim.common import ROOT
from sim.scenes3d import build_pages, export_scene

CFG = export_scene.load()


class GuardedScene(dict):
    """A scene that fails if anything reads its look or variants."""
    def __getitem__(self, k):
        if k in ("look", "variants"):
            raise AssertionError(f"exporter read look key {k!r}")
        return super().__getitem__(k)

    def get(self, k, default=None):
        if k in ("look", "variants"):
            raise AssertionError(f"exporter read look key {k!r}")
        return super().get(k, default)


class Coverage(unittest.TestCase):
    def test_every_hazard_has_a_scene_or_a_reason(self):
        hazards = {p.stem for p in (ROOT / "safety/hazards").glob("HAZ-*.yaml")}
        scened = {h for s in CFG["scenes"] for h in s["hazards"] if h.startswith("HAZ-")}
        reasons = {x["hazard"] for x in CFG["not_modelled"]}
        self.assertEqual(hazards - scened - reasons, set(), "hazards with neither a scene nor a not_modelled reason")
        self.assertEqual(scened & reasons, set(), "a hazard with a scene is also listed as not modelled")

    def test_scene_hazards_and_findings_exist(self):
        findings = {f["id"] for p in (ROOT / "sim/results").glob("search-*.json") for f in json.loads(p.read_text())["findings"]}
        for s in CFG["scenes"]:
            for h in s["hazards"]:
                ok = (ROOT / f"safety/hazards/{h}.yaml").exists() if h.startswith("HAZ-") else h in findings
                self.assertTrue(ok, f"{s['id']}: {h} not found")


class LookNeverChangesAnalysis(unittest.TestCase):
    def test_exporter_never_reads_the_look(self):
        for s in CFG["scenes"]:
            export_scene.export(GuardedScene(s))

    def test_changing_or_removing_the_look_leaves_the_export_identical(self):
        for s in CFG["scenes"]:
            base = export_scene.export(s)
            other = copy.deepcopy(s)
            other["look"] = {"environment": "yard", "condition": "fog", "camera": "nowhere"}
            other["variants"] = [{"id": "X", "look": {"condition": "dusk"}}]
            self.assertEqual(export_scene.export(other), base, s["id"])
            stripped = {k: v for k, v in s.items() if k not in ("look", "variants")}
            self.assertEqual(export_scene.export(stripped), base, s["id"])

    def test_variant_pages_embed_their_base_analysis(self):
        for s in CFG["scenes"]:
            base = self._analysis(s["id"])
            for v in s.get("variants") or []:
                self.assertEqual(self._analysis(v["id"]), base, v["id"])

    @staticmethod
    def _analysis(sid):
        text = (ROOT / f"docs/3d/{sid}.html").read_text()
        return json.loads(re.search(r"window\.SCENE = (.*);</script>", text).group(1))["analysis"]


class Outputs(unittest.TestCase):
    def test_exports_and_pages_current(self):
        for mod in (export_scene, build_pages):
            for rel, text in mod.outputs().items():
                self.assertEqual((ROOT / rel).read_text(encoding="utf-8"), text, f"{rel} stale")

    def test_three_is_pinned_in_every_page(self):
        v = CFG["three"]["version"]
        for p in (ROOT / "docs/3d").glob("S3-*.html"):
            urls = set(re.findall(r"https://cdn\.jsdelivr\.net/npm/three@([^/]+)/", p.read_text()))
            self.assertEqual(urls, {v}, p.name)

    def test_every_look_resolves(self):
        for e in build_pages.entries(CFG):
            self.assertIn("sun", e["look"]["condition"])

    def test_pages_carry_the_synthetic_stamp(self):
        for p in (ROOT / "docs/3d").glob("S3-*.html"):
            self.assertIn("no evidence credit", p.read_text())


if __name__ == "__main__":
    unittest.main()
