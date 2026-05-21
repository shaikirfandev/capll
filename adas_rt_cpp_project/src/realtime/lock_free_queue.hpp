#pragma once
/**
 * @file lock_free_queue.hpp
 * @brief Wait-free Single-Producer / Single-Consumer (SPSC) ring buffer.
 *
 * DESIGN
 * ──────
 * • Power-of-2 ring buffer for O(1) modulo via bitmask.
 * • Head/tail are separate std::atomic<uint64_t> on independent cache lines
 *   (64-byte aligned) to eliminate false-sharing between producer and consumer.
 * • Memory ordering:
 *     push: store(release) after writing item;  load head with relaxed.
 *     pop:  store(release) after reading item;  load tail with acquire.
 * • Zero heap allocations after construction.
 *
 * USAGE CONSTRAINTS
 * ─────────────────
 * • EXACTLY one producer thread and one consumer thread.
 * • T must be trivially copyable (memcpy semantics in ring buffer).
 * • Capacity must be a power of 2; CAPACITY is a compile-time template param.
 *
 * REAL-TIME SUITABILITY
 * ─────────────────────
 * • push() and pop() are O(1) and allocation-free → suitable for SCHED_FIFO
 *   threads with bounded execution time.
 */

#include <array>
#include <atomic>
#include <cstdint>
#include <optional>

namespace adas {
namespace realtime {

template<typename T, std::size_t CAPACITY>
class SpscQueue {
    static_assert((CAPACITY & (CAPACITY - 1)) == 0,
                  "CAPACITY must be a power of 2");
    static_assert(std::is_trivially_copyable_v<T>,
                  "T must be trivially copyable for lock-free ring buffer");

public:
    SpscQueue()  = default;
    ~SpscQueue() = default;

    // Non-copyable, non-movable
    SpscQueue(const SpscQueue&)            = delete;
    SpscQueue& operator=(const SpscQueue&) = delete;

    /**
     * @brief Try to push an item (producer side).
     * @return true on success, false if queue is full (non-blocking).
     */
    bool push(const T& item) noexcept {
        const uint64_t tail = tail_.load(std::memory_order_relaxed);
        const uint64_t next = tail + 1;
        // Full check: next head == current head
        if (next - head_.load(std::memory_order_acquire) > CAPACITY) {
            return false;
        }
        buffer_[tail & kMask] = item;
        tail_.store(next, std::memory_order_release);
        return true;
    }

    /**
     * @brief Try to pop an item (consumer side).
     * @return Item if available, std::nullopt if empty.
     */
    std::optional<T> pop() noexcept {
        const uint64_t head = head_.load(std::memory_order_relaxed);
        if (head == tail_.load(std::memory_order_acquire)) {
            return std::nullopt;  // empty
        }
        T item = buffer_[head & kMask];
        head_.store(head + 1, std::memory_order_release);
        return item;
    }

    /// Approximate size (not exact between threads)
    std::size_t size() const noexcept {
        return static_cast<std::size_t>(
            tail_.load(std::memory_order_acquire) -
            head_.load(std::memory_order_acquire));
    }

    bool empty() const noexcept { return size() == 0; }
    bool full()  const noexcept { return size() >= CAPACITY; }

    static constexpr std::size_t capacity() { return CAPACITY; }

private:
    static constexpr std::size_t kMask = CAPACITY - 1;

    // Cache-line separation (64 bytes) prevents false sharing
    alignas(64) std::atomic<uint64_t> head_{0};
    alignas(64) std::atomic<uint64_t> tail_{0};
    alignas(64) std::array<T, CAPACITY> buffer_;
};

}  // namespace realtime
}  // namespace adas
