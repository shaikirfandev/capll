/**
 * @file IRtosQueue.hpp
 * @brief RTOS queue abstraction interface
 */
#pragma once
#include <cstdint>
namespace bt::rtos {
class IRtosQueueBase {
public:
    virtual ~IRtosQueueBase() = default;
    virtual bool send_raw(const void *item, uint32_t timeout_ms) = 0;
    virtual bool receive_raw(void *item, uint32_t timeout_ms) = 0;
    virtual uint32_t size() const = 0;
    virtual bool     empty() const = 0;
};
}
