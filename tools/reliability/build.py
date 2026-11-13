"""Build the reliability pilot outputs from reliability/ and the tailoring.

    python -m tools.reliability.build            # write the outputs
    python -m tools.reliability.build --check    # fail if any output is stale

Outputs (generated; never edit by hand):

- docs/wiki/Reliability-Pilot.md          results page: bands, cut sets, drivers, inputs
- docs/wiki/images/rel-bands.svg          the three alternatives against the tailored probability bands
- docs/wiki/images/rel-ft-00n.svg         one fault-tree drawing per tree
- safety/generated/reliability.json       the numbers behind the page

While any input is `status: assumed`, everything here is illustrative: not evidence, not a probability rating, and
never written back into a hazard record. Proposing a hazard's probability stays with the safety lead (R13).
"""
from __future__ import annotations

import argparse
import html
import json
import math
import sys
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.reliability import engine  # noqa: E402
from tools.terms.terms import decorate  # noqa: E402

import yaml  # noqa: E402

GEN = "tools/reliability/build.py"
PAGE = "docs/wiki/Reliability-Pilot.md"
BANDS_SVG = "docs/wiki/images/rel-bands.svg"
JSON_OUT = "safety/generated/reliability.json"
INK, MUTED, LINE, ACCENT, WARN = "#152033", "#566275", "#cfd7e2", "#2a55a8", "#b54708"
FONT = "Inter, 'Segoe UI', Helvetica, Arial, sans-serif"


def sci(p: float) -> str:
    """Two significant figures in plain text: 1.23e-05 -> 1.2e-5."""
    if p == 0:
        return "0"
    m, e = f"{p:.1e}".split("e")
    return f"{m}e{int(e)}"


def tree_svg_name(tid: str) -> str:
    return f"docs/wiki/images/rel-{tid.lower()}.svg"


