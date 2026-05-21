#!/usr/bin/env bash
# scripts/generate_docs.sh — Generate Doxygen HTML docs
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

if ! command -v doxygen &>/dev/null; then
    echo "doxygen not found. Install with: brew install doxygen (macOS) or apt install doxygen (Linux)"
    exit 1
fi

cd "$PROJECT_ROOT"
doxygen Doxyfile
echo "Docs generated at: $PROJECT_ROOT/docs/html/index.html"
