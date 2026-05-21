/**
 * @file FreeRtosQueue.hpp
 */
#pragma once
#include "rtos/IRtosInterfaces.hpp"
#include <queue>
#include <mutex>
#include <condition_variable>
#include <cstring>

namespace fms::rtos {

class FreeRtosQueue : public IRtosQueueBase {
public:
    explicit FreeRtosQueue(std::size_t item_size) : item_size_(item_size) {}

    bool send_raw(const void* data, std::size_t sz, uint32_t /*timeout_ms*/) noexcept override {
        if (sz != item_size_) return false;
        std::vector<uint8_t> item(sz);
        std::memcpy(item.data(), data, sz);
        std::unique_lock lk(mtx_);
        q_.push(std::move(item));
        cv_.notify_one();
        return true;
    }

    bool receive_raw(void* data, std::size_t sz, uint32_t timeout_ms) noexcept override {
        std::unique_lock lk(mtx_);
        if (!cv_.wait_for(lk, std::chrono::milliseconds(timeout_ms),
                          [this] { return !q_.empty(); })) return false;
        std::memcpy(data, q_.front().data(), sz);
        q_.pop();
        return true;
    }

    std::size_t size()  const noexcept override { std::unique_lock lk(mtx_); return q_.size(); }
    bool        empty() const noexcept override { std::unique_lock lk(mtx_); return q_.empty(); }

private:
    std::size_t item_size_;
    mutable std::mutex mtx_;
    std::condition_variable cv_;
    std::queue<std::vector<uint8_t>> q_;
};

}  // namespace fms::rtos
