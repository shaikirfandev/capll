/**
 * @file IConnectionManager.hpp
 * @brief Application-level connection manager interface
 */
#pragma once
#include "../bt/BluetoothTypes.hpp"
#include <functional>
namespace bt::app {
using ConnectedCb    = std::function<void(ConnHandle, const BdAddr &)>;
using DisconnectedCb = std::function<void(ConnHandle, uint8_t reason)>;
class IConnectionManager {
public:
    virtual ~IConnectionManager() = default;
    virtual BtError connect(const BdAddr &peer, bool is_random) = 0;
    virtual BtError disconnect(ConnHandle handle) = 0;
    virtual BtError start_advertising() = 0;
    virtual BtError stop_advertising() = 0;
    virtual uint8_t active_connections() const = 0;
    virtual void    on_connected(ConnectedCb cb) = 0;
    virtual void    on_disconnected(DisconnectedCb cb) = 0;
};
}
