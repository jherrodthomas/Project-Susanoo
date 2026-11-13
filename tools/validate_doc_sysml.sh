#!/usr/bin/env bash
# Validate the SysML v2 files of the documentation tree (concept, PX4 integration, the decision register, the simulation evidence gate and every generated folder view
# under safety/mil-std-882e), together with the project model they import (models/sysml/model), with the OMG pilot implementation pinned by
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
# The project model first (in the reader's dependency order), then the documentation views that import it.
mapfile -t MODEL < <(python3 -c "from tools.sysml.model import MODEL_FILES, MODEL_DIR; print('\n'.join(str(MODEL_DIR / f) for f in MODEL_FILES))")
mapfile -t VIEWS < <(find safety/mil-std-882e -name '*.sysml' | sort)
FILES=("${MODEL[@]}" concept/ConceptOperations.sysml integrations/px4/PX4Integration.sysml decisions/DecisionRegister.sysml sim/SimulationEvidence.sysml framework/Lifecycle.sysml tools/Toolchain.sysml docs/Documentation.sysml cad/ConceptLayouts.sysml sim/uav/ObservedModes.sysml sim/plant/WalkerPlant.sysml sim/search/FailureSearch.sysml sim/mujoco/WalkerL2.sysml sim/trades/SupplyLossModes.sysml sim/spec/PlantSpecs.sysml sim/results/ResultSets.sysml sim/scenes3d/Scenes3D.sysml sim/figures/HazardScenes.sysml docs/3d/Pages3D.sysml docs/vcycle/MaturityLadder.sysml docs/diagrams/ProcessMaps.sysml docs/readme/FrontPage.sysml docs/wiki/WikiPublication.sysml docs/wiki/images/WikiImages.sysml "${VIEWS[@]}")
OUT="$(java -cp "$JAR:$BUILD" SysMLValidate "$KERNEL/sysml.library" "${FILES[@]}" 2>&1 \
  | grep -vE '^(Reading |log4j:|Picked up JAVA_TOOL_OPTIONS)')" || { echo "$OUT"; exit 1; }
echo "$OUT"
if grep -qE 'ERROR|WARNING' <<<"$OUT"; then
  echo "validate_doc_sysml.sh: SysML errors or warnings in ${#FILES[@]} files" >&2
  exit 1
fi
echo "OK: ${#FILES[@]} SysML files validated (${#MODEL[@]} project model + $(( ${#FILES[@]} - ${#MODEL[@]} )) documentation)"
