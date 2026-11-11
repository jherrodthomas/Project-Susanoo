"""Failure search over the walker plant (layer 4). Standard library only; seeded and deterministic.

Usage: python -m sim.search.search [--check]

For each family in sim/search/families.yaml:
 1. Monte Carlo: n uniform samples of the parameter space -> where failures happen and how often (unbiased).
 2. Cross-entropy falsification: rounds of sampling from a Gaussian (continuous) / categorical (choice) proposal
    refitted to the lowest-robustness elite -> the worst cases.
 3. Edge cases: the worst distinct failures. Each is re-run (a) with parameters rounded as a scene would write
    them, (b) without the fault (is it the fault or the terrain?), (c) under each assumption probe, then mapped
    to a hazard by the family's rules. An outcome no rule maps to a hazard becomes a finding; so does a mapped
    hazard whose record lists no causal factor for the fault.
"""
from __future__ import annotations

import argparse
import math
import random
import sys

from sim.common import ABOUT, ROOT, SIM, dumps, label_table, write_or_check
from sim.plant import spec, walker
from tools.pdac.load import _read_yaml

FAMILIES = SIM / "search" / "families.yaml"


class SearchError(Exception):
    pass


# ---------------------------------------------------------------- parameter space

def dims(space: dict):
    cont = [k for k, v in space.items() if "choice" not in v]
    cat = [k for k, v in space.items() if "choice" in v]
    return cont, cat


def decode(space: dict, u: dict) -> dict:
    out = {}
    for k, v in space.items():
        if "uniform" in v:
            lo, hi = v["uniform"]
            out[k] = lo + u[k] * (hi - lo)
        elif "loguniform" in v:
            lo, hi = v["loguniform"]
            out[k] = math.exp(math.log(lo) + u[k] * (math.log(hi) - math.log(lo)))
        elif "choice" in v:
            out[k] = u[k]
        else:
            raise SearchError(f"{k}: unknown distribution {v}")
    return out


def rounded(params: dict, steps: dict) -> dict:
    out = dict(params)
    for k, s in steps.items():
        out[k] = round(round(params[k] / s) * s, 6)
    return out


def evaluate(fam: dict, params: dict, p: dict, fault=True) -> dict:
    case = {**fam["base"], **params}
    case["fault"] = fam["fault"] if fault else None
    r = walker.simulate(case, p)
    return {"outcome": r["outcome"], "rho": r["rho"], "stop_active": r["stop_active"], "events": r["events"]}


def sample_mc(fam, rng):
    cont, cat = dims(fam["space"])
    u = {k: rng.random() for k in cont}
    for k in cat:
        u[k] = rng.choice(fam["space"][k]["choice"])
    return u


def cross_entropy(fam: dict, p: dict) -> list:
    cfg = fam["falsification"]
    rng = random.Random(cfg["seed"])
    cont, cat = dims(fam["space"])
    mean = {k: 0.5 for k in cont}
    std = {k: 0.3 for k in cont}
    probs = {k: {c: 1 / len(fam["space"][k]["choice"]) for c in fam["space"][k]["choice"]} for k in cat}
    out = []
    for rnd in range(cfg["rounds"]):
        batch = []
        for _ in range(cfg["n"]):
            u = {k: min(1.0, max(0.0, rng.gauss(mean[k], std[k]))) for k in cont}
            for k in cat:
                r, acc = rng.random(), 0.0
                for c, pr in probs[k].items():
                    acc += pr
                    if r <= acc:
                        u[k] = c
                        break
                else:
                    u[k] = list(probs[k])[-1]
            params = decode(fam["space"], u)
            res = evaluate(fam, params, p)
            batch.append((res["rho"], u, params, res))
        batch.sort(key=lambda b: (b[0], sorted((k, str(v)) for k, v in b[2].items())))
        elite = batch[:max(2, int(cfg["elite"] * len(batch)))]
        for k in cont:
            vals = [e[1][k] for e in elite]
            m = sum(vals) / len(vals)
            s = math.sqrt(sum((v - m) ** 2 for v in vals) / len(vals))
            mean[k] = 0.7 * m + 0.3 * mean[k]
            std[k] = max(0.02, 0.7 * s + 0.3 * std[k])
        for k in cat:
            for c in probs[k]:
                freq = sum(1 for e in elite if e[1][k] == c) / len(elite)
                probs[k][c] = max(0.05, 0.7 * freq + 0.3 * probs[k][c])
            tot = sum(probs[k].values())
            probs[k] = {c: v / tot for c, v in probs[k].items()}
        out += [{"round": rnd + 1, "params": b[2], **b[3]} for b in batch]
    return out


