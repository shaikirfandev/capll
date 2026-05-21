/**
 * @file IGattClient.hpp
 * @brief GATT Client interface — discovery and remote attribute operations
 */
#pragma once
#include "BluetoothTypes.hpp"
#include <functional>
namespace bt {
using GattDiscoveryCb   = std::function<void(const GattServiceDef &svc)>;
using GattReadResultCb  = std::function<void(AttHandle, const std::vector<uint8_t> &, BtError)>;
using GattWriteResultCb = std::function<void(AttHandle, BtError)>;
using GattNotifyCb      = std::function<void(AttHandle, const std::vector<uint8_t> &)>;

class IGattClient {
public:
    virtual ~IGattClient() = default;
    virtual BtError discover_services(ConnHandle conn, GattDiscoveryCb cb) = 0;
    virtual BtError read_characteristic(ConnHandle conn, AttHandle handle, GattReadResultCb cb) = 0;
    virtual BtError write_characteristic(ConnHandle conn, AttHandle handle,
                                          const uint8_t *data, uint16_t len,
                                          bool with_response, GattWriteResultCb cb) = 0;
    virtual BtError subscribe_notify(ConnHandle conn, AttHandle cccd_handle, bool enable, GattNotifyCb cb) = 0;
};
}
