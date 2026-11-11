#!/usr/bin/env bash
# Fetch and build the pinned PX4-Autopilot for the SUS-A1 SITL scenarios (sim/uav/harness.py).
# Usage: fetch_px4.sh DIR   -> DIR holds PX4-Autopilot at the pinned tag with build/px4_sitl_default built.
# Needs git, cmake, ninja, a C++ toolchain and the Python packages in sim/uav/requirements-px4-build.txt.
set -euo pipefail
TAG="v1.16.2"
DIR="${1:?usage: fetch_px4.sh DIR}"
if [ ! -d "$DIR/.git" ]; then
  git clone -q --depth 1 --branch "$TAG" --recurse-submodules --shallow-submodules \
    https://github.com/PX4/PX4-Autopilot.git "$DIR"
fi
test "$(git -C "$DIR" describe --tags --always)" = "$TAG" || { echo "fetch_px4.sh: $DIR is not at $TAG" >&2; exit 1; }
# A shallow clone carries no NuttX tags, which PX4's version header generator expects even for SITL builds.
# The local tag only satisfies that lookup; SITL does not use NuttX.
git -C "$DIR/platforms/nuttx/NuttX/nuttx" tag -f nuttx-0.0.0 >/dev/null
make -C "$DIR" px4_sitl_default
