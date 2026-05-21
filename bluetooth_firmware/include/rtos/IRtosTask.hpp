/**
 * @file IRtosTask.hpp
 * @brief RTOS task abstraction interface
 */
#pragma once
#include <cstdint>
#include <functional>
namespace bt::rtos {
using TaskFn = std::function<void()>;
enum class TaskPriority : uint8_t { IDLE=0, LOW=1, NORMAL=2, HIGH=3, REALTIME=4 };
class IRtosTask {
public:
    virtual ~IRtosTask() = default;
    virtual bool create(TaskFn fn, const char *name, uint32_t stack_words, TaskPriority prio) = 0;
    virtual void start() = 0;
    virtual void stop() = 0;
    virtual void delay_ms(uint32_t ms) = 0;
    virtual bool is_running() const = 0;
};
}
