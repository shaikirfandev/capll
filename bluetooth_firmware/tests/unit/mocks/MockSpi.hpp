/**
 * @file MockSpi.hpp
 */
#pragma once
#include "hal/ISpi.hpp"
#include <gmock/gmock.h>
namespace bt::mocks {
class MockSpi : public hal::ISpi {
public:
    MOCK_METHOD(bool,    init,      (const hal::SpiConfig &),                 (override));
    MOCK_METHOD(void,    deinit,    (),                                        (override));
    MOCK_METHOD(int32_t, transfer,  (const uint8_t *, uint8_t *, uint16_t),   (override));
    MOCK_METHOD(int32_t, write,     (const uint8_t *, uint16_t),               (override));
    MOCK_METHOD(int32_t, read,      (uint8_t *, uint16_t),                     (override));
    MOCK_METHOD(bool,    set_freq,  (uint32_t),                                (override));
};
}
