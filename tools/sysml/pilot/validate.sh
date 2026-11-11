#!/usr/bin/env bash
# Validate the Susanoo SysML v2 model with the OMG pilot implementation (pinned in fetch_pilot.py).
# Parses the model files in dependency order and fails on any syntax or semantic error.
# Usage: validate.sh [cache-dir]   (needs JDK 21+ (javac) and python3 with zstandard)
set -euo pipefail
JAVA_MAJOR="$(javac -version 2>&1 | grep -oE '[0-9]+' | head -1)"
if [ "${JAVA_MAJOR:-0}" -lt 21 ]; then
  echo "validate.sh: the pilot implementation needs JDK 21 or newer; javac reports ${JAVA_MAJOR:-none}" >&2
  exit 1
fi
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../../.." && pwd)"
CACHE="${1:-${XDG_CACHE_HOME:-$HOME/.cache}/susanoo-sysml-pilot}"
KERNEL="$(python3 "$HERE/fetch_pilot.py" "$CACHE")"
JAR="$(ls "$KERNEL"/jupyter-sysml-kernel-*-all.jar)"
BUILD="$CACHE/classes"
mkdir -p "$BUILD"
javac -d "$BUILD" -cp "$JAR" "$HERE/SysMLValidate.java"
mapfile -t FILES < <(cd "$ROOT" && python3 -c "from tools.sysml.model import MODEL_FILES, MODEL_DIR; print('\n'.join(str(MODEL_DIR / f) for f in MODEL_FILES))")
java -cp "$JAR:$BUILD" SysMLValidate "$KERNEL/sysml.library" "${FILES[@]}" 2>&1 | grep -vE '^(Reading |log4j:|Picked up JAVA_TOOL_OPTIONS)'
