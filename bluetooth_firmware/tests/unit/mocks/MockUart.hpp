/**
 * @file MockUart.hpp
 */
#pragma once
#include "hal/IUart.hpp"
#include <gmock/gmock.h>
namespace bt::mocks {
class MockUart : public hal::IUart {
public:
    MOCK_METHOD(bool,    init,       (const hal::UartConfig &), (override));
    MOCK_METHOD(void,    deinit,     (),                        (override));
    MOCK_METHOD(int32_t, send,       (const uint8_t *, uint16_t), (override));
    MOCK_METHOD(int32_t, receive,    (uint8_t *, uint16_t, uint32_t), (override));
    MOCK_METHOD(void,    set_rx_callback, (hal::UartRxCb),    (override));
    MOCK_METHOD(void,    flush,      (),                        (override));
    MOCK_METHOD(bool,    set_baud,   (uint32_t),                (override));
};
}
