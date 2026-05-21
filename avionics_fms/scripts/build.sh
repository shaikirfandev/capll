#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BUILD_TYPE=${1:-Debug}
cmake -B "$ROOT/build" -G Ninja \
  -DCMAKE_BUILD_TYPE="$BUILD_TYPE" \
  -DFMS_ENABLE_TESTS=ON \
  -DFMS_ENABLE_ASAN=ON \
  -DFMS_STRICT_WARNINGS=ON \
  "$ROOT"
cmake --build "$ROOT/build" --parallel
echo "Build complete: $ROOT/build"