# ---------------------------------------------------------------- mapping

def match(when: dict, ctx: dict) -> bool:
    return all(ctx.get(k) == v for k, v in when.items())


def map_case(fam: dict, ctx: dict) -> dict:
    for rule in fam["hazard_rules"]:
        if match(rule["when"], ctx):
            return {"hazard": rule.get("hazard"), "new": rule.get("new")}
    return {"hazard": None, "new": "Outcome matched no hazard rule"}


def fault_causes() -> dict:
    return {f["id"]: f["causes"] for f in _read_yaml(SIM / "faults.yaml")["faults"]}


# ---------------------------------------------------------------- family run

def fmt_params(params: dict) -> str:
    return ", ".join(f"{k}={v:g}" if isinstance(v, float) else f"{k}={v}" for k, v in params.items())


def run_family(fam: dict, p: dict) -> dict:
    rng = random.Random(fam["monte_carlo"]["seed"])
    mc = []
    for _ in range(fam["monte_carlo"]["n"]):
        params = decode(fam["space"], sample_mc(fam, rng))
        mc.append({"params": params, **evaluate(fam, params, p)})
    ce = cross_entropy(fam, p)
    n = len(mc)
    by_outcome = {o: sum(1 for r in mc if r["outcome"] == o) for o in walker.OUTCOMES}
    split = {}
    for k in dims(fam["space"])[1]:
        for c in fam["space"][k]["choice"]:
            sub = [r for r in mc if r["params"][k] == c]
            split[f"{k}={c}"] = {"n": len(sub), "failures": sum(1 for r in sub if r["outcome"] != "safe")}
    # edge cases: worst per (outcome, choices), then fill by robustness, skipping near-duplicates
    fails = sorted((r for r in mc + ce if r["outcome"] != "safe"),
                   key=lambda r: (r["rho"], fmt_params(r["params"])))
    cat = dims(fam["space"])[1]
    for r in fails:
        r["nofault"] = evaluate(fam, r["params"], p, fault=False)["outcome"]
    picked, keys = [], set()
    for r in fails:
        key = (r["outcome"], r["nofault"], tuple(r["params"][k] for k in cat))
        if key not in keys:
            keys.add(key)
            picked.append(r)
    for r in fails:
        if len(picked) >= fam["edge_cases"]:
            break
        if all(_dist(fam, r["params"], q["params"]) > 0.25 for q in picked):
            picked.append(r)
    picked = sorted(picked[:fam["edge_cases"]], key=lambda r: (r["rho"], fmt_params(r["params"])))
    causes = fault_causes()[fam["fault"]]
    edges, findings = [], []
    for i, r in enumerate(picked, 1):
        rp = rounded(r["params"], fam["round"])
        rr = evaluate(fam, rp, p)
        nf = evaluate(fam, rp, p, fault=False)
        probes = []
        for pr in fam["probes"]:
            pres = evaluate(fam, {**rp, **pr["set"]}, p)
            probes.append({"name": pr["name"], "outcome": pres["outcome"], "rho": pres["rho"]})
        ctx = {"outcome": rr["outcome"], "stop_active": rr["stop_active"], "nofault_outcome": nf["outcome"]}
        mapping = map_case(fam, ctx)
        ec = {"id": f"EC-{i:02d}", "family": fam["id"], "params": rp, "outcome": rr["outcome"], "rho": rr["rho"],
              "events": rr["events"], "stop_active": rr["stop_active"], "nofault_outcome": nf["outcome"],
              "probes": probes, "hazard": mapping["hazard"], "finding": mapping["new"], "cause_gap": None}
        if mapping["hazard"] and not any(c.startswith(mapping["hazard"] + ":") for c in causes):
            ec["cause_gap"] = (f"{mapping['hazard']} lists no causal factor for {fam['fault']} "
                               f"(fault causes: {', '.join(causes)})")
        for msg in (ec["finding"], ec["cause_gap"]):
            if msg and msg not in [f["text"] for f in findings]:
                findings.append({"text": msg, "edge_cases": []})
            if msg:
                next(f for f in findings if f["text"] == msg)["edge_cases"].append(ec["id"])
        edges.append(ec)
    for j, f in enumerate(findings, 1):
        f["id"] = f"FND-{fam['id']}-{j:02d}"
    return {"family": {k: fam[k] for k in ("id", "title", "fault", "base", "space")}, "about": ABOUT,
            "spec_digest": spec.digest(), "monte_carlo": {"n": n, "by_outcome": by_outcome, "split": split},
            "falsification": {"evaluations": len(ce), "worst_rho": min(r["rho"] for r in ce)},
            "edge_cases": edges, "findings": findings,
            "map": [[round(r["params"]["slope_deg"], 2), round(r["params"]["tau_leak_s"], 3), r["outcome"]] for r in mc]}


