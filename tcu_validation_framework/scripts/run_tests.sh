#!/usr/bin/env bash
# =============================================================================
# run_tests.sh — Run test suites with optional coverage report
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
BUILD_TYPE="${BUILD_TYPE:-Debug}"
BUILD_DIR="${PROJECT_ROOT}/build/${BUILD_TYPE}"
REPORT_DIR="${PROJECT_ROOT}/reports"
COVERAGE="${COVERAGE:-0}"
FILTER="${FILTER:-}"  # Optional test filter, e.g. "FILTER=*CAN*"

print_section() { echo -e "\n\033[1;36m==> $*\033[0m"; }
print_ok()      { echo -e "\033[0;32m    ✓ $*\033[0m"; }
print_fail()    { echo -e "\033[0;31m    ✗ $*\033[0m"; }

mkdir -p "${REPORT_DIR}"
cd "${PROJECT_ROOT}"

# ----------------------
# vcan0 setup
# ----------------------
print_section "Ensuring vcan0 is available"
if ip link show vcan0 > /dev/null 2>&1; then
    print_ok "vcan0 present"
else
    "${SCRIPT_DIR}/setup_vcan.sh" || print_section "vcan0 unavailable — integration tests will be skipped"
fi

# ----------------------
# Unit tests
# ----------------------
print_section "Running unit tests"
UNIT_BIN="${BUILD_DIR}/bin/unit_tests"
if [[ ! -f "${UNIT_BIN}" ]]; then
    echo "Unit test binary not found: ${UNIT_BIN}"
    echo "Run scripts/build.sh first."
    exit 1
fi

UNIT_ARGS="--gtest_output=xml:${REPORT_DIR}/unit_tests.xml"
[[ -n "${FILTER}" ]] && UNIT_ARGS="${UNIT_ARGS} --gtest_filter=${FILTER}"

if "${UNIT_BIN}" ${UNIT_ARGS}; then
    print_ok "Unit tests PASSED"
else
    print_fail "Unit tests FAILED"
    UNIT_FAILED=1
fi

# ----------------------
# Integration tests
# ----------------------
print_section "Running integration tests"
INTEG_BIN="${BUILD_DIR}/bin/integration_tests"
INTEG_ARGS="--gtest_output=xml:${REPORT_DIR}/integration_tests.xml"

if "${INTEG_BIN}" ${INTEG_ARGS}; then
    print_ok "Integration tests PASSED"
else
    print_fail "Integration tests FAILED"
    INTEG_FAILED=1
fi

# ----------------------
# Coverage (optional)
# ----------------------
if [[ "${COVERAGE}" == "1" ]]; then
    print_section "Generating coverage report"
    gcovr \
        --root "${PROJECT_ROOT}/src" \
        --html-details "${REPORT_DIR}/coverage.html" \
        --xml "${REPORT_DIR}/coverage.xml" \
        --exclude "${PROJECT_ROOT}/tests" \
        --exclude "${PROJECT_ROOT}/build" \
        --print-summary
    print_ok "Coverage report: ${REPORT_DIR}/coverage.html"
fi

# ----------------------
# Summary
# ----------------------
print_section "Test run complete"
echo "Reports: ${REPORT_DIR}/"
[[ -z "${UNIT_FAILED:-}" && -z "${INTEG_FAILED:-}" ]] && exit 0 || exit 1
