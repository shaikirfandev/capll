/**
 * @file BluetoothTypes.hpp
 * @brief Core Bluetooth type definitions and constants
 *
 * Defines the fundamental types, enumerations, and data structures used
 * across the entire Bluetooth firmware stack. Compatible with BLE 5.3,
 * Classic Bluetooth 5.0, and Dual-Mode operation.
 *
 * @version 2.1.0
 * @author  Automotive BT Firmware Team
 * @standard MISRA C++:2023 inspired, AUTOSAR Adaptive C++ Guidelines
 */

#pragma once

#include <array>
#include <cstdint>
#include <cstring>
#include <functional>
#include <optional>
#include <string>
#include <string_view>
#include <variant>
#include <vector>

namespace bt {

// ─────────────────────────────────────────────────────────────────────────────
// Version
// ─────────────────────────────────────────────────────────────────────────────
inline constexpr uint8_t  BT_MAJOR_VERSION = 2U;
inline constexpr uint8_t  BT_MINOR_VERSION = 1U;
inline constexpr uint8_t  BT_PATCH_VERSION = 0U;

// ─────────────────────────────────────────────────────────────────────────────
// Fundamental types
// ─────────────────────────────────────────────────────────────────────────────

/// Bluetooth device address (6 bytes, LSB first — Bluetooth spec ordering)
using BdAddr = std::array<uint8_t, 6>;

/// UUID-128 representation
using Uuid128 = std::array<uint8_t, 16>;

/// UUID-16 (short form, Bluetooth SIG assigned numbers)
using Uuid16 = uint16_t;

/// HCI handle for connections (12-bit active value range 0x0000–0x0EFF)
using ConnHandle = uint16_t;

/// ATT handle (1-based, 0x0001–0xFFFF)
using AttHandle = uint16_t;

inline constexpr ConnHandle INVALID_CONN_HANDLE = 0xFFFFU;
inline constexpr AttHandle  INVALID_ATT_HANDLE  = 0x0000U;

// ─────────────────────────────────────────────────────────────────────────────
// Bluetooth address helpers
// ─────────────────────────────────────────────────────────────────────────────
inline constexpr BdAddr NULL_BDADDR = {0x00, 0x00, 0x00, 0x00, 0x00, 0x00};

/// @brief Parse "XX:XX:XX:XX:XX:XX" string to BdAddr
inline BdAddr parse_bdaddr(std::string_view str) noexcept {
    BdAddr addr{};
    if (str.size() < 17U) { return addr; }
    for (int i = 5; i >= 0; --i) {
        auto pos  = static_cast<std::size_t>((5 - i) * 3);
        addr[static_cast<std::size_t>(i)] =
            static_cast<uint8_t>(std::stoi(std::string(str.substr(pos, 2U)), nullptr, 16));
    }
    return addr;
}

/// @brief Format BdAddr to "XX:XX:XX:XX:XX:XX" string
inline std::string format_bdaddr(const BdAddr &addr) {
    char buf[18];
    snprintf(buf, sizeof(buf), "%02X:%02X:%02X:%02X:%02X:%02X",
             addr[5], addr[4], addr[3], addr[2], addr[1], addr[0]);
    return std::string(buf);
}

// ─────────────────────────────────────────────────────────────────────────────
// Bluetooth mode
// ─────────────────────────────────────────────────────────────────────────────
enum class BtMode : uint8_t {
    BLE_ONLY     = 0x01U,  ///< BLE only (low-energy)
    CLASSIC_ONLY = 0x02U,  ///< Classic Bluetooth (BR/EDR) only
    DUAL_MODE    = 0x03U,  ///< Both BLE and Classic simultaneously
};

// ─────────────────────────────────────────────────────────────────────────────
// Connection state
// ─────────────────────────────────────────────────────────────────────────────
enum class ConnState : uint8_t {
    IDLE         = 0x00U,
    SCANNING     = 0x01U,
    ADVERTISING  = 0x02U,
    CONNECTING   = 0x03U,
    CONNECTED    = 0x04U,
    PAIRING      = 0x05U,
    PAIRED       = 0x06U,
    DISCONNECTING= 0x07U,
    ERROR        = 0xFFU,
};

inline constexpr std::string_view conn_state_str(ConnState s) noexcept {
    switch (s) {
        case ConnState::IDLE:          return "IDLE";
        case ConnState::SCANNING:      return "SCANNING";
        case ConnState::ADVERTISING:   return "ADVERTISING";
        case ConnState::CONNECTING:    return "CONNECTING";
        case ConnState::CONNECTED:     return "CONNECTED";
        case ConnState::PAIRING:       return "PAIRING";
        case ConnState::PAIRED:        return "PAIRED";
        case ConnState::DISCONNECTING: return "DISCONNECTING";
        case ConnState::ERROR:         return "ERROR";
        default:                       return "UNKNOWN";
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// BLE advertising types
// ─────────────────────────────────────────────────────────────────────────────
enum class AdvType : uint8_t {
    ADV_IND          = 0x00U,  ///< Connectable, undirected
    ADV_DIRECT_IND   = 0x01U,  ///< Connectable, directed (high duty)
    ADV_SCAN_IND     = 0x02U,  ///< Scannable, undirected
    ADV_NONCONN_IND  = 0x03U,  ///< Non-connectable, undirected (beacon)
    ADV_DIRECT_LOW   = 0x04U,  ///< Connectable, directed (low duty)
};

enum class AdvFilter : uint8_t {
    NO_FILTER        = 0x00U,  ///< Process all scan + connect
    WHITELIST_SCAN   = 0x01U,  ///< Scan only from whitelist
    WHITELIST_CONN   = 0x02U,  ///< Connect only from whitelist
    WHITELIST_ALL    = 0x03U,  ///< Both scan + connect from whitelist
};

/// BLE advertising parameters
struct AdvParams {
    uint16_t  interval_min_ms{100U};   ///< Min advertising interval (ms)
    uint16_t  interval_max_ms{150U};   ///< Max advertising interval (ms)
    AdvType   type{AdvType::ADV_IND};
    AdvFilter filter{AdvFilter::NO_FILTER};
    BdAddr    peer_addr{NULL_BDADDR};  ///< For directed advertising
    bool      own_addr_random{false};  ///< true = use random address
};

/// BLE advertising data structure
struct AdvData {
    std::vector<uint8_t> ad_records;  ///< Raw AD records (type-length-value)
    uint8_t              length{0U};  ///< Total length of ad_records

    /// @brief Append a standard AD record (AD type + payload)
    void append(uint8_t ad_type, const uint8_t *payload, uint8_t pay_len) {
        ad_records.push_back(static_cast<uint8_t>(pay_len + 1U));  // length
        ad_records.push_back(ad_type);
        ad_records.insert(ad_records.end(), payload, payload + pay_len);
        length = static_cast<uint8_t>(ad_records.size());
    }
};

// ─────────────────────────────────────────────────────────────────────────────
// GATT types
// ─────────────────────────────────────────────────────────────────────────────
enum class GattPerm : uint8_t {
    NONE         = 0x00U,
    READ         = 0x01U,
    WRITE        = 0x02U,
    READ_WRITE   = 0x03U,
    READ_ENCRYPT = 0x04U,  ///< Read requires encryption
    WRITE_ENCRYPT= 0x08U,  ///< Write requires encryption
    READ_AUTHEN  = 0x10U,  ///< Read requires authentication
    WRITE_AUTHEN = 0x20U,  ///< Write requires authentication
};

inline GattPerm operator|(GattPerm a, GattPerm b) {
    return static_cast<GattPerm>(static_cast<uint8_t>(a) | static_cast<uint8_t>(b));
}
inline bool has_perm(GattPerm perm, GattPerm flag) {
    return (static_cast<uint8_t>(perm) & static_cast<uint8_t>(flag)) != 0U;
}

enum class GattProp : uint8_t {
    BROADCAST       = 0x01U,
    READ            = 0x02U,
    WRITE_NO_RSP    = 0x04U,
    WRITE           = 0x08U,
    NOTIFY          = 0x10U,
    INDICATE        = 0x20U,
    AUTH_SIGNED     = 0x40U,
    EXTENDED        = 0x80U,
};

inline GattProp operator|(GattProp a, GattProp b) {
    return static_cast<GattProp>(static_cast<uint8_t>(a) | static_cast<uint8_t>(b));
}

/// GATT characteristic definition
struct GattCharDef {
    Uuid16                             uuid{0x0000U};
    GattProp                           properties{GattProp::READ};
    GattPerm                           permissions{GattPerm::READ};
    std::vector<uint8_t>               initial_value{};
    uint16_t                           max_value_len{512U};
    AttHandle                          handle{INVALID_ATT_HANDLE};
    AttHandle                          value_handle{INVALID_ATT_HANDLE};
    AttHandle                          cccd_handle{INVALID_ATT_HANDLE};  ///< For notify/indicate
};

/// GATT service definition
struct GattServiceDef {
    Uuid16                            service_uuid{0x0000U};
    bool                              is_primary{true};
    AttHandle                         start_handle{INVALID_ATT_HANDLE};
    AttHandle                         end_handle{INVALID_ATT_HANDLE};
    std::vector<GattCharDef>          characteristics{};
};

// ─────────────────────────────────────────────────────────────────────────────
// Pairing / Security
// ─────────────────────────────────────────────────────────────────────────────
enum class PairingMethod : uint8_t {
    JUST_WORKS       = 0x00U,  ///< No user interaction (low security)
    PASSKEY_ENTRY    = 0x01U,  ///< Passkey displayed or entered
    NUMERIC_COMP     = 0x02U,  ///< Both show 6-digit number to compare
    OOB              = 0x03U,  ///< Out-of-band (NFC, QR)
    LEGACY_PAIRING   = 0x04U,  ///< Classic BT PIN
};

enum class SecurityLevel : uint8_t {
    NONE             = 0x00U,
    UNAUTHENTICATED  = 0x01U,  ///< Encrypted but not authenticated
    AUTHENTICATED    = 0x02U,  ///< MITM protected
    SECURE_CONN      = 0x03U,  ///< LE Secure Connections (ECDH)
};

struct PairingKeys {
    std::array<uint8_t, 16> ltk{};     ///< Long Term Key (encryption)
    std::array<uint8_t, 8>  rand{};    ///< Random value for LTK
    uint16_t                ediv{0U};  ///< Encrypted Diversifier
    std::array<uint8_t, 16> irk{};     ///< Identity Resolving Key
    std::array<uint8_t, 16> csrk{};   ///< Connection Signature Resolving Key
    SecurityLevel           sec_level{SecurityLevel::NONE};
    bool                    valid{false};
};

// ─────────────────────────────────────────────────────────────────────────────
// HCI Event types
// ─────────────────────────────────────────────────────────────────────────────
enum class HciEventCode : uint8_t {
    INQUIRY_COMPLETE        = 0x01U,
    CONN_COMPLETE           = 0x03U,
    DISCONN_COMPLETE        = 0x05U,
    ENCRYPTION_CHANGE       = 0x08U,
    REMOTE_FEATURES         = 0x0BU,
    PIN_CODE_REQ            = 0x16U,
    LINK_KEY_NOTIFY         = 0x18U,
    NUM_COMPLETED_PKTS      = 0x13U,
    LE_META                 = 0x3EU,
};

enum class LeMetaSubEvent : uint8_t {
    LE_CONN_COMPLETE        = 0x01U,
    LE_ADV_REPORT           = 0x02U,
    LE_CONN_UPDATE_COMPLETE = 0x03U,
    LE_READ_REMOTE_FEATURES = 0x04U,
    LE_LTK_REQUEST          = 0x05U,
    LE_ENHANCED_CONN_COMPLETE = 0x0AU,
    LE_PHY_UPDATE_COMPLETE  = 0x0CU,
};

// ─────────────────────────────────────────────────────────────────────────────
// Bluetooth event data (std::variant for type-safe dispatch)
// ─────────────────────────────────────────────────────────────────────────────
struct EvtConnected {
    ConnHandle  handle;
    BdAddr      peer_addr;
    BtMode      mode;
    uint16_t    conn_interval_ms;
    uint16_t    supervision_timeout_ms;
};

struct EvtDisconnected {
    ConnHandle  handle;
    uint8_t     reason;  ///< HCI disconnect reason code
};

struct EvtPairingComplete {
    ConnHandle    handle;
    BdAddr        peer_addr;
    PairingKeys   keys;
    bool          success;
    uint8_t       fail_reason;  ///< SMP pairing failure reason (if !success)
};

struct EvtGattWrite {
    ConnHandle         handle;
    AttHandle          att_handle;
    std::vector<uint8_t> value;
    bool               with_response;  ///< true = Write Command, false = Write Request
};

struct EvtGattRead {
    ConnHandle  handle;
    AttHandle   att_handle;
};

struct EvtGattNotify {
    ConnHandle           handle;
    AttHandle            att_handle;
    std::vector<uint8_t> value;
    bool                 is_indication;
};

struct EvtOtaProgress {
    uint32_t  bytes_received;
    uint32_t  total_bytes;
    uint8_t   percent;
};

struct EvtBleAdv {
    BdAddr               peer_addr;
    int8_t               rssi;
    AdvType              type;
    std::vector<uint8_t> adv_data;
};

struct EvtError {
    uint32_t    error_code;
    std::string description;
};

/// Unified Bluetooth event variant
using BtEvent = std::variant<
    EvtConnected,
    EvtDisconnected,
    EvtPairingComplete,
    EvtGattWrite,
    EvtGattRead,
    EvtGattNotify,
    EvtOtaProgress,
    EvtBleAdv,
    EvtError
>;

// ─────────────────────────────────────────────────────────────────────────────
// Power management
// ─────────────────────────────────────────────────────────────────────────────
enum class PowerState : uint8_t {
    ACTIVE       = 0x00U,  ///< Full power, all functions available
    LOW_POWER    = 0x01U,  ///< Reduced scan/advertising interval
    SNIFF        = 0x02U,  ///< Classic BT sniff mode
    BLE_CONN_LP  = 0x03U,  ///< BLE connection with long interval
    SLEEP        = 0x04U,  ///< Deep sleep, minimal stack activity
    OFF          = 0x05U,  ///< Radio off
};

// ─────────────────────────────────────────────────────────────────────────────
// Error codes
// ─────────────────────────────────────────────────────────────────────────────
enum class BtError : int32_t {
    OK                     =  0,
    ERR_GENERIC            = -1,
    ERR_INVALID_PARAM      = -2,
    ERR_NOT_SUPPORTED      = -3,
    ERR_TIMEOUT            = -4,
    ERR_NO_RESOURCES       = -5,
    ERR_NOT_CONNECTED      = -6,
    ERR_ALREADY_CONNECTED  = -7,
    ERR_PAIRING_FAILED     = -8,
    ERR_SECURITY           = -9,
    ERR_GATT_ERROR         = -10,
    ERR_HCI_ERROR          = -11,
    ERR_OTA_ABORT          = -12,
    ERR_INVALID_STATE      = -13,
    ERR_BUFF_OVERFLOW      = -14,
    ERR_HARDWARE           = -15,
};

inline constexpr std::string_view bt_error_str(BtError e) noexcept {
    switch (e) {
        case BtError::OK:                    return "OK";
        case BtError::ERR_GENERIC:           return "GENERIC_ERROR";
        case BtError::ERR_INVALID_PARAM:     return "INVALID_PARAM";
        case BtError::ERR_NOT_SUPPORTED:     return "NOT_SUPPORTED";
        case BtError::ERR_TIMEOUT:           return "TIMEOUT";
        case BtError::ERR_NO_RESOURCES:      return "NO_RESOURCES";
        case BtError::ERR_NOT_CONNECTED:     return "NOT_CONNECTED";
        case BtError::ERR_ALREADY_CONNECTED: return "ALREADY_CONNECTED";
        case BtError::ERR_PAIRING_FAILED:    return "PAIRING_FAILED";
        case BtError::ERR_SECURITY:          return "SECURITY_ERROR";
        case BtError::ERR_GATT_ERROR:        return "GATT_ERROR";
        case BtError::ERR_HCI_ERROR:         return "HCI_ERROR";
        case BtError::ERR_OTA_ABORT:         return "OTA_ABORT";
        case BtError::ERR_INVALID_STATE:     return "INVALID_STATE";
        case BtError::ERR_BUFF_OVERFLOW:     return "BUFFER_OVERFLOW";
        case BtError::ERR_HARDWARE:          return "HARDWARE_ERROR";
        default:                             return "UNKNOWN_ERROR";
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// Bluetooth SIG assigned UUID-16 constants
// ─────────────────────────────────────────────────────────────────────────────
namespace uuid {
    // Services
    inline constexpr Uuid16 GENERIC_ACCESS         = 0x1800U;
    inline constexpr Uuid16 GENERIC_ATTRIBUTE      = 0x1801U;
    inline constexpr Uuid16 DEVICE_INFORMATION     = 0x180AU;
    inline constexpr Uuid16 BATTERY_SERVICE        = 0x180FU;
    inline constexpr Uuid16 HEART_RATE             = 0x180DU;
    inline constexpr Uuid16 HUMAN_INTERFACE_DEVICE = 0x1812U;
    inline constexpr Uuid16 AUDIO_SOURCE           = 0x110AU;
    inline constexpr Uuid16 AUDIO_SINK             = 0x110BU;
    inline constexpr Uuid16 HANDSFREE              = 0x111EU;
    inline constexpr Uuid16 OTA_SERVICE            = 0x1844U;
    inline constexpr Uuid16 AUTOMOTIVE_TELEMETRY   = 0xFF01U;  ///< Vendor-specific

    // Characteristics
    inline constexpr Uuid16 DEVICE_NAME            = 0x2A00U;
    inline constexpr Uuid16 APPEARANCE             = 0x2A01U;
    inline constexpr Uuid16 BATTERY_LEVEL          = 0x2A19U;
    inline constexpr Uuid16 FIRMWARE_REVISION      = 0x2A26U;
    inline constexpr Uuid16 MANUFACTURER_NAME      = 0x2A29U;
    inline constexpr Uuid16 MODEL_NUMBER            = 0x2A24U;
    inline constexpr Uuid16 HID_REPORT             = 0x2A4DU;
    inline constexpr Uuid16 HID_REPORT_MAP         = 0x2A4BU;
    inline constexpr Uuid16 HEART_RATE_MEASUREMENT = 0x2A37U;
    inline constexpr Uuid16 OTA_DATA               = 0xFF11U;  ///< Vendor-specific
    inline constexpr Uuid16 VEHICLE_SPEED          = 0xFF20U;  ///< Vendor-specific
    inline constexpr Uuid16 ENGINE_RPM             = 0xFF21U;  ///< Vendor-specific

    // Descriptors
    inline constexpr Uuid16 CCCD                   = 0x2902U;  ///< Client Characteristic Config
    inline constexpr Uuid16 SCCD                   = 0x2903U;  ///< Server Characteristic Config
    inline constexpr Uuid16 CHAR_USER_DESC         = 0x2901U;
}  // namespace uuid

}  // namespace bt
