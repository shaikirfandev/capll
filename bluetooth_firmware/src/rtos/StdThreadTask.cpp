/**
 * @file StdThreadTask.cpp  StdMutex.cpp  StdQueue.cpp  StdSemaphore.cpp
 * @brief RTOS abstraction using C++17 standard library primitives
 */

// ── StdThreadTask ─────────────────────────────────────────────────────────────
#include "rtos/StdThreadTask.hpp"
#include "common/Logger.hpp"
#include <thread>
#include <chrono>

namespace bt::rtos {

struct StdThreadTask::Impl {
    std::thread       thread;
    std::atomic<bool> running{false};
    TaskFn            fn;
    std::string       name;
};

StdThreadTask::StdThreadTask()  : impl_(std::make_unique<Impl>()) {}
StdThreadTask::~StdThreadTask() { stop(); }

bool StdThreadTask::create(TaskFn fn, const char *name, uint32_t /*stack*/, TaskPriority /*prio*/) {
    impl_->fn   = std::move(fn);
    impl_->name = name ? name : "unnamed";
    return true;
}

void StdThreadTask::start() {
    if (impl_->running.load()) { return; }
    impl_->running.store(true);
    impl_->thread = std::thread([this]() {
        BT_LOG_DEBUG("StdTask", "Task '{}' started", impl_->name);
        if (impl_->fn) { impl_->fn(); }
        impl_->running.store(false);
    });
}

void StdThreadTask::stop() {
    impl_->running.store(false);
    if (impl_->thread.joinable()) { impl_->thread.join(); }
}

void StdThreadTask::delay_ms(uint32_t ms) {
    std::this_thread::sleep_for(std::chrono::milliseconds(ms));
}

bool StdThreadTask::is_running() const { return impl_->running.load(); }

}  // namespace bt::rtos
