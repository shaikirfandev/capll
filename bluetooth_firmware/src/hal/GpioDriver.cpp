/**
 * @file GpioDriver.cpp
 */
#include "hal/GpioDriver.hpp"
#include "common/Logger.hpp"
#include <unordered_map>
#include <mutex>

namespace bt::hal {

struct GpioDriver::Impl {
    std::unordered_map<uint8_t, bool>       pin_state;   // pin -> level
    std::unordered_map<uint8_t, GpioIrqCb> irq_cbs;
    mutable std::mutex mtx;
};

GpioDriver::GpioDriver()  : impl_(std::make_unique<Impl>()) {}
GpioDriver::~GpioDriver() = default;

bool GpioDriver::configure(uint8_t pin, GpioDirn dir, GpioPull pull) {
    std::lock_guard<std::mutex> lock(impl_->mtx);
    impl_->pin_state[pin] = (pull == GpioPull::PULL_UP);
    return true;
}

void GpioDriver::write(uint8_t pin, bool high) {
    std::lock_guard<std::mutex> lock(impl_->mtx);
    const bool prev = impl_->pin_state[pin];
    impl_->pin_state[pin] = high;
    // Fire IRQ if edge matches
    auto it = impl_->irq_cbs.find(pin);
    if (it != impl_->irq_cbs.end()) {
        if (!prev && high) {  // Rising edge — simplified
            it->second(pin);
        }
    }
}

bool GpioDriver::read(uint8_t pin) const {
    std::lock_guard<std::mutex> lock(impl_->mtx);
    auto it = impl_->pin_state.find(pin);
    return (it != impl_->pin_state.end()) && it->second;
}

bool GpioDriver::attach_irq(uint8_t pin, GpioEdge /*edge*/, GpioIrqCb cb) {
    std::lock_guard<std::mutex> lock(impl_->mtx);
    impl_->irq_cbs[pin] = std::move(cb);
    return true;
}

void GpioDriver::detach_irq(uint8_t pin) {
    std::lock_guard<std::mutex> lock(impl_->mtx);
    impl_->irq_cbs.erase(pin);
}

}  // namespace bt::hal
