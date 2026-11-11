#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Write every generated view of the PDaC records.

    python3 tools/pdac/generate.py           # rewrite the views
    python3 tools/pdac/generate.py --check   # exit 1 if any view is stale (CI)

Views are blocks between `<!-- BEGIN GENERATED: name ... -->` and `<!-- END GENERATED: name -->` markers
in hand-written pages, plus pages that are generated whole. Output is deterministic: it depends only on
the records, so it changes only when they do.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pdaclib  # noqa: E402
from pdaclib import LEVELS, PROBABILITIES, SEVERITIES  # noqa: E402

TOOL = "tools/pdac/generate.py"


def _ids(values) -> str:
    return ", ".join(values) if values else "—"


def _cell(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


def records_digest(root: Path) -> str:
    h = hashlib.sha256()
    for path in [root / "pdac/product.yaml", root / "pdac/documents.yaml", *sorted((root / "pdac/items").glob("*.yaml"))]:
        h.update(path.relative_to(root).as_posix().encode())
        h.update(path.read_bytes())
    return h.hexdigest()[:12]


# --- Views -----------------------------------------------------------------------------------------

def status_block(model: pdaclib.Model, link_prefix: str) -> str:
    hazards = model.of_kind("hazard")
    levels = Counter(pdaclib._get(h, "risk.initial.level") for h in hazards)
    reqs = model.of_kind("requirement")
    req_status = Counter(r.get("status") for r in reqs)
    approvals = model.of_kind("approval")
    open_ts = [t for t in model.of_kind("trade-study") if t.get("status") != "decided"]
    level_text = ", ".join(f"{levels[lv]} {lv}" for lv in LEVELS if levels[lv])
    return (
        f"**Status:** {model.product['program_status']}\n\n"
        f"**PDaC records** (`{records_digest(model.root)}`): "
        f"{len(model.of_kind('scenario'))} scenarios · "
        f"[{len(hazards)} hazards]({link_prefix}safety/preliminary-hazard-list.md) (initial risk, proposed: {level_text}) · "
        f"{len(reqs)} requirements ({', '.join(f'{n} {s}' for s, n in sorted(req_status.items()))}) · "
        f"{len(open_ts)} open trade studies · {len(approvals)} recorded approvals · "
        f"release `{model.product['release']['id']}` {model.product['release']['status']}. "
        f"No risk has been accepted."
    )


def conops_trace(model: pdaclib.Model) -> str:
    hazards = model.of_kind("hazard")
    reqs = model.of_kind("requirement")
    rows = ["| Scenario | Type | Hazards | Candidate requirements |", "|---|---|---|---|"]
    for scn in model.of_kind("scenario"):
        hz = [h["id"] for h in hazards if scn["id"] in h.get("scenarios", [])]
        rq = sorted({r["id"] for r in reqs if scn["id"] in r.get("sources", [])}
                    | {m for h in hazards if h["id"] in hz for m in h.get("mitigated_by", [])})
        rows.append(f"| {scn['id']} {_cell(scn['title'])} | {scn['scenario_type']} | {_ids(hz)} | {_ids(rq)} |")
    return "\n".join(rows)


def requirements_list(model: pdaclib.Model) -> str:
    rows = ["| ID | Requirement | Type | Mitigates | Allocated to | Verification (planned) | Status |",
            "|---|---|---|---|---|---|---|"]
    for r in model.of_kind("requirement"):
        text = r["text"]
        if r.get("tbd"):
            text += " *TBD: " + "; ".join(r["tbd"]) + ".*"
        if r.get("design_dependency"):
            text += f" *Depends on {', '.join(r['design_dependency'])}.*"
        rows.append(f"| {r['id']} | {_cell(text)} | {r['req_type']} | {_ids(r.get('mitigates'))} | "
                    f"{_ids(r.get('allocated_to'))} | {', '.join(r['verification']['methods']) or '—'} | {r['status']} |")
    return "\n".join(rows)


def phl_page(model: pdaclib.Model) -> str:
    doc = model.by_id()["SUS-PHL-001"]
    hazards = model.of_kind("hazard")
    ids = model.by_id()
    prov = model.files["pdac/items/hazards.yaml"]["provenance"]
    reviewed = "reviewed" if prov.get("reviewed") else "not reviewed"

    grid = Counter((pdaclib._get(h, "risk.initial.severity"), pdaclib._get(h, "risk.initial.probability")) for h in hazards)
    matrix = ["| Probability \\ Severity | " + " | ".join(s.capitalize() for s in SEVERITIES) + " |",
              "|---|" + "---|" * len(SEVERITIES)]
    for prob in PROBABILITIES[:-1]:
        cells = []
        for sev in SEVERITIES:
            n = grid[(sev, prob)]
            cells.append(f"{pdaclib.risk_level(sev, prob).capitalize()}{f' · **{n}**' if n else ''}")
        matrix.append(f"| {prob.capitalize()} | " + " | ".join(cells) + " |")

    table = ["| ID | Hazard | Worst credible mishap | Energy | Exposed | Scenarios | Initial risk | Candidate mitigations | Depends on |",
             "|---|---|---|---|---|---|---|---|---|"]
    for h in hazards:
        ini = h["risk"]["initial"]
        exposed = ", ".join(ids[a]["title"].lower() if a in ids else a for a in h["exposed"])
        table.append(
            f"| {h['id']} | {_cell(h['title'])} | {_cell(h['mishap'])} | {', '.join(h['energy_sources'])} | {exposed} | "
            f"{_ids(h['scenarios'])} | **{ini['level'].capitalize()}** ({ini['severity']}, {ini['probability']}) | "
            f"{_ids(h['mitigated_by'])} | {_ids(h.get('design_dependency'))} |")

    by_ts = []
    for ts in model.of_kind("trade-study"):
        dep = [h["id"] for h in hazards if ts["id"] in h.get("design_dependency", [])]
        dep_r = [r["id"] for r in model.of_kind("requirement") if ts["id"] in r.get("design_dependency", [])]
        by_ts.append(f"| {ts['id']} {ts['title']} | {ts['status']} | {_ids(dep)} | {_ids(dep_r)} |")

    levels = Counter(h["risk"]["initial"]["level"] for h in hazards)
    summary = ", ".join(f"**{levels[lv]} {lv}**" for lv in LEVELS if levels[lv])

    return f"""# Preliminary Hazard List (PHL) — SUS-M1 / SUS-A1

**ID:** {doc['id']} · **Revision:** {doc['revision']} · **Status:** Draft, {reviewed}

<!-- GENERATED PAGE: written by {TOOL} from pdac/items/hazards.yaml. Edit the records, then regenerate. -->

> **Generated from [`pdac/items/hazards.yaml`](../pdac/items/hazards.yaml)** (author: {prov['author']}, independence {prov['independence']}, {prov['date']}).
> Every rating below is a **proposed initial risk**, before mitigation, made from the concept description alone. None has been reviewed by the safety lead, and **no risk has been accepted**. This list is an input to the Preliminary Hazard Analysis, not a substitute for it.

## 1. Method

The Preliminary Hazard List follows the MIL-STD-882E system safety method used as the project's integrated safety method ([standards applicability](../framework/standards-applicability.md)). Hazards were identified from the operating modes and scenarios of the [CONOPS](../concept/CONOPS.md) and from each energy source the concept contains: hydraulic pressure, stored mechanical energy, gravity (an elevated, legged platform), kinetic energy of limbs and payloads, rotor energy, electrical energy, heat and battery chemistry.

Each hazard is rated for its **worst credible mishap** with a severity category and a probability level, and the MIL-STD-882E risk assessment matrix gives the risk level. The validator recomputes every risk level from the matrix (check P5). Hazards that depend on an open trade study are rated for the alternative with the highest energy; they are re-rated when the study decides.

These are MIL-STD-882E ratings only. Aircraft failure conditions of the SUS-A1 UAV are classified separately with ARP4761A in its Functional Hazard Assessment and are never converted to or from these levels.

## 2. Summary

{len(hazards)} hazards: {summary}.

*Hazard count per cell of the MIL-STD-882E risk assessment matrix (initial risk). Each cell shows the risk level the matrix assigns.*

{chr(10).join(matrix)}

## 3. Hazard list

{chr(10).join(table)}

## 4. Hazards that depend on open trade studies

Deciding a trade study re-rates these hazards and reopens these requirements.

| Trade study | Status | Hazards | Requirements |
|---|---|---|---|
{chr(10).join(by_ts)}

## 5. Open items

1. The safety lead reviews every rating and candidate mitigation; reviewed ratings get `rating_status: reviewed`.
2. The risk-acceptance authority for each risk level is not yet defined. Until it is, no hazard can be closed (check P6).
3. The SUS-A1 Functional Hazard Assessment (ARP4761A) has not started; HAZ-014 and HAZ-015 will link to its failure conditions.
4. Next analysis: Preliminary Hazard Analysis (PHA) — causes in detail, target risk per hazard and verification of each mitigation.
"""


BLOCKS = {
    "README.md": {"status": lambda m: status_block(m, "")},
    "docs/wiki/Home.md": {"status": lambda m: status_block(m, "../../")},
    "concept/CONOPS.md": {"conops-trace": conops_trace},
    "concept/architecture.md": {"requirements": requirements_list},
}
PAGES = {"safety/preliminary-hazard-list.md": phl_page}


def replace_block(text: str, name: str, body: str, path: str) -> str:
    pattern = re.compile(rf"(<!-- BEGIN GENERATED: {re.escape(name)} [^>]*-->\n)(.*?)(<!-- END GENERATED: {re.escape(name)} -->)", re.S)
    if not pattern.search(text):
        raise SystemExit(f"{path}: missing markers for generated block {name!r}")
    return pattern.sub(lambda m: m.group(1) + body.rstrip("\n") + "\n" + m.group(3), text, count=1)


def render(model: pdaclib.Model) -> dict[str, str]:
    out: dict[str, str] = {}
    for rel, blocks in BLOCKS.items():
        text = (model.root / rel).read_text(encoding="utf-8")
        for name, fn in blocks.items():
            text = replace_block(text, name, fn(model), rel)
        out[rel] = text
    for rel, fn in PAGES.items():
        out[rel] = fn(model)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true", help="fail if a generated view is stale")
    args = ap.parse_args()
    model = pdaclib.load()
    stale = []
    for rel, text in render(model).items():
        path = model.root / rel
        current = path.read_text(encoding="utf-8") if path.exists() else None
        if current == text:
            continue
        if args.check:
            stale.append(rel)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
            print(f"wrote {rel}")
    if stale:
        for rel in stale:
            print(f"STALE {rel}: run python3 {TOOL}")
        return 1
    print("generated views are current" if args.check else "done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
