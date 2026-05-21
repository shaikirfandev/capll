/**
 * @file RingBuffer.hpp
 * @brief Lock-free Single-Producer Single-Consumer (SPSC) ring buffer
 *
 * Template ring buffer optimised for ISR → task or task → task communication.
 * Uses std::atomic for head/tail to avoid mutexes in the fast path.
 *
 * @tparam T    Element type (must be trivially copyable for ISR use)
 * @tparam N    Capacity (must be power of 2 for fast modulo via bitmask)
 */

#pragma once

#include <array>
#include <atomic>
#include <cstdint>
#include <optional>
#include <type_traits>

namespace bt {

template<typename T, std::size_t N>
class RingBuffer {
    static_assert((N & (N - 1U)) == 0U, "RingBuffer capacity must be power of 2");
    static_assert(std::is_trivially_copyable_v<T>,
                  "RingBuffer element type must be trivially copyable (ISR-safe)");

public:
    RingBuffer() noexcept : head_(0U), tail_(0U) {}

    // No copy or move (atomic members make it non-trivially-copyable anyway)
    RingBuffer(const RingBuffer &) = delete;
    RingBuffer &operator=(const RingBuffer &) = delete;

    /**
     * @brief Push an element (producer side).
     * @note Safe to call from ISR if only one producer exists.
     * @return true if pushed successfully; false if buffer is full.
     */
    [[nodiscard]] bool push(const T &item) noexcept {
        const std::size_t head = head_.load(std::memory_order_relaxed);
        const std::size_t next = (head + 1U) & MASK;
        if (next == tail_.load(std::memory_order_acquire)) {
            return false;  // Full
        }
        buf_[head] = item;
        head_.store(next, std::memory_order_release);
        return true;
    }

    /**
     * @brief Pop an element (consumer side).
     * @return Element if available, std::nullopt if empty.
     */
    [[nodiscard]] std::optional<T> pop() noexcept {
        const std::size_t tail = tail_.load(std::memory_order_relaxed);
        if (tail == head_.load(std::memory_order_acquire)) {
            return std::nullopt;  // Empty
        }
        T item = buf_[tail];
        tail_.store((tail + 1U) & MASK, std::memory_order_release);
        return item;
    }

    /**
     * @brief Peek at the next element without removing it.
     */
    [[nodiscard]] std::optional<T> peek() const noexcept {
        const std::size_t tail = tail_.load(std::memory_order_relaxed);
        if (tail == head_.load(std::memory_order_acquire)) {
            return std::nullopt;
        }
        return buf_[tail];
    }

    [[nodiscard]] bool empty() const noexcept {
        return tail_.load(std::memory_order_acquire) ==
               head_.load(std::memory_order_acquire);
    }

    [[nodiscard]] bool full() const noexcept {
        const std::size_t next = (head_.load(std::memory_order_acquire) + 1U) & MASK;
        return next == tail_.load(std::memory_order_acquire);
    }

    [[nodiscard]] std::size_t size() const noexcept {
        const std::size_t h = head_.load(std::memory_order_acquire);
        const std::size_t t = tail_.load(std::memory_order_acquire);
        return (h - t) & MASK;
    }

    static constexpr std::size_t capacity() noexcept { return N - 1U; }

    void clear() noexcept {
        tail_.store(head_.load(std::memory_order_acquire), std::memory_order_release);
    }

private:
    static constexpr std::size_t MASK = N - 1U;

    alignas(64U) std::atomic<std::size_t> head_;  // Written by producer
    alignas(64U) std::atomic<std::size_t> tail_;  // Written by consumer
    std::array<T, N>                      buf_{};
};

// Common automotive instantiations (extern template to avoid code bloat)
extern template class RingBuffer<uint8_t,   256U>;  // HCI byte stream
extern template class RingBuffer<uint8_t,  1024U>;  // ACL data
extern template class RingBuffer<uint32_t,   64U>;  // Event codes
extern template class RingBuffer<uint32_t,  128U>;  // CAN-style message IDs

}  // namespace bt
