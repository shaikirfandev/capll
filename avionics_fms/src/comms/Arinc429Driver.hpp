/**
 * @file Arinc429Driver.hpp
 */
#pragma once
#include "comms/IArinc429.hpp"
#include <unordered_map>
#include <functional>

namespace fms::comms {

class Arinc429Driver : public IArinc429 {
public:
    fms::FmsError init(uint8_t channel, uint32_t speed_kbps) noexcept override;
    void          deinit() noexcept override;
    fms::FmsError transmit(uint8_t label, uint8_t sdi, uint32_t data_bits,
                           Arinc429Ssm ssm) noexcept override;
    fms::FmsError transmit_raw(uint32_t word) noexcept override;
    void          set_rx_callback(uint8_t label, Arinc429RxCb cb) noexcept override;
    [[nodiscard]] fms::SystemStatus get_status() const noexcept override { return status_; }

    // Static helpers (also declared in IArinc429)
    static uint32_t encode_bnr(uint8_t label, uint8_t sdi,
                                double value, double resolution,
                                uint8_t bits, Arinc429Ssm ssm) noexcept;
    static double   decode_bnr(uint32_t data_bits, double resolution,
                                uint8_t bits) noexcept;
    static uint8_t  reverse_label(uint8_t label) noexcept;
    static uint32_t compute_parity(uint32_t word) noexcept;

private:
    SystemStatus status_{SystemStatus::NORMAL};
    std::unordered_map<uint8_t, Arinc429RxCb> callbacks_;
};

}  // namespace fms::comms
