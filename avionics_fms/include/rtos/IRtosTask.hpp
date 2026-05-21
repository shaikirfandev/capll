/**
 * @file IRtosTask.hpp
 */
#pragma once
#include <cstdint>
#include <functional>
namespace fms::rtos {
using TaskFn = std::function<void()>;
enum class TaskPriority : uint8_t {
    IDLE        = 0U,
    LOW         = 1U,
    NORMAL      = 2U,
    ABOVE_NORMAL = 3U,
    HIGH        = 4U,
    REALTIME    = 5U,
    CRITICAL    = 6U,  // Navigation/Guidance tasks
};
class IRtosTask {
public:
    virtual ~IRtosTask() = default;
    virtual bool create(TaskFn fn, const char *name,
                        uint32_t stack_words, TaskPriority prio) = 0;
    virtual void start()              = 0;
    virtual void stop()               = 0;
    virtual void suspend()            = 0;
    virtual void resume()             = 0;
    virtual void delay_ms(uint32_t ms) = 0;
    virtual bool is_running() const   = 0;
};
}
