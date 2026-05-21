/**
 * @file GattClient.cpp
 * @brief GATT Client — service discovery and remote read/write
 */
#include "bt/GattClient.hpp"
#include "common/Logger.hpp"
#include <mutex>
#include <unordered_map>

static constexpr const char *TAG = "GattClient";

namespace bt {

struct GattClient::Impl {
    std::unordered_map<ConnHandle, std::vector<GattServiceDef>> discovered;
    std::unordered_map<uint64_t, GattNotifyCb> notify_cbs;  // key: conn<<32|att
    mutable std::mutex mtx;

    static uint64_t notify_key(ConnHandle c, AttHandle a) {
        return (static_cast<uint64_t>(c) << 32U) | a;
    }
};

GattClient::GattClient() : impl_(std::make_unique<Impl>()) {}
GattClient::~GattClient() = default;

BtError GattClient::discover_services(ConnHandle conn, GattDiscoveryCb cb) {
    BT_LOG_INFO(TAG, "Starting service discovery conn=0x{:04X}", conn);
    // Simulation: immediately "discover" a Device Information Service
    GattServiceDef dis{};
    dis.service_uuid  = uuid::DEVICE_INFORMATION;
    dis.is_primary    = true;
    dis.start_handle  = 0x0010U;
    dis.end_handle    = 0x001FU;
    GattCharDef fw_rev{};
    fw_rev.uuid         = uuid::FIRMWARE_REVISION;
    fw_rev.properties   = GattProp::READ;
    fw_rev.value_handle = 0x0012U;
    dis.characteristics.push_back(fw_rev);
    if (cb) { cb(dis); }
    {
        std::lock_guard<std::mutex> lock(impl_->mtx);
        impl_->discovered[conn].push_back(dis);
    }
    return BtError::OK;
}

BtError GattClient::read_characteristic(ConnHandle conn, AttHandle handle,
                                          GattReadResultCb cb) {
    BT_LOG_DEBUG(TAG, "GATT Read conn=0x{:04X} att=0x{:04X}", conn, handle);
    // Simulation: return mock value
    const std::vector<uint8_t> mock_val = {'2', '.', '1', '.', '0'};
    if (cb) { cb(handle, mock_val, BtError::OK); }
    return BtError::OK;
}

BtError GattClient::write_characteristic(ConnHandle conn, AttHandle handle,
                                           const uint8_t *data, uint16_t len,
                                           bool with_response, GattWriteResultCb cb) {
    BT_LOG_DEBUG(TAG, "GATT Write conn=0x{:04X} att=0x{:04X} len={} rsp={}",
                 conn, handle, len, with_response);
    (void)data;
    if (cb) { cb(handle, BtError::OK); }
    return BtError::OK;
}

BtError GattClient::subscribe_notify(ConnHandle conn, AttHandle cccd_handle,
                                      bool enable, GattNotifyCb cb) {
    BT_LOG_INFO(TAG, "Subscribe conn=0x{:04X} cccd=0x{:04X} enable={}",
                conn, cccd_handle, enable);
    std::lock_guard<std::mutex> lock(impl_->mtx);
    const uint64_t key = Impl::notify_key(conn, cccd_handle);
    if (enable && cb) {
        impl_->notify_cbs[key] = std::move(cb);
    } else {
        impl_->notify_cbs.erase(key);
    }
    return BtError::OK;
}

}  // namespace bt
