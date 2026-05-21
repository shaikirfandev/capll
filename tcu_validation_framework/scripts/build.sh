#!/usr/bin/env bash
# =============================================================================
# build.sh — Configure and build TCU Validation Framework
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
BUILD_TYPE="${BUILD_TYPE:-Debug}"
BUILD_DIR="${PROJECT_ROOT}/build/${BUILD_TYPE}"
GENERATOR="${GENERATOR:-Ninja}"
JOBS="${JOBS:-$(nproc)}"

print_section() { echo -e "\n\033[1;36m==> $*\033[0m"; }
print_ok()      { echo -e "\033[0;32m    ✓ $*\033[0m"; }

cd "${PROJECT_ROOT}"

print_section "Build configuration"
echo "  Project root : ${PROJECT_ROOT}"
echo "  Build dir    : ${BUILD_DIR}"
echo "  Build type   : ${BUILD_TYPE}"
echo "  Generator    : ${GENERATOR}"
echo "  Jobs         : ${JOBS}"

mkdir -p "${BUILD_DIR}"
cd "${BUILD_DIR}"

print_section "Running CMake configure"
cmake "${PROJECT_ROOT}" \
    -G "${GENERATOR}" \
    -DCMAKE_BUILD_TYPE="${BUILD_TYPE}" \
    -DCMAKE_EXPORT_COMPILE_COMMANDS=ON \
    -DBUILD_TESTS=ON \
    "${@}"

print_ok "CMake configure complete"

print_section "Building"
cmake --build . --parallel "${JOBS}"

print_ok "Build complete"
echo ""
echo "Artifacts:"
echo "  Executable:  ${BUILD_DIR}/bin/tcu_validator"
echo "  Unit tests:  ${BUILD_DIR}/bin/unit_tests"
echo "  Integ tests: ${BUILD_DIR}/bin/integration_tests"
echo "  Libraries:   ${BUILD_DIR}/lib/"
echo ""
echo "Run tests with:"
echo "  scripts/run_tests.sh"