# ---------------------------------------------------------------- fault-tree drawing
def tree_svg(m: engine.Model, tree: dict, res: dict) -> str:
    gates = {g["id"]: g for g in tree["gates"]}
    events = {e["id"]: e for e in tree["events"]}
    pos: dict[str, tuple[float, int]] = {}
    xs = [0.0]
    COL, ROW, BW, BH = 200, 150, 184, 50

    def place(nid: str, depth: int) -> float:
        if nid in gates:
            cx = [place(i, depth + 1) for i in gates[nid]["inputs"]]
            x = sum(cx) / len(cx)
        else:
            x = xs[0]
            xs[0] += COL
        pos[nid] = (x, depth)
        return x
    place(tree["top"], 0)
    W = int(xs[0]) + 40
    depth = max(d for _, d in pos.values())
    H = 70 + (depth + 1) * ROW
    e = html.escape
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" font-family="{FONT}">',
         f'<rect width="{W}" height="{H}" fill="#ffffff"/>',
         f'<text x="20" y="26" font-size="16" font-weight="700" fill="{INK}">{e(tree["id"])} · {e(tree["title"])}</text>',
         f'<text x="20" y="46" font-size="12" fill="{MUTED}">Probability over the item life ({int(m.exposure_h)} walker operating hours), '
         f'holding devices checked every {res["tau_h"]:g} h. Illustrative: inputs assumed.</text>']

    def xy(nid):
        x, d = pos[nid]
        return x + 20 + COL / 2, 64 + d * ROW
    for gid, g in gates.items():
        px, py = xy(gid)
        for i in g["inputs"]:
            cx, cy = xy(i)
            o.append(f'<path d="M{px} {py + BH + 34} V{py + BH + 50} H{cx} V{cy}" fill="none" stroke="{LINE}" stroke-width="1.5"/>')
    for nid, (x, d) in pos.items():
        cx, cy = xy(nid)
        node = gates.get(nid) or events[nid]
        o.append(f'<rect x="{cx - BW / 2}" y="{cy}" width="{BW}" height="{BH}" rx="3" fill="#ffffff" stroke="{INK}" stroke-width="1.2"/>')
        lines = textwrap.wrap(node["title"], 30)[:2]
        for k, ln in enumerate(lines):
            o.append(f'<text x="{cx}" y="{cy + 16 + k * 14}" font-size="11.5" fill="{INK}" text-anchor="middle">{e(ln)}</text>')
        sub = node.get("mode") or ("common cause" if node.get("kind") == "common_cause" else node["type"])
        o.append(f'<text x="{cx}" y="{cy + BH - 6}" font-size="10.5" fill="{MUTED}" text-anchor="middle">{e(sub)} · p {e(sci(res["nodes"][nid]))}</text>')
        sy = cy + BH + 2
        if nid in gates:
            if node["type"] == "and":
                o.append(f'<path d="M{cx - 13} {sy + 30} V{sy + 12} A13 13 0 0 1 {cx + 13} {sy + 12} V{sy + 30} Z" fill="#ffffff" stroke="{ACCENT}" stroke-width="1.6"/>')
            else:
                o.append(f'<path d="M{cx - 14} {sy + 30} Q{cx - 14} {sy + 8} {cx} {sy} Q{cx + 14} {sy + 8} {cx + 14} {sy + 30} Q{cx} {sy + 22} {cx - 14} {sy + 30} Z" fill="#ffffff" stroke="{ACCENT}" stroke-width="1.6"/>')
        elif node.get("kind") == "common_cause":
            o.append(f'<path d="M{cx} {sy + 2} L{cx + 13} {sy + 16} L{cx} {sy + 30} L{cx - 13} {sy + 16} Z" fill="#ffffff" stroke="{WARN}" stroke-width="1.6"/>')
        else:
            o.append(f'<circle cx="{cx}" cy="{sy + 16}" r="13" fill="#ffffff" stroke="{INK}" stroke-width="1.4"/>')
        n = node.get("count")
        if n is not None:
            o.append(f'<text x="{cx + 20}" y="{sy + 21}" font-size="12" font-weight="700" fill="{ACCENT}">×{int(m.param(n))}</text>')
    lg = H - 22
    o.append(f'<text x="20" y="{lg}" font-size="11.5" fill="{MUTED}">Dome: all inputs (and). Shield: any input (or). '
             f'Circle: basic event. Diamond: common-cause share. ×n: n identical copies, any one fails.</text>')
    o.append("</svg>")
    return "\n".join(o) + "\n"


