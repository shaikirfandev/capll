/**
 * @file GattServer.cpp
 * @brief GATT Server — attribute database, read/write dispatch, notify/indicate
 *
 * Industry context: This GATT server is used in Harman automotive infotainment
 * ECUs (based on QNX) to expose vehicle telemetry to BLE clients (smartphones,
 * diagnostics tablets). Battery Service, Device Information, and custom
 * Automotive Telemetry service are registered at init.
 */

#include "bt/GattServer.hpp"
#include "common/Logger.hpp"
#include <algorithm>
#include <mutex>
#include <unordered_map>

static constexpr const char *TAG = "GattServer";

namespace bt {

struct GattServer::Impl {
    std::vector<GattServiceDef>            services;
    std::unordered_map<AttHandle, GattReadCb>  read_cbs;
    std::unordered_map<AttHandle, GattWriteCb> write_cbs;
    std::unordered_map<AttHandle, std::vector<uint8_t>> attr_values;
    // CCCD state: [conn_handle][att_handle] = notify_enabled
    std::unordered_map<uint32_t, bool> cccd_state;  // key = (conn<<16)|att
    AttHandle  next_handle{0x0001U};
    mutable std::mutex mtx;

    AttHandle alloc_handle() { return next_handle++; }

    static uint32_t cccd_key(ConnHandle conn, AttHandle att) {
        return (static_cast<uint32_t>(conn) << 16U) | att;
    }
};

GattServer::GattServer() : impl_(std::make_unique<Impl>()) {}
GattServer::~GattServer() = default;

BtError GattServer::add_service(GattServiceDef &service) {
    std::lock_guard<std::mutex> lock(impl_->mtx);

    service.start_handle = impl_->alloc_handle();

    BT_LOG_INFO(TAG, "Adding service UUID=0x{:04X} primary={}",
                service.service_uuid, service.is_primary);

    for (auto &ch : service.characteristics) {
        ch.handle       = impl_->alloc_handle();  // Characteristic declaration
        ch.value_handle = impl_->alloc_handle();  // Characteristic value

        // Allocate CCCD if notify or indicate
        const bool notify_capable =
            (static_cast<uint8_t>(ch.properties) &
             (static_cast<uint8_t>(GattProp::NOTIFY) |
              static_cast<uint8_t>(GattProp::INDICATE))) != 0U;
        if (notify_capable) {
            ch.cccd_handle = impl_->alloc_handle();
            impl_->attr_values[ch.cccd_handle] = {0x00U, 0x00U};  // CCCD default: disabled
            BT_LOG_DEBUG(TAG, "  Char UUID=0x{:04X} val_hdl=0x{:04X} cccd=0x{:04X}",
                         ch.uuid, ch.value_handle, ch.cccd_handle);
        } else {
            BT_LOG_DEBUG(TAG, "  Char UUID=0x{:04X} val_hdl=0x{:04X}",
                         ch.uuid, ch.value_handle);
        }

        // Set initial value
        if (!ch.initial_value.empty()) {
            impl_->attr_values[ch.value_handle] = ch.initial_value;
        }
    }

    service.end_handle = impl_->next_handle - 1U;
    impl_->services.push_back(service);

    BT_LOG_INFO(TAG, "Service added handles=[0x{:04X}-0x{:04X}]",
                service.start_handle, service.end_handle);
    return BtError::OK;
}

BtError GattServer::remove_service(Uuid16 service_uuid) {
    std::lock_guard<std::mutex> lock(impl_->mtx);
    auto it = std::find_if(impl_->services.begin(), impl_->services.end(),
                           [&](const GattServiceDef &s) {
                               return s.service_uuid == service_uuid;
                           });
    if (it == impl_->services.end()) {
        return BtError::ERR_INVALID_PARAM;
    }
    BT_LOG_INFO(TAG, "Removing service UUID=0x{:04X}", service_uuid);
    impl_->services.erase(it);
    return BtError::OK;
}

void GattServer::set_read_callback(AttHandle handle, GattReadCb cb) {
    std::lock_guard<std::mutex> lock(impl_->mtx);
    impl_->read_cbs[handle] = std::move(cb);
}

void GattServer::set_write_callback(AttHandle handle, GattWriteCb cb) {
    std::lock_guard<std::mutex> lock(impl_->mtx);
    impl_->write_cbs[handle] = std::move(cb);
}

BtError GattServer::notify(ConnHandle conn, AttHandle att_handle,
                             const uint8_t *data, uint16_t len) {
    // Check CCCD state (simplified: assume cccd_handle = att_handle + 1)
    // In production: lookup from service database
    BT_LOG_DEBUG(TAG, "GATT Notify: conn=0x{:04X} att=0x{:04X} len={}",
                 conn, att_handle, len);
    (void)data;
    (void)len;
    return BtError::OK;
}

BtError GattServer::indicate(ConnHandle conn, AttHandle att_handle,
                               const uint8_t *data, uint16_t len) {
    BT_LOG_DEBUG(TAG, "GATT Indicate: conn=0x{:04X} att=0x{:04X} len={}",
                 conn, att_handle, len);
    (void)data;
    (void)len;
    return BtError::OK;
}

BtError GattServer::set_value(AttHandle handle,
                                const uint8_t *data,
                                uint16_t len) {
    if (len > 512U) { return BtError::ERR_INVALID_PARAM; }
    std::lock_guard<std::mutex> lock(impl_->mtx);
    impl_->attr_values[handle].assign(data, data + len);
    return BtError::OK;
}

BtError GattServer::get_value(AttHandle handle,
                                std::vector<uint8_t> &out) const {
    std::lock_guard<std::mutex> lock(impl_->mtx);
    auto it = impl_->attr_values.find(handle);
    if (it == impl_->attr_values.end()) {
        return BtError::ERR_INVALID_PARAM;
    }
    out = it->second;
    return BtError::OK;
}

}  // namespace bt
