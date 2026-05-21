/**
 * @file StdMutex.hpp
 */
#pragma once
#include "rtos/IRtosMutex.hpp"
#include <memory>
namespace bt::rtos {
struct StdMutexImpl;
class StdMutex final : public IRtosMutex {
public:
    StdMutex(); ~StdMutex() override;
    void lock()                        override;
    void unlock()                      override;
    bool try_lock(uint32_t timeout_ms) override;
private:
    std::unique_ptr<StdMutexImpl> impl_;
};
}
