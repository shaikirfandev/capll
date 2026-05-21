/**
 * @file StdMutex.cpp
 */
#include "rtos/StdMutex.hpp"
#include <mutex>
#include <chrono>
namespace bt::rtos {
struct StdMutexImpl { std::timed_mutex mtx; };
StdMutex::StdMutex()  : impl_(std::make_unique<StdMutexImpl>()) {}
StdMutex::~StdMutex() = default;
void StdMutex::lock()   { impl_->mtx.lock(); }
void StdMutex::unlock() { impl_->mtx.unlock(); }
bool StdMutex::try_lock(uint32_t timeout_ms) {
    return impl_->mtx.try_lock_for(std::chrono::milliseconds(timeout_ms));
}
}
