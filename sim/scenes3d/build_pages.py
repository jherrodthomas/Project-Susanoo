"""Build the interactive 3D scene pages and the 3D-Scenes wiki page.

Usage: python -m sim.scenes3d.build_pages [--check]

For every scene and variant in sim/scenes3d/scenes.yaml writes docs/3d/<id>.html: one self-contained page with the
exported analysis (sim/scenes3d/out/<id>.json, variants share their base scene's analysis), the resolved look,
sim/scenes3d/viewer.js and an import map pinning three.js. Also writes docs/3d/index.html and docs/wiki/3D-Scenes.md.
Stills (docs/wiki/images/3d-*.png) are rendered by render.mjs and are not --checked (GPU output is not byte-stable).
"""
from __future__ import annotations

import argparse
import html
import json
import sys

from sim.common import ABOUT, ROOT, SIM, write_or_check
from tools.terms.terms import expand, find, label, load as load_terms
from sim.scenes3d.export_scene import load
from tools.pdac.load import _read_yaml

LIB = SIM / "scenes3d" / "library"
CDN = "https://cdn.jsdelivr.net/npm/three@{v}/"


def resolve_look(base: dict, over: dict | None) -> dict:
    look = {**base, **(over or {})}
    envs = _read_yaml(LIB / "environments.yaml")["environments"]
    conds = _read_yaml(LIB / "conditions.yaml")["conditions"]
    if look["environment"] not in envs:
        raise ValueError(f"unknown environment {look['environment']}")
    if look["condition"] not in conds:
        raise ValueError(f"unknown condition {look['condition']}")
    return {"environment": envs[look["environment"]], "condition": conds[look["condition"]], "camera": look.get("camera", "side"),
            "names": {"environment": look["environment"], "condition": look["condition"]}}


PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
html,body{{margin:0;height:100%;overflow:hidden;background:#0f172a;font-family:Inter,'Segoe UI',Helvetica,Arial,sans-serif}}
#hud{{position:fixed;left:12px;top:12px;max-width:min(640px,calc(100vw - 24px));background:rgba(255,255,255,.88);color:#0f172a;
border-radius:10px;padding:10px 12px;font-size:13px;line-height:1.45}}
#hud .title{{font-weight:700;font-size:15px}}
#hud .note{{color:#64748b;font-size:11.5px;margin-top:2px}}
#terms{{position:fixed;left:12px;right:12px;bottom:58px;background:rgba(255,255,255,.82);color:#475569;
border-radius:8px;padding:5px 10px;font-size:11px;line-height:1.4}}
#bar{{position:fixed;left:12px;right:12px;bottom:12px;display:flex;gap:10px;align-items:center;background:rgba(255,255,255,.88);
border-radius:10px;padding:8px 12px}}
#bar input{{flex:1}} button{{font:inherit;border:1px solid #cbd5e1;background:#fff;border-radius:6px;padding:4px 10px}}
</style>
<script type="importmap">{{"imports":{{"three":"{cdn}build/three.module.min.js","three/addons/":"{cdn}examples/jsm/"}}}}</script>
</head><body>
<div id="hud"></div>
<div id="terms">{terms}</div>
<div id="bar"><button id="play">Pause</button><input id="time" type="range" min="0" max="1" step="0.01" value="0"></div>
<script>window.SCENE = {scene};</script>
<script type="module">
{viewer}
</script>
</body></html>
"""


def terms_line(analysis: dict) -> str:
    """Terms for what the info panel shows: scene, hazards, source and, for the UAV, the PX4 flight modes."""
    shown = [analysis["id"], analysis["title"], *analysis["hazards"], str(analysis.get("reference", ""))]
    if analysis["kind"] == "uav":
        shown += ["UAV", "PX4", *(m.replace("AUTO.", "") for _, m in analysis.get("mode_changes") or [])]
    keys = expand(find(" ".join(shown))[0])
    defs, _ = load_terms()
    return "Terms: " + " · ".join(f"{html.escape(label(k))} = {html.escape(defs[k])}"
                                  for k in sorted(keys, key=lambda q: label(q).lower()))


def page(sid: str, title: str, analysis: dict, look: dict, version: str) -> str:
    data = json.dumps({"analysis": analysis, "look": look}, sort_keys=True, separators=(",", ":")).replace("</", "<\\/")
    viewer = (SIM / "scenes3d" / "viewer.js").read_text(encoding="utf-8")
    return PAGE.format(title=html.escape(f"{sid} {title}"), cdn=CDN.format(v=version), scene=data, viewer=viewer,
                       terms=terms_line(analysis))


def entries(cfg: dict) -> list[dict]:
    out = []
    for sc in cfg["scenes"]:
        out.append({"id": sc["id"], "base": sc["id"], "title": sc["title"], "hazards": sc["hazards"], "look": resolve_look(sc["look"], None)})
        for v in sc.get("variants") or []:
            out.append({"id": v["id"], "base": sc["id"], "title": sc["title"], "hazards": sc["hazards"],
                        "look": resolve_look(sc["look"], v.get("look"))})
    return out


def outputs() -> dict:
    cfg = load()
    version = cfg["three"]["version"]
    outs = {}
    rows = []
    for e in entries(cfg):
        analysis = json.loads((ROOT / f"sim/scenes3d/out/{e['base']}.json").read_text())
        outs[f"docs/3d/{e['id']}.html"] = page(e["id"], e["title"], analysis, e["look"], version)
        oc = analysis["performed"]["outcome"] if analysis["kind"] == "walker" else analysis["outcome"]
        rows.append({**e, "outcome": oc, "kind": analysis["kind"], "reference": analysis["reference"]})
    links = "\n".join(f'<li><a href="{r["id"]}.html">{html.escape(r["id"])}</a> · {html.escape(r["title"])} · '
                      f'{", ".join(r["hazards"])} · {r["outcome"]} ({r["look"]["names"]["condition"]})</li>' for r in rows)
    outs["docs/3d/index.html"] = (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" '
                                  f'content="width=device-width, initial-scale=1"><title>Susanoo 3D scenes</title>'
                                  f'<style>body{{font-family:Inter,Arial,sans-serif;margin:24px;max-width:900px;color:#0f172a}}'
                                  f'li{{margin:6px 0}}</style></head><body><h1>Susanoo 3D hazard scenes</h1><p>{html.escape(ABOUT)}</p>'
                                  f'<ul>{links}</ul></body></html>\n')
    nm = cfg.get("not_modelled") or []
    md = ["<!-- GENERATED by sim/scenes3d/build_pages.py from sim/scenes3d/scenes.yaml. Do not edit by hand. -->\n\n",
          "# 3D Scenes\n\n", f"> {ABOUT}\n\n",
          "Interactive three.js scenes replaying plant, failure-search and PX4 SITL results (`sim/scenes3d`). The walker and UAV are "
          "parametric models built from the plant and UAV specs, not designs. The look (environment, lighting, camera) never changes "
          "the analysis; `sim/tests/test_scenes3d.py` checks that. To view a scene, open `docs/3d/<id>.html` from a local checkout "
          "in a browser. Pages load three.js r" + cfg["three"]["version"] + " from jsDelivr.\n\n"]
    for r in rows:
        md.append(f"### {r['id']} · {r['title']}\n\n{', '.join(r['hazards'])} · {r['kind']} · source {r['reference']} · outcome "
                  f"**{r['outcome']}** · {r['look']['names']['environment']}, {r['look']['names']['condition']}\n\n"
                  f"![{r['id']}](images/3d-{r['id'].lower()}.png)\n\n")
    if nm:
        md.append("## Hazards without a scene\n\n| Hazard | Why |\n|---|---|\n" + "".join(f"| {x['hazard']} | {x['reason']} |\n" for x in nm))
    outs["docs/wiki/3D-Scenes.md"] = "".join(md)
    return outs


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    return write_or_check(outputs(), a.check, "python -m sim.scenes3d.build_pages")


if __name__ == "__main__":
    sys.exit(main())
