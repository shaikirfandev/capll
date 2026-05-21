/**
 * @file IRtosInterfaces.hpp
 * @brief RTOS mutex, queue, and timer abstractions
 */
#pragma once
#include "fms/FmsTypes.hpp"
#include <cstdint>
#include <functional>

namespace fms::rtos {

class IRtosMutex {
public:
    virtual ~IRtosMutex() = default;
    virtual bool lock(uint32_t timeout_ms = 0xFFFFFFFFU) noexcept = 0;
    virtual void unlock() noexcept = 0;
    virtual bool try_lock() noexcept = 0;
};

class IRtosQueueBase {
public:
    virtual ~IRtosQueueBase() = default;
    virtual bool   send_raw(const void* data, std::size_t size, uint32_t timeout_ms) noexcept = 0;
    virtual bool   receive_raw(void* data, std::size_t size, uint32_t timeout_ms) noexcept = 0;
    virtual std::size_t size() const noexcept = 0;
    virtual bool   empty() const noexcept = 0;
};

using TimerCb = std::function<void()>;

class IRtosTimer {
public:
    virtual ~IRtosTimer() = default;
    virtual FmsError create(const char* name, uint32_t period_ms,
                            bool periodic, TimerCb cb) noexcept = 0;
    virtual bool start() noexcept = 0;
    virtual bool stop() noexcept = 0;
    virtual bool reset() noexcept = 0;
    virtual bool is_active() const noexcept = 0;
};

}  // namespace fms::rtos
