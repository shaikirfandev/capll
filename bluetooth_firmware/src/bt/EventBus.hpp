/**
 * @file EventBus.hpp
 * @brief Concrete EventBus implementation header
 */
#pragma once
#include "bt/IEventBus.hpp"
#include <memory>
#include <shared_mutex>

namespace bt {

class EventBus final : public IEventBus {
public:
    EventBus();
    ~EventBus() override;

    SubscriberId subscribe(EventSubscriberCb cb) override;
    void         unsubscribe(SubscriberId id)    override;
    void         publish(const BtEvent &event)   override;
    void         publish_async(BtEvent event)    override;

private:
    struct Impl;
    std::unique_ptr<Impl> impl_;
};

}  // namespace bt
