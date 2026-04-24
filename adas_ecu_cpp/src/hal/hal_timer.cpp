/**
 * @file    hal_timer.cpp
 * @brief   HAL Timer implementation — simulation variant (std::chrono).
 *          On embedded target this would instead configure SysTick registers.
 */

#include "hal/hal_timer.hpp"

#ifdef SIMULATION_BUILD
#include <chrono>
#include <thread>

static std::chrono::steady_clock::time_point g_start;

void hal::Timer::init() {
    g_start = std::chrono::steady_clock::now();
}

TickType_t hal::Timer::getTick() {
    auto now     = std::chrono::steady_clock::now();
    auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(now - g_start);
    return static_cast<TickType_t>(elapsed.count());
}

void hal::Timer::delayMs(uint32_t ms) {
    std::this_thread::sleep_for(std::chrono::milliseconds(ms));
}

#else
// ── Bare-metal Cortex-M4 SysTick ─────────────────────────────────────────────
// SysTick is configured for 1ms interrupt at startup.
// g_tick is incremented in SysTick_Handler (defined in startup.s or here).

static volatile uint32_t g_tick = 0u;

extern "C" void SysTick_Handler() {
    g_tick++;
}

void hal::Timer::init() {
    // SysTick configuration (CMSIS)
    // SysTick_Config(SystemCoreClock / 1000);  // 1ms tick
}

TickType_t hal::Timer::getTick() {
    return g_tick;
}

void hal::Timer::delayMs(uint32_t ms) {
    TickType_t start = getTick();
    while ((getTick() - start) < ms) { /* busy wait */ }
}

#endif // SIMULATION_BUILD
