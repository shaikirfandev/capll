/**
 * @file BluetoothController.hpp
 * @brief Concrete simulated Bluetooth Controller (Singleton)
 */
#pragma once
#include "bt/IBluetoothController.hpp"
#include <memory>

namespace bt {

class BluetoothController final : public IBluetoothController {
public:
    static BluetoothController &instance();

    // Non-copyable, non-movable
    BluetoothController(const BluetoothController &) = delete;
    BluetoothController &operator=(const BluetoothController &) = delete;

    BtError   initialise(BtMode mode) override;
    BtError   reset()                 override;
    void      shutdown()              override;

    BdAddr    get_public_address()                           const override;
    BtError   set_random_address(const BdAddr &addr)               override;
    BtError   set_device_name(std::string_view name)               override;
    BtError   send_hci_command(uint16_t opcode,
                                const uint8_t *params, uint8_t len) override;
    BtError   send_acl_data(ConnHandle handle,
                             const uint8_t *data, uint16_t len)     override;
    void      register_event_callback(HciEventCb cb)               override;
    void      register_acl_callback(HciAclDataCb cb)               override;
    BtError   start_advertising(const AdvParams &p,
                                 const AdvData &adv,
                                 const AdvData &scan_rsp)           override;
    BtError   stop_advertising()                                   override;
    BtError   start_scan(uint16_t win, uint16_t intv,
                          bool active, bool dedup)                   override;
    BtError   stop_scan()                                          override;
    BtError   create_ble_connection(const BdAddr &peer,
                                    bool peer_is_random)            override;
    BtError   set_connectable(bool enable)                         override;
    BtError   set_discoverable(bool enable, uint16_t timeout_sec)  override;
    BtError   start_inquiry(uint8_t duration_s,
                             uint8_t max_responses)                 override;
    BtError   disconnect(ConnHandle handle, uint8_t reason)        override;
    BtError   update_conn_params(ConnHandle handle,
                                  uint16_t imin, uint16_t imax,
                                  uint16_t lat, uint16_t sto)       override;
    BtError   set_power_state(PowerState state)                    override;
    PowerState get_power_state()                               const override;
    BtError   set_tx_power(int8_t dbm)                             override;
    int8_t    get_rssi(ConnHandle handle)                          override;
    ControllerVersion get_version()                           const override;

private:
    BluetoothController();
    ~BluetoothController() override;
    struct Impl;
    std::unique_ptr<Impl> impl_;
};

}  // namespace bt
