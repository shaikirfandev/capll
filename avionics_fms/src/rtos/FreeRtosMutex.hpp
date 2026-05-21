/**
 * @file FreeRtosMutex.hpp / FreeRtosMutex.cpp
 */
#pragma once
#include "rtos/IRtosInterfaces.hpp"
#include <mutex>
namespace fms::rtos {
class FreeRtosMutex : public IRtosMutex {
public:
    bool lock(uint32_t /*timeout_ms*/) noexcept override { mtx_.lock(); return true; }
    void unlock() noexcept override { mtx_.unlock(); }
    bool try_lock() noexcept override { return mtx_.try_lock(); }
private:
    std::mutex mtx_;
};
}
