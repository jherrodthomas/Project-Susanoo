#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Check the PDaC records (checks P1-P9, see pdac/README.md). Exit status 1 on any finding.

    python3 tools/pdac/validate.py
"""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pdaclib  # noqa: E402


def main() -> int:
    model = pdaclib.load()
    findings = pdaclib.validate(model, pdaclib.load_schema())
    kinds = Counter(item.get("kind") for _, item in model.items)
    print(f"pdac: {len(model.files)} record files, {len(model.items)} records: "
          + ", ".join(f"{k}={n}" for k, n in sorted(kinds.items())))
    for finding in findings:
        print(f"FAIL {finding}")
    if findings:
        print(f"{len(findings)} finding(s)")
        return 1
    print("OK: checks P1-P9 passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
