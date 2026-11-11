"""Load sim/spec/walker.yaml and refuse unsourced or out-of-range parameters."""
from __future__ import annotations

import hashlib
from pathlib import Path

from tools.pdac.load import _read_yaml

SIM = Path(__file__).resolve().parents[1]
SPEC = SIM / "spec" / "walker.yaml"
STATUSES = {"assumed", "derived", "published"}


class SpecError(Exception):
    pass


def check(spec: dict) -> dict:
    """Return {name: value} after checking every parameter; raise SpecError on the first problem."""
    out = {}
    for name, p in (spec.get("params") or {}).items():
        for key in ("value", "unit", "range", "status", "source"):
            if key not in p or p[key] in (None, ""):
                raise SpecError(f"{name}: missing {key}")
        if p["status"] not in STATUSES:
            raise SpecError(f"{name}: status {p['status']!r} not in {sorted(STATUSES)}")
        lo, hi = p["range"]
        if not lo <= p["value"] <= hi:
            raise SpecError(f"{name}: value {p['value']} outside range [{lo}, {hi}]")
        out[name] = float(p["value"])
    return out


def load(path: Path = SPEC) -> dict:
    return check(_read_yaml(path))


def digest(path: Path = SPEC) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:12]
