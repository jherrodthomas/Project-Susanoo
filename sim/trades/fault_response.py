"""Supply-loss response of each trade-study alternative on both walker models -> sim/results/ts001-fault-response.*.

Usage: python -m sim.trades.fault_response [--compare]
  (no flag)   run every mode with load holding working and failed, on levels 1 and 2, and write the results
  --compare   re-run and compare with the committed JSON: per-case outcome classes must match exactly
The modes are data (sim/trades/fault_response.yaml). Synthetic, no evidence credit: the results are an input to the
trade study, not verification evidence.
"""
from __future__ import annotations

import argparse
import itertools
import json
import sys
from collections import Counter
from concurrent.futures import ProcessPoolExecutor

import mujoco

from sim.common import ABOUT, ROOT, SIM, dumps, label_table
from sim.mujoco import l2
from sim.mujoco.model import L2_SPEC, load_params
from sim.plant import spec, walker
from tools.pdac.load import _read_yaml
from tools.terms.terms import decorate

CFG = SIM / "trades" / "fault_response.yaml"
OUT_JSON = ROOT / "sim" / "results" / "ts001-fault-response.json"
OUT_MD = ROOT / "sim" / "results" / "ts001-fault-response.md"
KEYS = ("slope_deg", "stride_offset_m", "tau_leak_s", "pilot_reaction_s")
OUTCOMES = ("safe", "tip", "hard-drop")


def _one(job):
    level, case, params = job
    if level == 1:
        p = spec.load()
        p.update(params)
        r = walker.simulate(case, p)
    else:
        p = load_params()
        p.update(params)
        r = l2.simulate(case, p)
    return r["outcome"], r["events"]["impact_speed"]


def run() -> dict:
    cfg = _read_yaml(CFG)
    points = [dict(zip(KEYS, v)) for v in itertools.product(*(cfg["grid"][k] for k in KEYS))]
    p2 = load_params()
    rows = []
    for m in cfg["modes"]:
        for hold in cfg["holding"]:
            cases = [{**cfg["base"], **m["case"], "load_holding": hold, **pt} for pt in points]
            row = {"mode": m["id"], "alternatives": m["alternatives"], "title": m["title"], "load_holding": hold,
                   "params": m["params"]}
            for level in (1, 2):
                with ProcessPoolExecutor() as ex:
                    res = list(ex.map(_one, [(level, c, m["params"]) for c in cases], chunksize=8))
                n = Counter(o for o, _ in res)
                row[f"l{level}"] = {"counts": {k: n.get(k, 0) for k in OUTCOMES},
                                    "max_impact": max(v for _, v in res),
                                    "outcomes": [o for o, _ in res]}
            row["agree"] = sum(a == b for a, b in zip(row["l1"]["outcomes"], row["l2"]["outcomes"]))
            rows.append(row)
    return {"about": ABOUT, "id": cfg["id"], "title": cfg["title"], "trade": cfg["trade"], "mujoco": mujoco.__version__,
            "spec_digest": spec.digest(), "l2_spec": L2_SPEC.relative_to(ROOT).as_posix(), "grid": cfg["grid"],
            "cases": len(points), "points": points, "rows": rows,
            "torques": {k: p2[k] for k in ("ankle_torque_max_nm", "knee_torque_max_nm", "hip_torque_max_nm")},
            "electric_sag_floor": p2["electric_sag_floor"], "safe_drop_speed_mps": p2["safe_drop_speed_mps"]}


