/**
 * @file PowerManager.hpp
 */
#pragma once
#include "hal/IPower.hpp"
#include "bt/BluetoothTypes.hpp"
#include <memory>
namespace bt::hal {
class PowerManager final : public IPower {
public:
    PowerManager(); ~PowerManager() override;
    void    enter_sleep()                              override;
    void    wake_up()                                  override;
    float   get_voltage(SysVoltageRail rail) const     override;
    bool    is_charging() const                        override;
    uint8_t battery_percent() const                    override;
    void    power_down_radio()                         override;
    void    power_up_radio()                           override;
private:
    struct Impl; std::unique_ptr<Impl> impl_;
};
}
