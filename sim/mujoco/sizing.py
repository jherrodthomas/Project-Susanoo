"""Size joint torques against a hazard causal factor on the level-2 model -> sim/results/sizing-cf4.{md,json}.

Usage: python -m sim.mujoco.sizing [--compare]
  (no flag)   run every sweep value on the envelope grid and write the results
  --compare   re-run and compare with the committed JSON: the failing cases must match exactly
The sweep is data (sim/mujoco/sizing.yaml). Synthetic, no evidence credit: a proposal here is a draft input to the
actuation trade, not a design value.
"""
from __future__ import annotations

import argparse
import itertools
import json
import sys
from concurrent.futures import ProcessPoolExecutor

import mujoco

from sim.common import ABOUT, ROOT, SIM, dumps, label_table
from sim.mujoco import l2
from sim.mujoco.model import L2_SPEC, load_params
from sim.plant import spec
from tools.pdac.load import _read_yaml
from tools.terms.terms import decorate

CFG = SIM / "mujoco" / "sizing.yaml"
OUT_JSON = ROOT / "sim" / "results" / "sizing-cf4.json"
OUT_MD = ROOT / "sim" / "results" / "sizing-cf4.md"
KEYS = ("slope_deg", "stride_offset_m", "tau_leak_s", "pilot_reaction_s")


def grid(g: dict) -> list[dict]:
    return [dict(zip(KEYS, v)) for v in itertools.product(*(g[k] for k in KEYS))]


def _one(job):
    over, base, point = job
    p = load_params()
    p.update(over)
    r = l2.simulate({**base, **point}, p)
    return r["outcome"]


def failures(over: dict, base: dict, points: list[dict]) -> list[dict]:
    with ProcessPoolExecutor() as ex:
        outs = list(ex.map(_one, [(over, base, pt) for pt in points], chunksize=8))
    return [{**pt, "outcome": o} for pt, o in zip(points, outs) if o != "safe"]


def run() -> dict:
    cfg = _read_yaml(CFG)
    p = load_params()
    mgl = p["mass_kg"] * p["gravity_mps2"] * p["foot_half_length_m"]
    pts, corner = grid(cfg["grid"]), grid(cfg["corner_grid"])
    sweeps = []
    for s in cfg["sweeps"]:
        rows = []
        for v in s["values"]:
            over = {**s["with"], s["param"]: v}
            f = failures(over, cfg["base"], pts)
            rows.append({"value": v, "failures": len(f), "cases": f})
        clear = [r["value"] for r in rows if r["failures"] == 0]
        lowest = min(clear) if clear and all(r["failures"] == 0 for r in rows if r["value"] >= min(clear)) else None
        sweeps.append({"id": s["id"], "param": s["param"], "with": s["with"], "rows": rows, "lowest_clear": lowest})
    prop = {k: v for k, v in cfg["proposal"].items() if k != "rationale"}
    ankle = next(s for s in sweeps if s["param"] == "ankle_torque_max_nm")
    checks = {"proposal": failures(prop, cfg["base"], pts + corner)}
    if ankle["lowest_clear"] is not None:
        checks["lowest_clear_ankle"] = failures({"ankle_torque_max_nm": ankle["lowest_clear"]}, cfg["base"], corner)
    return {"about": ABOUT, "mujoco": mujoco.__version__, "spec_digest": spec.digest(),
            "l2_spec": L2_SPEC.relative_to(ROOT).as_posix(), "id": cfg["id"], "title": cfg["title"],
            "hazard": cfg["hazard"], "causal_factor": cfg["causal_factor"], "base": cfg["base"],
            "grid": cfg["grid"], "corner_grid": cfg["corner_grid"], "grid_cases": len(pts), "corner_cases": len(corner),
            "assumed": {k: p[k] for k in ("ankle_torque_max_nm", "knee_torque_max_nm", "hip_torque_max_nm")},
            "m_g_l_foot_nm": round(mgl, 1), "sweeps": sweeps,
            "proposal": {**prop, "rationale": " ".join(cfg["proposal"]["rationale"].split()),
                         "ankle_ratio": round(prop["ankle_torque_max_nm"] / mgl, 3),
                         "failures": len(checks["proposal"]), "cases": checks["proposal"]},
            "lowest_clear_ankle_corner_failures": (len(checks["lowest_clear_ankle"])
                                                   if "lowest_clear_ankle" in checks else None)}


def _fmt(c: dict) -> str:
    return (f"{c['slope_deg']}°, offset {c['stride_offset_m']} m, leak τ {c['tau_leak_s']} s, "
            f"pilot {c['pilot_reaction_s']} s → {c['outcome']}")


