/**
 * @file IPower.hpp
 * @brief Power management interface for HAL layer
 */
#pragma once
#include <cstdint>
namespace bt::hal {
enum class SysVoltageRail : uint8_t { VCC_MAIN, VCC_RF, VCC_IO, VCC_VBAT };
class IPower {
public:
    virtual ~IPower() = default;
    virtual void    enter_sleep() = 0;
    virtual void    wake_up() = 0;
    virtual float   get_voltage(SysVoltageRail rail) const = 0;
    virtual bool    is_charging() const = 0;
    virtual uint8_t battery_percent() const = 0;
    virtual void    power_down_radio() = 0;
    virtual void    power_up_radio() = 0;
};
}
