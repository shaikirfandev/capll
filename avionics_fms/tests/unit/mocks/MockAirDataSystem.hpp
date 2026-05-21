#pragma once
#include "sensors/IAirDataSystem.hpp"
#include <gmock/gmock.h>

struct MockAirDataSystem : fms::sensors::IAirDataSystem {
    MOCK_METHOD(fms::FmsError, init, (), (noexcept, override));
    MOCK_METHOD(void, shutdown, (), (noexcept, override));
    MOCK_METHOD(void, update, (), (noexcept, override));
    MOCK_METHOD(const fms::sensors::AdcRaw&, get_data, (), (const, noexcept, override));
    MOCK_METHOD(fms::SystemStatus, get_status, (), (const, noexcept, override));
};
