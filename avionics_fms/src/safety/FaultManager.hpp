/**
 * @file FaultManager.hpp
 */
#pragma once
#include "safety/IFaultManager.hpp"
#include "safety/SafetyTypes.hpp"
#include <array>
#include <mutex>

namespace fms::safety {

static constexpr std::size_t FAULT_TABLE_SIZE = 64U;

class FaultManager : public IFaultManager {
public:
    fms::FmsError init() noexcept override;
    void          shutdown() noexcept override;
    fms::FmsError report_fault(FaultId id, FaultSeverity sev, const char* desc) noexcept override;
    fms::FmsError clear_fault(FaultId id) noexcept override;
    [[nodiscard]] bool              is_fault_active(FaultId id) const noexcept override;
    [[nodiscard]] uint32_t          get_active_fault_count() const noexcept override;
    [[nodiscard]] fms::SystemStatus get_worst_status() const noexcept override;
    void set_fault_callback(FaultCallback cb) noexcept override;

private:
    std::array<FaultRecord, FAULT_TABLE_SIZE> table_{};
    uint32_t count_{0};
    FaultCallback  callback_;
    mutable std::mutex mtx_;

    FaultRecord* find_record(FaultId id) noexcept;
    const FaultRecord* find_record(FaultId id) const noexcept;
};

}  // namespace fms::safety
