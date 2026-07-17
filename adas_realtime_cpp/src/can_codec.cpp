// ============================================================
// adas/can_codec.cpp — CAN signal encoding/decoding
// ============================================================

#include "adas/can_codec.hpp"

#include <algorithm>
#include <cmath>
#include <cstring>

namespace adas {

namespace {

// Extract raw unsigned integer from a CAN frame using Intel byte order.
// Returns false if the frame DLC is insufficient.
[[nodiscard]] bool extract_intel(const CanFrame& frame, std::uint8_t start_bit,
                                  std::uint8_t length, std::uint64_t& raw) noexcept {
    const int last_byte = (start_bit + length - 1) / 8;
    if (last_byte >= frame.dlc) return false;

    raw = 0U;
    for (int bit = 0; bit < length; ++bit) {
        const int src_bit = start_bit + bit;
        const int byte_idx = src_bit / 8;
        const int bit_idx  = src_bit % 8;
        const std::uint64_t b = (frame.data[byte_idx] >> bit_idx) & 1U;
        raw |= b << bit;
    }
    return true;
}

// Extract raw unsigned integer using Motorola (big-endian) byte order.
[[nodiscard]] bool extract_motorola(const CanFrame& frame, std::uint8_t start_bit,
                                     std::uint8_t length, std::uint64_t& raw) noexcept {
    raw = 0U;
    for (int bit = 0; bit < length; ++bit) {
        // DBC Motorola start bit is the MSB position in the bit numbering scheme.
        const int src_bit = start_bit - bit;
        if (src_bit < 0) return false;
        // Convert from Motorola numbering to byte/bit
        const int byte_idx = 7 - (src_bit / 8);
        const int bit_idx  = src_bit % 8;
        if (byte_idx >= frame.dlc) return false;
        const std::uint64_t b = (frame.data[byte_idx] >> bit_idx) & 1U;
        raw |= b << (length - 1 - bit);
    }
    return true;
}

// Sign-extend a raw value to int64.
[[nodiscard]] std::int64_t sign_extend(std::uint64_t raw, std::uint8_t length) noexcept {
    const std::uint64_t sign_bit = std::uint64_t{1} << (length - 1U);
    if (raw & sign_bit) return static_cast<std::int64_t>(raw | ~(sign_bit - 1U));
    return static_cast<std::int64_t>(raw);
}

}  // namespace

bool decode(const CanFrame& frame, const CanSignal& signal, double& out_physical) noexcept {
    std::uint64_t raw = 0U;
    bool ok = false;
    if (signal.byte_order == ByteOrder::Intel)
        ok = extract_intel(frame, signal.start_bit, signal.length, raw);
    else
        ok = extract_motorola(frame, signal.start_bit, signal.length, raw);
    if (!ok) return false;

    const double physical = signal.is_signed
        ? static_cast<double>(sign_extend(raw, signal.length)) * signal.factor + signal.offset
        : static_cast<double>(raw) * signal.factor + signal.offset;

    if (physical < signal.min_value || physical > signal.max_value) return false;
    out_physical = physical;
    return true;
}

bool encode(CanFrame& frame, const CanSignal& signal, double physical) noexcept {
    if (!std::isfinite(physical)) return false;
    if (physical < signal.min_value || physical > signal.max_value) return false;

    const double raw_f = (physical - signal.offset) / signal.factor;
    const std::uint64_t raw = signal.is_signed
        ? static_cast<std::uint64_t>(static_cast<std::int64_t>(raw_f))
        : static_cast<std::uint64_t>(raw_f + 0.5);

    if (signal.byte_order == ByteOrder::Intel) {
        for (int bit = 0; bit < signal.length; ++bit) {
            const int dst_bit  = signal.start_bit + bit;
            const int byte_idx = dst_bit / 8;
            const int bit_idx  = dst_bit % 8;
            if (byte_idx >= frame.dlc) return false;
            const std::uint8_t b = static_cast<std::uint8_t>((raw >> bit) & 1U);
            frame.data[byte_idx] = static_cast<std::uint8_t>(
                (frame.data[byte_idx] & ~(std::uint8_t{1} << bit_idx)) | (b << bit_idx));
        }
    } else {
        for (int bit = 0; bit < signal.length; ++bit) {
            const int src_bit  = signal.start_bit - bit;
            if (src_bit < 0) return false;
            const int byte_idx = 7 - (src_bit / 8);
            const int bit_idx  = src_bit % 8;
            if (byte_idx >= frame.dlc) return false;
            const std::uint8_t b = static_cast<std::uint8_t>((raw >> (signal.length - 1 - bit)) & 1U);
            frame.data[byte_idx] = static_cast<std::uint8_t>(
                (frame.data[byte_idx] & ~(std::uint8_t{1} << bit_idx)) | (b << bit_idx));
        }
    }
    return true;
}

}  // namespace adas
