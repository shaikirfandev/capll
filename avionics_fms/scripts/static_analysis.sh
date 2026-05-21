#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
echo "=== cppcheck ==="
cppcheck --enable=all --inconclusive --std=c++17 \
  --suppress=missingIncludeSystem \
  --suppress=unusedFunction \
  -I "$ROOT/include" -I "$ROOT/src" \
  "$ROOT/src" 2>&1 | tee "$ROOT/build/cppcheck.log"
echo "=== clang-tidy ==="
if command -v clang-tidy-15 &>/dev/null; then
  find "$ROOT/src" -name "*.cpp" | xargs clang-tidy-15 \
    -p "$ROOT/build" \
    --checks="-*,clang-analyzer-*,bugprone-*,performance-*" 2>&1 | tee "$ROOT/build/clang_tidy.log"
fi
echo "Static analysis complete."
