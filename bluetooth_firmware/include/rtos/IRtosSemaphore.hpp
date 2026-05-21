/**
 * @file IRtosSemaphore.hpp
 * @brief RTOS counting semaphore abstraction
 */
#pragma once
#include <cstdint>
namespace bt::rtos {
class IRtosSemaphore {
public:
    virtual ~IRtosSemaphore() = default;
    virtual void give() = 0;
    virtual bool take(uint32_t timeout_ms) = 0;
    virtual uint32_t count() const = 0;
};
}
