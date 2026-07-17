#pragma once

// ============================================================
// adas/qnx_integration.hpp — QNX Neutrino RTOS integration layer
//
// Provides OS-abstraction helpers for the target QNX integration:
//
//   RtThread           — POSIX-compliant real-time thread with
//                        SCHED_FIFO, CPU-affinity, and memory-lock.
//   PeriodicBarrier    — clock_nanosleep-based deterministic release.
//   MonotonicClock     — steady monotonic clock (CLOCK_MONOTONIC).
//   WatchdogKicker     — sends a keep-alive pulse to a watchdog
//                        process (QNX resource manager interface).
//
// All types and functions either:
//   a) compile on host (macOS/Linux) using POSIX equivalents for unit test, or
//   b) activate QNX-specific system calls when __QNX__ is defined.
//
// Target integration:
//   1. Construct PeriodicBarrier for 20 ms (50 Hz) release.
//   2. Construct RtThread at priority 60, affinity mask for isolated core.
//   3. In the thread body:  barrier.wait();  runtime.run_cycle(now, dt);
//   4. Kick watchdog before sleep_until.
//
// SAFETY NOTE: Memory locking (mlockall) must be permitted by the
// process configuration. Verify with the platform team.
// ============================================================

#include "adas/types.hpp"

#include <chrono>
#include <cstdint>
#include <functional>

namespace adas {
namespace qnx {

// ──────────────────────────────────────────────────────────────────────────────
// Monotonic clock wrapper (steady, high-resolution)
// ──────────────────────────────────────────────────────────────────────────────
[[nodiscard]] inline TimePoint now() noexcept {
    return std::chrono::steady_clock::now();
}

// ──────────────────────────────────────────────────────────────────────────────
// Periodic release barrier — blocks until the next release point.
// ──────────────────────────────────────────────────────────────────────────────
class PeriodicBarrier {
public:
    explicit PeriodicBarrier(std::chrono::nanoseconds period) noexcept;

    /// @brief Block until the next periodic release point.
    /// @return Measured jitter (actual - expected) in microseconds.
    [[nodiscard]] std::chrono::microseconds wait() noexcept;

    [[nodiscard]] std::chrono::nanoseconds period() const noexcept { return period_; }

private:
    std::chrono::nanoseconds period_;
    TimePoint next_release_;
};

// ──────────────────────────────────────────────────────────────────────────────
// Real-time thread configuration
// ──────────────────────────────────────────────────────────────────────────────
struct RtThreadConfig {
    std::uint32_t cpu_affinity_mask{0xFFFFFFFFU};  // Bit per core; default: any
    int           sched_priority{60};              // SCHED_FIFO priority (1-99)
    std::size_t   stack_bytes{65536U};             // Pre-allocated stack
    bool          lock_memory{true};               // mlockall(MCL_CURRENT|MCL_FUTURE)
    const char*   name{"adas_ctrl"};
};

/// @brief Returns true if the current thread meets the supplied config.
/// @note  Implement with pthread_getattr_np / sched_getscheduler on target.
[[nodiscard]] bool verify_thread_config(const RtThreadConfig& cfg) noexcept;

}  // namespace qnx
}  // namespace adas
