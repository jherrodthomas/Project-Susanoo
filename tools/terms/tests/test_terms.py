"""Tests for the abbreviations and record-codes standard (tools/terms)."""
import unittest

from tools.terms import terms as T

SVG = ('<svg xmlns="http://www.w3.org/2000/svg" width="400" height="200" viewBox="0 0 400 200" role="img">'
       '<rect x="0" y="0" width="400" height="200" fill="#FFFFFF"/><text x="10" y="20">UAV dock HAZ-WLK-002</text></svg>\n')
MD = "# Title\n\nThe UAV docks on SUS-M1 per SYS-010.\n\n## More\n\nText.\n"


class Finding(unittest.TestCase):
    def test_codes_resolve_to_their_prefix(self):
        found, unknown = T.find("HAZ-WLK-002 and IF-PX4-005 and SYS-010")
        self.assertEqual(found, ["HAZ-", "IF-PX4-", "SYS-"])
        self.assertEqual(unknown, [])

    def test_element_ids_come_from_the_item_definition(self):
        found, _ = T.find("SUS-M1-SAF talks to EXT-PILOT")
        self.assertEqual(found, ["SUS-M1-SAF", "EXT-PILOT"])
        self.assertIn("safety monitor", T.load()[0]["SUS-M1-SAF"])

    def test_risk_codes_and_3d(self):
        found, _ = T.find("risk 1C to 1E in a 3D scene")
        self.assertIn("RAC#", found)
        self.assertIn("3D", found)

    def test_undefined_abbreviation_is_reported(self):
        _, unknown = T.find("the QZXW unit and a CamelCaseName")
        self.assertEqual(unknown, ["QZXW"])

    def test_definitions_only_use_defined_terms(self):
        for key, meaning in T.load()[0].items():
            self.assertEqual(T.find(meaning)[1], [], f"definition of {key}")


class Decorating(unittest.TestCase):
    def test_markdown_block_is_idempotent_and_placed_under_the_opening(self):
        once = T.decorate("x.md", MD)
        self.assertEqual(T.decorate("x.md", once), once)
        self.assertLess(once.index(T.START), once.index("## More"))
        self.assertGreater(once.index(T.START), once.index("The UAV docks"))
        for term in ("UAV", "SUS-M1", "SYS-nnn"):
            self.assertIn(f"| {term} |", once)

    def test_existing_block_stays_where_the_page_put_it(self):
        page = "<p>banner</p>\n\nIntro with UAV.\n\n" + T.START + "\nold\n" + T.END + "\n\nRest.\n"
        out = T.decorate("x.md", page)
        self.assertTrue(out.startswith("<p>banner</p>\n\nIntro with UAV.\n\n" + T.START))

    def test_svg_footer_is_idempotent_and_restores_height(self):
        once = T.decorate("x.svg", SVG)
        self.assertIn('<g class="terms" data-base-h="200">', once)
        self.assertNotIn('height="200"', once.split(">", 1)[0])
        self.assertEqual(T.decorate("x.svg", once), once)
        self.assertIn("UAV = uncrewed aerial vehicle", once)

    def test_page_without_terms_gets_no_block(self):
        self.assertEqual(T.decorate("x.md", "# Plain\n\nNothing to explain here.\n"), "# Plain\n\nNothing to explain here.\n")


class Repository(unittest.TestCase):
    def test_every_page_and_figure_explains_its_terms(self):
        self.assertEqual(T.main(["--check"]), 0)


if __name__ == "__main__":
    unittest.main()
