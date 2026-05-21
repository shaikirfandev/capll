#!/usr/bin/env bash
# =============================================================================
# setup_vcan.sh — Create and configure virtual CAN interface (vcan0)
# =============================================================================

set -euo pipefail

IFACE="${1:-vcan0}"

echo "Setting up virtual CAN interface: ${IFACE}"

# Load kernel module
if ! lsmod | grep -q "^vcan"; then
    echo "  Loading vcan kernel module..."
    sudo modprobe vcan
fi

# Create interface if it doesn't exist
if ! ip link show "${IFACE}" > /dev/null 2>&1; then
    echo "  Creating ${IFACE}..."
    sudo ip link add dev "${IFACE}" type vcan
    echo "  Interface created."
else
    echo "  ${IFACE} already exists."
fi

# Bring it up
STATE=$(ip link show "${IFACE}" | grep -oP '(?<=state )\w+')
if [[ "${STATE}" != "UNKNOWN" && "${STATE}" != "UP" ]]; then
    sudo ip link set up "${IFACE}"
fi
sudo ip link set up "${IFACE}"

echo "  ✓ ${IFACE} is UP"
ip link show "${IFACE}"

echo ""
echo "Virtual CAN ready. Test with:"
echo "  cansend ${IFACE} 123#DEADBEEF"
echo "  candump ${IFACE}"
