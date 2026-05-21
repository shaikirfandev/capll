#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cmake -B "$ROOT/build_cov" -G Ninja \
  -DCMAKE_BUILD_TYPE=Debug \
  -DFMS_ENABLE_TESTS=ON \
  -DFMS_ENABLE_COVERAGE=ON "$ROOT"
cmake --build "$ROOT/build_cov" --parallel
(cd "$ROOT/build_cov" && ctest --output-on-failure)
mkdir -p "$ROOT/build_cov/coverage"
gcovr -r "$ROOT" --html --html-details \
  -o "$ROOT/build_cov/coverage/index.html" \
  --exclude "$ROOT/tests" \
  --exclude ".*/_deps/.*"
echo "Coverage report: $ROOT/build_cov/coverage/index.html"
