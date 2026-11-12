"""Shared helpers for the simulation track: the synthetic-data label, stable JSON, and write-or-check."""
from __future__ import annotations

import json
from pathlib import Path

from sim.plant import spec
from tools.terms.terms import decorate  # noqa: E402

SIM = Path(__file__).resolve().parent
ROOT = SIM.parent
ABOUT = "Synthetic simulation output; design aid only, no evidence credit (sim/README.md, evidence gate)."


def label_table(simulator: str, scenario: str, extra: list[tuple[str, str]] = ()) -> str:
    rows = [("data_kind", "synthetic"), ("evidence credit", "none (no approved fidelity case)"),
            ("simulator", simulator), ("plant spec", f"sim/spec/walker.yaml digest `{spec.digest()}`"),
            ("scenario", scenario), *extra]
    return "| Label | Value |\n|---|---|\n" + "\n".join(f"| {k} | {v} |" for k, v in rows) + "\n"


def dumps(obj) -> str:
    return json.dumps(obj, indent=1, sort_keys=True) + "\n"


def write_or_check(outputs: dict, check: bool, hint: str) -> int:
    stale = []
    for rel, text in outputs.items():
        text = decorate(rel, text)          # terms block / line (tools/terms)
        path = ROOT / rel
        if path.exists() and path.read_text(encoding="utf-8") == text:
            continue
        if check:
            stale.append(rel)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
            print(f"wrote {rel}")
    if stale:
        print(f"Simulation outputs are out of date; run: {hint}")
        for s in stale:
            print(f"  {s}")
        return 1
    return 0
