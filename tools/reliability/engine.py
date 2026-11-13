"""Reliability engine: failure modes, fault trees, minimal cut sets, Monte Carlo and MIL-STD-882E probability bands.

Pure computation, standard library only (math, random). tools/reliability/build.py turns the results into the
generated page, figures and JSON.

Model, kept deliberately simple:

- a failure mode is `rate` (per hour over an exposure in hours: 1 - exp(-rate * T)), `cycle` (per cycle over an
  exposure in cycles: 1 - (1 - q)^N), `latent` (dormant failure found only by a check or a demand: rate * tau / 2,
  tau the check interval) or `demand` (probability per demand);
- `count: n` on an event or gate means n identical, independent copies, any one of which fails: 1 - (1 - p)^n;
- a `common_cause` event is the beta-factor share of its modes failing together: beta * sum(p_single);
- an `undeveloped` event (software, human, environment, interface, systematic, or hardware with no data) is shown
  and traced to its causal factor but never given a number. The quantified probability treats it as 0, so it covers
  only the cut sets made of hardware failure modes: a lower bound. Cut sets that hold an undeveloped event are
  reported separately, with the probability of the hardware defences in them;
- gates combine their inputs assuming independence (and: product; or: 1 - product of complements).

Results are only as good as their inputs. While any input has status `assumed`, every result is illustrative.
"""
from __future__ import annotations

import math
import random
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

KINDS = {"rate", "cycle", "latent", "demand"}
NATURES = {"software", "human", "environment", "interface", "systematic", "hardware"}
Z95 = 1.6448536269514722          # standard normal 95th percentile
BAND_ORDER = ["A", "B", "C", "D", "E"]


class ModelError(ValueError):
    """The reliability records are inconsistent."""


@dataclass
class Model:
    modes: dict[str, dict]
    parts: list[dict]
    params: dict[str, dict]
    trees: list[dict]                  # each tree carries hazard, exposure and its file's notes
    hazards: dict[str, dict]           # hazard id -> hazard record
    files: dict[str, dict]             # hazard id -> its fault-tree file (exposure, not_modelled, note)
    item_life: dict[str, float]
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
        m = re.search(r">=\s*([0-9.eE+-]+)", str(bands[k]))
        out[k] = float(m.group(1)) if m else 0.0
    if any(out[a] <= out[b] for a, b in zip(BAND_ORDER, BAND_ORDER[1:]) if b != "E"):
        raise ModelError(f"probability bands are not decreasing: {bands}")
    return out


def band_of(p: float, bands: dict[str, float]) -> str:
    for k in BAND_ORDER:
        if p >= bands[k]:
            return k
    return "E"


def unit_of(exposure_key: str) -> str:
    return "cycles" if exposure_key.endswith("_cycles") else "hours"


