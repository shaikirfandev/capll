/**
 * @file IGpio.hpp
 * @brief GPIO interface for BT enable/reset/IRQ pins
 */
#pragma once
#include <cstdint>
#include <functional>
namespace bt::hal {
enum class GpioDirn   : uint8_t { INPUT, OUTPUT };
enum class GpioPull   : uint8_t { NONE, PULL_UP, PULL_DOWN };
enum class GpioEdge   : uint8_t { RISING, FALLING, BOTH };
using GpioIrqCb = std::function<void(uint8_t pin)>;
class IGpio {
public:
    virtual ~IGpio() = default;
    virtual bool    configure(uint8_t pin, GpioDirn dir, GpioPull pull) = 0;
    virtual void    write(uint8_t pin, bool high) = 0;
    virtual bool    read(uint8_t pin) const = 0;
    virtual bool    attach_irq(uint8_t pin, GpioEdge edge, GpioIrqCb cb) = 0;
    virtual void    detach_irq(uint8_t pin) = 0;
};
}
