#!/usr/bin/env bash
# scripts/run_tests.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="$(dirname "$SCRIPT_DIR")/build"

if [[ ! -d "$BUILD_DIR" ]]; then
    echo "Build directory not found. Run scripts/build.sh first."
    exit 1
fi

echo "=== Running Unit Tests ==="
ctest --test-dir "$BUILD_DIR/tests/unit" \
    -V --output-on-failure --timeout 120 || UNIT_FAILED=1

echo ""
echo "=== Running Integration Tests ==="
ctest --test-dir "$BUILD_DIR/tests/integration" \
    -V --output-on-failure --timeout 120 || INTEG_FAILED=1

if [[ "${UNIT_FAILED:-0}" -ne 0 || "${INTEG_FAILED:-0}" -ne 0 ]]; then
    echo "TESTS FAILED"
    exit 1
fi
echo "All tests passed."
