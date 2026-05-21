/**
 * @file Arinc664Driver.hpp/.cpp — AFDX dual-network
 */
#pragma once
#include "comms/IArinc664.hpp"
#include <unordered_map>

namespace fms::comms {

class Arinc664Driver : public IArinc664 {
public:
    FmsError init(uint16_t vl_id, uint32_t bandwidth_bps) noexcept override;
    void     deinit() noexcept override;
    bool     transmit(const AfdxFrame& frame) noexcept override;
    void     set_rx_callback(uint16_t vl_id, AfdxRxCb cb) noexcept override;
    [[nodiscard]] bool         is_network_a_healthy() const noexcept override { return net_a_ok_; }
    [[nodiscard]] bool         is_network_b_healthy() const noexcept override { return net_b_ok_; }
    [[nodiscard]] SystemStatus get_status()           const noexcept override { return status_; }

private:
    SystemStatus status_{SystemStatus::NORMAL};
    bool net_a_ok_{false};
    bool net_b_ok_{false};
    uint16_t seq_counter_{0};
    std::unordered_map<uint16_t, AfdxRxCb> callbacks_;
};

}  // namespace fms::comms
