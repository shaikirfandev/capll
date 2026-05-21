/**
 * @file StdQueue.cpp
 * @brief Thread-safe queue with timeout using std::condition_variable
 */
#include "rtos/StdQueue.hpp"
#include <queue>
#include <mutex>
#include <condition_variable>
#include <chrono>
#include <cstring>

namespace bt::rtos {

struct StdQueueBase::Impl {
    std::queue<std::vector<uint8_t>> q;
    std::mutex                       mtx;
    std::condition_variable          cv;
    uint32_t                         item_size;
    explicit Impl(uint32_t sz) : item_size(sz) {}
};

StdQueueBase::StdQueueBase(uint32_t item_size)
    : impl_(std::make_unique<Impl>(item_size)) {}
StdQueueBase::~StdQueueBase() = default;

bool StdQueueBase::send_raw(const void *item, uint32_t timeout_ms) {
    std::unique_lock<std::mutex> lock(impl_->mtx);
    std::vector<uint8_t> buf(impl_->item_size);
    std::memcpy(buf.data(), item, impl_->item_size);
    impl_->q.push(std::move(buf));
    impl_->cv.notify_one();
    (void)timeout_ms;
    return true;
}

bool StdQueueBase::receive_raw(void *item, uint32_t timeout_ms) {
    std::unique_lock<std::mutex> lock(impl_->mtx);
    const bool ready = impl_->cv.wait_for(lock,
        std::chrono::milliseconds(timeout_ms),
        [this] { return !impl_->q.empty(); });
    if (!ready) { return false; }
    std::memcpy(item, impl_->q.front().data(), impl_->item_size);
    impl_->q.pop();
    return true;
}

uint32_t StdQueueBase::size() const {
    std::lock_guard<std::mutex> lock(impl_->mtx);
    return static_cast<uint32_t>(impl_->q.size());
}

bool StdQueueBase::empty() const {
    std::lock_guard<std::mutex> lock(impl_->mtx);
    return impl_->q.empty();
}

}  // namespace bt::rtos
