/**
 * @file StdThreadTask.hpp
 */
#pragma once
#include "rtos/IRtosTask.hpp"
#include <memory>
namespace bt::rtos {
class StdThreadTask final : public IRtosTask {
public:
    StdThreadTask(); ~StdThreadTask() override;
    bool create(TaskFn fn, const char *name, uint32_t stack_words, TaskPriority prio) override;
    void start()                   override;
    void stop()                    override;
    void delay_ms(uint32_t ms)     override;
    bool is_running() const        override;
private:
    struct Impl; std::unique_ptr<Impl> impl_;
};
}
