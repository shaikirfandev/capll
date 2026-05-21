#!/usr/bin/env bash
# =============================================================================
# setup.sh — Install all build dependencies for TCU Validation Framework
# Target OS: Ubuntu 20.04 / 22.04
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

print_section() { echo -e "\n\033[1;36m==> $*\033[0m"; }
print_ok()      { echo -e "\033[0;32m    ✓ $*\033[0m"; }
print_warn()    { echo -e "\033[0;33m    ⚠ $*\033[0m"; }

print_section "TCU Validation Framework — Dependency Setup"
echo "Project root: ${PROJECT_ROOT}"

# ----------------------
# System packages
# ----------------------
print_section "Installing system packages"
sudo apt-get update -q
sudo apt-get install -y \
    build-essential \
    cmake \
    ninja-build \
    git \
    pkg-config \
    python3 \
    python3-pip \
    curl \
    wget \
    unzip \
    lcov \
    gcovr \
    cppcheck \
    clang \
    clang-tidy \
    clang-format \
    valgrind \
    linux-tools-generic \
    can-utils \
    iproute2 \
    libssl-dev \
    doxygen \
    graphviz

print_ok "System packages installed"

# ----------------------
# CMake version check
# ----------------------
CMAKE_VERSION=$(cmake --version | head -1 | awk '{print $3}')
print_section "CMake version: ${CMAKE_VERSION}"
if [[ "$(printf '%s\n' "3.18" "${CMAKE_VERSION}" | sort -V | head -n1)" != "3.18" ]]; then
    print_warn "CMake < 3.18 detected — upgrading via pip"
    pip3 install cmake --upgrade
fi

# ----------------------
# Python tools (for can_replay.py)
# ----------------------
print_section "Installing Python tooling"
pip3 install python-can cantools

# ----------------------
# vcan kernel module
# ----------------------
print_section "Loading vcan kernel module"
if lsmod | grep -q "^vcan"; then
    print_ok "vcan already loaded"
else
    sudo modprobe vcan && print_ok "vcan loaded"
fi

# Make it persistent across reboots
if ! grep -q "vcan" /etc/modules 2>/dev/null; then
    echo "vcan" | sudo tee -a /etc/modules > /dev/null
    print_ok "vcan added to /etc/modules"
fi

# ----------------------
# Docker (optional)
# ----------------------
if ! command -v docker &>/dev/null; then
    print_section "Installing Docker"
    curl -fsSL https://get.docker.com | sudo bash
    sudo usermod -aG docker "${USER}"
    print_ok "Docker installed (re-login required for group)"
else
    print_ok "Docker already installed: $(docker --version)"
fi

# ----------------------
# Done
# ----------------------
print_section "Setup complete"
echo "Next steps:"
echo "  1. Run: scripts/setup_vcan.sh   — create vcan0 interface"
echo "  2. Run: scripts/build.sh        — configure and build"
echo "  3. Run: scripts/run_tests.sh    — execute test suite"