def _dist(fam, a, b) -> float:
    cont = dims(fam["space"])[0]
    d = 0.0
    for k in cont:
        v = fam["space"][k]
        lo, hi = v.get("uniform") or v.get("loguniform")
        if "loguniform" in v:
            x, y, lo, hi = math.log(a[k]), math.log(b[k]), math.log(lo), math.log(hi)
        else:
            x, y = a[k], b[k]
        d += ((x - y) / (hi - lo)) ** 2
    return math.sqrt(d / len(cont))


# ---------------------------------------------------------------- pages

def family_page(res: dict) -> str:
    f, mc = res["family"], res["monte_carlo"]
    out = [f"# Failure search {f['id']} · {f['title']}\n\n",
           label_table("sim/search/search.py over sim/plant/walker.py", f"{f['id']} ({f['fault']})",
                       [("method", "seeded Monte Carlo + cross-entropy falsification")]), "\n",
           "## Monte Carlo\n\n",
           f"{mc['n']} uniform samples: " + ", ".join(f"{k} {v} ({100 * v / mc['n']:.1f}%)" for k, v in mc["by_outcome"].items()) + ".\n\n",
           "| Subset | Samples | Failures |\n|---|---|---|\n",
           "".join(f"| {k} | {v['n']} | {v['failures']} ({100 * v['failures'] / max(v['n'], 1):.1f}%) |\n" for k, v in mc["split"].items()),
           f"\nCross-entropy falsification: {res['falsification']['evaluations']} evaluations, worst rho "
           f"{res['falsification']['worst_rho']}.\n\nParameter space: " +
           "; ".join(f"`{k}` {v}" for k, v in f["space"].items()) + ".\n\n",
           "## Edge cases\n\n| ID | Parameters (rounded) | Outcome | rho | No fault | Hazard | Probes that change the outcome |\n"
           "|---|---|---|---|---|---|---|\n"]
    for e in res["edge_cases"]:
        flips = [f"{pr['name']} → {pr['outcome']}" for pr in e["probes"] if pr["outcome"] != e["outcome"]]
        out.append(f"| {e['id']} | {fmt_params(e['params'])} | **{e['outcome']}** | {e['rho']} | {e['nofault_outcome']} | "
                   f"{e['hazard'] or 'finding'} | {'; '.join(flips) or 'none'} |\n")
    out.append("\n## Findings for review\n\n")
    out += [f"- **{fd['id']}** ({', '.join(fd['edge_cases'])}): {fd['text']}\n" for fd in res["findings"]] or ["None.\n"]
    out.append("\nFindings are drafts for the safety lead: a new hazard or causal factor is added to the hazard records only "
               "through review (CLAUDE.md).\n")
    return "".join(out)


def edge_page(results: list) -> str:
    out = ["# Edge cases\n\n", f"> {ABOUT}\n\n",
           "| ID | Family | Outcome | Hazard / finding | Mishap (s) | Stop | Load holding |\n|---|---|---|---|---|---|---|\n"]
    for res in results:
        for e in res["edge_cases"]:
            out.append(f"| {e['id']} | {e['family']} | {e['outcome']} | {e['hazard'] or e['finding']} | "
                       f"{e['events']['mishap_t']} | {'yes' if e['stop_active'] else 'no'} | {e['params'].get('load_holding')} |\n")
    return "".join(out)


def outputs() -> dict:
    p = spec.load()
    fams = _read_yaml(FAMILIES)["families"]
    outs, results = {}, []
    for fam in fams:
        res = run_family(fam, p)
        results.append(res)
        outs[f"sim/results/search-{fam['id']}.json"] = dumps(res)
        outs[f"sim/results/search-{fam['id']}.md"] = family_page(res)
    outs["sim/results/edge-cases.md"] = edge_page(results)
    return outs


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    return write_or_check(outputs(), a.check, "python -m sim.search.search")


if __name__ == "__main__":
    sys.exit(main())