# ---------------------------------------------------------------- bands chart
def bands_svg(m: engine.Model, results: list[dict], hazard: dict) -> str:
    W, L, R = 980, 170, 30
    lo, hi = -9, 0
    rows = len(results)
    H = 150 + rows * 56
    e = html.escape

    def X(p: float) -> float:
        p = max(p, 10 ** lo)
        return L + (math.log10(p) - lo) / (hi - lo) * (W - L - R)
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" font-family="{FONT}">',
         f'<rect width="{W}" height="{H}" fill="#ffffff"/>',
         f'<text x="20" y="26" font-size="16" font-weight="700" fill="{INK}">{e(m.hazard)} cockpit drop: probability over the item life by actuation alternative</text>',
         f'<text x="20" y="46" font-size="12" fill="{MUTED}">Illustrative: every input is an assumed order-of-magnitude value. '
         f'Bands from the tailored risk definitions; not a probability rating.</text>']
    top, bot = 64, 64 + rows * 56 + 10
    edges = [(k, m.bands[k], (m.bands[prev] if prev else 1.0)) for prev, k in zip([None] + engine.BAND_ORDER, engine.BAND_ORDER)]
    shade = ["#f4f6f9", "#ffffff"]
    target = (hazard.get("target_risk") or {}).get("probability")
    for i, (k, lower, upper) in enumerate(edges):
        x0, x1 = X(lower if lower > 0 else 10 ** lo), X(upper)
        fill = "#eaf4ee" if k == target else shade[i % 2]
        o.append(f'<rect x="{x0:.1f}" y="{top}" width="{x1 - x0:.1f}" height="{bot - top}" fill="{fill}"/>')
        o.append(f'<text x="{(x0 + x1) / 2:.1f}" y="{top + 14}" font-size="12" font-weight="700" fill="{MUTED}" text-anchor="middle">'
                 f'{k}{" (target)" if k == target else ""}</text>')
        if lower > 0:
            o.append(f'<line x1="{x0:.1f}" x2="{x0:.1f}" y1="{top}" y2="{bot}" stroke="{LINE}"/>')
    for ex in range(lo, hi + 1):
        x = X(10 ** ex)
        o.append(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{bot}" y2="{bot + 5}" stroke="{MUTED}"/>'
                 f'<text x="{x:.1f}" y="{bot + 18}" font-size="11" fill="{MUTED}" text-anchor="middle">1e{ex}</text>')
    for i, r in enumerate(results):
        y = top + 34 + i * 56
        o.append(f'<text x="{L - 12}" y="{y + 4}" font-size="13" font-weight="600" fill="{INK}" text-anchor="end">{e(r["alternative"])}</text>')
        o.append(f'<text x="{L - 12}" y="{y + 18}" font-size="10.5" fill="{MUTED}" text-anchor="end">{e(r["tree"])}</text>')
        mc = r["mc"]
        o.append(f'<line x1="{X(mc["p05"]):.1f}" x2="{X(mc["p95"]):.1f}" y1="{y}" y2="{y}" stroke="{ACCENT}" stroke-width="3" stroke-linecap="round" opacity=".45"/>')
        o.append(f'<circle cx="{X(r["no_test"]):.1f}" cy="{y}" r="6" fill="#ffffff" stroke="{WARN}" stroke-width="2"/>')
        o.append(f'<circle cx="{X(r["top"]):.1f}" cy="{y}" r="6.5" fill="{ACCENT}" stroke="#ffffff" stroke-width="2"/>')
        o.append(f'<text x="{X(r["top"]) + 10:.1f}" y="{y - 9}" font-size="11" fill="{INK}">{e(sci(r["top"]))} · band {r["band"]}</text>')
    ly = bot + 44
    o.append(f'<circle cx="26" cy="{ly - 4}" r="6" fill="{ACCENT}"/><text x="38" y="{ly}" font-size="11.5" fill="{MUTED}">checked before every sortie</text>'
             f'<circle cx="236" cy="{ly - 4}" r="6" fill="#ffffff" stroke="{WARN}" stroke-width="2"/><text x="248" y="{ly}" font-size="11.5" fill="{MUTED}">never checked</text>'
             f'<line x1="372" x2="400" y1="{ly - 4}" y2="{ly - 4}" stroke="{ACCENT}" stroke-width="3" opacity=".45"/>'
             f'<text x="408" y="{ly}" font-size="11.5" fill="{MUTED}">5th to 95th percentile of the input uncertainty (Monte Carlo)</text>')
    o.append("</svg>")
    return "\n".join(o) + "\n"


