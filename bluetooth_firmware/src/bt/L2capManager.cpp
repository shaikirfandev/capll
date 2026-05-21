/**
 * @file L2capManager.cpp
 * @brief L2CAP channel management and PSM registration
 */
#include "bt/L2capManager.hpp"
#include "common/Logger.hpp"
#include <mutex>
#include <unordered_map>

static constexpr const char *TAG = "L2CAP";

namespace bt {

struct L2capManager::Impl {
    struct Channel {
        ConnHandle conn;
        uint16_t   psm;
        uint16_t   cid;
        uint16_t   mtu{512U};
        bool       open{false};
    };
    std::unordered_map<uint16_t, L2capDataCb> psm_handlers;  // PSM → callback
    std::unordered_map<uint16_t, Channel>     channels;       // CID → channel
    uint16_t next_cid{0x0040U};  // Dynamic CIDs start at 0x0040
    mutable std::mutex mtx;
};

L2capManager::L2capManager() : impl_(std::make_unique<Impl>()) {}
L2capManager::~L2capManager() = default;

BtError L2capManager::register_psm(uint16_t psm, L2capDataCb cb) {
    std::lock_guard<std::mutex> lock(impl_->mtx);
    if (impl_->psm_handlers.count(psm)) {
        BT_LOG_WARN(TAG, "PSM 0x{:04X} already registered", psm);
        return BtError::ERR_INVALID_PARAM;
    }
    impl_->psm_handlers[psm] = std::move(cb);
    BT_LOG_INFO(TAG, "PSM 0x{:04X} registered", psm);
    return BtError::OK;
}

BtError L2capManager::open_channel(ConnHandle conn, uint16_t psm, uint16_t &out_cid) {
    std::lock_guard<std::mutex> lock(impl_->mtx);
    if (!impl_->psm_handlers.count(psm)) {
        BT_LOG_ERROR(TAG, "open_channel: PSM 0x{:04X} not registered", psm);
        return BtError::ERR_INVALID_PARAM;
    }
    const uint16_t cid = impl_->next_cid++;
    impl_->channels[cid] = {conn, psm, cid, 512U, true};
    out_cid = cid;
    BT_LOG_INFO(TAG, "L2CAP channel opened CID=0x{:04X} PSM=0x{:04X}", cid, psm);
    return BtError::OK;
}

BtError L2capManager::close_channel(ConnHandle conn, uint16_t cid) {
    std::lock_guard<std::mutex> lock(impl_->mtx);
    auto it = impl_->channels.find(cid);
    if (it == impl_->channels.end() || it->second.conn != conn) {
        return BtError::ERR_INVALID_PARAM;
    }
    it->second.open = false;
    impl_->channels.erase(it);
    BT_LOG_INFO(TAG, "L2CAP channel closed CID=0x{:04X}", cid);
    return BtError::OK;
}

BtError L2capManager::send_data(ConnHandle conn, uint16_t cid,
                                  const uint8_t *data, uint16_t len) {
    std::lock_guard<std::mutex> lock(impl_->mtx);
    auto it = impl_->channels.find(cid);
    if (it == impl_->channels.end() || !it->second.open) {
        return BtError::ERR_NOT_CONNECTED;
    }
    if (len > it->second.mtu) {
        BT_LOG_WARN(TAG, "Data len={} exceeds MTU={}", len, it->second.mtu);
        return BtError::ERR_INVALID_PARAM;
    }
    BT_LOG_DEBUG(TAG, "L2CAP TX conn=0x{:04X} CID=0x{:04X} len={}", conn, cid, len);
    (void)data;
    return BtError::OK;
}

BtError L2capManager::set_mtu(uint16_t cid, uint16_t mtu) {
    std::lock_guard<std::mutex> lock(impl_->mtx);
    auto it = impl_->channels.find(cid);
    if (it == impl_->channels.end()) { return BtError::ERR_INVALID_PARAM; }
    it->second.mtu = mtu;
    return BtError::OK;
}

}  // namespace bt
