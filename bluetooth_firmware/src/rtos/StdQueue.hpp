/**
 * @file StdQueue.hpp
 */
#pragma once
#include "rtos/IRtosQueue.hpp"
#include <memory>
namespace bt::rtos {
class StdQueueBase final : public IRtosQueueBase {
public:
    explicit StdQueueBase(uint32_t item_size);
    ~StdQueueBase() override;
    bool     send_raw(const void *item, uint32_t timeout_ms)    override;
    bool     receive_raw(void *item, uint32_t timeout_ms)       override;
    uint32_t size() const                                       override;
    bool     empty() const                                      override;

    template<typename T>
    bool send(const T &item, uint32_t timeout_ms = 1000U) {
        return send_raw(&item, timeout_ms);
    }
    template<typename T>
    bool receive(T &item, uint32_t timeout_ms = 1000U) {
        return receive_raw(&item, timeout_ms);
    }
private:
    struct Impl; std::unique_ptr<Impl> impl_;
};
}
