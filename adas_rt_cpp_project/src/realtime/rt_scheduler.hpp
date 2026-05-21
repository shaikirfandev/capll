#pragma once
/**
 * @file rt_scheduler.hpp
 * @brief POSIX real-time thread scheduler for the ADAS pipeline.
 *
 * REAL-TIME LINUX BACKGROUND
 * ──────────────────────────
 * Requires PREEMPT_RT kernel patch (or Xenomai) for deterministic latency.
 * Key kernel configurations needed:
 *   CONFIG_PREEMPT_RT=y
 *   CONFIG_HZ=1000
 *   CONFIG_NO_HZ_FULL=y   (tickless for CPU isolation)
 *
 * THREAD MODEL
 * ────────────
 * All tasks run in SCHED_FIFO (First-In-First-Out real-time policy).
 * Priority range: 1 (lowest RT) – 99 (highest RT).
 *
 * Task priorities (high = runs first when runnable):
 *   90  – Safety monitor   (checks for AEB conditions, WDT)
 *   80  – Sensor processing (camera 50 Hz, radar 20 Hz)
 *   70  – Fusion           (50 Hz)
 *   60  – Planning         (20 Hz)
 *   50  – Control output   (50 Hz → CAN Tx)
 *   40  – Diagnostics/log  (10 Hz)
 *
 * CPU AFFINITY
 * ────────────
 * Threads are pinned to isolated CPU cores (configured via kernel cmdline
 * isolcpus=2,3 nohz_full=2,3). Core 0 handles OS interrupts only.
 *
 * MEMORY LOCKING
 * ──────────────
 * mlockall(MCL_CURRENT | MCL_FUTURE) prevents page faults during execution.
 * Called once at startup before spawning RT threads.
 */

#include <chrono>
#include <functional>
#include <string>
#include <thread>
#include <vector>
#include <atomic>
#include <cstdint>

// POSIX RT headers (Linux)
#include <pthread.h>
#include <sched.h>

namespace adas {
namespace realtime {

// ─── Task definition ──────────────────────────────────────────────────────────

struct RtTask {
    std::string              name;
    int                      priority;        ///< SCHED_FIFO priority [1-99]
    int                      cpu_affinity;    ///< CPU core to pin (-1 = no pin)
    std::chrono::microseconds period_us;      ///< Periodic execution interval
    std::function<void()>    callback;        ///< Task body (must be bounded)
};

// ─── Statistics per task ──────────────────────────────────────────────────────

struct TaskStats {
    std::string name;
    uint64_t    executions{0};
    uint64_t    deadline_misses{0};
    int64_t     max_jitter_us{0};   ///< Maximum scheduling jitter observed [µs]
    int64_t     avg_jitter_us{0};
    double      cpu_util_pct{0.0};  ///< Approximate CPU utilisation [%]
};

// ─── RtScheduler class ───────────────────────────────────────────────────────

/**
 * @class RtScheduler
 * @brief Manages a set of POSIX SCHED_FIFO periodic real-time threads.
 *
 * Usage:
 * @code
 *   RtScheduler sched;
 *   sched.lockMemory();        // mlockall – call before adding tasks
 *   sched.addTask({
 *       .name       = "sensor_fusion",
 *       .priority   = 70,
 *       .cpu_affinity = 2,
 *       .period_us  = std::chrono::microseconds(20'000),  // 50 Hz
 *       .callback   = [&]{ fusion.update(...); }
 *   });
 *   sched.start();
 *   // ... run until signal
 *   sched.stop();
 * @endcode
 */
class RtScheduler {
public:
    RtScheduler();
    ~RtScheduler();

    RtScheduler(const RtScheduler&)            = delete;
    RtScheduler& operator=(const RtScheduler&) = delete;

    /**
     * @brief Lock all current and future process memory pages.
     *        Must be called before start(), ideally as root or with
     *        CAP_IPC_LOCK capability.
     * @return true on success
     */
    bool lockMemory();

    /// Add a periodic RT task (must be called before start())
    void addTask(RtTask task);

    /// Launch all registered RT threads
    void start();

    /// Signal all threads to stop; blocks until all have joined
    void stop();

    /// Retrieve collected statistics (thread-safe snapshot)
    std::vector<TaskStats> getStats() const;

    bool isRunning() const { return running_.load(); }

private:
    struct ThreadContext {
        RtTask                   task;
        std::thread              thread;
        std::atomic<bool>        stop_flag{false};
        TaskStats                stats;
    };

    void runTask(ThreadContext& ctx);

    static void applySchedPolicy(pthread_t handle,
                                  int policy, int priority);
    static void applyCpuAffinity(pthread_t handle, int cpu);

    std::vector<ThreadContext> contexts_;
    std::atomic<bool>          running_{false};
};

// ─── Utility: set calling thread to RT ────────────────────────────────────────

/// Call this inside a thread to promote it to SCHED_FIFO at the given priority.
bool setThreadRealtimePriority(int priority);

/// Get current clock monotonic timestamp in microseconds
int64_t monotonicNowUs();

}  // namespace realtime
}  // namespace adas
