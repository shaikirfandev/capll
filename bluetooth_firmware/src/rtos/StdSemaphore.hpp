/**
 * @file StdSemaphore.hpp
 */
#pragma once
#include "rtos/IRtosSemaphore.hpp"
#include <memory>
namespace bt::rtos {
class StdSemaphore final : public IRtosSemaphore {
public:
    explicit StdSemaphore(uint32_t initial_count = 0U);
    ~StdSemaphore() override;
    void     give()                    override;
    bool     take(uint32_t timeout_ms) override;
    uint32_t count() const             override;
private:
    struct Impl; std::unique_ptr<Impl> impl_;
};
}
