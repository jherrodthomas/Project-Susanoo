#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0
# Build the concept layouts, render the review images and regenerate the review page.
#   FREECAD_PYTHON=/opt/freecad/bin/python tools/cad/make.sh [--no-render]
set -euo pipefail
cd "$(dirname "$0")/../.."
PY="${FREECAD_PYTHON:-/opt/freecad/bin/python}"
"$PY" tools/cad/build_concepts.py
if [[ "${1:-}" != "--no-render" ]]; then
  [[ -d tools/cad/node_modules/three ]] || (cd tools/cad && npm ci --no-audit --no-fund)
  node tools/cad/render.cjs
fi
"$PY" tools/cad/drawings.py
if [[ "${1:-}" != "--no-render" ]]; then
  node tools/cad/sheet_png.cjs cad/drawings/CL-*.svg --pdf
fi
python3 tools/pdac/generate.py
python3 tools/pdac/validate.py