# ---------------------------------------------------------------- page
def page(m: engine.Model, results: list[dict], hazard: dict) -> str:
    ir, tr = hazard.get("initial_risk") or {}, hazard.get("target_risk") or {}
    n_assumed = len(m.assumed)
    out = [f"<!-- GENERATED by {GEN} from reliability/ and standards/tailoring/mil-std-882e.yaml. Do not edit by hand. -->\n",
           "# Reliability Pilot\n",
           f"> **Illustrative.** All {n_assumed} inputs (failure-mode values and tree parameters) are assumed order-of-magnitude "
           "placeholders drafted by an AI at independence I0, not handbook or supplier data. Nothing here is evidence, a "
           "probability rating or a risk acceptance, and nothing is written back into a hazard record.\n",
           f"The pilot asks how likely the top event of **{m.hazard} {m.causal_factor}** is over the item life, for each "
           "TS-001 actuation alternative: leg support is lost suddenly and the load-holding device does not hold, so the "
           f"cockpit drops with the pilot aboard. The exposure is the tailored item life of {int(m.exposure_h)} walker "
           "operating hours, and the result is placed in the tailored probability bands (SUS-RISKDEF-001). The hazard's "
           f"current rating is {ir.get('rac', '?')} (probability {ir.get('probability', '?')}); its target is "
           f"{tr.get('rac', '?')} (probability {tr.get('probability', '?')}).\n",
           f"![Probability of the cockpit drop by alternative](images/{Path(BANDS_SVG).name})\n",
           "## Results\n",
           "| Alternative | Tree | Checked every sortie | Never checked | Monte Carlo 5th / 50th / 95th | Samples per band (C / D / E) |",
           "|---|---|---|---|---|---|"]
    for r in results:
        s = r["mc"]["band_share"]
        out.append(f"| {r['alternative']} | {r['tree']} | {sci(r['top'])} (band {r['band']}) | {sci(r['no_test'])} "
                   f"(band {r['no_test_band']}) | {sci(r['mc']['p05'])} / {sci(r['mc']['p50'])} / {sci(r['mc']['p95'])} | "
                   f"{s['C']:.0%} / {s['D']:.0%} / {s['E']:.0%} |")
    out.append("")
    out.append("**What the numbers say, with these assumed inputs:**\n")
    for r in results:
        top = r["cut_sets"][0]
        d = r["drivers"][0]
        line = (f"- **{r['alternative']}:** {top['share']:.0%} of the result is the cut set "
                f"{' + '.join(top['events'])}{' (any of ' + str(int(top['multiplicity'])) + ' joints)' if top['multiplicity'] > 1 else ''}. "
                f"The biggest driver is {d['mode']} ({m.modes[d['mode']]['mode'].split(' (')[0].lower()}): "
                f"its error factor moves the result ×{d['factor']:.1f}.")
        rc = r.get("reach_e")
        if rc and rc["factor"] is not None:
            line += (f" Band {tr.get('probability', 'E')} needs it at or below {sci(rc['value'])} "
                     f"{m.modes[rc['mode']]['unit']} (about {rc['factor']:.2g} times the assumed value), other inputs unchanged.")
        elif rc:
            line += f" No value of {rc['mode']} alone reaches band {tr.get('probability', 'E')}: another cut set limits it."
        out.append(line)
    out.append("- **Checking the holding devices before every sortie** removes most of the dormant-failure contribution "
               "(compare the two columns); the on-demand failure is not affected by testing.\n")
    for r in results:
        t = next(x for x in m.trees if x["id"] == r["tree"])
        out += [f"## {t['id']} · {t['alternative']}\n", f"![{t['id']}](images/{Path(tree_svg_name(t['id'])).name})\n",
                "| Minimal cut set | Copies | Probability | Share |", "|---|---|---|---|"]
        for c in r["cut_sets"]:
            out.append(f"| {' + '.join(c['events'])} | {int(c['multiplicity'])} | {sci(c['p'])} | {c['share']:.1%} |")
        out += ["", "| Failure mode | Result × when the mode is × its error factor |", "|---|---|"]
        out += [f"| {d['mode']} | ×{d['factor']:.2f} |" for d in r["drivers"]]
        out.append("")
    out += ["## Inputs\n", "| Failure mode | Part | Mode | Kind | Value | Error factor | Status | Where a sourced value should come from |",
            "|---|---|---|---|---|---|---|---|"]
    for mid, md in m.modes.items():
        out.append(f"| {mid} | {md['part_title']} | {md['mode']} | {md['kind']} | {sci(md['value'])} {md['unit']} | "
                   f"{md['error_factor']:g} | {md['status']} | {md['to_source']} |")
    out += ["", "| Parameter | Value | Status | Note |", "|---|---|---|---|"]
    out += [f"| {k} | {v['value']:g} | {v['status']} | {v['note']} |" for k, v in m.params.items()]
    out += ["", "## How the numbers are computed\n",
            f"- `rate` modes give 1 − e^(−λ T) over T = {int(m.exposure_h)} h; `latent` modes give λ τ / 2 with τ the "
            "check interval (or the whole item life when never checked); `demand` modes give their probability per demand.",
            "- `×n` means n identical, independent copies, any one of which fails: 1 − (1 − p)^n.",
            "- The common-cause event is the beta-factor share of the holding-device modes; the independent events are "
            "not reduced by it, which is slightly conservative.",
            "- Gates assume independent inputs. Minimal cut sets are found by top-down expansion; their shares use the "
            "rare-event approximation.",
            f"- Monte Carlo: {results[0]['mc']['n']} samples, seed {results[0]['mc']['seed']}, one lognormal draw per failure "
            "mode (median = the assumed value, 95th percentile = value × error factor), shared by every event that uses it.",
            "",
            "## Not modelled\n",
            "- **CF2**, holding that engages too slowly: a design-adequacy question for SYS-009 and HAZ-PIL-002 M3, not a "
            "random failure.",
            "- Slow supply decay (an engine stop with charged accumulators): it leaves time for a protective stop.",
            "- Whether one joint that does not hold always drops the cockpit: the pilot assumes it does (conservative).",
            "",
            "## Next steps\n",
            "1. Replace each assumed value with a sourced one (the last column of the inputs table) and set its status.",
            "2. Have the safety lead review the trees and the assumptions; only then can a result inform the hazard's "
            "probability, through a review record.",
            "3. Add trees for other hazards and the per-element failure-mode tables for Tasks 204 and 205.",
            "",
            f"Generated by `{GEN}` (`python -m tools.reliability.build`) from `reliability/parts.yaml`, "
            "`reliability/fault-trees.yaml` and `standards/tailoring/mil-std-882e.yaml`. Numbers: "
            f"`{JSON_OUT}`.\n"]
    return "\n".join(out)


