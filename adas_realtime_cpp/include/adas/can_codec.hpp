#pragma once

// ============================================================
// adas/can_codec.hpp — CAN/CAN-FD signal encoder / decoder
//
// Provides:
//   CanFrame         — raw 64-byte CAN frame (compatible with socketCAN)
//   CanSignal        — signal descriptor (matches DBC signal attributes)
//   CanCodec         — encode/decode using descriptor, no DBC parser at runtime
//
// All signal descriptors are compile-time constexpr where possible.
// Range checking is explicit: out-of-range values return false and do not
// corrupt the output.
//
// Endianness: both Intel (little-endian) and Motorola (big-endian) byte orders.
//
// AUTOSAR COM mapping:
//   - Replace encode/decode calls with generated ComWriteSignal / ComReadSignal
//     functions from the AUTOSAR COM layer in the target integration.
//   - Keep the descriptor structure as the interface control document source.
// ============================================================

#include <cstdint>
#include <cstring>
#include <span>

namespace adas {

struct CanFrame {
    std::uint32_t can_id{};
    std::uint8_t  dlc{};
    std::uint8_t  data[64]{};
    bool extended_id{};
    bool fd{};
};

enum class ByteOrder : std::uint8_t { Intel, Motorola };

struct CanSignal {
    const char*  name{};
    std::uint8_t start_bit{};
    std::uint8_t length{};          // Number of bits, max 32 for scaled signals
    ByteOrder    byte_order{ByteOrder::Intel};
    bool         is_signed{};
    double       factor{1.0};
    double       offset{0.0};
    double       min_value{};
    double       max_value{};
};

/// @brief Decode a CAN signal to physical double.
/// @return false if DLC is too small or extracted raw value is out of range.
[[nodiscard]] bool decode(const CanFrame& frame,
                           const CanSignal& signal,
                           double& out_physical) noexcept;

/// @brief Encode a physical double into a CAN frame data buffer.
/// @return false if physical value is out of [min_value, max_value].
[[nodiscard]] bool encode(CanFrame& frame,
                           const CanSignal& signal,
                           double physical) noexcept;

// ──────────────────────────────────────────────────────────────────────────────
// Typical vehicle signal descriptors (examples matching common OEM DBCs).
// Adapt factor/offset/range to the actual vehicle DBC.
// ──────────────────────────────────────────────────────────────────────────────
namespace signals {

constexpr CanSignal kVehicleSpeed       {"VehicleSpeed",       0,  16, ByteOrder::Intel,   false, 0.01,  0.0,   0.0, 327.67};
constexpr CanSignal kYawRate            {"YawRate",            16, 16, ByteOrder::Intel,   true,  0.01,  0.0,  -327.68, 327.67};
constexpr CanSignal kSteeringAngle      {"SteeringAngle",      0,  16, ByteOrder::Intel,   true,  0.1,   0.0,  -800.0, 800.0};
constexpr CanSignal kAccelPedalPosition {"AccelPedalPos",      0,   8, ByteOrder::Intel,   false, 0.4,   0.0,   0.0, 100.0};
constexpr CanSignal kBrakePressure      {"BrakePressure",      0,  12, ByteOrder::Intel,   false, 0.1,   0.0,   0.0, 409.5};

}  // namespace signals
}  // namespace adas
