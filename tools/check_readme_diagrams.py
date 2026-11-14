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
    "concept": {"skip_dirs": {"figures"}, "generator": ["tools/figures/build_figures.py", "--check"],
                # The record-driven section (modes and scenarios, figures 6-7) between the concept-records markers.
                "extra_generators": [["tools/figures/concept_readme.py", "--check"]]},
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
    # Generated README of the standard model and tailoring; the two subfolders keep their own pages.
    "standards": {"skip_dirs": {"figures", "mil-std-882e", "tailoring"},
                  "generator": ["tools/figures/standards_readme.py", "--check"]},
    # Generated README of the system models; models/sysml/ keeps its hand-written page.
    "models": {"skip_dirs": {"figures", "sysml"}, "generator": ["tools/figures/models_readme.py", "--check"]},
    "integrations": {"skip_dirs": {"figures", "px4"}, "generator": ["tools/figures/integrations_readme.py", "--check"]},
    # framework/figures.yaml (documentation-standard figure) is built by build_figures.py; the README top by its own.
    "framework": {"skip_dirs": {"figures"}, "generator": ["tools/figures/framework_readme.py", "--check"],
                  "extra_generators": [["tools/figures/build_figures.py", "--check"]]},
    # Generated README of the tools; the packages are code (pdac/ keeps its own page).
    "tools": {"skip_dirs": {"cad", "figures", "pdac", "previews", "readme", "reliability", "sysml", "terms", "vcycle",
                            "wiki", "worksheets", "__pycache__"},
              "generator": ["tools/figures/tools_readme.py", "--check"]},
    # Generated README of the documentation sources; the subfolders keep their folder previews.
    "docs": {"skip_dirs": {"3d", "diagrams", "figures", "readme", "vcycle", "wiki"},
             "generator": ["tools/figures/docs_readme.py", "--check"]},
    # Hand-written layout review (SUS-CAD-001) with two generated parts: the layout tables (tools/cad/readme.py)
    # and the cad-records section with the documentation-standard figures.
    "cad/params": {"skip_dirs": {"figures"}, "generator": ["tools/figures/params_readme.py", "--check"]},
    "cad/drawings": {"skip_dirs": {"figures"}, "generator": ["tools/figures/drawings_readme.py", "--check"]},
    "cad/renders": {"skip_dirs": {"blender", "figures"}, "generator": ["tools/figures/renders_readme.py", "--check"]},
    "cad/concept-art": {"skip_dirs": {"figures"}, "generator": ["tools/figures/art_readme.py", "--check"]},
    "cad/renders/blender": {"skip_dirs": {"figures"}, "generator": ["tools/figures/blender_readme.py", "--check"]},
    "cad": {"skip_dirs": {"concept-art", "drawings", "figures", "params", "renders"},
            "generator": ["tools/figures/cad_readme.py", "--check"],
            "extra_generators": [["tools/cad/readme.py", "--check"]]},
    # Generated README of the PX4 SITL harness (sim/ skips its subfolders; this one has its own page).
    "sim/uav": {"skip_dirs": {"figures", "__pycache__"}, "generator": ["tools/figures/uav_readme.py", "--check"]},
    "sim/plant": {"skip_dirs": {"figures", "__pycache__"}, "generator": ["tools/figures/plant_readme.py", "--check"]},
    "sim/search": {"skip_dirs": {"figures", "__pycache__"}, "generator": ["tools/figures/search_readme.py", "--check"]},
    "sim/mujoco": {"skip_dirs": {"figures", "__pycache__"}, "generator": ["tools/figures/mujoco_readme.py", "--check"]},
    "sim/trades": {"skip_dirs": {"figures", "__pycache__"}, "generator": ["tools/figures/trades_readme.py", "--check"]},
    "sim/spec": {"skip_dirs": {"figures"}, "generator": ["tools/figures/spec_readme.py", "--check"]},
    # Committed results; uav/ keeps its folder preview.
    "sim/results": {"skip_dirs": {"figures", "uav"}, "generator": ["tools/figures/results_readme.py", "--check"]},
    "sim/results/uav": {"skip_dirs": {"figures"}, "generator": ["tools/figures/uavresults_readme.py", "--check"]},
    "sim/scenes3d/library": {"skip_dirs": {"figures"}, "generator": ["tools/figures/lookslib_readme.py", "--check"]},
    "sim/scenes3d/out": {"skip_dirs": {"figures"}, "generator": ["tools/figures/sceneout_readme.py", "--check"]},
    # 3D scene builder; library/ and out/ keep their folder previews.
    # 2D scene code; its *.svg are the sim page's figures, its own figures sit in readme/.
    "sim/figures": {"skip_dirs": {"readme", "__pycache__"}, "generator": ["tools/figures/simfigs_readme.py", "--check"]},
    "docs/3d": {"skip_dirs": {"assets", "figures"}, "generator": ["tools/figures/pages3d_readme.py", "--check"]},
    "docs/vcycle": {"skip_dirs": {"figures"}, "generator": ["tools/figures/vcycle_readme.py", "--check"]},
    "docs/diagrams": {"skip_dirs": {"figures", "mil-std-882e"}, "generator": ["tools/figures/diagrams_readme.py", "--check"]},
    "docs/readme": {"skip_dirs": {"figures"}, "generator": ["tools/figures/frontpage_readme.py", "--check"]},
    "docs/wiki": {"skip_dirs": {"images"}, "generator": ["tools/figures/wiki_readme.py", "--check"]},
    "docs/wiki/images": {"skip_dirs": {"readme"}, "generator": ["tools/figures/wikiimages_readme.py", "--check"]},
    "docs/3d/assets": {"skip_dirs": {"figures"}, "generator": ["tools/figures/assets3d_readme.py", "--check"]},
    "docs/diagrams/mil-std-882e": {"skip_dirs": {"figures"}, "generator": ["tools/figures/maps882e_readme.py", "--check"]},
    "sim/scenes3d": {"skip_dirs": {"figures", "library", "out", "__pycache__"},
                     "generator": ["tools/figures/scenes3d_readme.py", "--check"]},
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
        for gen in ([prof["generator"]] if prof.get("generator") else []) + prof.get("extra_generators", []):
            if tuple(gen) in ran:
                continue
            ran.add(tuple(gen))
            r = subprocess.run([sys.executable, *gen], cwd=ROOT, capture_output=True, text=True)
            if r.returncode != 0:
                errs.append(f"{root_rel}: generated docs are stale or catalog invalid:\n{r.stdout}{r.stderr}")
    if errs:
        print("Documentation standard violations:\n  " + "\n  ".join(errs))
        return 1
    print(f"OK: {checked} folder READMEs meet framework/documentation-standard.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
