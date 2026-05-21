/**
 * @file EventBus.cpp
 * @brief Thread-safe Observer event bus with async dispatch
 *
 * Automotive grade: supports high-frequency GATT notification events
 * from BLE sensor nodes (100Hz heart rate, 10Hz vehicle telemetry)
 * without blocking the BT stack thread.
 */

#include "bt/EventBus.hpp"
#include "common/Logger.hpp"
#include <algorithm>
#include <atomic>
#include <condition_variable>
#include <map>
#include <mutex>
#include <queue>
#include <stdexcept>
#include <thread>

static constexpr const char *TAG = "EventBus";

namespace bt {

struct EventBus::Impl {
    // Subscriber registry
    std::map<SubscriberId, EventSubscriberCb> subscribers;
    mutable std::shared_mutex                 sub_mtx;
    std::atomic<SubscriberId>                 next_id{1U};

    // Async dispatch queue
    std::queue<BtEvent>    async_queue;
    std::mutex             q_mtx;
    std::condition_variable q_cv;
    std::thread            dispatch_thread;
    std::atomic<bool>      running{false};

    void dispatch_worker() {
        while (running.load(std::memory_order_acquire)) {
            std::unique_lock<std::mutex> lock(q_mtx);
            q_cv.wait(lock, [this] {
                return !async_queue.empty() || !running.load();
            });
            while (!async_queue.empty()) {
                BtEvent ev = std::move(async_queue.front());
                async_queue.pop();
                lock.unlock();
                // Deliver to all subscribers
                std::shared_lock<std::shared_mutex> sub_lock(sub_mtx);
                for (const auto &[id, cb] : subscribers) {
                    try {
                        cb(ev);
                    } catch (const std::exception &ex) {
                        BT_LOG_ERROR(TAG, "Subscriber {} threw: {}", id, ex.what());
                    }
                }
                lock.lock();
            }
        }
    }
};

EventBus::EventBus() : impl_(std::make_unique<Impl>()) {
    impl_->running.store(true);
    impl_->dispatch_thread = std::thread(&Impl::dispatch_worker, impl_.get());
    BT_LOG_DEBUG(TAG, "EventBus initialised");
}

EventBus::~EventBus() {
    impl_->running.store(false);
    impl_->q_cv.notify_all();
    if (impl_->dispatch_thread.joinable()) {
        impl_->dispatch_thread.join();
    }
}

IEventBus::SubscriberId EventBus::subscribe(EventSubscriberCb cb) {
    if (!cb) {
        BT_LOG_WARN(TAG, "subscribe() called with null callback");
        return INVALID_SUBSCRIBER;
    }
    const SubscriberId id = impl_->next_id.fetch_add(1U, std::memory_order_relaxed);
    std::unique_lock<std::shared_mutex> lock(impl_->sub_mtx);
    impl_->subscribers.emplace(id, std::move(cb));
    BT_LOG_DEBUG(TAG, "New subscriber id={}, total={}", id, impl_->subscribers.size());
    return id;
}

void EventBus::unsubscribe(SubscriberId id) {
    std::unique_lock<std::shared_mutex> lock(impl_->sub_mtx);
    const auto erased = impl_->subscribers.erase(id);
    if (erased == 0U) {
        BT_LOG_WARN(TAG, "unsubscribe: id={} not found", id);
    } else {
        BT_LOG_DEBUG(TAG, "Unsubscribed id={}", id);
    }
}

void EventBus::publish(const BtEvent &event) {
    // Synchronous delivery — called in caller's thread context
    std::shared_lock<std::shared_mutex> lock(impl_->sub_mtx);
    for (const auto &[id, cb] : impl_->subscribers) {
        try {
            cb(event);
        } catch (const std::exception &ex) {
            BT_LOG_ERROR(TAG, "publish: Subscriber {} threw: {}", id, ex.what());
        }
    }
}

void EventBus::publish_async(BtEvent event) {
    // Non-blocking — enqueue and return immediately
    {
        std::lock_guard<std::mutex> lock(impl_->q_mtx);
        impl_->async_queue.push(std::move(event));
    }
    impl_->q_cv.notify_one();
}

}  // namespace bt
