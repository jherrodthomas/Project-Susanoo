"""Load the MIL-STD-882E model, project tailoring and PDaC object records."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]

# kind -> (directory, schema file, id field)
COLLECTIONS = {
    "hazard": ("safety/hazards", "hazard.schema.json", "id"),
    "ssf": ("safety/software", "ssf.schema.json", "id"),
    "requirement": ("requirements", "requirement.schema.json", "id"),
    "event": ("safety/events", "event.schema.json", "id"),
    "change": ("changes", "change-request.schema.json", "id"),
    "verification": ("verification", "verification.schema.json", "id"),
    "task": ("safety/mil-std-882e/tasks", "task-record.schema.json", "task_id"),
    "review": ("reviews", "review.schema.json", "id"),
    "trade": ("architecture/trades", "trade-study.schema.json", "id"),
}

MODEL_PATH = "standards/mil-std-882e/model.yaml"
TAILORING_PATH = "standards/tailoring/mil-std-882e.yaml"
PRODUCT_PATH = "pdac/product.yaml"
ITEM_PATH = "architecture/item-definition.yaml"
ITEM_SCHEMA = "item-definition.schema.json"
DECISIONS_PATH = "decisions/register.yaml"
DECISIONS_SCHEMA = "decision-register.schema.json"
SCHEMA_DIR = "pdac/schemas"


@dataclass
class Repo:
    root: Path
    model: dict
    tailoring: dict
    product: dict
    schemas: dict = field(default_factory=dict)
    objects: dict = field(default_factory=dict)   # kind -> {id: record}
    paths: dict = field(default_factory=dict)     # (kind, id) -> relative path
    load_errors: list = field(default_factory=list)  # (path, message)
    item: dict = field(default_factory=dict)          # architecture/item-definition.yaml
    decisions: dict = field(default_factory=dict)     # decisions/register.yaml

    def all_ids(self) -> set:
        ids = set()
        for recs in self.objects.values():
            ids.update(str(k) for k in recs)
        return ids


class _Loader(yaml.SafeLoader):
    """SafeLoader that keeps dates as ISO strings, so JSON Schema "format: date" and string comparisons work."""


_Loader.yaml_implicit_resolvers = {
    k: [(tag, rx) for tag, rx in v if tag != "tag:yaml.org,2002:timestamp"]
    for k, v in yaml.SafeLoader.yaml_implicit_resolvers.items()
}


def _read_yaml(path: Path):
    with path.open(encoding="utf-8") as fh:
        return yaml.load(fh, Loader=_Loader)  # noqa: S506 - _Loader is a SafeLoader subclass


def load(root: Path | str = ROOT) -> Repo:
    root = Path(root)
    repo = Repo(
        root=root,
        model=_read_yaml(root / MODEL_PATH),
        tailoring=_read_yaml(root / TAILORING_PATH),
        product=_read_yaml(root / PRODUCT_PATH) if (root / PRODUCT_PATH).exists() else {},
    )
    schema_dir = root / SCHEMA_DIR
    repo.schemas["item"] = json.loads((schema_dir / ITEM_SCHEMA).read_text(encoding="utf-8"))
    if (root / ITEM_PATH).exists():
        repo.item = _read_yaml(root / ITEM_PATH) or {}
    repo.schemas["decisions"] = json.loads((schema_dir / DECISIONS_SCHEMA).read_text(encoding="utf-8"))
    if (root / DECISIONS_PATH).exists():
        repo.decisions = _read_yaml(root / DECISIONS_PATH) or {}
    for kind, (directory, schema_file, id_field) in COLLECTIONS.items():
        repo.schemas[kind] = json.loads((root / SCHEMA_DIR / schema_file).read_text(encoding="utf-8"))
        repo.objects[kind] = {}
        folder = root / directory
        if not folder.is_dir():
            continue
        for path in sorted(folder.glob("*.yaml")):
            rel = path.relative_to(root).as_posix()
            try:
                data = _read_yaml(path)
            except yaml.YAMLError as exc:
                repo.load_errors.append((rel, f"YAML parse error: {exc}"))
                continue
            if not isinstance(data, dict) or id_field not in data:
                repo.load_errors.append((rel, f"record has no '{id_field}' field"))
                continue
            oid = data[id_field]
            if oid in repo.objects[kind]:
                repo.load_errors.append((rel, f"duplicate {kind} id {oid}"))
                continue
            repo.objects[kind][oid] = data
            repo.paths[(kind, oid)] = rel
    return repo
