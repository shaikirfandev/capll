/**
 * @file MockFaultManager.hpp
 */
#pragma once
#include "safety/IFaultManager.hpp"
#include <gmock/gmock.h>

struct MockFaultManager : fms::safety::IFaultManager {
    MOCK_METHOD(fms::FmsError, init,     (),            (noexcept, override));
    MOCK_METHOD(void,         shutdown,  (),            (noexcept, override));
    MOCK_METHOD(fms::FmsError, report_fault,
                (fms::safety::FaultId, fms::safety::FaultSeverity, const char*), (noexcept, override));
    MOCK_METHOD(fms::FmsError, clear_fault, (fms::safety::FaultId), (noexcept, override));
    MOCK_METHOD(bool,     is_fault_active,      (fms::safety::FaultId), (const, noexcept, override));
    MOCK_METHOD(uint32_t, get_active_fault_count, (), (const, noexcept, override));
    MOCK_METHOD(fms::SystemStatus, get_worst_status, (), (const, noexcept, override));
    MOCK_METHOD(void, set_fault_callback, (fms::safety::FaultCb), (noexcept, override));
};
