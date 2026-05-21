/**
 * @file RingBuffer.hpp
 * @brief Lock-free single-producer single-consumer ring buffer
 * @req SRS-PERF-002
 */
#pragma once
#include <atomic>
#include <array>
#include <cstddef>
#include <type_traits>

namespace fms {

template <typename T, std::size_t N>
class RingBuffer {
    static_assert((N & (N - 1)) == 0, "N must be a power of 2");
public:
    RingBuffer() noexcept : head_(0), tail_(0) {}

    [[nodiscard]] bool push(const T& item) noexcept {
        const std::size_t h = head_.load(std::memory_order_relaxed);
        const std::size_t next = (h + 1) & (N - 1);
        if (next == tail_.load(std::memory_order_acquire)) return false;
        buf_[h] = item;
        head_.store(next, std::memory_order_release);
        return true;
    }

    [[nodiscard]] bool pop(T& item) noexcept {
        const std::size_t t = tail_.load(std::memory_order_relaxed);
        if (t == head_.load(std::memory_order_acquire)) return false;
        item = buf_[t];
        tail_.store((t + 1) & (N - 1), std::memory_order_release);
        return true;
    }

    [[nodiscard]] bool empty() const noexcept {
        return head_.load(std::memory_order_acquire) ==
               tail_.load(std::memory_order_acquire);
    }

private:
    alignas(64) std::atomic<std::size_t> head_;
    alignas(64) std::atomic<std::size_t> tail_;
    std::array<T, N> buf_{};
};

}  // namespace fms
