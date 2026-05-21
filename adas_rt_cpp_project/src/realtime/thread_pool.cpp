/**
 * @file thread_pool.cpp
 * @brief Work-stealing thread pool implementation.
 */

#include "thread_pool.hpp"

#include <stdexcept>

namespace adas {
namespace realtime {

ThreadPool::ThreadPool(unsigned int num_threads) {
    if (num_threads == 0) {
        num_threads = std::max(1u, std::thread::hardware_concurrency());
    }

    workers_.resize(num_threads);
    threads_.reserve(num_threads);

    for (unsigned int i = 0; i < num_threads; ++i) {
        threads_.emplace_back([this, i] { workerLoop(i); });
    }
}

ThreadPool::~ThreadPool() {
    stop_.store(true);
    cv_.notify_all();
    for (auto& t : threads_) {
        if (t.joinable()) t.join();
    }
}

void ThreadPool::workerLoop(unsigned int id) {
    while (true) {
        std::function<void()> task;

        // ① Try to pop from own queue
        {
            std::lock_guard<std::mutex> lock(workers_[id].mutex);
            if (!workers_[id].queue.empty()) {
                task = std::move(workers_[id].queue.front());
                workers_[id].queue.pop_front();
            }
        }

        // ② If own queue is empty, try stealing from siblings
        if (!task && !trySteal(task, id)) {
            // ③ Nothing to steal: wait for notification
            std::unique_lock<std::mutex> lock(cv_mutex_);
            cv_.wait(lock, [this, id] {
                if (stop_.load()) return true;
                // Wake if own queue has work or any sibling has work
                for (auto& w : workers_) {
                    std::lock_guard<std::mutex> wlock(w.mutex);
                    if (!w.queue.empty()) return true;
                }
                return false;
            });
            if (stop_.load()) break;
            continue;
        }

        if (task) {
            ++active_tasks_;
            task();
            --active_tasks_;
        }
    }
}

bool ThreadPool::trySteal(std::function<void()>& task, unsigned int thief_id) {
    const unsigned int n = static_cast<unsigned int>(workers_.size());
    for (unsigned int offset = 1; offset < n; ++offset) {
        unsigned int victim = (thief_id + offset) % n;
        std::lock_guard<std::mutex> lock(workers_[victim].mutex);
        if (!workers_[victim].queue.empty()) {
            // Steal from the back (workers pop from front → back is older)
            task = std::move(workers_[victim].queue.back());
            workers_[victim].queue.pop_back();
            return true;
        }
    }
    return false;
}

void ThreadPool::wait() {
    // Poll until all queues are empty and no tasks are active
    while (active_tasks_.load() > 0 || pendingTasks() > 0) {
        std::this_thread::yield();
    }
}

std::size_t ThreadPool::pendingTasks() const {
    std::size_t total = 0;
    for (const auto& w : workers_) {
        std::lock_guard<std::mutex> lock(w.mutex);
        total += w.queue.size();
    }
    return total;
}

}  // namespace realtime
}  // namespace adas
