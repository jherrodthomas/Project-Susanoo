# SPDX-License-Identifier: Apache-2.0
"""Tests of the wiki build: the real pages build, includes and links are rewritten, breakage is reported."""
from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_wiki  # noqa: E402

REPO, BRANCH = "owner/repo", "main"


class Build(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.root = self.tmp / "root"
        (self.root / "docs/wiki").mkdir(parents=True)
        (self.root / "framework").mkdir()
        (self.root / "framework/doc.md").write_text("# Doc\n\nBody with [other](other.md).\n")
        (self.root / "framework/other.md").write_text("# Other\n")
        (self.root / "docs/wiki/Home.md").write_text(
            "# Home\n[Page](Page) [repo file](../../framework/doc.md#sec)\n<!-- include: framework/doc.md -->\n"
            "<!-- BEGIN GENERATED: status (x) -->\nS\n<!-- END GENERATED: status -->\n")
        (self.root / "docs/wiki/Page.md").write_text("# Page\n")
        (self.root / "docs/wiki/README.md").write_text("# not a page\n")

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_real_pages_build(self):
        errors = build_wiki.build(self.tmp / "real", REPO, BRANCH, "abcdef0")
        self.assertEqual([], errors)

    def test_include_links_and_markers(self):
        errors = build_wiki.build(self.tmp / "out", REPO, BRANCH, "abcdef0123", self.root)
        self.assertEqual([], errors)
        home = (self.tmp / "out/Home.md").read_text()
        self.assertIn("[Page](Page)", home)
        self.assertIn("https://github.com/owner/repo/blob/main/framework/doc.md#sec", home)
        self.assertIn("Body with [other](https://github.com/owner/repo/blob/main/framework/other.md)", home)
        self.assertNotIn("# Doc", home)
        self.assertNotIn("GENERATED", home)
        self.assertIn("`abcdef0`", home)
        self.assertFalse((self.tmp / "out/README.md").exists())

    def test_broken_page_link(self):
        (self.root / "docs/wiki/Page.md").write_text("[x](Missing-Page)\n")
        self.assertTrue(build_wiki.build(self.tmp / "out", REPO, BRANCH, None, self.root))

    def test_missing_include(self):
        (self.root / "docs/wiki/Page.md").write_text("<!-- include: framework/none.md -->\n")
        self.assertTrue(build_wiki.build(self.tmp / "out", REPO, BRANCH, None, self.root))

    def test_missing_repo_file(self):
        (self.root / "docs/wiki/Page.md").write_text("[x](../../nowhere.md)\n")
        self.assertTrue(build_wiki.build(self.tmp / "out", REPO, BRANCH, None, self.root))


if __name__ == "__main__":
    unittest.main()
