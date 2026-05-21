/**
 * @file CRCValidator.cpp
 * @brief CRC-32/ISO-HDLC and CRC-16/CCITT implementations.
 */

#include "firmware/CRCValidator.h"
#include <array>

namespace tcu::firmware {

// ============================================================
// CRC-32/ISO-HDLC (polynomial 0xEDB88320)
// ============================================================

static std::array<uint32_t, 256> make_crc32_table() {
    std::array<uint32_t, 256> tbl{};
    for (uint32_t i = 0; i < 256; ++i) {
        uint32_t crc = i;
        for (int j = 0; j < 8; ++j) {
            crc = (crc & 1) ? ((crc >> 1) ^ 0xEDB88320U) : (crc >> 1);
        }
        tbl[i] = crc;
    }
    return tbl;
}

uint32_t CRCValidator::crc32(const uint8_t* data, size_t length,
                              uint32_t initial) {
    static const auto tbl = make_crc32_table();
    uint32_t crc = initial ^ 0xFFFFFFFFU;
    for (size_t i = 0; i < length; ++i) {
        crc = (crc >> 8) ^ tbl[(crc ^ data[i]) & 0xFF];
    }
    return crc ^ 0xFFFFFFFFU;
}

// ============================================================
// CRC-16/CCITT-FALSE (polynomial 0x1021, init 0xFFFF)
// ============================================================

static std::array<uint16_t, 256> make_crc16_table() {
    std::array<uint16_t, 256> tbl{};
    for (uint32_t i = 0; i < 256; ++i) {
        uint16_t crc = static_cast<uint16_t>(i << 8);
        for (int j = 0; j < 8; ++j) {
            crc = (crc & 0x8000U) ? ((crc << 1) ^ 0x1021U) : (crc << 1);
        }
        tbl[i] = crc;
    }
    return tbl;
}

uint16_t CRCValidator::crc16(const uint8_t* data, size_t length,
                              uint16_t initial) {
    static const auto tbl = make_crc16_table();
    uint16_t crc = initial;
    for (size_t i = 0; i < length; ++i) {
        crc = static_cast<uint16_t>((crc << 8) ^
              tbl[((crc >> 8) ^ data[i]) & 0xFF]);
    }
    return crc;
}

// ============================================================
// File verification
// ============================================================

bool CRCValidator::verify_file_crc32(const std::string& path, uint32_t expected) {
    std::ifstream file(path, std::ios::binary);
    if (!file.is_open()) { return false; }

    constexpr size_t BUF_SIZE = 65536;
    std::vector<uint8_t> buf(BUF_SIZE);
    uint32_t crc = 0xFFFFFFFFU;
    static const auto tbl = make_crc32_table();

    while (file) {
        file.read(reinterpret_cast<char*>(buf.data()),
                  static_cast<std::streamsize>(BUF_SIZE));
        auto bytes_read = static_cast<size_t>(file.gcount());
        for (size_t i = 0; i < bytes_read; ++i) {
            crc = (crc >> 8) ^ tbl[(crc ^ buf[i]) & 0xFF];
        }
    }
    return (crc ^ 0xFFFFFFFFU) == expected;
}

} // namespace tcu::firmware
