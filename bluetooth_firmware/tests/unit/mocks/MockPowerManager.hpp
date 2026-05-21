/**
 * @file MockPowerManager.hpp
 */
#pragma once
#include "hal/IPower.hpp"
#include <gmock/gmock.h>
namespace bt::mocks {
class MockPowerManager : public hal::IPower {
public:
    MOCK_METHOD(void,    enter_sleep,       (),                         (override));
    MOCK_METHOD(void,    wake_up,           (),                         (override));
    MOCK_METHOD(float,   get_voltage,       (hal::SysVoltageRail rail), (const, override));
    MOCK_METHOD(bool,    is_charging,       (),                         (const, override));
    MOCK_METHOD(uint8_t, battery_percent,   (),                         (const, override));
    MOCK_METHOD(void,    power_down_radio,  (),                         (override));
    MOCK_METHOD(void,    power_up_radio,    (),                         (override));
};
}
