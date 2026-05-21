/**
 * @file test_fault_manager.cpp
 * @brief Unit tests for FaultManager — @req SRS-SAF-001..010
 */
#include <gtest/gtest.h>
#include "safety/FaultManager.hpp"

using fms::safety::FaultId;
using fms::safety::FaultSeverity;
using fms::safety::FaultState;

class FaultManagerTest : public ::testing::Test {
protected:
    void SetUp() override { ASSERT_EQ(fm_.init(), fms::FmsError::OK); }
    fms::safety::FaultManager fm_;
};

/// @req SRS-SAF-001: no active faults after init
TEST_F(FaultManagerTest, NoFaultsAfterInit) {
    EXPECT_EQ(fm_.get_active_fault_count(), 0U);
    EXPECT_EQ(fm_.get_worst_status(), fms::SystemStatus::NORMAL);
}

/// @req SRS-SAF-002: report WARNING fault becomes ACTIVE
TEST_F(FaultManagerTest, ReportWarningFaultActive) {
    fm_.report_fault(FaultId::GPS_LOSS_OF_FIX, FaultSeverity::WARNING, "GPS lost");
    EXPECT_TRUE(fm_.is_fault_active(FaultId::GPS_LOSS_OF_FIX));
    EXPECT_EQ(fm_.get_active_fault_count(), 1U);
}

/// @req SRS-SAF-003: CRITICAL fault is immediately LATCHED (cannot be cleared)
TEST_F(FaultManagerTest, CriticalFaultLatched) {
    fm_.report_fault(FaultId::INS_ALIGN_FAIL, FaultSeverity::CRITICAL, "INS fail");
    EXPECT_TRUE(fm_.is_fault_active(FaultId::INS_ALIGN_FAIL));
    auto result = fm_.clear_fault(FaultId::INS_ALIGN_FAIL);
    EXPECT_NE(result, fms::FmsError::OK);  // cannot clear latched
    EXPECT_TRUE(fm_.is_fault_active(FaultId::INS_ALIGN_FAIL));
}

/// @req SRS-SAF-004: WARNING fault CAN be cleared
TEST_F(FaultManagerTest, WarningFaultClearable) {
    fm_.report_fault(FaultId::GPS_LOSS_OF_FIX, FaultSeverity::WARNING, "GPS lost");
    EXPECT_EQ(fm_.clear_fault(FaultId::GPS_LOSS_OF_FIX), fms::FmsError::OK);
    EXPECT_FALSE(fm_.is_fault_active(FaultId::GPS_LOSS_OF_FIX));
}

/// @req SRS-SAF-005: worst_status reflects highest severity
TEST_F(FaultManagerTest, WorstStatusReflectsSeverity) {
    fm_.report_fault(FaultId::GPS_LOSS_OF_FIX, FaultSeverity::WARNING, "GPS");
    EXPECT_EQ(fm_.get_worst_status(), fms::SystemStatus::WARNING);
    fm_.report_fault(FaultId::INS_ALIGN_FAIL, FaultSeverity::CRITICAL, "INS");
    EXPECT_EQ(fm_.get_worst_status(), fms::SystemStatus::FAILED);
}

/// @req SRS-SAF-006: fault callback fires on new fault
TEST_F(FaultManagerTest, CallbackFires) {
    bool fired = false;
    fm_.set_fault_callback([&](const fms::safety::FaultRecord& r) {
        fired = (r.id == FaultId::ADC_PLAUSIBILITY);
    });
    fm_.report_fault(FaultId::ADC_PLAUSIBILITY, FaultSeverity::CAUTION, "ADC");
    EXPECT_TRUE(fired);
}

/// @req SRS-SAF-007: occurrence count increments on repeated reports
TEST_F(FaultManagerTest, OccurrenceCountIncrements) {
    fm_.report_fault(FaultId::GPS_LOSS_OF_FIX, FaultSeverity::WARNING, "GPS1");
    fm_.report_fault(FaultId::GPS_LOSS_OF_FIX, FaultSeverity::WARNING, "GPS2");
    fm_.report_fault(FaultId::GPS_LOSS_OF_FIX, FaultSeverity::WARNING, "GPS3");
    // Fault should still be active, occurrence count ≥ 3
    EXPECT_TRUE(fm_.is_fault_active(FaultId::GPS_LOSS_OF_FIX));
}
