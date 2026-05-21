/**
 * @file Arinc429Driver.cpp
 * @brief ARINC 429 BNR encoding, odd parity, loopback RX dispatch
 * @req SRS-COMM-001, SRS-COMM-002
 */
#include "Arinc429Driver.hpp"
#include <cmath>
#include <cstring>

namespace fms::comms {

fms::FmsError Arinc429Driver::init(uint8_t /*ch*/, uint32_t /*speed*/) noexcept {
    callbacks_.clear();
    status_ = fms::SystemStatus::NORMAL;
    return fms::FmsError::OK;
}

void Arinc429Driver::deinit() noexcept {
    callbacks_.clear();
    status_ = SystemStatus::NORMAL;
}

uint8_t Arinc429Driver::reverse_label(uint8_t label) noexcept {
    uint8_t r = 0;
    for (int i = 0; i < 8; ++i) {
        r = static_cast<uint8_t>((r << 1) | (label & 1));
        label >>= 1;
    }
    return r;
}

uint32_t Arinc429Driver::compute_parity(uint32_t word) noexcept {
    // Odd parity over bits 0-30
    uint32_t p = word & 0x7FFFFFFFu;
    p ^= p >> 16;
    p ^= p >> 8;
    p ^= p >> 4;
    p ^= p >> 2;
    p ^= p >> 1;
    return (~p) & 1u;  // odd: set bit if even number of ones
}

uint32_t Arinc429Driver::encode_bnr(uint8_t label, uint8_t sdi,
                                     double value, double resolution,
                                     uint8_t bits, Arinc429Ssm ssm) noexcept {
    int32_t  scaled = static_cast<int32_t>(std::round(value / resolution));
    uint32_t mask   = (1u << bits) - 1u;
    uint32_t data   = static_cast<uint32_t>(scaled) & mask;
    uint32_t word   = static_cast<uint32_t>(reverse_label(label))
                    | (static_cast<uint32_t>(sdi & 3u) << 8)
                    | (data << 10)
                    | (static_cast<uint32_t>(ssm) << 29);
    return word | (compute_parity(word) << 31);
}

double Arinc429Driver::decode_bnr(uint32_t data_bits, double resolution,
                                   uint8_t bits) noexcept {
    const uint32_t mask   = (1u << bits) - 1u;
    const uint32_t raw    = data_bits & mask;
    // 2's complement sign extend
    const int32_t  sign   = (raw & (1u << (bits - 1))) ? -1 : 1;
    int32_t        val;
    if (sign < 0) {
        val = static_cast<int32_t>(raw) - static_cast<int32_t>(1u << bits);
    } else {
        val = static_cast<int32_t>(raw);
    }
    return static_cast<double>(val) * resolution;
}

fms::FmsError Arinc429Driver::transmit(uint8_t label, uint8_t sdi,
                                        uint32_t data_bits,
                                        Arinc429Ssm ssm) noexcept {
    const uint32_t word = encode_bnr(label, sdi, static_cast<double>(data_bits), 1.0,
                                     18U, ssm);
    return transmit_raw(word);
}

fms::FmsError Arinc429Driver::transmit_raw(uint32_t word) noexcept {
    // Loopback: extract label (reversed) and dispatch to callback
    const uint8_t label_rev = static_cast<uint8_t>(word & 0xFFu);
    const uint8_t label     = reverse_label(label_rev);
    auto it = callbacks_.find(label);
    if (it != callbacks_.end()) {
        Arinc429Frame frame{};
        frame.label     = label;
        frame.sdi       = static_cast<uint8_t>((word >> 8) & 3u);
        frame.data_bits = (word >> 10) & 0x7FFFFu;
        frame.ssm       = static_cast<Arinc429Ssm>((word >> 29) & 3u);
        frame.parity_ok  = (compute_parity(word) != 0u);
        it->second(frame);
    }
    return fms::FmsError::OK;
}

void Arinc429Driver::set_rx_callback(uint8_t label, Arinc429RxCb cb) noexcept {
    callbacks_[label] = std::move(cb);
}

}  // namespace fms::comms
