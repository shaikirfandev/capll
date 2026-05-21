/**
 * @file test_guidance_computer.cpp
 * @brief Unit tests for GuidanceComputer — @req SRS-GNC-001..010
 */
#include <gtest/gtest.h>
#include "fms/GuidanceComputer.hpp"
#include "fms/FlightPlanManager.hpp"
#include "fms/PerformanceComputer.hpp"

// Helper to build a minimal NavState
static fms::NavState make_nav(double lat, double lon, float alt, float tas = 460.0f) {
    fms::NavState ns{};
    ns.position = {lat, lon, alt};
    ns.tas_kt = tas;
    ns.ground_speed_kt = tas;
    ns.mode = fms::NavMode::GPS_AIDED;
    ns.status = fms::SystemStatus::NORMAL;
    ns.rnp_nm = 2.0f;
    ns.anp_nm = 0.05f;
    return ns;
}

class GuidanceTest : public ::testing::Test {
protected:
    void SetUp() override {
        ASSERT_EQ(gc_.init(), fms::FmsError::OK);
        pc_.init();
        fpm_.init(nullptr);
        fpm_.set_origin("EGLL");
        fpm_.set_destination("KSFO");
        // Build minimal flight plan
        fms::Waypoint egll{}, ksfo{};
        fpm_.find_waypoint("EGLL", egll);
        fpm_.find_waypoint("KSFO", ksfo);
        fpm_.insert_waypoint(0U, egll);
        fpm_.insert_waypoint(1U, ksfo);
        fpm_.activate();
    }
    fms::GuidanceComputer  gc_;
    fms::PerformanceComputer pc_;
    fms::FlightPlanManager  fpm_;
};

/// @req SRS-GNC-001: initial modes are STANDBY/STANDBY
TEST_F(GuidanceTest, InitModesStandby) {
    EXPECT_EQ(gc_.get_fms_mode().lnav, fms::LnavMode::STANDBY);
    EXPECT_EQ(gc_.get_fms_mode().vnav, fms::VnavMode::STANDBY);
}

/// @req SRS-GNC-002: set LNAV mode changes mode
TEST_F(GuidanceTest, SetLnavMode) {
    gc_.set_lnav_mode(fms::LnavMode::LNAV);
    EXPECT_EQ(gc_.get_fms_mode().lnav, fms::LnavMode::LNAV);
}

/// @req SRS-GNC-003: LNAV roll command magnitude ≤ 25°
TEST_F(GuidanceTest, LnavRollWithinLimit) {
    gc_.set_lnav_mode(fms::LnavMode::LNAV);
    auto ns = make_nav(51.4775, 0.5, 35000.0f);  // 0.5° off track → big XTE
    const auto& pd = pc_.get_perf_data();
    for (int i = 0; i < 5; ++i)
        gc_.update(ns, fpm_.get_active_fp(), pd);
    EXPECT_LE(std::abs(gc_.get_roll_cmd_deg()), 25.5f);
}

/// @req SRS-GNC-004: VNAV descend VS command is negative when above target alt
TEST_F(GuidanceTest, VnavDescentBelowTargetAlt) {
    gc_.set_vnav_mode(fms::VnavMode::VNAV_PTH);
    auto ns = make_nav(51.4775, -0.4614, 40000.0f);  // above cruise alt
    const auto& pd = pc_.get_perf_data();
    for (int i = 0; i < 5; ++i)
        gc_.update(ns, fpm_.get_active_fp(), pd);
    EXPECT_LT(gc_.get_vs_cmd_fpm(), 0.0f);  // descend
}

/// @req SRS-GNC-005: VNAV climb VS command is positive when below target alt
TEST_F(GuidanceTest, VnavClimbAboveTargetAlt) {
    gc_.set_vnav_mode(fms::VnavMode::VNAV_PTH);
    auto ns = make_nav(51.4775, -0.4614, 10000.0f);  // below cruise alt
    const auto& pd = pc_.get_perf_data();
    for (int i = 0; i < 5; ++i)
        gc_.update(ns, fpm_.get_active_fp(), pd);
    EXPECT_GT(gc_.get_vs_cmd_fpm(), 0.0f);  // climb
}

/// @req SRS-GNC-006: missed approach → HDG_SEL
TEST_F(GuidanceTest, MissedApproachEngagesHdgSel) {
    gc_.set_lnav_mode(fms::LnavMode::APPROACH);
    gc_.execute_missed_approach();
    EXPECT_EQ(gc_.get_fms_mode().lnav, fms::LnavMode::HDG_SEL);
}

/// @req SRS-GNC-007: STANDBY guidance outputs zero commands
TEST_F(GuidanceTest, StandbyOutputsZero) {
    // modes remain STANDBY
    auto ns = make_nav(51.4775, -0.4614, 35000.0f);
    const auto& pd = pc_.get_perf_data();
    gc_.update(ns, fpm_.get_active_fp(), pd);
    EXPECT_NEAR(gc_.get_roll_cmd_deg(), 0.0f, 0.1f);
}
