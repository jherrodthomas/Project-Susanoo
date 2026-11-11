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
}

MODEL_PATH = "standards/mil-std-882e/model.yaml"
TAILORING_PATH = "standards/tailoring/mil-std-882e.yaml"
PRODUCT_PATH = "pdac/product.yaml"
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

    def all_ids(self) -> set:
        ids = set()
        for recs in self.objects.values():
            ids.update(str(k) for k in recs)
        return ids


def _read_yaml(path: Path):
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def load(root: Path | str = ROOT) -> Repo:
    root = Path(root)
    repo = Repo(
        root=root,
        model=_read_yaml(root / MODEL_PATH),
        tailoring=_read_yaml(root / TAILORING_PATH),
        product=_read_yaml(root / PRODUCT_PATH) if (root / PRODUCT_PATH).exists() else {},
    )
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
