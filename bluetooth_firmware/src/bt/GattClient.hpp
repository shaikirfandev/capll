/**
 * @file GattClient.hpp
 */
#pragma once
#include "bt/IGattClient.hpp"
#include <memory>
namespace bt {
class GattClient final : public IGattClient {
public:
    GattClient();
    ~GattClient() override;
    BtError discover_services(ConnHandle conn, GattDiscoveryCb cb)                                           override;
    BtError read_characteristic(ConnHandle conn, AttHandle handle, GattReadResultCb cb)                      override;
    BtError write_characteristic(ConnHandle conn, AttHandle handle,
                                  const uint8_t *data, uint16_t len,
                                  bool with_response, GattWriteResultCb cb)                                  override;
    BtError subscribe_notify(ConnHandle conn, AttHandle cccd, bool enable, GattNotifyCb cb)                  override;
private:
    struct Impl;
    std::unique_ptr<Impl> impl_;
};
}
