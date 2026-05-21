/**
 * @file rt_scheduler.cpp
 * @brief POSIX SCHED_FIFO real-time scheduler implementation.
 *
 * IMPLEMENTATION NOTES
 * ────────────────────
 * 1. Each task runs as a periodic thread using clock_nanosleep(TIMER_ABSTIME)
 *    rather than nanosleep(): ABSTIME avoids drift accumulation because we
 *    always sleep until an absolute wall-clock deadline, not a relative offset.
 *
 * 2. Jitter is measured as: actual_wake_time - expected_wake_time.
 *    Any jitter > period/2 is counted as a deadline miss.
 *
 * 3. The main process must have CAP_SYS_NICE (or run as root) to set
 *    SCHED_FIFO; otherwise pthread_setschedparam returns EPERM.
 *
 * 4. Pre-fault stack: we touch a 256 KB buffer before entering the RT loop
 *    to force stack pages into RAM (avoids first-access page faults).
 */

#include "rt_scheduler.hpp"

#include <cerrno>
#include <cstring>
#include <iostream>
#include <stdexcept>
#include <sys/mman.h>   // mlockall
#include <time.h>       // clock_gettime, clock_nanosleep

namespace adas {
namespace realtime {

// ─── Utility ─────────────────────────────────────────────────────────────────

int64_t monotonicNowUs() {
    struct timespec ts{};
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return static_cast<int64_t>(ts.tv_sec) * 1'000'000LL
         + static_cast<int64_t>(ts.tv_nsec) / 1'000LL;
}

static struct timespec usToTimespec(int64_t us) {
    struct timespec ts{};
    ts.tv_sec  = us / 1'000'000LL;
    ts.tv_nsec = (us % 1'000'000LL) * 1'000LL;
    return ts;
}

static int64_t timespecToUs(const struct timespec& ts) {
    return static_cast<int64_t>(ts.tv_sec) * 1'000'000LL
         + static_cast<int64_t>(ts.tv_nsec) / 1'000LL;
}

/// Pre-fault the stack (touch every page to bring into RAM before RT start)
static void prefaultStack() {
    constexpr size_t kStackSize = 256 * 1024;
    volatile char stack_buf[kStackSize];
    for (size_t i = 0; i < kStackSize; i += 4096) {
        stack_buf[i] = 0;  // touch each page
    }
    (void)stack_buf;
}

bool setThreadRealtimePriority(int priority) {
    struct sched_param param{};
    param.sched_priority = priority;
    if (pthread_setschedparam(pthread_self(), SCHED_FIFO, &param) != 0) {
        std::cerr << "[RT] Warning: cannot set SCHED_FIFO (errno="
                  << errno << ":" << std::strerror(errno) << ")\n";
        return false;
    }
    return true;
}

// ─── RtScheduler ─────────────────────────────────────────────────────────────

RtScheduler::RtScheduler()  = default;
RtScheduler::~RtScheduler() { stop(); }

bool RtScheduler::lockMemory() {
    if (mlockall(MCL_CURRENT | MCL_FUTURE) != 0) {
        std::cerr << "[RT] mlockall failed: " << std::strerror(errno)
                  << " (run as root or grant CAP_IPC_LOCK)\n";
        return false;
    }
    std::cout << "[RT] Memory locked (MCL_CURRENT | MCL_FUTURE)\n";
    return true;
}

void RtScheduler::addTask(RtTask task) {
    if (running_.load()) {
        throw std::logic_error("RtScheduler: cannot addTask() while running");
    }
    contexts_.emplace_back();
    contexts_.back().task  = std::move(task);
    contexts_.back().stats.name = contexts_.back().task.name;
}

void RtScheduler::start() {
    if (running_.exchange(true)) return;  // already running

    for (auto& ctx : contexts_) {
        ctx.stop_flag.store(false);
        ctx.thread = std::thread([this, &ctx] { runTask(ctx); });
    }
    std::cout << "[RT] Started " << contexts_.size() << " RT tasks\n";
}

void RtScheduler::stop() {
    if (!running_.exchange(false)) return;

    for (auto& ctx : contexts_) {
        ctx.stop_flag.store(true);
    }
    for (auto& ctx : contexts_) {
        if (ctx.thread.joinable()) {
            ctx.thread.join();
        }
    }
    std::cout << "[RT] All tasks stopped\n";
}

void RtScheduler::runTask(ThreadContext& ctx) {
    // ① Set SCHED_FIFO priority
    applySchedPolicy(pthread_self(), SCHED_FIFO, ctx.task.priority);

    // ② CPU affinity
    if (ctx.task.cpu_affinity >= 0) {
        applyCpuAffinity(pthread_self(), ctx.task.cpu_affinity);
    }

    // ③ Pre-fault stack
    prefaultStack();

    // ④ Compute first absolute deadline
    struct timespec ts{};
    clock_gettime(CLOCK_MONOTONIC, &ts);
    int64_t next_wake_us = timespecToUs(ts);

    const int64_t period_us = ctx.task.period_us.count();

    while (!ctx.stop_flag.load(std::memory_order_relaxed)) {
        next_wake_us += period_us;

        // ⑤ Sleep until absolute deadline
        struct timespec abs_deadline = usToTimespec(next_wake_us);
        while (clock_nanosleep(CLOCK_MONOTONIC, TIMER_ABSTIME,
                               &abs_deadline, nullptr) == EINTR) {
            // Restarted by signal – loop
        }

        // ⑥ Measure actual wake-up jitter
        const int64_t actual_us = monotonicNowUs();
        const int64_t jitter_us = actual_us - next_wake_us;

        // ⑦ Execute task body
        ctx.task.callback();

        // ⑧ Update stats
        ++ctx.stats.executions;
        if (jitter_us > ctx.stats.max_jitter_us) {
            ctx.stats.max_jitter_us = jitter_us;
        }
        if (jitter_us > period_us / 2) {
            ++ctx.stats.deadline_misses;
        }
        // Exponential moving average for avg jitter
        constexpr double kAlpha = 0.01;
        ctx.stats.avg_jitter_us = static_cast<int64_t>(
            (1.0 - kAlpha) * ctx.stats.avg_jitter_us + kAlpha * jitter_us);
    }
}

void RtScheduler::applySchedPolicy(pthread_t handle, int policy, int priority) {
    struct sched_param param{};
    param.sched_priority = priority;
    if (pthread_setschedparam(handle, policy, &param) != 0) {
        std::cerr << "[RT] pthread_setschedparam failed: "
                  << std::strerror(errno) << "\n";
    }
}

void RtScheduler::applyCpuAffinity(pthread_t handle, int cpu) {
    cpu_set_t cpuset;
    CPU_ZERO(&cpuset);
    CPU_SET(cpu, &cpuset);
    if (pthread_setaffinity_np(handle, sizeof(cpu_set_t), &cpuset) != 0) {
        std::cerr << "[RT] pthread_setaffinity_np failed for CPU "
                  << cpu << ": " << std::strerror(errno) << "\n";
    }
}

std::vector<TaskStats> RtScheduler::getStats() const {
    std::vector<TaskStats> out;
    out.reserve(contexts_.size());
    for (const auto& ctx : contexts_) {
        out.push_back(ctx.stats);
    }
    return out;
}

}  // namespace realtime
}  // namespace adas
