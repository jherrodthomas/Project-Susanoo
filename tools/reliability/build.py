"""Build the reliability pilot outputs from reliability/ and the tailoring.

    python -m tools.reliability.build            # write the outputs
    python -m tools.reliability.build --check    # fail if any output is stale

Outputs (generated; never edit by hand):

- docs/wiki/Reliability-Pilot.md          results page: summary per hazard, cut sets, drivers, inputs
- docs/wiki/images/rel-bands.svg          every quantified tree against the tailored probability bands
- docs/wiki/images/rel-ft-nnn.svg         one fault-tree drawing per tree
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

GEN = "tools/reliability/build.py"
PAGE = "docs/wiki/Reliability-Pilot.md"
BANDS_SVG = "docs/wiki/images/rel-bands.svg"
JSON_OUT = "safety/generated/reliability.json"
INK, MUTED, LINE, ACCENT, WARN, GOOD = "#152033", "#566275", "#cfd7e2", "#2a55a8", "#b54708", "#2d7a4c"
FONT = "Inter, 'Segoe UI', Helvetica, Arial, sans-serif"
EXPOSURE_WORDS = {"walker_operating_hours": "walker operating hours", "docking_cycles": "docking cycles",
                  "uav_flight_hours": "UAV flight hours"}


def sci(p) -> str:
    """Two significant figures in plain text: 1.23e-05 -> 1.2e-5."""
    if p is None:
        return "–"
    if p == 0:
        return "0"
    m, e = f"{p:.1e}".split("e")
    return f"{m}e{int(e)}"


def tree_svg_name(tid: str) -> str:
    return f"docs/wiki/images/rel-{tid.lower()}.svg"


def exposure_text(key: str, value: float) -> str:
    return f"{int(value)} {EXPOSURE_WORDS.get(key, key)}"


def worse(band: str | None, target: str | None) -> bool:
    return bool(band and target and engine.BAND_ORDER.index(band) < engine.BAND_ORDER.index(target))


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
    W = max(int(xs[0]) + 40, 820)
    depth = max(d for _, d in pos.values())
    H = 96 + (depth + 1) * ROW
    e = html.escape
    alt = f" · alternative {tree['alternative']}" if tree.get("alternative") else ""
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" font-family="{FONT}">',
         f'<rect width="{W}" height="{H}" fill="#ffffff"/>',
         f'<text x="20" y="26" font-size="16" font-weight="700" fill="{INK}">{e(tree["id"])} · {e(tree["hazard"])}{e(alt)}</text>',
         f'<text x="20" y="46" font-size="12" fill="{MUTED}">{e(tree["title"])}. Probability over '
         f'{e(exposure_text(tree["exposure"], res["exposure_value"]))}; dormant failures checked every {res["tau_h"]:g} h. '
         'Illustrative: inputs assumed.</text>']

    def xy(nid):
        x, d = pos[nid]
        return x + 20 + COL / 2, 70 + d * ROW
    for gid, g in gates.items():
        px, py = xy(gid)
        for i in g["inputs"]:
            cx, cy = xy(i)
            o.append(f'<path d="M{px} {py + BH + 34} V{py + BH + 50} H{cx} V{cy}" fill="none" stroke="{LINE}" stroke-width="1.5"/>')
    for nid in pos:
        cx, cy = xy(nid)
        node = gates.get(nid) or events[nid]
        und = engine.is_undeveloped(node)
        dash = ' stroke-dasharray="4 3"' if und else ""
        o.append(f'<rect x="{cx - BW / 2}" y="{cy}" width="{BW}" height="{BH}" rx="3" fill="#ffffff" '
                 f'stroke="{WARN if und else INK}" stroke-width="1.2"{dash}/>')
        for k, ln in enumerate(textwrap.wrap(node["title"], 30)[:2]):
            o.append(f'<text x="{cx}" y="{cy + 16 + k * 14}" font-size="11.5" fill="{INK}" text-anchor="middle">{e(ln)}</text>')
        if und:
            sub = node["nature"] + (f" · {node['ssf']}" if node.get("ssf") else "") + " · not quantified"
        else:
            kind = node.get("mode") or ("common cause" if node.get("kind") == "common_cause" else node["type"])
            p = res["nodes"][nid]
            sub = f"{kind} · " + (f"p {sci(p)}" if p > 0 else "not quantified")
        o.append(f'<text x="{cx}" y="{cy + BH - 6}" font-size="10.5" fill="{MUTED}" text-anchor="middle">{e(sub)}</text>')
        sy = cy + BH + 2
        if nid in gates:
            if node["type"] == "and":
                o.append(f'<path d="M{cx - 13} {sy + 30} V{sy + 12} A13 13 0 0 1 {cx + 13} {sy + 12} V{sy + 30} Z" fill="#ffffff" stroke="{ACCENT}" stroke-width="1.6"/>')
            else:
                o.append(f'<path d="M{cx - 14} {sy + 30} Q{cx - 14} {sy + 8} {cx} {sy} Q{cx + 14} {sy + 8} {cx + 14} {sy + 30} Q{cx} {sy + 22} {cx - 14} {sy + 30} Z" fill="#ffffff" stroke="{ACCENT}" stroke-width="1.6"/>')
        elif und:
            o.append(f'<path d="M{cx} {sy + 2} L{cx + 14} {sy + 16} L{cx} {sy + 30} L{cx - 14} {sy + 16} Z" fill="#ffffff" stroke="{WARN}" stroke-width="1.6"/>')
        elif node.get("kind") == "common_cause":
            o.append(f'<circle cx="{cx}" cy="{sy + 16}" r="13" fill="#ffffff" stroke="{INK}" stroke-width="1.4"/>'
                     f'<circle cx="{cx}" cy="{sy + 16}" r="8" fill="none" stroke="{INK}" stroke-width="1.2"/>')
        else:
            o.append(f'<circle cx="{cx}" cy="{sy + 16}" r="13" fill="#ffffff" stroke="{INK}" stroke-width="1.4"/>')
        n = node.get("count")
        if n is not None:
            o.append(f'<text x="{cx + 20}" y="{sy + 21}" font-size="12" font-weight="700" fill="{ACCENT}">×{int(m.param(n))}</text>')
    o.append(f'<text x="20" y="{H - 22}" font-size="11.5" fill="{MUTED}">Dome: all inputs (and). Shield: any input (or). '
             'Circle: failure mode. Double circle: common-cause share. Diamond: undeveloped cause, not quantified. '
             '×n: n identical copies.</text>')
    o.append("</svg>")
    return "\n".join(o) + "\n"


# ---------------------------------------------------------------- bands chart
def bands_svg(m: engine.Model, results: list[dict]) -> str:
    rows = [r for r in results if r["quantified"]]
    W, L, R = 980, 230, 30
    lo, hi = -10, 0
    RH = 44
    H = 150 + len(rows) * RH
    e = html.escape

    def X(p: float) -> float:
        p = max(p, 10 ** lo)
        return L + (math.log10(p) - lo) / (hi - lo) * (W - L - R)
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" font-family="{FONT}">',
         f'<rect width="{W}" height="{H}" fill="#ffffff"/>',
         f'<text x="20" y="26" font-size="16" font-weight="700" fill="{INK}">Quantified hardware paths against the tailored probability bands</text>',
         f'<text x="20" y="46" font-size="12" fill="{MUTED}">Probability over the item life of the cut sets made only of hardware failure '
         'modes: a lower bound. Illustrative: every input is assumed. Not a probability rating.</text>']
    top, bot = 64, 64 + len(rows) * RH + 16
    uppers = [1.0] + [m.bands[k] for k in engine.BAND_ORDER[:-1]]
    for i, k in enumerate(engine.BAND_ORDER):
        lower = m.bands[k] if m.bands[k] > 0 else 10 ** lo
        x0, x1 = X(lower), X(uppers[i])
        o.append(f'<rect x="{x0:.1f}" y="{top}" width="{x1 - x0:.1f}" height="{bot - top}" fill="{["#f4f6f9", "#ffffff"][i % 2]}"/>')
        o.append(f'<text x="{(x0 + x1) / 2:.1f}" y="{top + 14}" font-size="12" font-weight="700" fill="{MUTED}" text-anchor="middle">{k}</text>')
        if m.bands[k] > 0:
            o.append(f'<line x1="{x0:.1f}" x2="{x0:.1f}" y1="{top}" y2="{bot}" stroke="{LINE}"/>')
    for ex in range(lo, hi + 1, 2):
        x = X(10 ** ex)
        o.append(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{bot}" y2="{bot + 5}" stroke="{MUTED}"/>'
                 f'<text x="{x:.1f}" y="{bot + 18}" font-size="11" fill="{MUTED}" text-anchor="middle">1e{ex}</text>')
    for i, r in enumerate(rows):
        y = top + 34 + i * RH
        hz = m.hazards[r["hazard"]]
        tgt = (hz.get("target_risk") or {}).get("probability")
        if tgt in engine.BAND_ORDER:
            j = engine.BAND_ORDER.index(tgt)
            lower = m.bands[tgt] if m.bands[tgt] > 0 else 10 ** lo
            o.append(f'<rect x="{X(lower):.1f}" y="{y + 9}" width="{X(uppers[j]) - X(lower):.1f}" height="4" fill="{GOOD}" opacity=".7"/>')
        label = r["hazard"] + (f" · {r['alternative']}" if r.get("alternative") else "")
        o.append(f'<text x="{L - 12}" y="{y + 4}" font-size="12.5" font-weight="600" fill="{INK}" text-anchor="end">{e(label)}</text>')
        o.append(f'<text x="{L - 12}" y="{y + 17}" font-size="10.5" fill="{MUTED}" text-anchor="end">{e(r["tree"])}</text>')
        mc = r["mc"]
        o.append(f'<line x1="{X(mc["p05"]):.1f}" x2="{X(mc["p95"]):.1f}" y1="{y}" y2="{y}" stroke="{ACCENT}" stroke-width="3" stroke-linecap="round" opacity=".45"/>')
        if r["no_test"]:
            o.append(f'<circle cx="{X(r["no_test"]):.1f}" cy="{y}" r="5.5" fill="#ffffff" stroke="{WARN}" stroke-width="2"/>')
        o.append(f'<circle cx="{X(r["top"]):.1f}" cy="{y}" r="6" fill="{ACCENT}" stroke="#ffffff" stroke-width="2"/>')
        o.append(f'<text x="{X(r["top"]) + 10:.1f}" y="{y - 8}" font-size="10.5" fill="{INK}">{e(sci(r["top"]))} · {r["band"]}</text>')
    ly = bot + 44
    o.append(f'<circle cx="26" cy="{ly - 4}" r="6" fill="{ACCENT}"/><text x="38" y="{ly}" font-size="11.5" fill="{MUTED}">dormant failures checked every sortie</text>'
             f'<circle cx="276" cy="{ly - 4}" r="5.5" fill="#ffffff" stroke="{WARN}" stroke-width="2"/><text x="288" y="{ly}" font-size="11.5" fill="{MUTED}">never checked</text>'
             f'<line x1="392" x2="420" y1="{ly - 4}" y2="{ly - 4}" stroke="{ACCENT}" stroke-width="3" opacity=".45"/>'
             f'<text x="428" y="{ly}" font-size="11.5" fill="{MUTED}">5th to 95th percentile (Monte Carlo)</text>'
             f'<rect x="672" y="{ly - 6}" width="28" height="4" fill="{GOOD}" opacity=".7"/>'
             f'<text x="708" y="{ly}" font-size="11.5" fill="{MUTED}">the hazard\'s target band</text>')
    o.append("</svg>")
    return "\n".join(o) + "\n"


# ---------------------------------------------------------------- page
def risk(hz: dict, key: str, what: str) -> str | None:
    return (hz.get(key) or {}).get(what)


def cut_row(r: dict, c: dict, events: dict) -> str:
    names = []
    for ev in c["events"]:
        x = events[ev]
        names.append(f"{ev} ({x['nature']}{', ' + x['ssf'] if x.get('ssf') else ''})" if engine.is_undeveloped(x) else ev)
    if c["kind"] == "quantified":
        val, share = sci(c["p"]), f"{c['share']:.1%}"
    elif c["kind"] == "mixed":
        val, share = f"hardware part {sci(c['defence_p'])}", "not quantified"
    else:
        val, share = "–", "not quantified"
    copies = int(c["multiplicity"])
    return f"| {' + '.join(names)} | {c['kind']} | {copies} | {val} | {share} |"


def page(m: engine.Model, results: list[dict]) -> str:
    by_hz: dict[str, list[dict]] = {}
    for r in results:
        by_hz.setdefault(r["hazard"], []).append(r)
    out = [f"<!-- GENERATED by {GEN} from reliability/ and standards/tailoring/mil-std-882e.yaml. Do not edit by hand. -->\n",
           "# Reliability Pilot\n",
           f"> **Illustrative.** All {len(m.assumed)} inputs (failure-mode values and tree parameters) are assumed "
           "order-of-magnitude placeholders drafted by an AI at independence I0, not handbook or supplier data. Nothing "
           "here is evidence, a probability rating or a risk acceptance, and nothing is written back into a hazard record.\n",
           f"Every hazard has a fault tree ({len(results)} trees for {len(by_hz)} hazards). Hardware causes are failure modes "
           "with an assumed value. Software, human, environmental, interface and systematic causes are **undeveloped** "
           "events: they appear in the tree and its cut sets, traced to their causal factor, but carry no number. "
           "Software is handled by the level-of-rigour tasks of MIL-STD-882E section 4.4, not by a probability.\n",
           "Each tree gives three things:\n",
           "- the **quantified probability**: the cut sets made only of hardware failure modes, over the item life, placed "
           "in the tailored bands (SUS-RISKDEF-001). With undeveloped causes left out, it is a lower bound;",
           "- **mixed cut sets**: an undeveloped cause together with hardware, with the probability of the hardware part. "
           "This is the defence that stands behind the software or human cause;",
           "- **single-point undeveloped causes**: a software, human or environmental cause that reaches the top event "
           "with no hardware in the way.\n",
           f"![Quantified hardware paths against the bands](images/{Path(BANDS_SVG).name})\n",
           "## Summary\n",
           "| Hazard | Rated now | Target | Tree | Quantified (band) | Mixed cut sets: hardware part | Single-point undeveloped causes |",
           "|---|---|---|---|---|---|---|"]
    for hid, rs in by_hz.items():
        hz = m.hazards[hid]
        for r in rs:
            mixed = [c["defence_p"] for c in r["cut_sets"] if c["kind"] == "mixed"]
            mx = (f"{len(mixed)}: {sci(min(mixed))} to {sci(max(mixed))}" if len(mixed) > 1 else
                  f"1: {sci(mixed[0])}" if mixed else "none")
            q = f"{sci(r['top'])} ({r['band']})" if r["quantified"] else "not quantified"
            if worse(r["band"], risk(hz, "target_risk", "probability")):
                q += " **above target**"
            sp = ", ".join(r["single_points"]) or "none"
            alt = f" ({r['alternative']})" if r.get("alternative") else ""
            out.append(f"| {hid} {hz['title']} | {risk(hz, 'initial_risk', 'rac')} | {risk(hz, 'target_risk', 'rac')} | "
                       f"{r['tree']}{alt} | {q} | {mx} | {sp} |")
    out.append("")
    above = [r for r in results if worse(r["band"], risk(m.hazards[r["hazard"]], "target_risk", "probability"))]
    only_undev = [hid for hid, rs in by_hz.items() if all(not r["quantified"] and not any(c["kind"] == "mixed" for c in r["cut_sets"]) for r in rs)]
    singles = sorted({hid for hid, rs in by_hz.items() for r in rs if r["single_points"]})
    out.append("**What the trees say, with these assumed inputs:**\n")
    if above:
        out.append("- **Quantified paths already above the target band:** " + "; ".join(
            f"{r['hazard']} {r['tree']}{' (' + r['alternative'] + ')' if r.get('alternative') else ''} at {sci(r['top'])}, band "
            f"{r['band']} against {risk(m.hazards[r['hazard']], 'target_risk', 'probability')}" for r in above) + ".")
    if singles:
        out.append(f"- **{len(singles)} hazards have causes with no hardware defence behind them:** {', '.join(singles)}. "
                   "Their risk rests on procedures, training, design adequacy or software rigour, which the trees cannot "
                   "quantify.")
    if only_undev:
        out.append(f"- **Not quantifiable at all:** {', '.join(only_undev)}. Every cause is human, environmental, "
                   "interface or systematic; these hazards are rated by judgement, not by a tree.")
    out.append("- **Mixed cut sets show where hardware backs up software or people:** the smaller the hardware part, the "
               "more the hazard is protected if the software or the person gets it wrong.\n")
    for hid, rs in by_hz.items():
        hz = m.hazards[hid]
        f = m.files[hid]
        out.append(f"## {hid} · {hz['title']}\n")
        out.append(f"Rated {risk(hz, 'initial_risk', 'rac')} now, target {risk(hz, 'target_risk', 'rac')}. Exposure: "
                   f"{exposure_text(f['exposure'], m.item_life[f['exposure']])}.")
        if f.get("note"):
            out.append(f"{f['note']}")
        for cf, why in (f.get("not_modelled") or {}).items():
            out.append(f"Not modelled, {cf}: {' '.join(str(why).split())}")
        out.append("")
        for r in rs:
            t = next(x for x in m.trees if x["id"] == r["tree"])
            events = {e["id"]: e for e in t["events"]}
            alt = f" · alternative {t['alternative']}" if t.get("alternative") else ""
            out += [f"### {t['id']}{alt}\n", f"![{t['id']}](images/{Path(tree_svg_name(t['id'])).name})\n"]
            if r["quantified"]:
                line = f"Quantified: {sci(r['top'])}, band {r['band']}"
                if r["no_test"]:
                    line += f"; never checked: {sci(r['no_test'])}, band {r['no_test_band']}"
                mc = r["mc"]
                line += f". Monte Carlo 5th / 50th / 95th: {sci(mc['p05'])} / {sci(mc['p50'])} / {sci(mc['p95'])}."
                d = r["drivers"][0]
                line += (f" Biggest driver: {d['mode']} ({m.modes[d['mode']]['mode'].split(' (')[0].lower()}), "
                         f"×{d['factor']:.1f} at its error factor.")
                rc = r.get("reach_e")
                tgt = risk(hz, "target_risk", "probability")
                if rc and rc["factor"] is not None:
                    line += (f" Band E needs it at or below {sci(rc['value'])} {m.modes[rc['mode']]['unit']} "
                             f"(about {rc['factor']:.2g} times the assumed value){' and the target is ' + tgt if tgt != 'E' else ''}.")
                elif rc:
                    line += f" No value of {rc['mode']} alone reaches band E."
                out.append(line + "\n")
            out += ["| Minimal cut set | Kind | Copies | Probability | Share |", "|---|---|---|---|---|"]
            out += [cut_row(r, c, events) for c in r["cut_sets"]]
            out.append("")
    out += ["## Inputs\n", "| Failure mode | Part | Mode | Kind | Value | Error factor | Status | Where a sourced value should come from |",
            "|---|---|---|---|---|---|---|---|"]
    for mid, md in m.modes.items():
        out.append(f"| {mid} | {md['part_title']} | {md['mode']} | {md['kind']} | {sci(md['value'])} {md['unit']} | "
                   f"{md['error_factor']:g} | {md['status']} | {md['to_source']} |")
    out += ["", "| Parameter | Value | Status | Note |", "|---|---|---|---|"]
    out += [f"| {k} | {v['value']:g} | {v['status']} | {v['note']} |" for k, v in m.params.items()]
    mc0 = next(r["mc"] for r in results if r["mc"])
    out += ["", "## How the numbers are computed\n",
            "- `rate` modes give 1 − e^(−λ T) over the exposure T in hours; `cycle` modes give 1 − (1 − q)^N over N "
            "cycles; `latent` modes give λ τ / 2 with τ the check interval (or the exposure when never checked); "
            "`demand` modes give their probability per demand. The exposures are the tailored item life.",
            "- `×n` means n identical, independent copies, any one of which fails: 1 − (1 − p)^n.",
            "- A common-cause event is the beta-factor share of its modes; the independent events are not reduced by it, "
            "which is slightly conservative.",
            "- Undeveloped events count as 0 in the quantified probability. Gates assume independent inputs. Minimal cut "
            "sets are found by top-down expansion; shares use the rare-event approximation.",
            f"- Monte Carlo: {mc0['n']} samples per tree, seed {mc0['seed']}, one lognormal draw per failure mode (median = "
            "the assumed value, 95th percentile = value × error factor), shared by every event that uses it.",
            "",
            "## Next steps\n",
            "1. Replace each assumed value with a sourced one (the last column of the inputs table) and set its status.",
            "2. Have the safety lead review the trees and their assumptions; only then can a result inform a hazard's "
            "probability, through a review record.",
            "3. Add the per-element failure-mode tables for Tasks 204 and 205 from the same parts.",
            "",
            f"Generated by `{GEN}` (`python -m tools.reliability.build`) from `reliability/` and "
            f"`standards/tailoring/mil-std-882e.yaml`. Numbers: `{JSON_OUT}`.\n"]
    return "\n".join(out)


def outputs() -> dict[str, str]:
    m = engine.load(ROOT)
    results = [engine.analyse(m, t) for t in m.trees]
    outs = {PAGE: page(m, results), BANDS_SVG: bands_svg(m, results)}
    for t, r in zip(m.trees, results):
        outs[tree_svg_name(t["id"])] = tree_svg(m, t, r)

    def clean(o):
        if isinstance(o, dict):
            return {k: clean(v) for k, v in o.items()}
        if isinstance(o, list):
            return [clean(v) for v in o]
        return float(f"{o:.4g}") if isinstance(o, float) else o
    payload = {"illustrative": bool(m.assumed), "assumed_inputs": m.assumed, "item_life": m.item_life,
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
    stale_figs = sorted(p.relative_to(ROOT).as_posix() for p in (ROOT / "docs/wiki/images").glob("rel-ft-*.svg")
                        if p.relative_to(ROOT).as_posix() not in outs)
    if stale_figs:
        if a.check:
            stale += stale_figs
        else:
            for s in stale_figs:
                (ROOT / s).unlink()
                print(f"removed {s} (no tree any more)")
    if stale:
        print("Reliability outputs are out of date; run: python -m tools.reliability.build")
        for s in stale:
            print(f"  {s}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
