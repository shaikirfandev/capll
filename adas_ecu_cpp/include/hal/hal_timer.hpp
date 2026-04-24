/**
 * @file    hal_timer.hpp
 * @brief   Hardware timer abstraction — systick / free-running counter.
 *
 * On embedded (Cortex-M4): wraps SysTick peripheral (1ms resolution).
 * On simulation: wraps std::chrono steady_clock.
 */

#pragma once
#include "hal_types.hpp"

namespace hal {

/**
 * @class Timer
 * @brief Monotonic millisecond timer.
 *        Never wraps within normal operation (49-day rollover).
 */
class Timer {
public:
    /** Initialise SysTick or simulation clock. Called once in main(). */
    static void     init();

    /** Return current tick count in milliseconds (monotonic). */
    static TickType_t   getTick();

    /** Busy-wait delay in milliseconds. Use only in init paths. */
    static void     delayMs(uint32_t ms);

    /** Return elapsed ms since a recorded start tick. */
    static uint32_t elapsed(TickType_t start_tick) {
        return getTick() - start_tick;
    }

    /** Check if ms have elapsed since start_tick (non-blocking). */
    static bool     hasElapsed(TickType_t start_tick, uint32_t ms) {
        return elapsed(start_tick) >= ms;
    }
};

/**
 * @class SoftwareTimer
 * @brief Lightweight periodic or one-shot software timer.
 *
 * Usage:
 *   SoftwareTimer t(20);   // 20ms periodic
 *   if (t.hasExpired()) { t.reload(); doWork(); }
 */
class SoftwareTimer {
public:
    explicit SoftwareTimer(uint32_t period_ms, bool auto_reload = true)
        : period_ms_(period_ms)
        , auto_reload_(auto_reload)
        , start_(0)
        , running_(false)
    {}

    void start()  { start_ = Timer::getTick(); running_ = true; }
    void stop()   { running_ = false; }
    void reload() { start_ = Timer::getTick(); }

    bool hasExpired() {
        if (!running_) return false;
        if (Timer::hasElapsed(start_, period_ms_)) {
            if (auto_reload_) reload();
            return true;
        }
        return false;
    }

    bool isRunning() const { return running_; }

private:
    uint32_t    period_ms_;
    bool        auto_reload_;
    TickType_t  start_;
    bool        running_;
};

} // namespace hal
