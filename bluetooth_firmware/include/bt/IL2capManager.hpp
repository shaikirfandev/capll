/**
 * @file IL2capManager.hpp
 * @brief L2CAP channel management interface
 */
#pragma once
#include "BluetoothTypes.hpp"
#include <functional>
namespace bt {
using L2capDataCb = std::function<void(ConnHandle conn, uint16_t cid, const uint8_t *data, uint16_t len)>;

class IL2capManager {
public:
    virtual ~IL2capManager() = default;
    virtual BtError register_psm(uint16_t psm, L2capDataCb cb) = 0;
    virtual BtError open_channel(ConnHandle conn, uint16_t psm, uint16_t &out_cid) = 0;
    virtual BtError close_channel(ConnHandle conn, uint16_t cid) = 0;
    virtual BtError send_data(ConnHandle conn, uint16_t cid, const uint8_t *data, uint16_t len) = 0;
    virtual BtError set_mtu(uint16_t cid, uint16_t mtu) = 0;
};
}
