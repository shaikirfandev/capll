/**
 * @file IArinc664.hpp
 * @brief ARINC 664 / AFDX dual-network interface
 * @req SRS-COMM-003
 */
#pragma once
#include "fms/FmsTypes.hpp"
#include "comms/CommsTypes.hpp"
#include <functional>

namespace fms::comms {

using AfdxRxCb = std::function<void(const AfdxFrame&)>;

class IArinc664 {
public:
    virtual ~IArinc664() = default;
    virtual FmsError init(uint16_t vl_id, uint32_t bandwidth_bps) noexcept = 0;
    virtual void     deinit() noexcept = 0;
    virtual bool     transmit(const AfdxFrame& frame) noexcept = 0;
    virtual void     set_rx_callback(uint16_t vl_id, AfdxRxCb cb) noexcept = 0;
    [[nodiscard]] virtual bool is_network_a_healthy() const noexcept = 0;
    [[nodiscard]] virtual bool is_network_b_healthy() const noexcept = 0;
    [[nodiscard]] virtual SystemStatus get_status() const noexcept = 0;
};

}  // namespace fms::comms
