#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Build the GitHub wiki from docs/wiki/.

    python3 tools/wiki/build_wiki.py --out build/wiki [--repo owner/name] [--branch main] [--commit SHA]

docs/wiki/*.md (except README.md) are the page sources, reviewed by pull request. The build:
  * replaces `<!-- include: path/from/repo/root.md -->` with that file's content (its first heading
    dropped), so a page can show a controlled document without keeping a second copy of it;
  * rewrites relative links to repository files as absolute GitHub links on the given branch
    (the wiki is a separate repository, so relative links would break there);
  * leaves wiki page links ([text](Page-Name)) as they are, after checking the page exists;
  * strips generated-block markers and appends a footer naming the source commit.
It exits 1 on a missing include, a broken page link or a link to a missing repository file.
The .github/workflows/wiki.yaml workflow publishes the output to <repo>.wiki.git on every push to main.
"""
from __future__ import annotations

import argparse
import posixpath
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "docs/wiki"
LINK = re.compile(r"(!?\[[^\]]*\]\()([^)\s]+)(\))")
INCLUDE = re.compile(r"^<!-- include: (\S+) -->$", re.M)
MARKER = re.compile(r"^<!-- (?:BEGIN|END) GENERATED:[^>]*-->\n", re.M)


class BuildError(Exception):
    pass


def rewrite_links(text: str, src_dir: str, pages: set[str], repo: str, branch: str, root: Path) -> str:
    """Rewrite the links of text whose file lives in repo-relative directory src_dir."""
    def fix(match: re.Match) -> str:
        head, target, tail = match.groups()
        if re.match(r"^[a-z][a-z0-9+.-]*:", target, re.I) or target.startswith("#"):
            return match.group(0)
        path, _, anchor = target.partition("#")
        if src_dir == "docs/wiki" and "/" not in path and "." not in path:
            if path not in pages:
                raise BuildError(f"link to missing wiki page {path!r}")
            return match.group(0)
        rel = posixpath.normpath(posixpath.join(src_dir, path))
        if rel.startswith("..") or not (root / rel).exists():
            raise BuildError(f"link to missing repository path {target!r} (resolved {rel})")
        kind = "tree" if (root / rel).is_dir() else "blob"
        url = f"https://github.com/{repo}/{kind}/{branch}/{rel}" + (f"#{anchor}" if anchor else "")
        return f"{head}{url}{tail}"
    return LINK.sub(fix, text)


def build_page(name: str, pages: set[str], repo: str, branch: str, root: Path = ROOT) -> str:
    text = (root / "docs/wiki" / f"{name}.md").read_text(encoding="utf-8")
    text = rewrite_links(text, "docs/wiki", pages, repo, branch, root)

    def include(match: re.Match) -> str:
        rel = match.group(1)
        path = root / rel
        if not path.is_file():
            raise BuildError(f"include of missing file {rel}")
        body = path.read_text(encoding="utf-8")
        body = re.sub(r"\A# [^\n]*\n+", "", body)  # the page has its own title
        body = rewrite_links(body, posixpath.dirname(rel), pages, repo, branch, root)
        source = f"https://github.com/{repo}/blob/{branch}/{rel}"
        return f"{body.rstrip()}\n\n*Included from [`{rel}`]({source}); edit it there.*"

    text = INCLUDE.sub(include, text)
    return MARKER.sub("", text)


def build(out: Path, repo: str, branch: str, commit: str | None, root: Path = ROOT) -> list[str]:
    names = sorted(p.stem for p in (root / "docs/wiki").glob("*.md") if p.name != "README.md")
    pages = set(names)
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    errors = []
    stamp = f" at `{commit[:7]}`" if commit else ""
    for name in names:
        try:
            text = build_page(name, pages, repo, branch, root)
        except BuildError as exc:
            errors.append(f"{name}: {exc}")
            continue
        if not name.startswith("_"):
            text = (f"{text.rstrip()}\n\n---\n*Built from [`docs/wiki/{name}.md`](https://github.com/{repo}/blob/{branch}/docs/wiki/{name}.md)"
                    f"{stamp}. The wiki is a generated mirror: edit the page in the repository, not here.*\n")
        (out / f"{name}.md").write_text(text, encoding="utf-8")
    return errors


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, default=ROOT / "build/wiki")
    ap.add_argument("--repo", default="jherrodthomas/Project-Susanoo")
    ap.add_argument("--branch", default="main")
    ap.add_argument("--commit")
    args = ap.parse_args()
    errors = build(args.out, args.repo, args.branch, args.commit)
    for err in errors:
        print(f"FAIL {err}")
    if errors:
        return 1
    print(f"wiki: {len(list(args.out.glob('*.md')))} pages built in {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
