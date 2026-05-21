/**
 * @file GpioDriver.hpp
 */
#pragma once
#include "hal/IGpio.hpp"
#include <memory>
namespace bt::hal {
class GpioDriver final : public IGpio {
public:
    GpioDriver(); ~GpioDriver() override;
    bool configure(uint8_t pin, GpioDirn dir, GpioPull pull)     override;
    void write(uint8_t pin, bool high)                           override;
    bool read(uint8_t pin) const                                 override;
    bool attach_irq(uint8_t pin, GpioEdge edge, GpioIrqCb cb)   override;
    void detach_irq(uint8_t pin)                                 override;
private:
    struct Impl; std::unique_ptr<Impl> impl_;
};
}
