"""Cross-check the level-1 plant against the level-2 MuJoCo model -> sim/results/l2-crosscheck.{md,json}.

Usage: python -m sim.mujoco.crosscheck [--compare]
  (no flag)   run every case on both models and write the results
  --compare   re-run and compare with the committed JSON: outcome classes must match exactly, mishap times within
              0.05 s and impact speeds within 0.1 m/s (MuJoCo results can differ in the last digits across CPUs)
Synthetic, no evidence credit. Agreement between two models is not validation against the real machine.
"""
from __future__ import annotations

import argparse
import json
import sys

import mujoco

from sim.common import ABOUT, ROOT, SIM, dumps, label_table
from sim.mujoco import l2
from sim.mujoco.model import L2_SPEC
from sim.plant import spec, walker
from tools.pdac.load import _read_yaml
from tools.terms.terms import decorate

CFG = SIM / "mujoco" / "crosscheck.yaml"
OUT_JSON = ROOT / "sim" / "results" / "l2-crosscheck.json"
OUT_MD = ROOT / "sim" / "results" / "l2-crosscheck.md"


def cases() -> tuple[dict, list]:
    cfg = _read_yaml(CFG)
    out = list(cfg["cases"])
    fams = dict(cfg["families"])
    for path in sorted((ROOT / "sim" / "results").glob("search-*.json")):
        res = json.loads(path.read_text())
        fid = res["family"]["id"]
        fams[fid] = f"Failure search {fid}: {res['family']['title']} (edge cases)"
        for e in res["edge_cases"]:
            out.append({"id": f"{fid}/{e['id']}", "family": fid,
                        "case": {**res["family"]["base"], **e["params"], "fault": res["family"]["fault"]}})
    return {"families": fams, "notes": cfg.get("notes") or {}}, out


def run() -> dict:
    meta, cs = cases()
    p1 = spec.load()
    p2 = l2.load_params()
    rows = []
    for c in cs:
        a, b = walker.simulate(c["case"], p1), l2.simulate(c["case"], p2)
        rows.append({"id": c["id"], "family": c["family"], "case": c["case"],
                     "l1": {"outcome": a["outcome"], "mishap_t": a["events"]["mishap_t"], "impact_speed": a["events"]["impact_speed"],
                            "lock_t": a["events"]["lock_t"]},
                     "l2": {"outcome": b["outcome"], "mishap_t": b["events"]["mishap_t"], "impact_speed": b["events"]["impact_speed"],
                            "lock_t": b["events"]["lock_t"]},
                     "agree": a["outcome"] == b["outcome"], "note": meta["notes"].get(c["id"])})
    fams = {}
    for r in rows:
        f = fams.setdefault(r["family"], {"title": meta["families"][r["family"]], "cases": 0, "agree": 0})
        f["cases"] += 1
        f["agree"] += int(r["agree"])
    return {"about": ABOUT, "mujoco": mujoco.__version__, "spec_digest": spec.digest(),
            "l2_spec": L2_SPEC.relative_to(ROOT).as_posix(), "families": fams, "rows": rows,
            "unexplained": [r["id"] for r in rows if not r["agree"] and not r["note"]]}


def page(res: dict) -> str:
    out = ["# Level-1 vs level-2 cross-check\n\n",
           label_table("sim/plant/walker.py (level 1) and sim/mujoco/l2.py (level 2, MuJoCo " + res["mujoco"] + ")",
                       "Fault catalogue, no-fault slopes and every failure-search edge case",
                       [("purpose", "fidelity cross-check between two models; not validation against hardware")]), "\n",
           "## Agreement by family\n\n| Family | Cases | Same outcome |\n|---|---|---|\n"]
    out += [f"| {k} · {v['title']} | {v['cases']} | {v['agree']} ({100 * v['agree'] / v['cases']:.0f}%) |\n"
            for k, v in res["families"].items()]
    out.append("\n## Cases\n\n| ID | Level 1 | Level 2 | Mishap time L1 / L2 (s) | Impact L1 / L2 (m/s) | Agree |\n"
               "|---|---|---|---|---|---|\n")
    for r in res["rows"]:
        a, b = r["l1"], r["l2"]
        out.append(f"| {r['id']} | {a['outcome']} | {b['outcome']} | {a['mishap_t'] or '—'} / {b['mishap_t'] or '—'} | "
                   f"{a['impact_speed']} / {b['impact_speed']} | {'yes' if r['agree'] else '**no**'} |\n")
    out.append("\n## Disagreements\n\n")
    dis = [r for r in res["rows"] if not r["agree"]]
    out += [f"- **{r['id']}** (L1 {r['l1']['outcome']}, L2 {r['l2']['outcome']}): {r['note'] or 'not yet explained'}\n" for r in dis] or ["None.\n"]
    if res["unexplained"]:
        out.append(f"\nUnexplained disagreements: {', '.join(res['unexplained'])}.\n")
    out.append("\nNotes are AI drafts (I0). A disagreement is a finding about the models: the level that is closer to the real "
               "machine is unknown until hardware data exists.\n")
    return "".join(out)


def compare(new: dict, old: dict) -> list[str]:
    bad = []
    old_rows = {r["id"]: r for r in old["rows"]}
    for r in new["rows"]:
        o = old_rows.get(r["id"])
        if o is None:
            bad.append(f"{r['id']}: not in the committed results")
            continue
        for lvl in ("l1", "l2"):
            a, b = r[lvl], o[lvl]
            if a["outcome"] != b["outcome"]:
                bad.append(f"{r['id']} {lvl}: outcome {a['outcome']} vs committed {b['outcome']}")
            if (a["mishap_t"] is None) != (b["mishap_t"] is None) or (a["mishap_t"] and abs(a["mishap_t"] - b["mishap_t"]) > 0.05):
                bad.append(f"{r['id']} {lvl}: mishap time {a['mishap_t']} vs {b['mishap_t']}")
            if abs(a["impact_speed"] - b["impact_speed"]) > 0.1:
                bad.append(f"{r['id']} {lvl}: impact speed {a['impact_speed']} vs {b['impact_speed']}")
    if len(new["rows"]) != len(old["rows"]):
        bad.append("case list changed; re-run without --compare")
    return bad


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--compare", action="store_true")
    a = ap.parse_args(argv)
    res = run()
    if a.compare:
        bad = compare(res, json.loads(OUT_JSON.read_text()))
        if not bad and OUT_MD.read_text() != decorate(OUT_MD, page(json.loads(OUT_JSON.read_text()))):
            bad.append("l2-crosscheck.md does not match l2-crosscheck.json")
        for b in bad:
            print(b)
        print(f"{len(res['rows'])} cases, {len(bad)} difference(s) from the committed results")
        return 1 if bad else 0
    OUT_JSON.write_text(dumps(res), encoding="utf-8")
    OUT_MD.write_text(decorate(OUT_MD, page(json.loads(dumps(res)))), encoding="utf-8")   # built from the JSON
    print(f"wrote {OUT_JSON.relative_to(ROOT)} and {OUT_MD.relative_to(ROOT)}; unexplained: {res['unexplained'] or 'none'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
