#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Check that every relative link in the repository's Markdown resolves.

    python3 tools/check_links.py

A relative link must name an existing file or directory (an optional #anchor is not checked). In
docs/wiki/, a link without a slash or extension is a wiki page link and must name a page there.
External (scheme://, mailto:) and in-page (#...) links are skipped.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
LINK = re.compile(r"!?\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
FENCE = re.compile(r"^```.*?^```", re.S | re.M)
WIKI_DIR = ROOT / "docs/wiki"


def markdown_files(root: Path) -> list[Path]:
    skip = {".git", "build", "node_modules"}
    return sorted(p for p in root.rglob("*.md") if not skip & set(p.relative_to(root).parts))


def broken_links(path: Path, root: Path = ROOT) -> list[str]:
    text = FENCE.sub("", path.read_text(encoding="utf-8"))
    out = []
    for target in LINK.findall(text):
        if re.match(r"^[a-z][a-z0-9+.-]*:", target, re.I) or target.startswith("#"):
            continue
        target = unquote(target.split("#", 1)[0])
        if not target:
            continue
        if path.parent == root / "docs/wiki" and "/" not in target and "." not in target:
            if not (path.parent / f"{target}.md").is_file():
                out.append(f"wiki page {target!r} does not exist")
            continue
        if not (path.parent / target).exists():
            out.append(f"{target} does not exist")
    return out


def main() -> int:
    failures = 0
    files = markdown_files(ROOT)
    for path in files:
        for problem in broken_links(path):
            print(f"FAIL {path.relative_to(ROOT).as_posix()}: {problem}")
            failures += 1
    print(f"links: {len(files)} Markdown files checked, {failures} broken link(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
