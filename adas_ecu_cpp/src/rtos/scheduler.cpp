/**
 * @file    scheduler.cpp
 * @brief   Cyclic executive scheduler implementation.
 *
 * Key embedded insight:
 *   No OS overhead — just a loop that checks elapsed time per task.
 *   In production: replace with OSEK/AUTOSAR OS task activation via alarms.
 */

#include "rtos/scheduler.hpp"
#include "hal/hal_timer.hpp"
#include <cstdio>

namespace rtos {

Status Scheduler::registerTask(const char* name, TaskFn func, uint32_t period_ms) {
    if (task_count_ >= MAX_TASKS) {
        std::printf("[SCHED] ERROR: task table full, cannot register '%s'\n", name);
        return Status::OVERFLOW;
    }
    tasks_[task_count_] = {
        name,
        func,
        period_ms,
        0u,   // last_run
        0u,   // overrun_count
        0u    // max_exec_us
    };
    task_count_++;
    std::printf("[SCHED] Registered task %-20s period=%ums\n", name, period_ms);
    return Status::OK;
}

void Scheduler::start() {
    TickType_t now = hal::Timer::getTick();
    for (uint8_t i = 0; i < task_count_; i++) {
        tasks_[i].last_run = now;
    }
    running_ = true;
    std::printf("[SCHED] Scheduler started — %u tasks registered\n", task_count_);
}

void Scheduler::dispatch() {
    if (!running_) return;

    TickType_t now = hal::Timer::getTick();

    for (uint8_t i = 0; i < task_count_; i++) {
        TaskDescriptor& t = tasks_[i];

        if ((now - t.last_run) >= t.period_ms) {
            // Record execution start
            TickType_t exec_start = hal::Timer::getTick();

            // Execute task
            t.func();

            // Measure execution time (µs approximation from ms ticks)
            uint32_t exec_ms = hal::Timer::getTick() - exec_start;

            // Overrun detection: task took longer than its period
            if (exec_ms > t.period_ms) {
                t.overrun_count++;
#ifdef SIMULATION_BUILD
                std::printf("[SCHED] OVERRUN: task '%s' exec=%ums period=%ums count=%u\n",
                            t.name, exec_ms, t.period_ms, t.overrun_count);
#endif
            }

            if (exec_ms > t.max_exec_us) {
                t.max_exec_us = exec_ms;
            }

            t.last_run = now;
        }
    }
}

bool Scheduler::hasOverrun() const {
    for (uint8_t i = 0; i < task_count_; i++) {
        if (tasks_[i].overrun_count > 0u) return true;
    }
    return false;
}

} // namespace rtos
