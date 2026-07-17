// ============================================================
// adas/qnx_integration.cpp — QNX/POSIX integration helpers
// ============================================================

#include "adas/qnx_integration.hpp"

#include <thread>

namespace adas {
namespace qnx {

PeriodicBarrier::PeriodicBarrier(std::chrono::nanoseconds period) noexcept
    : period_(period), next_release_(std::chrono::steady_clock::now()) {}

std::chrono::microseconds PeriodicBarrier::wait() noexcept {
    next_release_ += period_;
    const auto before = std::chrono::steady_clock::now();
    std::this_thread::sleep_until(next_release_);
    const auto after = std::chrono::steady_clock::now();
    // Jitter = actual wakeup - scheduled wakeup
    const auto jitter = std::chrono::duration_cast<std::chrono::microseconds>(after - next_release_);
    return jitter;
}

bool verify_thread_config([[maybe_unused]] const RtThreadConfig& cfg) noexcept {
    // On QNX/Linux: query pthread attributes and sched policy.
    // On host (macOS), return true for unit-test compatibility.
#if defined(__QNX__) || defined(__linux__)
    // TODO: implement pthread_getattr_np / sched_getscheduler verification.
    return false;  // Placeholder: return false until target implementation is done.
#else
    return true;
#endif
}

}  // namespace qnx
}  // namespace adas
