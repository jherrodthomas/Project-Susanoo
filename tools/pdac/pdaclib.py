# SPDX-License-Identifier: Apache-2.0
"""Load the PDaC records of Project Susanoo and check them.

The records are pdac/product.yaml, pdac/documents.yaml and pdac/items/*.yaml. Each check has an ID
(P1...P9) that error messages carry; pdac/README.md lists what each one enforces. Checks report, they
never repair: a failing record is fixed by a person (or an assistant, as a proposal) in the record.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

import jsonschema
import yaml

ROOT = Path(__file__).resolve().parents[2]

# --- MIL-STD-882E risk assessment matrix (risk level from severity x probability) -------------------
SEVERITIES = ["catastrophic", "critical", "marginal", "negligible"]
PROBABILITIES = ["frequent", "probable", "occasional", "remote", "improbable", "eliminated"]
_MATRIX = {
    "frequent":   ["high", "high", "serious", "medium"],
    "probable":   ["high", "high", "serious", "medium"],
    "occasional": ["high", "serious", "medium", "low"],
    "remote":     ["serious", "medium", "medium", "low"],
    "improbable": ["medium", "medium", "medium", "low"],
}
LEVELS = ["high", "serious", "medium", "low", "eliminated"]


def risk_level(severity: str, probability: str) -> str:
    """Risk level for a MIL-STD-882E severity category and probability level."""
    if probability == "eliminated":
        return "eliminated"
    return _MATRIX[probability][SEVERITIES.index(severity)]


# --- Reference rules: field -> kinds its IDs must resolve to (check P3) ----------------------------
REFS: dict[str, dict[str, tuple[str, ...]]] = {
    "scenario": {"modes": ("mode",)},
    "interface": {"endpoints": ("component", "actor")},
    "requirement": {
        "sources": ("scenario", "hazard"),
        "mitigates": ("hazard",),
        "allocated_to": ("component",),
        "verification.cases": ("test-case",),
        "design_dependency": ("trade-study",),
        "approval_ref": ("approval",),
    },
    "hazard": {
        "exposed": ("actor",),
        "scenarios": ("scenario",),
        "modes": ("mode",),
        "components": ("component",),
        "mitigated_by": ("requirement",),
        "design_dependency": ("trade-study",),
        "related_failure_conditions": ("failure-condition",),
        "acceptance_ref": ("approval",),
    },
    "failure-condition": {"related_hazards": ("hazard",)},
    "trade-study": {"decision_ref": ("approval",)},
    "approval": {"objects": ("*",)},
    "concept-layout": {"informs": ("hazard", "requirement")},
}
# Every kind except document may name the controlled document it comes from.
SOURCE_KINDS = ("document",)

# IDs that may appear in Markdown and must then exist as records (check P8).
MARKDOWN_ID = re.compile(r"\b(?:SCN-\d{3}|MOD-\d{2}|SYS-\d{3}|HAZ-\d{3}|TS-\d{3}|IF-\d{2}|FC-\d{3}|APR-\d{3}|CL-\d{2})\b")


@dataclass
class Finding:
    check: str
    where: str
    message: str

    def __str__(self) -> str:
        return f"[{self.check}] {self.where}: {self.message}"


@dataclass
class Model:
    root: Path
    product: dict
    files: dict[str, dict] = field(default_factory=dict)  # repo-relative path -> parsed file
    items: list[tuple[str, dict]] = field(default_factory=list)  # (file path, item) in file order

    def by_id(self) -> dict[str, dict]:
        out: dict[str, dict] = {}
        for _, item in self.items:
            out.setdefault(item.get("id"), item)
        return out

    def of_kind(self, kind: str) -> list[dict]:
        return [it for _, it in self.items if it.get("kind") == kind]


def _load_yaml(path: Path):
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def load(root: Path = ROOT) -> Model:
    root = Path(root)
    model = Model(root=root, product=_load_yaml(root / "pdac/product.yaml"))
    paths = [root / "pdac/documents.yaml", *sorted((root / "pdac/items").glob("*.yaml"))]
    for path in paths:
        rel = path.relative_to(root).as_posix()
        data = _load_yaml(path)
        model.files[rel] = data
        for item in (data or {}).get("items", []) or []:
            model.items.append((rel, item))
    return model


def load_schema(root: Path = ROOT) -> dict:
    return json.loads((Path(root) / "pdac/schema/pdac.schema.json").read_text(encoding="utf-8"))


def _get(item: dict, dotted: str):
    value = item
    for part in dotted.split("."):
        if not isinstance(value, dict):
            return None
        value = value.get(part)
    return value


def _as_list(value) -> list:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


# --- Checks ---------------------------------------------------------------------------------------

def check_schema(model: Model, schema: dict) -> list[Finding]:
    """P1: product, file headers and every item against the JSON schema of its kind."""
    out: list[Finding] = []
    defs = schema["$defs"]

    def run(instance, def_name: str, where: str):
        sub = {"$schema": schema["$schema"], "$defs": defs, "$ref": f"#/$defs/{def_name}"}
        validator = jsonschema.Draft202012Validator(sub)
        for err in sorted(validator.iter_errors(instance), key=lambda e: list(e.absolute_path)):
            loc = "/".join(str(p) for p in err.absolute_path)
            out.append(Finding("P1", f"{where}{'/' + loc if loc else ''}", err.message))

    run(model.product, "product", "pdac/product.yaml")
    for rel, data in model.files.items():
        run(data, "itemFile", rel)
    for rel, item in model.items:
        kind = item.get("kind")
        where = f"{rel}:{item.get('id')}"
        if kind not in defs or kind in {"common", "itemFile", "product", "provenance"} or "kind" not in defs[kind].get("properties", {}):
            out.append(Finding("P1", where, f"unknown kind {kind!r}"))
            continue
        run(item, kind, where)
    return out


def check_unique(model: Model) -> list[Finding]:
    """P2: IDs are unique across all records."""
    seen: dict[str, str] = {}
    out = []
    for rel, item in model.items:
        iid = item.get("id")
        if iid in seen:
            out.append(Finding("P2", f"{rel}:{iid}", f"duplicate ID (first defined in {seen[iid]})"))
        else:
            seen[iid] = rel
    return out


def check_references(model: Model) -> list[Finding]:
    """P3: every reference resolves to a record of an allowed kind."""
    ids = model.by_id()
    out = []
    for rel, item in model.items:
        kind = item.get("kind")
        rules = dict(REFS.get(kind, {}))
        if kind != "document":
            rules["source"] = SOURCE_KINDS
        for fld, kinds in rules.items():
            for ref in _as_list(_get(item, fld)):
                target = ids.get(ref)
                where = f"{rel}:{item.get('id')}"
                if target is None:
                    out.append(Finding("P3", where, f"{fld} -> {ref}: no such record"))
                elif "*" not in kinds and target.get("kind") not in kinds:
                    out.append(Finding("P3", where, f"{fld} -> {ref}: is a {target.get('kind')}, expected {' or '.join(kinds)}"))
    for layout in model.of_kind("concept-layout"):
        for ts_id, option in (layout.get("options") or {}).items():
            ts = ids.get(ts_id)
            if ts is None or ts.get("kind") != "trade-study":
                out.append(Finding("P3", layout["id"], f"options -> {ts_id}: no such trade study"))
            elif option not in ts.get("alternatives", []):
                out.append(Finding("P3", layout["id"], f"options -> {ts_id}: {option!r} is not one of its alternatives"))
    return out


def check_bidirectional(model: Model) -> list[Finding]:
    """P4: requirement.mitigates <-> hazard.mitigated_by; hazard <-> failure-condition links."""
    out = []
    ids = model.by_id()
    pairs = [
        ("requirement", "mitigates", "hazard", "mitigated_by"),
        ("failure-condition", "related_hazards", "hazard", "related_failure_conditions"),
    ]
    for kind_a, fld_a, kind_b, fld_b in pairs:
        for a in model.of_kind(kind_a):
            for ref in _as_list(a.get(fld_a)):
                b = ids.get(ref)
                if b is not None and b.get("kind") == kind_b and a["id"] not in _as_list(b.get(fld_b)):
                    out.append(Finding("P4", a["id"], f"{fld_a} lists {ref}, but {ref}.{fld_b} does not list {a['id']}"))
        for b in model.of_kind(kind_b):
            for ref in _as_list(b.get(fld_b)):
                a = ids.get(ref)
                if a is not None and a.get("kind") == kind_a and b["id"] not in _as_list(a.get(fld_a)):
                    out.append(Finding("P4", b["id"], f"{fld_b} lists {ref}, but {ref}.{fld_a} does not list {b['id']}"))
    return out


def check_risk(model: Model) -> list[Finding]:
    """P5: MIL-STD-882E levels follow the matrix; ARP4761A classes stay on aircraft failure conditions."""
    out = []
    for hz in model.of_kind("hazard"):
        for stage in ("initial", "target", "residual"):
            rating = _get(hz, f"risk.{stage}")
            if not isinstance(rating, dict):
                continue
            sev, prob, lvl = rating.get("severity"), rating.get("probability"), rating.get("level")
            if sev in SEVERITIES and prob in PROBABILITIES and lvl != risk_level(sev, prob):
                out.append(Finding("P5", hz["id"], f"risk.{stage}: {sev} x {prob} is {risk_level(sev, prob)!r} on the MIL-STD-882E matrix, record says {lvl!r}"))
    for fc in model.of_kind("failure-condition"):
        if "SUS-A1" not in _as_list(fc.get("applicability")):
            out.append(Finding("P5", fc["id"], "an ARP4761A failure condition must apply to the aircraft variant SUS-A1"))
    return out


def check_acceptance(model: Model) -> list[Finding]:
    """P6: only recorded human approvals baseline, accept or release anything."""
    out = []
    ids = model.by_id()

    def approval_ok(ref, obj_id: str, decision: str) -> str | None:
        apr = ids.get(ref)
        if apr is None or apr.get("kind") != "approval":
            return f"needs an approval record, has {ref!r}"
        if apr.get("status") != "recorded":
            return f"approval {ref} is {apr.get('status')}"
        if apr.get("decision") != decision:
            return f"approval {ref} records decision {apr.get('decision')!r}, needs {decision!r}"
        if obj_id not in _as_list(apr.get("objects")):
            return f"approval {ref} does not list {obj_id}"
        return None

    for hz in model.of_kind("hazard"):
        if hz.get("status") == "closed":
            problem = approval_ok(hz.get("acceptance_ref"), hz["id"], "accept-risk")
            if problem:
                out.append(Finding("P6", hz["id"], f"closed hazard {problem}"))
            if not _get(hz, "risk.residual"):
                out.append(Finding("P6", hz["id"], "closed hazard needs a residual risk rating"))
            if _get(hz, "risk.rating_status") != "reviewed":
                out.append(Finding("P6", hz["id"], "closed hazard needs risk.rating_status: reviewed"))
    for req in model.of_kind("requirement"):
        if req.get("status") == "baselined":
            if not _get(req, "verification.methods"):
                out.append(Finding("P6", req["id"], "baselined requirement needs a verification method"))
            problem = approval_ok(req.get("approval_ref"), req["id"], "baseline")
            if problem:
                out.append(Finding("P6", req["id"], f"baselined requirement {problem}"))
    release = model.product.get("release", {})
    approvals = [ids.get(r) for r in _as_list(release.get("approvals"))]
    for ref, apr in zip(_as_list(release.get("approvals")), approvals):
        if apr is None or apr.get("kind") != "approval":
            out.append(Finding("P6", "pdac/product.yaml:release", f"approval {ref} is not an approval record"))
    if release.get("status") == "released" and not any(
        a and a.get("decision") == "release" and a.get("authority_type") == "real" and a.get("status") == "recorded" for a in approvals
    ):
        out.append(Finding("P6", "pdac/product.yaml:release", "a released release needs a recorded real (not simulated) release approval"))
    return out


def check_applicability(model: Model) -> list[Finding]:
    """P7: applicability uses declared variants; allocations and hazard components share a variant."""
    out = []
    declared = {v.get("id") for v in model.product.get("variants", [])}
    ids = model.by_id()
    for rel, item in model.items:
        extra = set(_as_list(item.get("applicability"))) - declared
        if extra:
            out.append(Finding("P7", f"{rel}:{item.get('id')}", f"applicability names undeclared variants {sorted(extra)}"))
    for kind, fld in (("requirement", "allocated_to"), ("hazard", "components")):
        for item in model.of_kind(kind):
            mine = set(_as_list(item.get("applicability")))
            for ref in _as_list(item.get(fld)):
                target = ids.get(ref)
                if target and not mine & set(_as_list(target.get("applicability"))):
                    out.append(Finding("P7", item["id"], f"{fld} -> {ref}: no variant in common"))
    return out


def markdown_files(root: Path) -> list[Path]:
    skip = {".git", "build", "node_modules"}
    return sorted(p for p in Path(root).rglob("*.md") if not skip & set(p.relative_to(root).parts))


def check_documents(model: Model) -> list[Finding]:
    """P8: registered documents exist and carry their registered ID and revision; Markdown names only real IDs;
    every scenario and mode record appears in the CONOPS."""
    out = []
    root = model.root
    for doc in model.of_kind("document"):
        path = root / doc.get("path", "")
        if not path.is_file():
            out.append(Finding("P8", doc["id"], f"{doc.get('path')} does not exist"))
            continue
        head = "\n".join(path.read_text(encoding="utf-8").splitlines()[:6])
        expected = f"**ID:** {doc['id']} · **Revision:** {doc.get('revision')}"
        if expected not in head:
            out.append(Finding("P8", doc["id"], f"{doc['path']} must carry '{expected}' in its first lines"))
    ids = model.by_id()
    for path in markdown_files(root):
        text = path.read_text(encoding="utf-8")
        for mid in sorted(set(MARKDOWN_ID.findall(text))):
            if mid not in ids:
                out.append(Finding("P8", path.relative_to(root).as_posix(), f"mentions {mid}, which has no record"))
    metrics_path = root / "cad/metrics.json"
    metrics = json.loads(metrics_path.read_text(encoding="utf-8")).get("concepts", {}) if metrics_path.is_file() else {}
    for layout in model.of_kind("concept-layout"):
        params = root / layout.get("params", "")
        if not params.is_file():
            out.append(Finding("P8", layout["id"], f"params file {layout.get('params')} does not exist"))
        elif f"id: {layout['id']}" not in params.read_text(encoding="utf-8"):
            out.append(Finding("P8", layout["id"], f"{layout['params']} does not declare id: {layout['id']}"))
        entry = metrics.get(layout["id"])
        if entry is None:
            out.append(Finding("P8", layout["id"], "no entry in cad/metrics.json: run tools/cad/make.sh"))
        elif entry.get("title") != layout.get("title"):
            out.append(Finding("P8", layout["id"], "title differs from cad/metrics.json: rebuild the layouts"))
    conops_doc = ids.get("SUS-CONOPS-001")
    if conops_doc and (root / conops_doc["path"]).is_file():
        conops = (root / conops_doc["path"]).read_text(encoding="utf-8")
        for item in model.of_kind("scenario") + model.of_kind("mode"):
            if item["id"] not in conops:
                out.append(Finding("P8", item["id"], f"{item['kind']} record is not described in {conops_doc['path']}"))
    return out


def check_coverage(model: Model) -> list[Finding]:
    """P9: every scenario has a hazard, every high or serious hazard a candidate mitigation, every safety
    requirement a hazard, every component a requirement."""
    out = []
    hazards = model.of_kind("hazard")
    reqs = model.of_kind("requirement")
    covered = {s for hz in hazards for s in _as_list(hz.get("scenarios"))}
    for scn in model.of_kind("scenario"):
        if scn["id"] not in covered:
            out.append(Finding("P9", scn["id"], "no hazard is derived from this scenario"))
    for hz in hazards:
        if _get(hz, "risk.initial.level") in ("high", "serious") and not _as_list(hz.get("mitigated_by")):
            out.append(Finding("P9", hz["id"], "high or serious hazard without a candidate mitigation"))
    for req in reqs:
        if req.get("req_type") == "safety" and not _as_list(req.get("mitigates")):
            out.append(Finding("P9", req["id"], "safety requirement mitigates no hazard"))
    allocated = {c for r in reqs for c in _as_list(r.get("allocated_to"))}
    for comp in model.of_kind("component"):
        if comp["id"] not in allocated:
            out.append(Finding("P9", comp["id"], "no requirement is allocated to this component"))
    return out


CHECKS = [check_unique, check_references, check_bidirectional, check_risk, check_acceptance,
          check_applicability, check_documents, check_coverage]


def validate(model: Model, schema: dict) -> list[Finding]:
    findings = check_schema(model, schema)
    for check in CHECKS:
        findings.extend(check(model))
    return findings
