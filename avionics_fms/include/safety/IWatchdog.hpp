/**
 * @file IWatchdog.hpp
 * @brief Hardware watchdog interface — DO-178C DAL-A
 * @req SRS-SAFE-003
 */
#pragma once
#include "fms/FmsTypes.hpp"

namespace fms::safety {

class IWatchdog {
public:
    virtual ~IWatchdog() = default;
    virtual FmsError init(uint32_t timeout_ms) noexcept = 0;
    virtual void     shutdown() noexcept = 0;
    virtual void     kick() noexcept = 0;
    [[nodiscard]] virtual bool is_expired() const noexcept = 0;
    [[nodiscard]] virtual uint32_t timeout_ms() const noexcept = 0;
    [[nodiscard]] virtual SystemStatus get_status() const noexcept = 0;
};

}  // namespace fms::safety
