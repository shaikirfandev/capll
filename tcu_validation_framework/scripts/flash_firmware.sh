#!/usr/bin/env bash
# =============================================================================
# flash_firmware.sh — Flash TCU firmware via UDS or Renesas RFP CLI
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
BUILD_TYPE="${BUILD_TYPE:-Release}"
BUILD_DIR="${PROJECT_ROOT}/build/${BUILD_TYPE}"

# Defaults (override via environment variables)
FIRMWARE_FILE="${FIRMWARE_FILE:-firmware/tcu_firmware.hex}"
FIRMWARE_VERSION="${FIRMWARE_VERSION:-unknown}"
CAN_INTERFACE="${CAN_INTERFACE:-can0}"
FLASH_METHOD="${FLASH_METHOD:-uds}"   # uds | rfp
TARGET_ADDRESS="${TARGET_ADDRESS:-0x08000000}"
CONFIG_FILE="${CONFIG_FILE:-${PROJECT_ROOT}/configs/production.json}"

print_section() { echo -e "\n\033[1;36m==> $*\033[0m"; }
print_ok()      { echo -e "\033[0;32m    ✓ $*\033[0m"; }

# ----------------------
# Validation
# ----------------------
print_section "Firmware Flash"
echo "  File      : ${FIRMWARE_FILE}"
echo "  Version   : ${FIRMWARE_VERSION}"
echo "  Interface : ${CAN_INTERFACE}"
echo "  Method    : ${FLASH_METHOD}"
echo "  Address   : ${TARGET_ADDRESS}"

if [[ ! -f "${FIRMWARE_FILE}" ]]; then
    echo "ERROR: Firmware file not found: ${FIRMWARE_FILE}"
    exit 1
fi

VALIDATOR="${BUILD_DIR}/bin/tcu_validator"
if [[ ! -f "${VALIDATOR}" ]]; then
    echo "ERROR: tcu_validator binary not found at ${VALIDATOR}"
    echo "       Run: BUILD_TYPE=Release scripts/build.sh"
    exit 1
fi

# ----------------------
# Execute flash via tcu_validator
# ----------------------
print_section "Starting flash via tcu_validator"
"${VALIDATOR}" \
    --config "${CONFIG_FILE}" \
    --interface "${CAN_INTERFACE}" \
    --suite "FirmwareFlash"

EXIT_CODE=$?

if [[ ${EXIT_CODE} -eq 0 ]]; then
    print_ok "Firmware flash SUCCEEDED"
else
    echo "ERROR: Firmware flash FAILED (exit code ${EXIT_CODE})"
    exit ${EXIT_CODE}
fi