def outputs() -> dict[str, str]:
    m = engine.load(ROOT)
    hazard = yaml.safe_load((ROOT / f"safety/hazards/{m.hazard}.yaml").read_text(encoding="utf-8"))
    results = [engine.analyse(m, t) for t in m.trees]
    outs = {PAGE: page(m, results, hazard), BANDS_SVG: bands_svg(m, results, hazard)}
    for t, r in zip(m.trees, results):
        outs[tree_svg_name(t["id"])] = tree_svg(m, t, r)
    rnd = lambda x: float(f"{x:.4g}") if isinstance(x, float) else x  # noqa: E731

    def clean(o):
        if isinstance(o, dict):
            return {k: clean(v) for k, v in o.items()}
        if isinstance(o, list):
            return [clean(v) for v in o]
        return rnd(o)
    payload = {"illustrative": bool(m.assumed), "assumed_inputs": m.assumed, "hazard": m.hazard,
               "causal_factor": m.causal_factor, "exposure": {m.exposure_key: m.exposure_h},
               "bands": m.bands, "results": clean(results)}
    outs[JSON_OUT] = json.dumps(payload, indent=1, sort_keys=True) + "\n"
    return outs


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="fail if an output is stale")
    a = ap.parse_args(argv)
    try:
        outs = outputs()
    except engine.ModelError as exc:
        print(f"reliability records are inconsistent: {exc}", file=sys.stderr)
        return 1
    stale = []
    for rel, text in outs.items():
        text = decorate(rel, text)
        p = ROOT / rel
        if p.exists() and p.read_text(encoding="utf-8") == text:
            continue
        if a.check:
            stale.append(rel)
        else:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding="utf-8")
            print(f"wrote {rel}")
    if stale:
        print("Reliability outputs are out of date; run: python -m tools.reliability.build")
        for s in stale:
            print(f"  {s}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
