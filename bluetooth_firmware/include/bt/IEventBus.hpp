/**
 * @file IEventBus.hpp
 * @brief Observer pattern event bus for Bluetooth stack events
 *
 * Decouples event producers (GATT server, connection manager, OTA)
 * from event consumers (application layer, diagnostics, telemetry).
 * Uses std::variant BtEvent for type-safe dispatch.
 */

#pragma once

#include "BluetoothTypes.hpp"
#include <functional>

namespace bt {

/// Subscriber callback — receives a const reference to the variant event
using EventSubscriberCb = std::function<void(const BtEvent &event)>;

/**
 * @interface IEventBus
 * @brief Publish/Subscribe event bus for the Bluetooth stack
 *
 * All Bluetooth events flow through this bus. Subscribers register
 * with a callback and optionally filter by event type at runtime.
 *
 * Thread safety: publish() may be called from any thread; callbacks
 * are invoked in the caller's thread unless an async dispatcher is used.
 */
class IEventBus {
public:
    virtual ~IEventBus() = default;

    using SubscriberId = uint32_t;
    static constexpr SubscriberId INVALID_SUBSCRIBER = 0U;

    /**
     * @brief Subscribe to all Bluetooth events.
     * @param cb Callback to invoke on every event
     * @return Unique subscriber ID (use to unsubscribe)
     */
    virtual SubscriberId subscribe(EventSubscriberCb cb) = 0;

    /**
     * @brief Unsubscribe from events.
     * @param id Previously returned subscriber ID
     */
    virtual void unsubscribe(SubscriberId id) = 0;

    /**
     * @brief Publish a Bluetooth event to all subscribers.
     * @param event The event to publish
     */
    virtual void publish(const BtEvent &event) = 0;

    /**
     * @brief Publish asynchronously (enqueue to internal dispatcher thread).
     * Use this from ISR context or high-priority tasks to avoid blocking.
     */
    virtual void publish_async(BtEvent event) = 0;
};

}  // namespace bt