def page(res: dict) -> str:
    n = res["cases"]
    out = [f"# {res['id']} · {res['title']}\n\n",
           label_table(f"sim/plant/walker.py (level 1) and sim/mujoco/l2.py (level 2, MuJoCo {res['mujoco']}); {res['l2_spec']}",
                       f"Trade study {res['trade']}: supply loss for each actuation and power alternative",
                       [("purpose", "trade-study input; not verification evidence")]), "\n",
           f"Each row runs {n} cases over the operating envelope ({', '.join(f'`{k}` {v}' for k, v in res['grid'].items())}) "
           f"on both models. Torques as adopted in the level-2 spec: ankle {res['torques']['ankle_torque_max_nm']:.0f}, "
           f"knee {res['torques']['knee_torque_max_nm']:.0f}, hip {res['torques']['hip_torque_max_nm']:.0f} N m. "
           f"Residual bus floor (B-SAG) {res['electric_sag_floor']} of full torque (assumed). A cockpit arriving faster than "
           f"{res['safe_drop_speed_mps']} m/s is a hard drop.\n\n",
           "| Mode | Alternatives | Load holding | Level 1: safe / tip / drop | Level 2: safe / tip / drop | "
           "Worst impact L1 / L2 (m/s) | Same outcome |\n|---|---|---|---|---|---|---|\n"]
    for r in res["rows"]:
        a, b = r["l1"]["counts"], r["l2"]["counts"]
        out.append(f"| {r['mode']} | {', '.join(r['alternatives'])} | {r['load_holding']} | "
                   f"{a['safe']} / {a['tip']} / {a['hard-drop']} | {b['safe']} / {b['tip']} / {b['hard-drop']} | "
                   f"{r['l1']['max_impact']} / {r['l2']['max_impact']} | {r['agree']} of {n} |\n")
    out.append("\n## Modes\n\n")
    seen = set()
    for r in res["rows"]:
        if r["mode"] in seen:
            continue
        seen.add(r["mode"])
        extra = f" Parameters changed: {', '.join(f'`{k}` {v}' for k, v in r['params'].items())}." if r["params"] else ""
        out.append(f"- **{r['mode']}** ({', '.join(r['alternatives'])}): {r['title']}.{extra}\n")
    out.append("\nAt this fidelity the alternatives differ only in how joint torque falls with supply (the capacity curve "
               "in `sim/plant/walker.py`). Local faults of one joint (an electrohydraulic actuator's own leak, a motor "
               "winding fault) are not modelled.\n")
    return "".join(out)


def compare(new: dict, old: dict) -> list[str]:
    bad = []
    if new["points"] != old["points"] or [r["mode"] for r in new["rows"]] != [r["mode"] for r in old["rows"]]:
        return ["grid or modes changed; re-run without --compare"]
    for rn, ro in zip(new["rows"], old["rows"]):
        for lvl in ("l1", "l2"):
            if rn[lvl]["outcomes"] != ro[lvl]["outcomes"]:
                diff = sum(a != b for a, b in zip(rn[lvl]["outcomes"], ro[lvl]["outcomes"]))
                bad.append(f"{rn['mode']} holding {rn['load_holding']} {lvl}: {diff} case outcome(s) differ")
            if abs(rn[lvl]["max_impact"] - ro[lvl]["max_impact"]) > 0.1:
                bad.append(f"{rn['mode']} holding {rn['load_holding']} {lvl}: worst impact "
                           f"{rn[lvl]['max_impact']} vs {ro[lvl]['max_impact']}")
    return bad


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--compare", action="store_true")
    a = ap.parse_args(argv)
    res = run()
    if a.compare:
        old = json.loads(OUT_JSON.read_text())
        bad = compare(res, old)
        if not bad and OUT_MD.read_text() != decorate(OUT_MD, page(old)):
            bad.append("ts001-fault-response.md does not match ts001-fault-response.json")
        for b in bad:
            print(b)
        print(f"{len(res['rows'])} rows, {len(bad)} difference(s) from the committed results")
        return 1 if bad else 0
    OUT_JSON.write_text(dumps(res), encoding="utf-8")
    OUT_MD.write_text(decorate(OUT_MD, page(json.loads(dumps(res)))), encoding="utf-8")   # built from the JSON
    print(f"wrote {OUT_JSON.relative_to(ROOT)} and {OUT_MD.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
