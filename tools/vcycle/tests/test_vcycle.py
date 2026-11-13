"""Tests for the System V cycle generator (tools/vcycle/build_vcycle.py)."""
import json
import re
import unittest
from pathlib import Path

from tools.vcycle import build_vcycle as vc

ROOT = Path(__file__).resolve().parents[3]


def embedded(page: str, name: str):
    m = re.search(rf"const {name} = (.*?);\n", page)
    return json.loads(m.group(1))


class TestVcycle(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = vc.records()
        cls.outs = vc.outputs()

    def test_outputs_are_deterministic(self):
        self.assertEqual(self.outs, vc.outputs())

    def test_page_embeds_every_record(self):
        head = embedded(self.outs[vc.PAGE], "HEAD")
        for key, folder in (("reqs", "requirements/SYS-*.yaml"), ("haz", "safety/hazards/HAZ-*.yaml"),
                            ("ssf", "safety/software/SSF-*.yaml"), ("changes", "changes/CR-*.yaml")):
            want = sorted(p.stem for p in ROOT.glob(folder))
            self.assertEqual(sorted(x["id"] for x in head[key]), want, key)

    def test_committed_page_has_no_history(self):
        # history makes the page stale after every record commit, so it is local-only (--history)
        self.assertEqual(embedded(self.outs[vc.PAGE], "HIST"), [])

    def test_no_placeholders_left(self):
        page = self.outs[vc.PAGE]
        self.assertNotIn("__DATA__", page)
        self.assertNotIn("__HIST__", page)
        line = re.search(r"const HEAD = (.*?);\n", page).group(1)
        self.assertNotIn("</", line, "embedded data must not be able to close the script element")

    def test_gates_follow_the_tailoring(self):
        t = vc._read_yaml(ROOT / "standards/tailoring/mil-std-882e.yaml")
        self.assertEqual([g["id"] for g in self.data["gates"]], list(t["gates"]))
        self.assertEqual(self.data["current_gate"], t["current_gate"])
        self.assertTrue(all(g["exit"] for g in self.data["gates"]), "every gate has exit evidence in framework/lifecycle.md")

    def test_block_maturity_never_claims_more_than_the_records(self):
        # a block is only as mature as its least mature record; with no evidence the right side cannot be past Draft
        for b in vc.system_blocks(self.data):
            self.assertEqual(b["state"], min(b["states"]) if b["states"] else 0)
        r2 = next(b for b in vc.system_blocks(self.data) if b["k"] == "R2")
        if not any(r["evidence"] for r in self.data["reqs"]):
            self.assertEqual(r2["state"], 0)

    def test_examples_are_labelled_as_examples(self):
        src = (vc.HERE / "page.html").read_text(encoding="utf-8")
        self.assertIn("example, not a record", src)
        self.assertRegex(src, r'id:"CR-EX-\d"')

    def test_ripple_mirrors_rule_r10_links(self):
        # page.html impactedHazards must use the same link set as tools/pdac/rules.py impacted_hazards
        src = (vc.HERE / "page.html").read_text(encoding="utf-8")
        self.assertIn("[h.id,...h.reqids,...h.ssf,...h.cfg]", src)
        self.assertIn('L.add(h.id+":"+m.id);m.reqs.forEach(r=>L.add(r))', src)


if __name__ == "__main__":
    unittest.main()
