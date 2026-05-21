/**
 * @file FreeRtosTask.cpp
 */
#include "FreeRtosTask.hpp"
#include <chrono>
#include <thread>

namespace fms::rtos {

bool FreeRtosTask::create(TaskFn fn, const char* name,
                           uint32_t, TaskPriority) {
    name_ = name;
    fn_   = fn;
    return true;
}

void FreeRtosTask::start() {
    if (!fn_) return;
    running_.store(true);
    thread_ = std::thread([this] {
        while (running_.load()) {
            if (!suspended_.load()) fn_();
        }
    });
}

void FreeRtosTask::stop() {
    running_.store(false);
    if (thread_.joinable()) thread_.join();
}

void FreeRtosTask::suspend() { suspended_.store(true); }
void FreeRtosTask::resume()  { suspended_.store(false); }

void FreeRtosTask::delay_ms(uint32_t ms) {
    std::this_thread::sleep_for(std::chrono::milliseconds(ms));
}

}  // namespace fms::rtos
