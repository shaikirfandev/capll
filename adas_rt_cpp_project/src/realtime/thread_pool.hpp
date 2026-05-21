#pragma once
/**
 * @file thread_pool.hpp
 * @brief Work-stealing thread pool for parallelising non-RT background tasks.
 *
 * DESIGN
 * ──────
 * • N worker threads, each with a local task deque (double-ended queue).
 * • Producers push to the local deque of a chosen worker (round-robin or
 *   caller-chosen).
 * • Workers steal from the back of sibling deques when their own is empty
 *   (Chase-Lev work-stealing algorithm, simplified).
 * • Uses std::packaged_task<void()> for type-erasure; submit() returns a
 *   std::future so callers can wait for results.
 *
 * NOT FOR RT THREADS
 * ──────────────────
 * This pool uses SCHED_OTHER (default Linux scheduling), making it
 * unsuitable for the RT pipeline. Use it for background tasks like:
 *   • Log flushing
 *   • Debug data recording
 *   • Offline map updates
 */

#include <atomic>
#include <condition_variable>
#include <deque>
#include <functional>
#include <future>
#include <mutex>
#include <thread>
#include <vector>

namespace adas {
namespace realtime {

class ThreadPool {
public:
    /**
     * @param num_threads  Number of worker threads (0 = hardware_concurrency)
     */
    explicit ThreadPool(unsigned int num_threads = 0);
    ~ThreadPool();

    ThreadPool(const ThreadPool&)            = delete;
    ThreadPool& operator=(const ThreadPool&) = delete;

    /**
     * @brief Submit a callable and return a future to its result.
     *
     * @code
     *   auto fut = pool.submit([&]{ return compute_something(); });
     *   int result = fut.get();  // blocks until done
     * @endcode
     */
    template<typename Func, typename... Args>
    auto submit(Func&& func, Args&&... args)
        -> std::future<std::invoke_result_t<Func, Args...>>
    {
        using ReturnType = std::invoke_result_t<Func, Args...>;
        auto task = std::make_shared<std::packaged_task<ReturnType()>>(
            std::bind(std::forward<Func>(func), std::forward<Args>(args)...));
        std::future<ReturnType> fut = task->get_future();

        {
            // Push to the queue of the next worker in round-robin fashion
            const unsigned int idx = next_worker_.fetch_add(1) % workers_.size();
            std::lock_guard<std::mutex> lock(workers_[idx].mutex);
            workers_[idx].queue.emplace_back([task]{ (*task)(); });
        }
        cv_.notify_one();
        return fut;
    }

    /// Wait for all queued tasks to complete (drains the pool)
    void wait();

    std::size_t numThreads() const { return workers_.size(); }

    /// Approximate number of pending tasks across all queues
    std::size_t pendingTasks() const;

private:
    struct Worker {
        std::deque<std::function<void()>> queue;
        mutable std::mutex                mutex;
    };

    void workerLoop(unsigned int id);
    bool trySteal(std::function<void()>& task, unsigned int thief_id);

    std::vector<Worker>      workers_;
    std::vector<std::thread> threads_;
    std::condition_variable  cv_;
    std::mutex               cv_mutex_;
    std::atomic<bool>        stop_{false};
    std::atomic<unsigned int> next_worker_{0};
    std::atomic<int>         active_tasks_{0};
};

}  // namespace realtime
}  // namespace adas
