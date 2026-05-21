/**
 * @file Arinc664Driver.cpp
 * @req SRS-COMM-003
 */
#include "Arinc664Driver.hpp"

namespace fms::comms {

FmsError Arinc664Driver::init(uint16_t /*vl_id*/, uint32_t /*bw*/) noexcept {
    callbacks_.clear();
    net_a_ok_    = true;
    net_b_ok_    = true;
    seq_counter_ = 0;
    status_      = SystemStatus::NORMAL;
    return FmsError::OK;
}

void Arinc664Driver::deinit() noexcept {
    callbacks_.clear();
    net_a_ok_ = net_b_ok_ = false;
}

bool Arinc664Driver::transmit(const AfdxFrame& frame) noexcept {
    AfdxFrame copy = frame;
    copy.seq_num = ++seq_counter_;
    // Dual network: loopback on both A and B
    auto it = callbacks_.find(frame.vl_id);
    if (it != callbacks_.end()) {
        it->second(copy);  // A
        it->second(copy);  // B (duplicate — receiver deduplicates by seq)
    }
    return true;
}

void Arinc664Driver::set_rx_callback(uint16_t vl_id, AfdxRxCb cb) noexcept {
    callbacks_[vl_id] = std::move(cb);
}

}  // namespace fms::comms