def load(root: Path) -> Model:
    rel = root / "reliability"
    parts_doc = yaml.safe_load((rel / "parts.yaml").read_text(encoding="utf-8"))
    params = (yaml.safe_load((rel / "parameters.yaml").read_text(encoding="utf-8")) or {}).get("parameters") or {}
    tail = yaml.safe_load((root / "standards/tailoring/mil-std-882e.yaml").read_text(encoding="utf-8"))
    prob = tail["risk_definitions"]["probability"]
    item_life = {k: float(v) for k, v in prob["item_life"].items()}
    ssfs = {p.stem for p in (root / "safety/software").glob("SSF-*.yaml")}
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
            if not isinstance(v, (int, float)) or v <= 0 or (m.get("kind") in ("demand", "cycle") and v >= 1):
                errors.append(f"{m['id']}: value must be positive (and below 1 for a probability)")
            if not isinstance(m.get("error_factor"), (int, float)) or m["error_factor"] < 1:
                errors.append(f"{m['id']}: error_factor must be at least 1")
            if m.get("status") == "assumed":
                assumed.append(m["id"])
            modes[m["id"]] = {**m, "part": part["id"], "part_title": part["title"]}
    assumed += [k for k, v in params.items() if v.get("status") == "assumed"]

    trees: list[dict] = []
    hazards: dict[str, dict] = {}
    files: dict[str, dict] = {}
    seen_ids: set[str] = set()
    for f in sorted(rel.glob("HAZ-*.yaml")):
        doc = yaml.safe_load(f.read_text(encoding="utf-8"))
        hid = doc.get("hazard")
        if hid != f.stem:
            errors.append(f"{f.name}: hazard {hid} does not match the file name")
            continue
        hp = root / "safety/hazards" / f"{hid}.yaml"
        if not hp.exists():
            errors.append(f"{f.name}: no hazard record {hid}")
            continue
        hz = yaml.safe_load(hp.read_text(encoding="utf-8"))
        hazards[hid] = hz
        files[hid] = doc
        cfs = {c["id"] for c in hz.get("causal_factors") or []}
        if doc.get("exposure") not in item_life:
            errors.append(f"{f.name}: exposure {doc.get('exposure')} is not in the tailoring item_life")
            continue
        covered = set(doc.get("not_modelled") or {})
        for cf in covered - cfs:
            errors.append(f"{f.name}: not_modelled names {cf}, which {hid} does not have")
        for t in doc.get("trees") or []:
            t = {**t, "hazard": hid, "exposure": doc["exposure"]}
            if t["id"] in seen_ids:
                errors.append(f"duplicate tree id {t['id']}")
            seen_ids.add(t["id"])
            covered |= set(t.get("causal_factors") or [])
            errors += _check_tree(t, modes, params, item_life, ssfs, cfs, covered)
            trees.append(t)
        for cf in sorted(cfs - covered):
            errors.append(f"{f.name}: causal factor {cf} of {hid} is neither in a tree nor listed under not_modelled")
    if errors:
        raise ModelError("; ".join(errors))
    return Model(modes=modes, parts=parts_doc["parts"], params=params, trees=trees, hazards=hazards, files=files,
                 item_life=item_life, bands=parse_bands(prob["bands"]), assumed=assumed)


def _check_tree(t, modes, params, item_life, ssfs, cfs, covered) -> list[str]:
    errors = []
    tid = t["id"]
    nodes = {g["id"]: g for g in t.get("gates") or []}
    for e in t.get("events") or []:
        if e["id"] in nodes:
            errors.append(f"{tid}: {e['id']} is both a gate and an event")
        nodes[e["id"]] = e
    if t.get("top") not in nodes or t.get("top") not in {g["id"] for g in t.get("gates") or []}:
        errors.append(f"{tid}: top {t.get('top')} is not a gate")
        return errors
    gate_keys = {"id", "type", "count", "title", "inputs"}
    event_keys = {"id", "title", "mode", "count", "kind", "nature", "causal_factor", "ssf", "modes", "beta", "exposure"}
    for g in t["gates"]:
        if set(g) - gate_keys:
            errors.append(f"{tid}/{g['id']}: unknown keys {sorted(set(g) - gate_keys)} (an unquoted comma in a title?)")
    for e in t["events"]:
        if set(e) - event_keys:
            errors.append(f"{tid}/{e['id']}: unknown keys {sorted(set(e) - event_keys)} (an unquoted comma in a title?)")
    for g in t["gates"]:
        if g.get("type") not in ("and", "or"):
            errors.append(f"{tid}/{g['id']}: type must be and or or")
        for i in g.get("inputs") or []:
            if i not in nodes:
                errors.append(f"{tid}/{g['id']}: input {i} is not defined")
    for e in t["events"]:
        kind = e.get("kind")
        cf = e.get("causal_factor")
        if cf is not None:
            if cf not in cfs:
                errors.append(f"{tid}/{e['id']}: causal factor {cf} is not in {t['hazard']}")
            covered.add(cf)
        if kind == "undeveloped":
            if e.get("nature") not in NATURES:
                errors.append(f"{tid}/{e['id']}: nature must be one of {sorted(NATURES)}")
            if cf is None:
                errors.append(f"{tid}/{e['id']}: an undeveloped event must name its causal factor")
            if e.get("ssf") and e["ssf"] not in ssfs:
                errors.append(f"{tid}/{e['id']}: unknown SSF {e['ssf']}")
            continue
        refs = e["modes"] if kind == "common_cause" else [e.get("mode")]
        for r in refs:
            if r not in modes:
                errors.append(f"{tid}/{e['id']}: unknown failure mode {r}")
                continue
            exp = e.get("exposure", t["exposure"])
            if exp not in item_life:
                errors.append(f"{tid}/{e['id']}: exposure {exp} is not in the tailoring item_life")
            elif modes[r]["kind"] == "rate" and unit_of(exp) != "hours":
                errors.append(f"{tid}/{e['id']}: a per-hour mode needs an exposure in hours, not {exp}")
            elif modes[r]["kind"] == "cycle" and unit_of(exp) != "cycles":
                errors.append(f"{tid}/{e['id']}: a per-cycle mode needs an exposure in cycles, not {exp}")
    for n in list(t["gates"]) + list(t["events"]):
        for key in ("count", "beta"):
            ref = n.get(key)
            if isinstance(ref, str) and ref not in params:
                errors.append(f"{tid}/{n['id']}: unknown parameter {ref}")
    seen: set[str] = set()

    def walk(nid: str, path: tuple):
        if nid in path:
            errors.append(f"{tid}: cycle through {nid}")
            return
        seen.add(nid)
        for i in (nodes.get(nid) or {}).get("inputs") or []:
            walk(i, path + (nid,))
    walk(t["top"], ())
    for nid in nodes:
        if nid not in seen:
            errors.append(f"{tid}: {nid} is not reached from the top")
    return errors


