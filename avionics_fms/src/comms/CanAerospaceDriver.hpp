/**
 * @file CanAerospaceDriver.hpp
 */
#pragma once
#include "comms/ICanAerospace.hpp"
#include <unordered_map>
#include <atomic>

namespace fms::comms {

class CanAerospaceDriver : public ICanAerospace {
public:
    fms::FmsError init(uint8_t node_id, uint32_t baud_kbps) noexcept override;
    void          deinit() noexcept override;
    bool          transmit(const CanAeroMessage& msg) noexcept override;
    void          set_rx_callback(uint16_t msg_id, CanAeroRxCb cb) noexcept override;
    [[nodiscard]] bool              is_bus_active()   const noexcept override { return bus_active_.load(); }
    [[nodiscard]] uint32_t          get_error_count() const noexcept override { return error_count_.load(); }
    [[nodiscard]] fms::SystemStatus get_status()      const noexcept override { return status_; }

private:
    SystemStatus status_{SystemStatus::NORMAL};
    std::atomic<bool>     bus_active_{false};
    std::atomic<uint32_t> error_count_{0};
    uint8_t node_id_{0};
    std::unordered_map<uint16_t, CanAeroRxCb> callbacks_;
};

}  // namespace fms::comms
