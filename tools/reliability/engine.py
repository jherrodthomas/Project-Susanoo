"""Reliability engine: failure modes, fault trees, minimal cut sets, Monte Carlo and MIL-STD-882E probability bands.

Pure computation, standard library only (math, random). tools/reliability/build.py turns the results into the
generated page, figures and JSON.

Model, kept deliberately simple for the pilot:

- a failure mode is `rate` (per hour over the exposure T: 1 - exp(-rate * T)), `latent` (dormant failure found only
  by a test or a demand: rate * tau / 2, tau the test interval) or `demand` (probability per demand);
- `count: n` on an event or gate means n identical, independent copies, any one of which fails: 1 - (1 - p)^n;
- a `common_cause` event is the beta-factor share of its modes failing together: beta * sum(p_single);
- gates combine their inputs assuming independence (and: product; or: 1 - product of complements);
- an AND of an initiator over the item life and a probability on demand gives the probability of the top event
  over the item life, which is what the tailored bands (SUS-RISKDEF-001) are defined on.

Results are only as good as their inputs. While any input has status `assumed`, every result is illustrative.
"""
from __future__ import annotations

import math
import random
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

KINDS = {"rate", "latent", "demand"}
Z95 = 1.6448536269514722          # standard normal 95th percentile
BAND_ORDER = ["A", "B", "C", "D", "E"]


class ModelError(ValueError):
    """The reliability records are inconsistent."""


@dataclass
class Model:
    modes: dict[str, dict]
    parts: list[dict]
    params: dict[str, dict]
    trees: list[dict]
    hazard: str
    causal_factor: str
    exposure_key: str
    exposure_h: float
    bands: dict[str, float]            # band letter -> lower bound of probability over the item life
    assumed: list[str] = field(default_factory=list)   # ids of inputs still assumed

    def param(self, ref) -> float:
        if isinstance(ref, (int, float)):
            return float(ref)
        return float(self.params[ref]["value"])


# ---------------------------------------------------------------- loading and validation
def parse_bands(bands: dict) -> dict[str, float]:
    """Tailored band strings (">= 1e-1", "< 1e-1 and >= 1e-2", "< 1e-6") -> lower bound per band."""
    out = {}
    for k in BAND_ORDER:
        s = str(bands[k])
        m = re.search(r">=\s*([0-9.eE+-]+)", s)
        out[k] = float(m.group(1)) if m else 0.0
    if any(out[a] <= out[b] for a, b in zip(BAND_ORDER, BAND_ORDER[1:]) if b != "E"):
        raise ModelError(f"probability bands are not decreasing: {bands}")
    return out


def band_of(p: float, bands: dict[str, float]) -> str:
    for k in BAND_ORDER:
        if p >= bands[k]:
            return k
    return "E"