# ---------------------------------------------------------------- probabilities
def single(mode: dict, value: float, tau: float, T: float) -> float:
    """Probability that one part's mode has occurred when it matters, over exposure T with check interval tau."""
    k = mode["kind"]
    if k == "rate":
        return -math.expm1(-value * T)
    if k == "cycle":
        return -math.expm1(T * math.log1p(-value))
    if k == "latent":
        return min(1.0, value * tau / 2.0)
    return min(1.0, value)


def repeat(p: float, n: float) -> float:
    return -math.expm1(n * math.log1p(-p)) if p < 1 else 1.0


def is_undeveloped(ev: dict) -> bool:
    return ev.get("kind") == "undeveloped"


def event_p(m: Model, tree: dict, ev: dict, values: dict[str, float], tau: float, undev: float = 0.0) -> float:
    if is_undeveloped(ev):
        return undev
    T = m.item_life[ev.get("exposure", tree["exposure"])]
    if ev.get("kind") == "common_cause":
        return min(1.0, m.param(ev["beta"]) * sum(single(m.modes[x], values[x], tau, T) for x in ev["modes"]))
    p = single(m.modes[ev["mode"]], values[ev["mode"]], tau, T)
    return repeat(p, m.param(ev.get("count", 1)))


def tree_p(m: Model, tree: dict, values: dict[str, float], tau: float, undev: float = 0.0) -> dict[str, float]:
    """Probability of every node of a tree; the top is at tree['top']. Undeveloped events count as `undev`."""
    gates = {g["id"]: g for g in tree["gates"]}
    events = {e["id"]: e for e in tree["events"]}
    memo: dict[str, float] = {}

    def p(nid: str) -> float:
        if nid in memo:
            return memo[nid]
        if nid in events:
            r = event_p(m, tree, events[nid], values, tau, undev)
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
    best: dict[frozenset, float] = {}
    for s, mult in expand(tree["top"]):
        best[s] = max(best.get(s, 0.0), mult)
    sets = sorted(best, key=lambda s: (len(s), sorted(s)))
    minimal = [s for s in sets if not any(o < s for o in sets)]
    return [(s, best[s]) for s in minimal]


def nominal_values(m: Model) -> dict[str, float]:
    return {k: float(v["value"]) for k, v in m.modes.items()}


def modes_used(tree: dict) -> list[str]:
    return sorted({e["mode"] for e in tree["events"] if "mode" in e}
                  | {x for e in tree["events"] if e.get("kind") == "common_cause" for x in e["modes"]})


