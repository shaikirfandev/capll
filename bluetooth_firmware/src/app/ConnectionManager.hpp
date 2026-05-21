/**
 * @file ConnectionManager.hpp
 */
#pragma once
#include "app/IConnectionManager.hpp"
#include "bt/IBluetoothController.hpp"
#include <memory>
namespace bt::app {
class ConnectionManager final : public IConnectionManager {
public:
    explicit ConnectionManager(IBluetoothController *controller);
    ~ConnectionManager() override;
    BtError connect(const BdAddr &peer, bool is_random)  override;
    BtError disconnect(ConnHandle handle)                override;
    BtError start_advertising()                          override;
    BtError stop_advertising()                           override;
    uint8_t active_connections() const                   override;
    void    on_connected(ConnectedCb cb)                 override;
    void    on_disconnected(DisconnectedCb cb)           override;
private:
    void _handle_hci_event(const uint8_t *data, uint16_t len);
    struct Impl;
    std::unique_ptr<Impl> impl_;
};
}