def page(res: dict) -> str:
    mgl = res["m_g_l_foot_nm"]
    out = [f"# {res['id']} · {res['title']}\n\n",
           label_table(f"sim/mujoco/l2.py (level 2, MuJoCo {res['mujoco']}); {res['l2_spec']}",
                       f"{res['hazard']} {res['causal_factor']}: FLT-01 supply loss with load holding working",
                       [("purpose", "draft sizing input to the actuation trade (TS-001, DQ-006); not a design value")]), "\n",
           f"Envelope grid: {res['grid_cases']} cases ({', '.join(f'`{k}` {v}' for k, v in res['grid'].items())}). "
           f"Corner grid: {res['corner_cases']} cases. A failure is any outcome other than safe. "
           f"m g L_foot = {mgl:.0f} N m. Assumed in `sim/spec/walker_l2.yaml`: ankle {res['assumed']['ankle_torque_max_nm']:.0f}, "
           f"knee {res['assumed']['knee_torque_max_nm']:.0f}, hip {res['assumed']['hip_torque_max_nm']:.0f} N m.\n\n"]
    for s in res["sweeps"]:
        w = ", ".join(f"{k} {v}" for k, v in s["with"].items()) or "other joints as assumed"
        ankle = s["param"] == "ankle_torque_max_nm"
        out.append(f"## Sweep: {s['param']} ({w})\n\n| Value (N m) |" + (" Ratio to m g L_foot |" if ankle else "")
                   + " Failures | Failing cases (first 3) |\n|---|" + ("---|" if ankle else "") + "---|---|\n")
        for r in s["rows"]:
            ex = "; ".join(_fmt(c) for c in r["cases"][:3]) or "—"
            out.append(f"| {r['value']} |" + (f" {r['value'] / mgl:.2f} |" if ankle else "") + f" {r['failures']} | {ex} |\n")
        out.append(f"\nLowest value that clears the grid: {s['lowest_clear'] if s['lowest_clear'] is not None else 'none in the sweep'}.\n\n")
    pr = res["proposal"]
    out.append("## Proposal (draft, I0)\n\n"
               f"Ankle {pr['ankle_torque_max_nm']} N m ({pr['ankle_ratio']} m g L_foot), knee {pr['knee_torque_max_nm']} N m. "
               f"{pr['rationale']}\n\n"
               f"Failures with the proposal on the envelope and corner grids: {pr['failures']}"
               + ("" if not pr["cases"] else " (" + "; ".join(_fmt(c) for c in pr["cases"][:5]) + ")") + ".\n")
    if res["lowest_clear_ankle_corner_failures"] is not None:
        out.append(f"Failures on the corner grid at the lowest clear ankle value: {res['lowest_clear_ankle_corner_failures']}.\n")
    out.append("\nLevel 2 only: level 1 has no joint torques. Supply loss with failed load holding drops the cockpit at any "
               "torque (HAZ-PIL-002); sizing does not address it.\n")
    return "".join(out)


def compare(new: dict, old: dict) -> list[str]:
    bad = []
    key = lambda c: tuple(c[k] for k in (*KEYS, "outcome"))
    for sn, so in zip(new["sweeps"], old["sweeps"]):
        for rn, ro in zip(sn["rows"], so["rows"]):
            if sorted(map(key, rn["cases"])) != sorted(map(key, ro["cases"])):
                bad.append(f"{sn['param']}={rn['value']}: {rn['failures']} failure(s) vs committed {ro['failures']}")
    if sorted(map(key, new["proposal"]["cases"])) != sorted(map(key, old["proposal"]["cases"])):
        bad.append(f"proposal: {new['proposal']['failures']} failure(s) vs committed {old['proposal']['failures']}")
    if len(new["sweeps"]) != len(old["sweeps"]) or new["grid"] != old["grid"]:
        bad.append("sweep or grid changed; re-run without --compare")
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
            bad.append("sizing-cf4.md does not match sizing-cf4.json")
        for b in bad:
            print(b)
        print(f"{len(res['sweeps'])} sweeps, {len(bad)} difference(s) from the committed results")
        return 1 if bad else 0
    OUT_JSON.write_text(dumps(res), encoding="utf-8")
    OUT_MD.write_text(decorate(OUT_MD, page(json.loads(dumps(res)))), encoding="utf-8")   # built from the JSON
    print(f"wrote {OUT_JSON.relative_to(ROOT)} and {OUT_MD.relative_to(ROOT)}; proposal failures: {res['proposal']['failures']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