def analyse(m: Model, tree: dict, n_mc: int = 4000, seed: int = 1) -> dict:
    tau = m.param("test_interval_h") if "test_interval_h" in m.params else m.item_life[tree["exposure"]]
    nominal = nominal_values(m)
    events = {e["id"]: e for e in tree["events"]}
    pts = tree_p(m, tree, nominal, tau)
    top = pts[tree["top"]]
    used = modes_used(tree)
    has_latent = any(m.modes[x]["kind"] == "latent" for x in used)
    no_test = tree_p(m, tree, nominal, m.item_life[tree["exposure"]])[tree["top"]] if has_latent else None

    # minimal cut sets: fully quantified (rare-event share), mixed (hardware defence behind an undeveloped event),
    # unquantified (undeveloped events only)
    rows = []
    for s, mult in cut_sets(m, tree):
        undev = sorted(e for e in s if is_undeveloped(events[e]))
        hw = sorted(e for e in s if not is_undeveloped(events[e]))
        hw_p = mult * math.prod(pts[e] for e in hw) if hw else None
        kind = "quantified" if not undev else ("mixed" if hw else "unquantified")
        rows.append({"events": sorted(s), "undeveloped": undev, "hardware": hw, "multiplicity": mult,
                     "p": hw_p if kind == "quantified" else None, "defence_p": hw_p if kind == "mixed" else None,
                     "kind": kind})
    total = sum(r["p"] for r in rows if r["p"]) or 1.0
    for r in rows:
        r["share"] = (r["p"] / total) if r["p"] else None
    order = {"unquantified": 0, "mixed": 1, "quantified": 2}
    rows.sort(key=lambda r: (order[r["kind"]], -(r["p"] or r["defence_p"] or 0), r["events"]))

    natures = {}
    for e in tree["events"]:
        if is_undeveloped(e):
            natures[e["nature"]] = natures.get(e["nature"], 0) + 1

    res = {"tree": tree["id"], "hazard": tree["hazard"], "alternative": tree.get("alternative"),
           "title": tree["title"], "exposure": tree["exposure"], "exposure_value": m.item_life[tree["exposure"]],
           "top": top, "quantified": top > 0, "band": band_of(top, m.bands) if top > 0 else None,
           "no_test": no_test, "no_test_band": band_of(no_test, m.bands) if no_test else None,
           "nodes": pts, "cut_sets": rows, "undeveloped": natures, "tau_h": tau,
           "single_points": [r["events"][0] for r in rows if r["kind"] == "unquantified" and len(r["events"]) == 1],
           "drivers": [], "reach_e": None, "mc": None}
    if top <= 0:
        return res

    # drivers: the quantified top when one mode's value is multiplied by its error factor
    drivers = []
    for mid in used:
        v = dict(nominal)
        ef = float(m.modes[mid]["error_factor"])
        v[mid] = min(nominal[mid] * ef, 0.999999) if m.modes[mid]["kind"] in ("demand", "cycle") else nominal[mid] * ef
        drivers.append({"mode": mid, "factor": tree_p(m, tree, v, tau)[tree["top"]] / top})
    drivers.sort(key=lambda d: (-d["factor"], d["mode"]))
    res["drivers"] = drivers

    # what the top driver alone would have to become for the quantified top to fall below band D (into E)
    target = m.bands["D"]
    if top >= target:
        mid = drivers[0]["mode"]

        def at(f: float) -> float:
            v = dict(nominal)
            v[mid] = nominal[mid] * f
            return tree_p(m, tree, v, tau)[tree["top"]]
        if at(1e-9) < target:
            lo, hi = 1e-9, 1.0
            for _ in range(80):
                mf = math.sqrt(lo * hi)
                lo, hi = (lo, mf) if at(mf) >= target else (mf, hi)
            res["reach_e"] = {"mode": mid, "factor": lo, "value": nominal[mid] * lo}   # largest factor below band D
        else:
            res["reach_e"] = {"mode": mid, "factor": None, "value": None}

    # Monte Carlo over the lognormal uncertainty of every quantified mode (one draw per mode, shared by its events)
    rng = random.Random(seed)
    samples = []
    for _ in range(n_mc):
        v = dict(nominal)
        for mid in used:
            sigma = math.log(float(m.modes[mid]["error_factor"])) / Z95
            x = nominal[mid] * math.exp(rng.gauss(0.0, sigma))
            v[mid] = min(x, 0.999999) if m.modes[mid]["kind"] in ("demand", "cycle") else x
        samples.append(tree_p(m, tree, v, tau)[tree["top"]])
    samples.sort()

    def q(f: float) -> float:
        return samples[min(len(samples) - 1, int(f * len(samples)))]
    res["mc"] = {"n": n_mc, "seed": seed, "p05": q(0.05), "p50": q(0.50), "p95": q(0.95),
                 "band_share": {k: sum(1 for s in samples if band_of(s, m.bands) == k) / len(samples) for k in BAND_ORDER}}
    return res
