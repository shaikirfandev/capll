/**
 * @file L2capManager.hpp
 */
#pragma once
#include "bt/IL2capManager.hpp"
#include <memory>
namespace bt {
class L2capManager final : public IL2capManager {
public:
    L2capManager();
    ~L2capManager() override;
    BtError register_psm(uint16_t psm, L2capDataCb cb)                              override;
    BtError open_channel(ConnHandle conn, uint16_t psm, uint16_t &out_cid)           override;
    BtError close_channel(ConnHandle conn, uint16_t cid)                             override;
    BtError send_data(ConnHandle conn, uint16_t cid, const uint8_t *data, uint16_t len) override;
    BtError set_mtu(uint16_t cid, uint16_t mtu)                                      override;
private:
    struct Impl;
    std::unique_ptr<Impl> impl_;
};
}
