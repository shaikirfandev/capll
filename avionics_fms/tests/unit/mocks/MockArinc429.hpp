#pragma once
#include "comms/IArinc429.hpp"
#include <gmock/gmock.h>

struct MockArinc429 : fms::comms::IArinc429 {
    MOCK_METHOD(fms::FmsError, init, (uint8_t, uint32_t), (noexcept, override));
    MOCK_METHOD(void, deinit, (), (noexcept, override));
    MOCK_METHOD(bool, transmit_raw, (uint32_t), (noexcept, override));
    MOCK_METHOD(void, set_rx_callback, (uint8_t, fms::comms::Arinc429RxCb), (noexcept, override));
    MOCK_METHOD(fms::SystemStatus, get_status, (), (const, noexcept, override));
};
