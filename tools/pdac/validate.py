"""Validate PDaC records against MIL-STD-882E (2012) model and project tailoring.

Usage: python -m tools.pdac.validate [--strict]
Exit 1 on any error (or any warning with --strict).
"""
from __future__ import annotations

import argparse
import sys

from .load import load
from .rules import RULES, run_all


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--strict", action="store_true", help="treat warnings as errors")
    ap.add_argument("--root", default=None)
    args = ap.parse_args(argv)
    repo = load(args.root) if args.root else load()
    findings = run_all(repo)
    errors = [f for f in findings if f.level == "error"]
    warnings = [f for f in findings if f.level == "warning"]
    counts = {k: len(v) for k, v in repo.objects.items()}
    print("PDaC / MIL-STD-882E (11 May 2012) validation")
    print("records: " + ", ".join(f"{k}={v}" for k, v in counts.items()))
    for f in errors + warnings:
        print(f)
    failed = {f.rule for f in errors}
    print(f"\n{len(RULES) - len(failed)}/{len(RULES)} rules without errors; {len(errors)} error(s), {len(warnings)} warning(s)")
    print("Automated checks cover data, links and logic only. They do not judge technical adequacy or accept risk.")
    return 1 if errors or (args.strict and warnings) else 0


if __name__ == "__main__":
    sys.exit(main())
