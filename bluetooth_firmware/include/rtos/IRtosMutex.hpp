/**
 * @file IRtosMutex.hpp
 * @brief RTOS mutex abstraction interface
 */
#pragma once
#include <cstdint>
namespace bt::rtos {
class IRtosMutex {
public:
    virtual ~IRtosMutex() = default;
    virtual void lock() = 0;
    virtual void unlock() = 0;
    virtual bool try_lock(uint32_t timeout_ms) = 0;
};
}
