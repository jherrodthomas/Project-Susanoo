"""Fault catalogue runs on the walker plant -> sim/results/plant-results.{md,json}.

Usage: python -m sim.plant.report [--check]
Each fault in sim/faults.yaml is run on flat ground and on an 8 degree slope, with its mitigations present and
absent, so the table shows what each mitigation buys under the plant's stated assumptions.
"""
from __future__ import annotations

import argparse
import sys

from sim.common import ABOUT, ROOT, SIM, dumps, label_table, write_or_check
from sim.plant import spec, walker
from tools.pdac.load import _read_yaml

FAULTS = SIM / "faults.yaml"
CONFIGS = [  # (label, case overrides) per fault family
    ("mitigated", {"load_holding": "works", "monitor": True, "pilot_reaction_s": 1.5}),
    ("no load holding", {"load_holding": "fails", "monitor": True, "pilot_reaction_s": 1.5}),
    ("no monitor", {"load_holding": "works", "monitor": False, "pilot_reaction_s": 1.5}),
    ("no hold, slow pilot", {"load_holding": "fails", "monitor": True, "pilot_reaction_s": 3.0}),
]
SLOPES = [0.0, 8.0]


class CatalogueError(Exception):
    pass


def check_faults(faults: dict) -> None:
    for f in faults["faults"]:
        for ref in f["causes"]:
            hid, cf = ref.split(":")
            path = ROOT / "safety" / "hazards" / f"{hid}.yaml"
            if not path.exists():
                raise CatalogueError(f"{f['id']}: hazard {hid} does not exist")
            if cf not in {c["id"] for c in _read_yaml(path)["causal_factors"]}:
                raise CatalogueError(f"{f['id']}: {hid} has no causal factor {cf}")


def run() -> dict:
    p = spec.load()
    faults = _read_yaml(FAULTS)
    check_faults(faults)
    rows = []
    for f in faults["faults"]:
        variant = "electric" if f["variant"] == "electric" else "hydraulic"
        for slope in SLOPES:
            for label, over in CONFIGS:
                case = {"variant": variant, "fault": f["id"], "slope_deg": slope, **f["params"], **over}
                r = walker.simulate(case, p)
                rows.append({"fault": f["id"], "slope_deg": slope, "config": label, "outcome": r["outcome"],
                             "rho": r["rho"], "events": r["events"], "stop_reason": r["stop_reason"]})
    nominal = [{"slope_deg": s, **{k: v for k, v in walker.simulate({"slope_deg": s}, p).items() if k in ("outcome", "rho")}}
               for s in (0, 4, 8, 10, 12, 15, 20, 25, 30)]
    return {"about": ABOUT, "spec_digest": spec.digest(), "faults": faults["faults"], "runs": rows, "nominal": nominal}


def page(res: dict) -> str:
    out = ["# Plant results: fault catalogue\n\n", label_table("sim/plant/walker.py (reduced-order, stdlib)",
           "Fault catalogue sim/faults.yaml on flat ground and an 8 degree slope"), "\n",
           "Outcome per fault and configuration. `rho` is the robustness margin (negative = margin exhausted). "
           "A mishap ends the run (contact not modelled).\n\n"]
    out.append("## No-fault capability\n\n| Slope (deg) | Outcome | rho |\n|---|---|---|\n")
    out += [f"| {n['slope_deg']} | {n['outcome']} | {n['rho']} |\n" for n in res["nominal"]]
    out.append("\n## Faults\n\n")
    for f in res["faults"]:
        out.append(f"### {f['id']} · {f['name']}\n\nCauses: {', '.join(f['causes'])}. Injection: {f['injection']}.\n\n")
        out.append("| Slope | Configuration | Outcome | rho | Alarm (s) | Stop (s, by) | Hold (s) | Mishap (s) | Impact (m/s) |\n"
                   "|---|---|---|---|---|---|---|---|---|\n")
        for r in res["runs"]:
            if r["fault"] != f["id"]:
                continue
            e = r["events"]
            stop = f"{e['stop_t']} ({r['stop_reason']})" if e["stop_t"] is not None else "—"
            out.append(f"| {r['slope_deg']:g} | {r['config']} | **{r['outcome']}** | {r['rho']} | {e['alarm_t'] or '—'} | {stop} | "
                       f"{e['lock_t'] or '—'} | {e['mishap_t'] or '—'} | {e['impact_speed']} |\n")
        out.append("\n")
    return "".join(out)


def outputs() -> dict:
    res = run()
    return {"sim/results/plant-results.json": dumps(res), "sim/results/plant-results.md": page(res)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    return write_or_check(outputs(), a.check, "python -m sim.plant.report")


if __name__ == "__main__":
    sys.exit(main())
