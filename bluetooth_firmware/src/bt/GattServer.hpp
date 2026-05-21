/**
 * @file GattServer.hpp
 */
#pragma once
#include "bt/IGattServer.hpp"
#include <memory>
namespace bt {
class GattServer final : public IGattServer {
public:
    GattServer();
    ~GattServer() override;
    BtError add_service(GattServiceDef &service)                                         override;
    BtError remove_service(Uuid16 service_uuid)                                          override;
    void    set_read_callback(AttHandle handle, GattReadCb cb)                           override;
    void    set_write_callback(AttHandle handle, GattWriteCb cb)                         override;
    BtError notify(ConnHandle conn, AttHandle att, const uint8_t *data, uint16_t len)    override;
    BtError indicate(ConnHandle conn, AttHandle att, const uint8_t *data, uint16_t len)  override;
    BtError set_value(AttHandle handle, const uint8_t *data, uint16_t len)               override;
    BtError get_value(AttHandle handle, std::vector<uint8_t> &out)                 const override;
private:
    struct Impl;
    std::unique_ptr<Impl> impl_;
};
}
