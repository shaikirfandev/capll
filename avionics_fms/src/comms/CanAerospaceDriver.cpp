/**
 * @file CanAerospaceDriver.cpp
 * @req SRS-COMM-004
 */
#include "CanAerospaceDriver.hpp"

namespace fms::comms {

fms::FmsError CanAerospaceDriver::init(uint8_t node_id, uint32_t /*baud*/) noexcept {
    node_id_     = node_id;
    callbacks_.clear();
    error_count_.store(0);
    bus_active_.store(true);
    status_ = fms::SystemStatus::NORMAL;
    return fms::FmsError::OK;
}

void CanAerospaceDriver::deinit() noexcept {
    bus_active_.store(false);
    callbacks_.clear();
}

bool CanAerospaceDriver::transmit(const CanAeroMessage& msg) noexcept {
    if (!bus_active_.load()) { error_count_.fetch_add(1); return false; }
    auto it = callbacks_.find(msg.message_id);
    if (it != callbacks_.end()) it->second(msg);
    return true;
}

void CanAerospaceDriver::set_rx_callback(uint16_t msg_id, CanAeroRxCb cb) noexcept {
    callbacks_[msg_id] = std::move(cb);
}

}  // namespace fms::comms
