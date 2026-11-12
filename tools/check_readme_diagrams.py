#!/usr/bin/env python3
"""Enforce framework/documentation-standard.md on folder READMEs.

For every enforced root, each folder (except listed data folders) must have a
README.md containing the required sections; each diagram section must embed at
least one generated SVG figure that exists; the SysML section must link an
existing .sysml file; and every generator must report its output as current.

Exit status 0 = compliant, 1 = violations found.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Sections every folder README must have; True = must embed an SVG figure.
BASE_SECTIONS = {
    "Purpose": False,
    "Block diagram": True,
    "Boundary diagram": True,
    "SysML model": True,
    "Inputs and outputs": True,
    "Folder contents": False,
}

# Enforced documentation roots and any profile-specific extra sections.
ENFORCED = {
    "safety/mil-std-882e": {
        "extra": {"Position in the MIL-STD-882E flow": True},
        # Data folders that hold records, not documentation.
        "skip_dirs": {"sysml", "hazards", "reports", "reviews", "test-safety-releases", "figures", "tasks"},
        "generator": ["tools/gen_safety_docs.py", "--check"],
    },
    # Hand-authored READMEs; figures come from <folder>/figures.yaml.
    "concept": {"skip_dirs": {"figures"}, "generator": ["tools/figures/build_figures.py", "--check"]},
    "integrations/px4": {"skip_dirs": {"figures"}, "generator": ["tools/figures/build_figures.py", "--check"]},
    # Generated README; figures and tables from requirements/SYS-*.yaml.
    "requirements": {"skip_dirs": {"figures"}, "generator": ["tools/figures/requirements_readme.py", "--check"]},
    # Generated README; figures and tables from verification/, safety/hazards/ and requirements/.
    "verification": {"skip_dirs": {"figures"}, "generator": ["tools/figures/verification_readme.py", "--check"]},
    # Generated README; figures and tables from changes/ and the hazard links rule R10 follows.
    "changes": {"skip_dirs": {"figures"}, "generator": ["tools/figures/changes_readme.py", "--check"]},
    # Generated README; what is waiting on a human review, from the tailoring and the records rule R13 checks.
    "reviews": {"skip_dirs": {"figures"}, "generator": ["tools/figures/reviews_readme.py", "--check"]},
    # Generated README and SysML lifecycle from decisions/register.yaml.
    "decisions": {"skip_dirs": {"figures"}, "generator": ["tools/figures/decisions_readme.py", "--check"]},
    # Generated README from the item definition; trades/ keeps its preview page (docs/previews.yaml).
    "architecture": {"skip_dirs": {"figures", "trades"}, "generator": ["tools/figures/architecture_readme.py", "--check"]},
    # Generated front page of the safety records; the subfolders keep their own pages (mil-std-882e/ is its own root).
    "safety": {"skip_dirs": {"figures", "mil-std-882e", "hazards", "software", "events", "generated"},
               "generator": ["tools/figures/safety_readme.py", "--check"]},
    # Generated top of the simulation page (hand-written part below the END marker); subfolders keep their own pages.
    "sim": {"skip_dirs": {"figures", "mujoco", "plant", "results", "scenes3d", "search", "spec", "tests", "trades", "uav",
                          "__pycache__"},
            "generator": ["tools/figures/sim_readme.py", "--check"]},
}

H2 = re.compile(r"^## (.+?)\s*$", re.M)
FIGURE = re.compile(r"!\[[^\]]*\]\(([^)]+\.svg)\)")
SYSML_LINK = re.compile(r"\]\(([^)]+\.sysml)\)")


def sections(text: str) -> dict[str, str]:
    heads = list(H2.finditer(text))
    out = {}
    for i, h in enumerate(heads):
        end = heads[i + 1].start() if i + 1 < len(heads) else len(text)
        out[h.group(1)] = text[h.end():end]
    return out


def check_readme(readme: Path, required: dict[str, bool]) -> list[str]:
    errs = []
    text = readme.read_text()
    secs = sections(text)
    rel = readme.relative_to(ROOT)
    for name, needs_diagram in required.items():
        if name not in secs:
            errs.append(f"{rel}: missing section '## {name}'")
        elif needs_diagram:
            figs = FIGURE.findall(secs[name])
            if not figs:
                errs.append(f"{rel}: section '## {name}' embeds no SVG figure")
            for fig in figs:
                if not (readme.parent / fig).exists():
                    errs.append(f"{rel}: figure '{fig}' in '## {name}' does not exist")
    if "```mermaid" in text:
        errs.append(f"{rel}: uses Mermaid; use generated SVG figures (framework/documentation-standard.md)")
    if "SysML model" in secs:
        links = SYSML_LINK.findall(secs["SysML model"])
        if not links:
            errs.append(f"{rel}: '## SysML model' does not link a .sysml file")
        for link in links:
            if not (readme.parent / link).resolve().exists():
                errs.append(f"{rel}: SysML link '{link}' does not resolve")
    return errs


def main() -> int:
    errs: list[str] = []
    checked = 0
    ran: set[tuple[str, ...]] = set()
    for root_rel, prof in ENFORCED.items():
        required = dict(BASE_SECTIONS, **prof.get("extra", {}))
        base = ROOT / root_rel
        for d in sorted([base, *[p for p in base.rglob("*") if p.is_dir()]]):
            if any(part in prof["skip_dirs"] for part in d.relative_to(base).parts):
                continue
            readme = d / "README.md"
            if not readme.exists():
                errs.append(f"{d.relative_to(ROOT)}/: folder has no README.md")
                continue
            checked += 1
            errs += check_readme(readme, required)
        if prof.get("generator") and tuple(prof["generator"]) not in ran:
            ran.add(tuple(prof["generator"]))
            r = subprocess.run([sys.executable, *prof["generator"]], cwd=ROOT, capture_output=True, text=True)
            if r.returncode != 0:
                errs.append(f"{root_rel}: generated docs are stale or catalog invalid:\n{r.stdout}{r.stderr}")
    if errs:
        print("Documentation standard violations:\n  " + "\n  ".join(errs))
        return 1
    print(f"OK: {checked} folder READMEs meet framework/documentation-standard.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
