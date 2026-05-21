/**
 * @file MockRtosQueue.hpp
 */
#pragma once
#include "rtos/IRtosQueue.hpp"
#include <gmock/gmock.h>
namespace bt::mocks {
class MockRtosQueue : public rtos::IRtosQueueBase {
public:
    MOCK_METHOD(bool,     send_raw,    (const void *, uint32_t), (override));
    MOCK_METHOD(bool,     receive_raw, (void *, uint32_t),       (override));
    MOCK_METHOD(uint32_t, size,        (),                       (const, override));
    MOCK_METHOD(bool,     empty,       (),                       (const, override));
};
}