def load(root: Path) -> Model:
    parts_doc = yaml.safe_load((root / "reliability/parts.yaml").read_text(encoding="utf-8"))
    ft_doc = yaml.safe_load((root / "reliability/fault-trees.yaml").read_text(encoding="utf-8"))
    tail = yaml.safe_load((root / "standards/tailoring/mil-std-882e.yaml").read_text(encoding="utf-8"))
    prob = tail["risk_definitions"]["probability"]
    errors: list[str] = []

    modes: dict[str, dict] = {}
    assumed: list[str] = []
    for part in parts_doc["parts"]:
        for m in part["failure_modes"]:
            if m["id"] in modes:
                errors.append(f"duplicate failure mode {m['id']}")
            if not m["id"].startswith(part["id"] + "-"):
                errors.append(f"{m['id']} is not named after its part {part['id']}")
            if m.get("kind") not in KINDS:
                errors.append(f"{m['id']}: kind must be one of {sorted(KINDS)}")
            v = m.get("value")
            if not isinstance(v, (int, float)) or v <= 0 or (m.get("kind") == "demand" and v >= 1):
                errors.append(f"{m['id']}: value must be positive (and below 1 for a demand probability)")
            if not isinstance(m.get("error_factor"), (int, float)) or m["error_factor"] < 1:
                errors.append(f"{m['id']}: error_factor must be at least 1")
            if m.get("status") == "assumed":
                assumed.append(m["id"])
            modes[m["id"]] = {**m, "part": part["id"], "part_title": part["title"]}

    params = ft_doc.get("parameters") or {}
    assumed += [k for k, v in params.items() if v.get("status") == "assumed"]
    trees = ft_doc["trees"]
    for t in trees:
        nodes = {g["id"]: g for g in t["gates"]}
        for e in t["events"]:
            if e["id"] in nodes:
                errors.append(f"{t['id']}: {e['id']} is both a gate and an event")
            nodes[e["id"]] = e
        if t["top"] not in nodes:
            errors.append(f"{t['id']}: top {t['top']} is not a gate")
        for g in t["gates"]:
            if g.get("type") not in ("and", "or"):
                errors.append(f"{t['id']}/{g['id']}: type must be and or or")
            for i in g.get("inputs") or []:
                if i not in nodes:
                    errors.append(f"{t['id']}/{g['id']}: input {i} is not defined")
        for e in t["events"]:
            refs = e["modes"] if e.get("kind") == "common_cause" else [e.get("mode")]
            for r in refs:
                if r not in modes:
                    errors.append(f"{t['id']}/{e['id']}: unknown failure mode {r}")
        for n in list(t["gates"]) + list(t["events"]):
            for key in ("count", "beta"):
                ref = n.get(key)
                if isinstance(ref, str) and ref not in params:
                    errors.append(f"{t['id']}/{n['id']}: unknown parameter {ref}")
        # every node reachable once from the top, no cycles
        seen: set[str] = set()

        def walk(nid: str, path: tuple):
            if nid in path:
                errors.append(f"{t['id']}: cycle through {nid}")
                return
            seen.add(nid)
            for i in (nodes.get(nid) or {}).get("inputs") or []:
                walk(i, path + (nid,))
        if t["top"] in nodes:
            walk(t["top"], ())
        for nid in nodes:
            if nid not in seen:
                errors.append(f"{t['id']}: {nid} is not reached from the top")
    key = ft_doc["exposure"]
    if key not in prob["item_life"]:
        errors.append(f"exposure {key} is not in the tailoring item_life")
    if errors:
        raise ModelError("; ".join(errors))
    return Model(modes=modes, parts=parts_doc["parts"], params=params, trees=trees, hazard=ft_doc["hazard"],
                 causal_factor=ft_doc.get("causal_factor", ""), exposure_key=key,
                 exposure_h=float(prob["item_life"][key]), bands=parse_bands(prob["bands"]), assumed=assumed)


# ---------------------------------------------------------------- probabilities
def single(mode: dict, value: float, tau: float, T: float) -> float:
    """Probability that one part's mode has occurred when it matters, over exposure T with test interval tau."""
    if mode["kind"] == "rate":
        return -math.expm1(-value * T)
    if mode["kind"] == "latent":
        return min(1.0, value * tau / 2.0)
    return min(1.0, value)


def repeat(p: float, n: float) -> float:
    return -math.expm1(n * math.log1p(-p)) if p < 1 else 1.0


def event_p(m: Model, ev: dict, values: dict[str, float], tau: float) -> float:
    T = m.exposure_h
    if ev.get("kind") == "common_cause":
        return min(1.0, m.param(ev["beta"]) * sum(single(m.modes[x], values[x], tau, T) for x in ev["modes"]))
    p = single(m.modes[ev["mode"]], values[ev["mode"]], tau, T)
    return repeat(p, m.param(ev.get("count", 1)))


def tree_p(m: Model, tree: dict, values: dict[str, float], tau: float) -> dict[str, float]:
    """Probability of every node of a tree; the top is at tree['top']."""
    gates = {g["id"]: g for g in tree["gates"]}
    events = {e["id"]: e for e in tree["events"]}
    memo: dict[str, float] = {}

    def p(nid: str) -> float:
        if nid in memo:
            return memo[nid]
        if nid in events:
            r = event_p(m, events[nid], values, tau)
        else:
            g = gates[nid]
            ins = [p(i) for i in g["inputs"]]
            r = math.prod(ins) if g["type"] == "and" else 1.0 - math.prod(1.0 - x for x in ins)
            r = repeat(r, m.param(g.get("count", 1)))
        memo[nid] = r
        return r
    p(tree["top"])
    return memo


