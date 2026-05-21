/**
 * @file StdSemaphore.cpp
 */
#include "rtos/StdSemaphore.hpp"
#include <mutex>
#include <condition_variable>
#include <chrono>

namespace bt::rtos {

struct StdSemaphore::Impl {
    std::mutex              mtx;
    std::condition_variable cv;
    uint32_t                count;
    explicit Impl(uint32_t init) : count(init) {}
};

StdSemaphore::StdSemaphore(uint32_t initial_count)
    : impl_(std::make_unique<Impl>(initial_count)) {}
StdSemaphore::~StdSemaphore() = default;

void StdSemaphore::give() {
    {
        std::lock_guard<std::mutex> lock(impl_->mtx);
        impl_->count++;
    }
    impl_->cv.notify_one();
}

bool StdSemaphore::take(uint32_t timeout_ms) {
    std::unique_lock<std::mutex> lock(impl_->mtx);
    const bool ok = impl_->cv.wait_for(lock,
        std::chrono::milliseconds(timeout_ms),
        [this] { return impl_->count > 0U; });
    if (ok) { impl_->count--; }
    return ok;
}

uint32_t StdSemaphore::count() const {
    std::lock_guard<std::mutex> lock(impl_->mtx);
    return impl_->count;
}

}  // namespace bt::rtos
