import unittest

from tools.previews import build_previews as bp


class Patterns(unittest.TestCase):
    def test_globs(self):
        self.assertTrue(bp._pattern("**/figures").match("concept/figures"))
        self.assertTrue(bp._pattern("**/figures").match("figures"))
        self.assertTrue(bp._pattern("tools/**").match("tools/sysml/pilot"))
        self.assertFalse(bp._pattern("tools/**").match("toolsx"))
        self.assertFalse(bp._pattern("safety/mil-std-882e").match("safety/mil-std-882e/templates"))


class Repository(unittest.TestCase):
    def test_every_folder_is_covered(self):
        unlisted, missing = bp.coverage(bp.load())
        self.assertEqual(unlisted, [], "folders with no preview entry")
        self.assertEqual(missing, [], "entries for folders that do not exist")

    def test_outputs_are_current(self):
        stale = [p for p, t in bp.build().items() if not p.exists() or p.read_text(encoding="utf-8") != t]
        self.assertEqual(stale, [], "run: python -m tools.previews.build_previews")


class Block(unittest.TestCase):
    def test_block_goes_after_terms_and_is_replaced_in_place(self):
        entry = {"planned": "a figure"}
        text = f"# T\n\nIntro.\n\n{bp.TERMS_START}\nterms\n{bp.TERMS_END}\n\n## A\n"
        once = bp.with_block(text, bp.preview_block("sim", entry))
        self.assertLess(once.index("terms:end"), once.index("preview:start"))
        self.assertLess(once.index("preview:end"), once.index("## A"))
        twice = bp.with_block(once, bp.preview_block("sim", {"planned": "another"}))
        self.assertEqual(twice.count("preview:start"), 1)
        self.assertIn("another", twice)

    def test_missing_image_is_an_error(self):
        with self.assertRaises(bp.PreviewError):
            bp.preview_block("sim", {"hero": {"img": "docs/nope.svg", "caption": "x"}})


class RecordFigures(unittest.TestCase):
    def test_figures_are_current_and_described(self):
        from tools.previews import record_figures as rf
        for p, svg in rf.build().items():
            self.assertTrue(p.exists() and p.read_text(encoding="utf-8") == svg,
                            f"stale {p.name}; run: python -m tools.previews.record_figures")
            self.assertIn("<title>Figure", svg)
            self.assertIn("Terms:", svg)


if __name__ == "__main__":
    unittest.main()
