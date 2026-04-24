/**
 * @file    scheduler.hpp
 * @brief   Cooperative cyclic executive (Rate-Monotonic) task scheduler.
 *
 * This is the most common RTOS pattern in automotive ECU software:
 *   - Fixed task table with predefined periods (no dynamic task creation)
 *   - Cyclic execution driven by SysTick 1ms interrupt
 *   - Tasks are simple function pointers — no context switching (bare-metal safe)
 *   - Overrun detection: records if a task exceeds its deadline
 *
 *  Execution cycles:
 *    1ms  → SysTick ISR increments tick counter
 *    10ms → Task_FastCycle (sensor reading, CAN decode)
 *    20ms → Task_ControlCycle (ACC, LKA, BSD compute)
 *    50ms → Task_MediumCycle (parking, HHA)
 *   100ms → Task_SlowCycle (diagnostics, DTC check, LDW HMI)
 *  1000ms → Task_BackgroundCycle (ECU health, NVM write)
 */

#pragma once
#include "hal/hal_types.hpp"

namespace rtos {

// ── Task descriptor ───────────────────────────────────────────────────────────

using TaskFn = void(*)();     ///< Task function pointer type

struct TaskDescriptor {
    const char*     name;
    TaskFn          func;
    uint32_t        period_ms;    ///< Execution period
    TickType_t      last_run;
    uint32_t        overrun_count;
    uint32_t        max_exec_us;  ///< Worst-case execution time recorded
};

// ── Scheduler ─────────────────────────────────────────────────────────────────

/**
 * @class Scheduler
 * @brief Fixed-table cyclic executive scheduler.
 *
 * Usage:
 *   Scheduler& sched = Scheduler::instance();
 *   sched.registerTask("FastCycle", task_fast, 10);
 *   sched.start();
 *   while (true) { sched.dispatch(); }
 */
class Scheduler {
public:
    static constexpr uint8_t MAX_TASKS = 16u;

    static Scheduler& instance() {
        static Scheduler inst;
        return inst;
    }

    /**
     * @brief Register a task with a fixed period.
     * @param name       Debug name (stored in ROM on embedded)
     * @param func       Task function pointer
     * @param period_ms  Execution period (must be a multiple of 1ms)
     * @return Status::OK | Status::OVERFLOW if table full
     */
    Status registerTask(const char* name, TaskFn func, uint32_t period_ms);

    /**
     * @brief Start the scheduler. Call once after all tasks registered.
     *        On embedded: enables SysTick. On simulation: sets start time.
     */
    void start();

    /**
     * @brief Main dispatch loop — call from while(true) in main().
     *        Checks each registered task and executes if its period has elapsed.
     */
    void dispatch();

    /** Returns number of registered tasks */
    uint8_t taskCount() const { return task_count_; }

    /** Returns task stats for monitoring / DTC purposes */
    const TaskDescriptor& getTask(uint8_t idx) const { return tasks_[idx]; }

    /** Returns true if any task overrun was recorded */
    bool hasOverrun() const;

private:
    Scheduler() = default;
    Scheduler(const Scheduler&) = delete;

    TaskDescriptor  tasks_[MAX_TASKS];
    uint8_t         task_count_ = 0;
    bool            running_    = false;
};

} // namespace rtos
