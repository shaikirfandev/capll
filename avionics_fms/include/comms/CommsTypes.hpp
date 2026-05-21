/**
 * @file CommsTypes.hpp
 * @brief ARINC 429, ARINC 664 (AFDX), CAN Aerospace data structures
 *
 * ARINC 429 word format (32-bit):
 *   [31:29] SSM (Sign/Status Matrix)
 *   [28:11] Data (18 bits for BNR, 19 bits for BCD/Dis)
 *   [10:8]  SDI (Source/Destination Identifier)
 *   [7:0]   Label (octal, LSB transmitted first)
 *   [32]    Parity (odd parity over bits 1-32)
 */
#pragma once
#include <cstdint>
#include <array>

namespace fms::comms {

// ── ARINC 429 ─────────────────────────────────────────────────────────────────
using Arinc429Word = uint32_t;

enum class Arinc429Ssm : uint8_t {
    FAILURE_WARN   = 0b00U,  // Failure Warning
    NO_COMPUTED    = 0b01U,  // No Computed Data
    FUNCTIONAL_TEST = 0b10U, // Functional Test
    NORMAL_OP      = 0b11U,  // Normal Operation
};

// Selected ARINC 429 labels (octal → decimal for common navigation parameters)
namespace label {
    static constexpr uint8_t DISCRETE_WORD_1       = 0270U;  // 184d
    static constexpr uint8_t LATITUDE              = 0310U;  // 200d
    static constexpr uint8_t LONGITUDE             = 0311U;  // 201d
    static constexpr uint8_t ALTITUDE_CORRECTED    = 0203U;  // 131d
    static constexpr uint8_t AIRSPEED_IAS          = 0206U;  // 134d
    static constexpr uint8_t AIRSPEED_TAS          = 0210U;  // 136d
    static constexpr uint8_t MACH                  = 0205U;  // 133d
    static constexpr uint8_t VSPEED                = 0212U;  // 138d
    static constexpr uint8_t PITCH_ANGLE           = 0324U;  // 212d
    static constexpr uint8_t ROLL_ANGLE            = 0325U;  // 213d
    static constexpr uint8_t TRUE_HEADING          = 0314U;  // 204d
    static constexpr uint8_t TRACK_ANGLE           = 0303U;  // 195d
    static constexpr uint8_t GROUND_SPEED          = 0312U;  // 202d
    static constexpr uint8_t WIND_SPEED            = 0315U;  // 205d
    static constexpr uint8_t WIND_DIRECTION        = 0316U;  // 206d
    static constexpr uint8_t FUEL_QUANTITY         = 0163U;  // 115d
    static constexpr uint8_t XTE                   = 0356U;  // 238d
    static constexpr uint8_t DESIRED_TRACK         = 0003U;  // 003d
    static constexpr uint8_t DISTANCE_TO_WPT       = 0020U;  // 016d
    static constexpr uint8_t ETA                   = 0025U;  // 021d
    static constexpr uint8_t FMS_STATUS            = 0273U;  // 187d
}

struct Arinc429Frame {
    uint8_t      label{0U};
    uint8_t      sdi{0U};       // [0-3]
    uint32_t     data_bits{0U}; // 18-bit BNR or 19-bit BCD
    Arinc429Ssm  ssm{Arinc429Ssm::NORMAL_OP};
    bool         parity_ok{true};
    uint64_t     timestamp_us{0U};
};

static constexpr uint8_t ARINC429_HIGH_SPEED_KBPS  = 100U;
static constexpr uint8_t ARINC429_LOW_SPEED_KBPS   = 12U;

// ── ARINC 664 / AFDX ─────────────────────────────────────────────────────────
static constexpr uint16_t AFDX_MAX_FRAME_BYTES    = 1471U;
static constexpr uint16_t AFDX_MIN_FRAME_BYTES    = 17U;
static constexpr uint32_t AFDX_MAX_BAG_MS         = 128U;  // Max BAG period

struct AfdxVirtualLink {
    uint16_t vl_id{0U};
    uint32_t bandwidth_bps{0U};
    uint16_t max_frame_size{0U};
    uint16_t bag_ms{0U};         // Bandwidth Allocation Gap
    bool     redundant_a{true};  // Network A
    bool     redundant_b{true};  // Network B
};

struct AfdxFrame {
    uint16_t vl_id{0U};
    uint16_t seq_num{0U};         // SN wraps 0-255
    std::array<uint8_t, AFDX_MAX_FRAME_BYTES> payload{};
    uint16_t payload_len{0U};
    uint64_t timestamp_us{0U};
};

// ── CAN Aerospace ─────────────────────────────────────────────────────────────
static constexpr uint32_t CAN_AERO_BAUD_1MBPS  = 1000000U;
static constexpr uint32_t CAN_AERO_BAUD_500KBPS = 500000U;

enum class CanAeroDataType : uint8_t {
    NODATA   = 0U,
    ERROR    = 1U,
    FLOAT    = 2U,
    LONG     = 3U,
    ULONG    = 4U,
    BLONG    = 5U,
    SHORT    = 6U,
    USHORT   = 7U,
    BSHORT   = 8U,
    CHAR     = 9U,
    UCHAR    = 10U,
    BCHAR    = 11U,
};

struct CanAeroMessage {
    uint16_t          message_id{0U};
    uint8_t           node_id{0U};
    uint8_t           data_type{0U};
    uint8_t           service_code{0U};
    uint8_t           message_code{0U};
    uint32_t          data{0U};
    uint64_t          timestamp_us{0U};
};

// CAN Aerospace message IDs (from CANaerospace v1.7 specification)
namespace can_id {
    static constexpr uint16_t BARO_CORRECTED_ALT    = 0x0105U;  // 261
    static constexpr uint16_t AIRSPEED_CAS          = 0x0106U;  // 262
    static constexpr uint16_t AIRSPEED_TAS          = 0x0107U;  // 263
    static constexpr uint16_t MACH_NUMBER           = 0x010AU;  // 266
    static constexpr uint16_t VERTICAL_SPEED        = 0x010BU;  // 267
    static constexpr uint16_t PITCH_ANGLE           = 0x010FU;  // 271
    static constexpr uint16_t ROLL_ANGLE            = 0x0110U;  // 272
    static constexpr uint16_t HEADING_ANGLE         = 0x0111U;  // 273
    static constexpr uint16_t LATITUDE              = 0x011BU;  // 283
    static constexpr uint16_t LONGITUDE             = 0x011CU;  // 284
    static constexpr uint16_t GROUND_SPEED          = 0x012FU;  // 303
    static constexpr uint16_t TRACK_ANGLE           = 0x0130U;  // 304
    static constexpr uint16_t FMS_ACTIVE_WAYPOINT   = 0x0200U;  // 512
    static constexpr uint16_t FMS_XTE               = 0x0201U;  // 513
    static constexpr uint16_t FMS_DISTANCE_TO_WPT   = 0x0202U;  // 514
}

}  // namespace fms::comms