def cut_sets(m: Model, tree: dict) -> list[tuple[frozenset, float]]:
    """Minimal cut sets (top-down expansion) with the multiplicity from counted gates above them."""
    gates = {g["id"]: g for g in tree["gates"]}

    def expand(nid: str) -> list[tuple[frozenset, float]]:
        if nid not in gates:
            return [(frozenset([nid]), 1.0)]
        g = gates[nid]
        parts = [expand(i) for i in g["inputs"]]
        if g["type"] == "or":
            out = [cs for sub in parts for cs in sub]
        else:
            out = [(frozenset(), 1.0)]
            for sub in parts:
                out = [(a | b, ma * mb) for a, ma in out for b, mb in sub]
        n = m.param(g.get("count", 1))
        return [(s, mult * n) for s, mult in out]
    raw = expand(tree["top"])
    best: dict[frozenset, float] = {}
    for s, mult in raw:
        best[s] = max(best.get(s, 0.0), mult)
    sets = sorted(best, key=lambda s: (len(s), sorted(s)))
    minimal = [s for s in sets if not any(o < s for o in sets)]
    return [(s, best[s]) for s in minimal]


def nominal_values(m: Model) -> dict[str, float]:
    return {k: float(v["value"]) for k, v in m.modes.items()}


def analyse(m: Model, tree: dict, n_mc: int = 4000, seed: int = 1) -> dict:
    tau = m.param("test_interval_h") if "test_interval_h" in m.params else m.exposure_h
    nominal = nominal_values(m)
    pts = tree_p(m, tree, nominal, tau)
    top = pts[tree["top"]]
    no_test = tree_p(m, tree, nominal, m.exposure_h)[tree["top"]]

    # minimal cut sets, rare-event approximation for their contribution
    rows = []
    for s, mult in cut_sets(m, tree):
        pr = mult * math.prod(pts[e] for e in s)
        rows.append({"events": sorted(s), "multiplicity": mult, "p": pr})
    total = sum(r["p"] for r in rows) or 1.0
    for r in rows:
        r["share"] = r["p"] / total
    rows.sort(key=lambda r: -r["p"])

    # drivers: the top probability when one mode's value is multiplied by its error factor
    used = sorted({e["mode"] for e in tree["events"] if "mode" in e}
                  | {x for e in tree["events"] if e.get("kind") == "common_cause" for x in e["modes"]})
    drivers = []
    for mid in used:
        v = dict(nominal)
        ef = float(m.modes[mid]["error_factor"])
        v[mid] = min(nominal[mid] * ef, 0.999999) if m.modes[mid]["kind"] == "demand" else nominal[mid] * ef
        drivers.append({"mode": mid, "factor": tree_p(m, tree, v, tau)[tree["top"]] / top})
    drivers.sort(key=lambda d: -d["factor"])

    # what the top driver alone would have to become for the top event to fall below band D (into E)
    target = m.bands["D"]
    reach = None
    if drivers and top >= target:
        mid = drivers[0]["mode"]

        def at(f: float) -> float:
            v = dict(nominal)
            v[mid] = nominal[mid] * f
            return tree_p(m, tree, v, tau)[tree["top"]]
        if at(1e-9) < target:
            lo, hi = 1e-9, 1.0
            for _ in range(80):
                mid_f = math.sqrt(lo * hi)
                lo, hi = (lo, mid_f) if at(mid_f) >= target else (mid_f, hi)
            reach = {"mode": mid, "factor": lo, "value": nominal[mid] * lo}   # largest factor still below band D
        else:
            reach = {"mode": mid, "factor": None, "value": None}

    # Monte Carlo over the lognormal uncertainty of every mode (one sample per mode, shared by its events)
    rng = random.Random(seed)
    samples = []
    for _ in range(n_mc):
        v = {}
        for mid in used:
            sigma = math.log(float(m.modes[mid]["error_factor"])) / Z95
            x = nominal[mid] * math.exp(rng.gauss(0.0, sigma))
            v[mid] = min(x, 0.999999) if m.modes[mid]["kind"] == "demand" else x
        samples.append(tree_p(m, tree, {**nominal, **v}, tau)[tree["top"]])
    samples.sort()

    def q(f: float) -> float:
        return samples[min(len(samples) - 1, int(f * len(samples)))]
    shares = {k: sum(1 for s in samples if band_of(s, m.bands) == k) / len(samples) for k in BAND_ORDER}
    return {"tree": tree["id"], "alternative": tree["alternative"], "title": tree["title"], "top": top,
            "band": band_of(top, m.bands), "no_test": no_test, "no_test_band": band_of(no_test, m.bands),
            "mc": {"n": n_mc, "seed": seed, "p05": q(0.05), "p50": q(0.50), "p95": q(0.95), "band_share": shares},
            "nodes": pts, "cut_sets": rows, "drivers": drivers, "reach_e": reach, "tau_h": tau}
