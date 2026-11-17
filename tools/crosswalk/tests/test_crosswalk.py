import copy
import unittest

from tools.crosswalk import build as b


class Crosswalk(unittest.TestCase):
    def test_record_is_valid_and_page_current(self):
        d = b.load()
        self.assertEqual(b.validate(d), [])
        text = b.decorate(b.PAGE.relative_to(b.ROOT).as_posix(), b.page(d))
        self.assertEqual(b.PAGE.read_text(encoding="utf-8"), text, "run: python -m tools.crosswalk.build")

    def test_spans_must_cover_every_level(self):
        d = copy.deepcopy(b.load())
        d["parameters"][0]["cells"]["61508"][0]["span"] = 1
        self.assertTrue(any("spans add up" in e for e in b.validate(d)))

    def test_verified_cell_names_who_and_edition(self):
        d = copy.deepcopy(b.load())
        d["parameters"][0]["cells"]["882E"][0]["verified"] = True
        self.assertTrue(any("verified_by" in e for e in b.validate(d)))

    def test_page_says_it_is_not_an_equivalence_table(self):
        self.assertIn("Not an equivalence table", b.page(b.load()))


if __name__ == "__main__":
    unittest.main()
