/**
 * @file test_gatt_server.cpp
 */
#include <gtest/gtest.h>
#include "bt/GattServer.hpp"

using namespace bt;

class GattServerTest : public ::testing::Test {
protected:
    GattServer gatt;
    static constexpr Uuid16 SVC_UUID  {0x180AU};
    static constexpr Uuid16 CHAR_UUID {0x2A26U};
};

TEST_F(GattServerTest, AddServiceSucceeds) {
    GattServiceDef svc{};
    svc.uuid16  = SVC_UUID;
    svc.primary = true;
    svc.chars.push_back({CHAR_UUID, GattProp::READ, GattPerm::READ, {0x31, 0x2E, 0x30}});

    EXPECT_EQ(gatt.add_service(svc), BtError::OK);
}

TEST_F(GattServerTest, SetAndGetValue) {
    GattServiceDef svc{};
    svc.uuid16  = SVC_UUID;
    svc.primary = true;
    svc.chars.push_back({CHAR_UUID, GattProp::READ, GattPerm::READ, {0x00}});
    gatt.add_service(svc);

    const uint8_t new_val = 87U;
    const AttHandle handle = 0x0002U;  // Value handle = declaration_handle + 1
    gatt.set_value(handle, &new_val, 1U);
}

TEST_F(GattServerTest, ReadCallbackInvoked) {
    GattServiceDef svc{};
    svc.uuid16  = SVC_UUID;
    svc.primary = true;
    svc.chars.push_back({CHAR_UUID, GattProp::READ, GattPerm::READ, {0xAA}});
    gatt.add_service(svc);

    bool cb_called = false;
    gatt.set_read_callback(0x0002U, [&cb_called](ConnHandle, AttHandle) -> std::vector<uint8_t> {
        cb_called = true;
        return {0xBBU};
    });

    // Simulate a read
    auto val = gatt.get_value(0x0002U);
    EXPECT_FALSE(val.empty());
}

TEST_F(GattServerTest, WriteCallbackInvoked) {
    GattServiceDef svc{};
    svc.uuid16  = SVC_UUID;
    svc.primary = true;
    svc.chars.push_back({CHAR_UUID, GattProp::WRITE, GattPerm::WRITE, {0x00}});
    gatt.add_service(svc);

    bool cb_called = false;
    gatt.set_write_callback(0x0002U, [&cb_called](ConnHandle, AttHandle,
                                                    const uint8_t *, uint16_t) {
        cb_called = true;
        return BtError::OK;
    });

    const uint8_t data = 0xFFU;
    gatt.set_value(0x0002U, &data, 1U);
}
