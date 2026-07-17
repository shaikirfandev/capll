#pragma once

#include <array>
#include <atomic>
#include <cstddef>
#include <optional>
#include <type_traits>

namespace adas {

// Lock-free bounded hand-off for exactly one producer and one consumer.
// Capacity must be a power of two. No allocation and no blocking in push/pop.
template <typename T, std::size_t Capacity>
class SpscQueue final {
    static_assert(std::is_trivially_copyable_v<T>);
    static_assert(Capacity >= 2U && (Capacity & (Capacity - 1U)) == 0U);

public:
    [[nodiscard]] bool try_push(const T& value) noexcept {
        const auto write = write_index_.load(std::memory_order_relaxed);
        const auto next = (write + 1U) & kMask;
        if (next == read_index_.load(std::memory_order_acquire)) return false;
        storage_[write] = value;
        write_index_.store(next, std::memory_order_release);
        return true;
    }

    [[nodiscard]] std::optional<T> try_pop() noexcept {
        const auto read = read_index_.load(std::memory_order_relaxed);
        if (read == write_index_.load(std::memory_order_acquire)) return std::nullopt;
        const T value = storage_[read];
        read_index_.store((read + 1U) & kMask, std::memory_order_release);
        return value;
    }

    [[nodiscard]] bool empty() const noexcept {
        return read_index_.load(std::memory_order_acquire) == write_index_.load(std::memory_order_acquire);
    }

private:
    static constexpr std::size_t kMask = Capacity - 1U;
    std::array<T, Capacity> storage_{};
    alignas(64) std::atomic<std::size_t> write_index_{0U};
    alignas(64) std::atomic<std::size_t> read_index_{0U};
};

}  // namespace adas
