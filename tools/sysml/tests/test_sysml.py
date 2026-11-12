"""Tests for the SysML reader, model checks and views."""
import copy
import tempfile
import unittest
from pathlib import Path

from tools.pdac.load import ROOT, _read_yaml
from tools.sysml import check, gen_requirements, views
from tools.sysml.model import MODEL_DIR, ModelError, load, parse_text
from tools.terms.terms import decorate

M = load()
ITEM = _read_yaml(ROOT / "architecture/item-definition.yaml")
REQS = [_read_yaml(p) for p in sorted((ROOT / "requirements").glob("SYS-*.yaml"))]
HAZ = {p.stem for p in (ROOT / "safety/hazards").glob("HAZ-*.yaml")}


def findings(item=None, reqs=None, hazards=None, model=None):
    return check.check(model or M, item or ITEM, reqs or REQS, HAZ if hazards is None else hazards)


class Reader(unittest.TestCase):
    def test_unsupported_construct_names_file_and_line(self):
        with self.assertRaisesRegex(ModelError, r"x.sysml:2: construct not supported"):
            parse_text("package P {\n  state def S;\n}", "x.sysml")

    def test_attribute_and_item_defs_with_ref_features(self):
        d = parse_text("package P {\n attribute def R { attribute s : E; }\n"
                       " item def H { attribute r : R; ref item m : M[0..*]; }\n}", "x")
        r, h = d[0].members
        self.assertEqual((r.kind, r.name, r.members[0].type), ("attribute_def", "R", "E"))
        self.assertEqual((h.kind, [m.kind for m in h.members]), ("item_def", ["attribute", "ref"]))
        self.assertEqual((h.members[1].name, h.members[1].type), ("m", "M"))

    def test_metadata_values(self):
        d = parse_text("package P { part <'A-1'> a : T { @M { k = E::v; s = \"x\"; t = (\"a\", \"b\"); } } }", "x")
        part = d[0].members[0]
        self.assertEqual(part.short, "A-1")
        self.assertEqual(part.meta["M"], {"k": "v", "s": "x", "t": ["a", "b"]})

    def test_connection_end_must_exist(self):
        files = [MODEL_DIR / f for f in ("SusanooLibrary.sysml", "Functions.sysml")]
        text = (MODEL_DIR / "Architecture.sysml").read_text().replace("connect pilot to", "connect nobody to", 1)
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "Architecture.sysml"
            bad.write_text(text)
            with self.assertRaisesRegex(ModelError, "nobody is not a part"):
                load(files + [bad])

    def test_model_counts_match_item_definition(self):
        self.assertEqual(len([e for e in M.elements.values() if e.external]), len(ITEM["externals"]))
        self.assertEqual(len(M.connections), len(ITEM["interfaces"]))
        self.assertEqual(len(M.functions), len(ITEM["functions"]))


class Checks(unittest.TestCase):
    def test_committed_model_is_consistent(self):
        self.assertEqual(findings(), [])

    def test_m1_parent_and_kind(self):
        item = copy.deepcopy(ITEM)
        e = next(x for x in item["elements"] if x["id"] == "SUS-M1-SAF")
        e["parent"], e["kind"] = "SUS-A1", "mechanical"
        f = findings(item=item)
        self.assertTrue(any(x.startswith("M1 SUS-M1-SAF: parent") for x in f))
        self.assertTrue(any(x.startswith("M1 SUS-M1-SAF: kind") for x in f))

    def test_m1_missing_element(self):
        item = copy.deepcopy(ITEM)
        item["elements"].append(dict(item["elements"][1], id="SUS-M1-NEW"))
        self.assertIn("M1 SUS-M1-NEW: in the item definition but not a part of SUS-I1 in Architecture.sysml", findings(item=item))

    def test_m4_endpoint_and_hazards(self):
        item = copy.deepcopy(ITEM)
        i = next(x for x in item["interfaces"] if x["id"] == "IF-006")
        i["to"], i["hazard_ids"] = "SUS-A1-FC", ["HAZ-DCK-001"]
        f = findings(item=item)
        self.assertTrue(any(x.startswith("M4 IF-006: to") for x in f))
        self.assertTrue(any(x.startswith("M4 IF-006: hazard_ids") for x in f))

    def test_m9_performers(self):
        item = copy.deepcopy(ITEM)
        item["functions"][0]["performed_by"] = ["SUS-M1-CTL"]
        self.assertTrue(any(x.startswith("M9 F-01: performed by") for x in findings(item=item)))

    def test_r2_allocation_must_match_satisfy(self):
        reqs = copy.deepcopy(REQS)
        reqs[0]["allocated_to"] = ["SUS-M1-SAF"]
        self.assertTrue(any(x.startswith("R2 SYS-001") for x in findings(reqs=reqs)))

    def test_r3_hazard_must_exist(self):
        f = findings(hazards=HAZ - {"HAZ-PIL-001"})
        self.assertIn("R3 SYS-001: hazard HAZ-PIL-001 does not exist in safety/hazards/", f)


class Generated(unittest.TestCase):
    def test_generated_model_files_current(self):
        for path, text in gen_requirements.build().items():
            self.assertEqual(path.read_text(encoding="utf-8"), text, f"{path.name} stale")

    def test_views_current(self):
        for rel, text in views.build().items():
            self.assertEqual((ROOT / rel).read_text(encoding="utf-8"), decorate(rel, text), f"{rel} stale; run tools.sysml.views")

    def test_n2_lists_every_interface(self):
        svg = views.v08(M, "x")
        for c in M.connections:
            self.assertIn(c, svg)


if __name__ == "__main__":
    unittest.main()
