#!/usr/bin/env bash
# Validate the SysML v2 files of the documentation tree (canonical models, concept, PX4 integration and every
# generated folder view under safety/mil-std-882e) with the OMG pilot implementation pinned by
# tools/sysml/pilot. Files are passed in dependency order. Needs JDK 21+ and python3 with zstandard.
# Usage: tools/validate_doc_sysml.sh [cache-dir]
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CACHE="${1:-${XDG_CACHE_HOME:-$HOME/.cache}/susanoo-sysml-pilot}"
KERNEL="$(python3 "$ROOT/tools/sysml/pilot/fetch_pilot.py" "$CACHE")"
JAR="$(ls "$KERNEL"/jupyter-sysml-kernel-*-all.jar)"
BUILD="$CACHE/classes"
mkdir -p "$BUILD"
javac -d "$BUILD" -cp "$JAR" "$ROOT/tools/sysml/pilot/SysMLValidate.java"
cd "$ROOT"
BASE=safety/mil-std-882e/00-system-definition/sysml
mapfile -t VIEWS < <(find safety/mil-std-882e -name '*.sysml' -not -path "$BASE/*" | sort)
# Task203_SRHA must come first: other views reference its requirement definitions.
mapfile -t ORDERED < <(printf '%s\n' "${VIEWS[@]}" | grep Task203_SRHA; printf '%s\n' "${VIEWS[@]}" | grep -v Task203_SRHA | sort)
FILES=("$BASE/SusanooSystem.sysml" "$BASE/SusanooSafety.sysml" concept/ConceptOperations.sysml \
       integrations/px4/PX4Integration.sysml "${ORDERED[@]}")
OUT="$(java -cp "$JAR:$BUILD" SysMLValidate "$KERNEL/sysml.library" "${FILES[@]}" 2>&1 \
  | grep -vE '^(Reading |log4j:|Picked up JAVA_TOOL_OPTIONS)')" || { echo "$OUT"; exit 1; }
echo "$OUT"
if grep -qE 'ERROR|WARNING' <<<"$OUT"; then
  echo "validate_doc_sysml.sh: SysML errors or warnings in ${#FILES[@]} files" >&2
  exit 1
fi
echo "OK: ${#FILES[@]} documentation SysML files validated"
