#!/usr/bin/env bash
# scripts/build.sh — Convenience build wrapper
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BUILD_DIR="${PROJECT_ROOT}/build"

# Defaults
BUILD_TYPE="${BUILD_TYPE:-Debug}"
ENABLE_TESTS="${ENABLE_TESTS:-ON}"
ENABLE_ASAN="${ENABLE_ASAN:-OFF}"
ENABLE_TSAN="${ENABLE_TSAN:-OFF}"
ENABLE_COVERAGE="${ENABLE_COVERAGE:-OFF}"
GENERATOR="${GENERATOR:-Ninja}"

echo "=== Bluetooth Firmware Build ==="
echo "  BUILD_TYPE     : $BUILD_TYPE"
echo "  ENABLE_TESTS   : $ENABLE_TESTS"
echo "  ENABLE_ASAN    : $ENABLE_ASAN"
echo "  ENABLE_TSAN    : $ENABLE_TSAN"
echo "  ENABLE_COVERAGE: $ENABLE_COVERAGE"
echo "================================"

cmake -B "$BUILD_DIR" \
    -DCMAKE_BUILD_TYPE="$BUILD_TYPE" \
    -DBT_ENABLE_TESTS="$ENABLE_TESTS" \
    -DBT_ASAN="$ENABLE_ASAN" \
    -DBT_TSAN="$ENABLE_TSAN" \
    -DBT_COVERAGE="$ENABLE_COVERAGE" \
    -G "$GENERATOR" \
    "$PROJECT_ROOT"

cmake --build "$BUILD_DIR" --parallel "$(nproc 2>/dev/null || sysctl -n hw.ncpu)"

echo "Build complete: $BUILD_DIR"
