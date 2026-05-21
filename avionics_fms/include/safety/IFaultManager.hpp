/**
 * @file IFaultManager.hpp
 * @brief Fault Detection, Isolation and Recovery (FDIR) interface
 */
#pragma once
#include "safety/SafetyTypes.hpp"
#include "fms/FmsTypes.hpp"
#include <functional>

namespace fms::safety {

using FaultCallback = std::function<void(const FaultRecord &)>;

class IFaultManager {
public:
    virtual ~IFaultManager() = default;

    virtual fms::FmsError init()     = 0;
    virtual void          shutdown() = 0;

    /** Report a fault — thread-safe, called from any task */
    virtual fms::FmsError report_fault(FaultId id, FaultSeverity severity,
                                        const char *description) = 0;
    virtual fms::FmsError clear_fault(FaultId id) = 0;

    /** Query */
    virtual bool     is_fault_active(FaultId id) const = 0;
    virtual uint32_t get_active_fault_count() const = 0;

    /** Callback for new fault events */
    virtual void set_fault_callback(FaultCallback cb) = 0;

    virtual fms::SystemStatus get_worst_status() const = 0;
};

}  // namespace fms::safety
