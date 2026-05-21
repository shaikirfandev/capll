/**
 * @file FreeRtosTask.hpp
 */
#pragma once
#include "rtos/IRtosTask.hpp"
#include <thread>
#include <atomic>
#include <string>

namespace fms::rtos {

class FreeRtosTask : public IRtosTask {
public:
    FreeRtosTask() = default;
    ~FreeRtosTask() override { stop(); }

    bool create(TaskFn fn, const char* name,
               uint32_t stack_words, TaskPriority prio) override;
    void start()   override;
    void stop()    override;
    void     suspend() override;
    void     resume()  override;
    void     delay_ms(uint32_t ms) override;
    [[nodiscard]] bool is_running() const override { return running_.load(); }

private:
    std::string name_;
    TaskFn fn_;
    std::thread thread_;
    std::atomic<bool> running_{false};
    std::atomic<bool> suspended_{false};
};

}  // namespace fms::rtos
