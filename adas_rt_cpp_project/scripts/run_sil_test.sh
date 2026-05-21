#!/usr/bin/env bash
# =============================================================================
# run_sil_test.sh — Build and run the SIL AEB scenario test
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
info()  { echo -e "${GREEN}[SIL]${NC}  $*"; }
warn()  { echo -e "${YELLOW}[SIL]${NC}  $*"; }
error() { echo -e "${RED}[SIL]${NC}  $*"; exit 1; }

cd "$PROJECT_ROOT"

info "======= ADAS SIL Test Runner ======="

# ── Verify Bazel ──────────────────────────────────────────────────────────────
if ! command -v bazel &>/dev/null; then
    error "Bazel not found. Install from: https://bazel.build"
fi

# ── Build ─────────────────────────────────────────────────────────────────────
info "Building SIL test binary..."
bazel build //tests/sil:sil_aeb_scenario --config=rt 2>&1 | tail -20

# ── Run unit tests first ──────────────────────────────────────────────────────
info "Running unit tests..."
bazel test //tests/unit/... --test_output=short 2>&1

# ── Run SIL AEB scenario ──────────────────────────────────────────────────────
info "Running SIL AEB scenario..."
bazel test //tests/sil:sil_aeb_scenario \
    --test_output=all \
    --config=rt \
    2>&1

info "======= SIL Tests Complete ======="
