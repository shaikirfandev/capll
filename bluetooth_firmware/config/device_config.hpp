/**
 * @file device_config.hpp
 * @brief Compile-time device configuration constants
 */
#pragma once
#include <cstdint>

namespace bt::config {

// ── Device Identity ───────────────────────────────────────────────────────────
inline constexpr char DEVICE_NAME[]      = "BT-Firmware-Demo";
inline constexpr uint16_t COMPANY_ID     = 0x0059U;  // Qualcomm Inc.
inline constexpr uint8_t  FW_MAJOR       = 2U;
inline constexpr uint8_t  FW_MINOR       = 1U;
inline constexpr uint8_t  FW_PATCH       = 0U;

// ── BLE Connection Parameters ─────────────────────────────────────────────────
inline constexpr uint16_t ADV_INTERVAL_MIN_MS   = 100U;
inline constexpr uint16_t ADV_INTERVAL_MAX_MS   = 150U;
inline constexpr uint16_t CONN_INTERVAL_MIN_MS  = 15U;
inline constexpr uint16_t CONN_INTERVAL_MAX_MS  = 30U;
inline constexpr uint16_t SUPERVISION_TIMEOUT_MS = 4000U;
inline constexpr uint8_t  SLAVE_LATENCY         = 0U;
inline constexpr uint8_t  MAX_CONNECTIONS        = 7U;

// ── Security ──────────────────────────────────────────────────────────────────
inline constexpr uint8_t  MAX_BONDS              = 8U;
inline constexpr bool     REQUIRE_MITM           = true;
inline constexpr bool     SECURE_CONNECTIONS     = true;

// ── OTA ───────────────────────────────────────────────────────────────────────
inline constexpr uint32_t OTA_MAX_FW_SIZE_BYTES  = 1024U * 1024U;  // 1 MB
inline constexpr uint16_t OTA_CHUNK_SIZE_BYTES   = 244U;  // Max GATT ATT payload
inline constexpr uint32_t OTA_TIMEOUT_SECONDS    = 300U;

// ── Hardware Pins ─────────────────────────────────────────────────────────────
inline constexpr uint8_t GPIO_BT_RESET           = 4U;
inline constexpr uint8_t GPIO_BT_WAKE            = 5U;
inline constexpr uint8_t GPIO_BT_HOST_WAKE       = 6U;

// ── UART HCI ──────────────────────────────────────────────────────────────────
inline constexpr uint32_t HCI_UART_BAUD          = 3000000U;
inline constexpr bool     HCI_UART_FLOW_CTRL     = true;

}  // namespace bt::config
