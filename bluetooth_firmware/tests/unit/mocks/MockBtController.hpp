/**
 * @file MockBtController.hpp
 * @brief GMock mock for IBluetoothController
 */
#pragma once
#include "bt/IBluetoothController.hpp"
#include <gmock/gmock.h>

namespace bt::mocks {

class MockBtController : public IBluetoothController {
public:
    MOCK_METHOD(BtError, initialise,          (BtMode mode), (override));
    MOCK_METHOD(BtError, reset,               (),            (override));
    MOCK_METHOD(void,    shutdown,            (),            (override));
    MOCK_METHOD(BdAddr,  get_public_address,  (),            (const, override));
    MOCK_METHOD(BtError, set_random_address,  (const BdAddr &), (override));
    MOCK_METHOD(BtError, set_device_name,     (std::string_view), (override));
    MOCK_METHOD(BtError, send_hci_command,    (uint16_t, const uint8_t *, uint8_t), (override));
    MOCK_METHOD(BtError, send_acl_data,       (ConnHandle, const uint8_t *, uint16_t), (override));
    MOCK_METHOD(void,    register_event_callback, (HciEventCb),   (override));
    MOCK_METHOD(void,    register_acl_callback,   (HciAclDataCb), (override));
    MOCK_METHOD(BtError, start_advertising,   (const AdvParams &, const AdvData &, const AdvData &), (override));
    MOCK_METHOD(BtError, stop_advertising,    (),          (override));
    MOCK_METHOD(BtError, start_scan,          (bool, uint16_t, uint16_t), (override));
    MOCK_METHOD(BtError, stop_scan,           (),          (override));
    MOCK_METHOD(BtError, create_ble_connection, (const BdAddr &, bool), (override));
    MOCK_METHOD(BtError, set_connectable,     (bool),      (override));
    MOCK_METHOD(BtError, set_discoverable,    (bool, uint16_t), (override));
    MOCK_METHOD(BtError, start_inquiry,       (uint8_t),   (override));
    MOCK_METHOD(BtError, disconnect,          (ConnHandle, uint8_t), (override));
    MOCK_METHOD(BtError, update_conn_params,  (ConnHandle, uint16_t, uint16_t, uint16_t, uint16_t), (override));
    MOCK_METHOD(void,    set_power_state,     (PowerState), (override));
    MOCK_METHOD(PowerState, get_power_state,  (),           (const, override));
    MOCK_METHOD(BtError, set_tx_power,        (int8_t),    (override));
    MOCK_METHOD(int8_t,  get_rssi,            (ConnHandle), (const, override));
    MOCK_METHOD((std::array<uint8_t,4>), get_version, (), (const, override));
};

}  // namespace bt::mocks
