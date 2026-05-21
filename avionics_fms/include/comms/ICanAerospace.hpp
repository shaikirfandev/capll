/**
 * @file ICanAerospace.hpp
 * @brief CANaerospace v1.7 interface
 * @req SRS-COMM-004
 */
#pragma once
#include "fms/FmsTypes.hpp"
#include "comms/CommsTypes.hpp"
#include <functional>

namespace fms::comms {

using CanAeroRxCb = std::function<void(const CanAeroMessage&)>;

class ICanAerospace {
public:
    virtual ~ICanAerospace() = default;
    virtual fms::FmsError init(uint8_t node_id, uint32_t baud_kbps) noexcept = 0;
    virtual void          deinit() noexcept = 0;
    virtual bool          transmit(const CanAeroMessage& msg) noexcept = 0;
    virtual void          set_rx_callback(uint16_t msg_id, CanAeroRxCb cb) noexcept = 0;
    [[nodiscard]] virtual bool              is_bus_active()   const noexcept = 0;
    [[nodiscard]] virtual uint32_t          get_error_count() const noexcept = 0;
    [[nodiscard]] virtual fms::SystemStatus get_status()      const noexcept = 0;
};

}  // namespace fms::comms
