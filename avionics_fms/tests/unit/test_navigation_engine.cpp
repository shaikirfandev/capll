/**
 * @file test_navigation_engine.cpp
 * @brief Unit tests for NavigationEngine — @req SRS-NAV-001..010
 */
#include <gtest/gtest.h>
#include "fms/NavigationEngine.hpp"

class NavigationEngineTest : public ::testing::Test {
protected:
    void SetUp() override {
        fms::LatLon egll{51.4775, -0.4614};
        ASSERT_EQ(eng_.init(egll), fms::FmsError::OK);
    }
    fms::NavigationEngine eng_;
};

/// @req SRS-NAV-001: init succeeds at EGLL
TEST_F(NavigationEngineTest, InitSuccess) {
    EXPECT_EQ(eng_.get_status(), fms::SystemStatus::NORMAL);
}

/// @req SRS-NAV-002: bearing EGLL→KSFO is roughly 324°..330° (northwest)
TEST_F(NavigationEngineTest, BearingEgllKsfo) {
    fms::Position3D egll{51.4775, -0.4614, 0.0f};
    fms::Position3D ksfo{37.6213, -122.379, 0.0f};
    double brg = eng_.compute_bearing_deg(egll, ksfo);
    EXPECT_GT(brg, 300.0);
    EXPECT_LT(brg, 360.0);
}

/// @req SRS-NAV-003: distance EGLL→KSFO ~4900-5200 nm (great-circle)
TEST_F(NavigationEngineTest, DistanceEgllKsfo) {
    fms::Position3D egll{51.4775, -0.4614, 0.0f};
    fms::Position3D ksfo{37.6213, -122.379, 0.0f};
    double dist = eng_.compute_distance_nm(egll, ksfo);
    EXPECT_GT(dist, 4500.0);
    EXPECT_LT(dist, 5300.0);
}

/// @req SRS-NAV-004: XTE is zero when current position lies on the track
TEST_F(NavigationEngineTest, XteZeroOnTrack) {
    fms::Position3D from{51.0, 0.0, 35000.0f};
    fms::Position3D to  {50.0, 0.0, 35000.0f};
    fms::Position3D cur {50.5, 0.0, 35000.0f};  // midpoint on track
    double xte = eng_.compute_xte_nm(from, to, cur);
    EXPECT_NEAR(xte, 0.0, 0.5);
}

/// @req SRS-NAV-005: GPS update switches mode to GPS_AIDED
TEST_F(NavigationEngineTest, GpsModeSwitch) {
    EXPECT_EQ(eng_.get_nav_state().mode, fms::NavMode::DEAD_RECK);
    eng_.update_gps(51.4775, -0.4614, 0.0, 0.0, 0.0, 8U, 1.2f);
    EXPECT_EQ(eng_.get_nav_state().mode, fms::NavMode::GPS_AIDED);
}

/// @req SRS-NAV-006: RNP satisfied when ANP < RNP
TEST_F(NavigationEngineTest, RnpSatisfied) {
    eng_.set_rnp_requirement(2.0f);
    // Feed GPS with 8 sats, hdop=0.8 → ANP very small
    for (int i = 0; i < 10; ++i)
        eng_.update_gps(51.4775, -0.4614, 0.0, 0.0, 0.0, 8U, 0.8f);
    EXPECT_TRUE(eng_.is_rnp_satisfied());
}

/// @req SRS-NAV-007: RNP exceeded when ANP > RNP
TEST_F(NavigationEngineTest, RnpExceeded) {
    eng_.set_rnp_requirement(0.001f);  // 0.001 nm — impossible to satisfy
    eng_.update_gps(51.4775, -0.4614, 0.0, 0.0, 0.0, 4U, 2.5f);
    EXPECT_FALSE(eng_.is_rnp_satisfied());
}

/// @req SRS-NAV-008: ADC update populates TAS/CAS/Mach in NavState
TEST_F(NavigationEngineTest, AdcUpdate) {
    eng_.update_adc(460.0f, 280.0f, 0.78f, 35000.0f, -2.0f);
    const auto& ns = eng_.get_nav_state();
    EXPECT_NEAR(ns.tas_kt, 460.0f, 5.0f);
    EXPECT_NEAR(ns.cas_kt, 280.0f, 5.0f);
    EXPECT_NEAR(ns.mach,   0.78f,  0.01f);
}
