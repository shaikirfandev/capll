/**
 * @file test_navigation_integration.cpp
 * @brief Navigation sensor fusion integration — @req SRS-INT-010..015
 */
#include <gtest/gtest.h>
#include "sensors/GpsReceiver.hpp"
#include "sensors/InertialNavSystem.hpp"
#include "sensors/SensorFusion.hpp"
#include "fms/NavigationEngine.hpp"

class NavIntegrationTest : public ::testing::Test {
protected:
    void SetUp() override {
        fms::LatLon egll{51.4775, -0.4614};
        fms::Position3D egll_pos{51.4775, -0.4614, 0.0};
        ASSERT_EQ(gps_.init(), fms::FmsError::OK);
        ASSERT_EQ(ins_.init(egll_pos), fms::FmsError::OK);
        ASSERT_EQ(fusion_.init(), fms::FmsError::OK);
        ASSERT_EQ(nav_.init(egll), fms::FmsError::OK);
        nav_.set_rnp_requirement(2.0f);
    }
    fms::sensors::GpsReceiver       gps_;
    fms::sensors::InertialNavSystem ins_;
    fms::sensors::SensorFusion      fusion_;
    fms::NavigationEngine           nav_;
};

/// @req SRS-INT-010: NavMode transitions to GPS_AIDED after GPS updates
TEST_F(NavIntegrationTest, NavModeGpsAided) {
    EXPECT_EQ(nav_.get_nav_state().mode, fms::NavMode::DEAD_RECK);
    for (int i = 0; i < 20; ++i) {
        gps_.update();
        const auto& g = gps_.get_data();
        if (g.valid)
            nav_.update_gps(g.lat_deg, g.lon_deg, g.alt_wgs84_m,
                             g.vel_north_ms, g.vel_east_ms, g.num_satellites, g.hdop);
    }
    EXPECT_EQ(nav_.get_nav_state().mode, fms::NavMode::GPS_AIDED);
}

/// @req SRS-INT-011: ANP < 0.1 nm after 20 GPS updates with good signal
TEST_F(NavIntegrationTest, AnpConvergesAfterGpsUpdates) {
    for (int i = 0; i < 20; ++i) {
        gps_.update();
        const auto& g = gps_.get_data();
        if (g.valid)
            nav_.update_gps(g.lat_deg, g.lon_deg, g.alt_wgs84_m,
                             g.vel_north_ms, g.vel_east_ms, g.num_satellites, g.hdop);
    }
    EXPECT_LT(nav_.get_nav_state().anp_nm, 0.1f);
}

/// @req SRS-INT-012: RNP satisfied after 20 GPS updates (RNP=2.0 nm)
TEST_F(NavIntegrationTest, RnpSatisfiedAfterConvergence) {
    for (int i = 0; i < 20; ++i) {
        gps_.update();
        const auto& g = gps_.get_data();
        if (g.valid)
            nav_.update_gps(g.lat_deg, g.lon_deg, g.alt_wgs84_m,
                             g.vel_north_ms, g.vel_east_ms, g.num_satellites, g.hdop);
    }
    EXPECT_TRUE(nav_.is_rnp_satisfied());
}

/// @req SRS-INT-013: SensorFusion fuses GPS + INS, returns valid position
TEST_F(NavIntegrationTest, SensorFusionProducesValidPosition) {
    for (int i = 0; i < 10; ++i) {
        gps_.update(); ins_.update();
        const auto& g = gps_.get_data();
        const auto& in = ins_.get_data();
        fms::sensors::AdcRaw adc{};
        adc.valid = false;
        fusion_.update(g, in, adc);
    }
    const auto& fused = fusion_.get_state();
    EXPECT_GT(std::abs(fused.lat_deg), 0.0);
    EXPECT_GT(std::abs(fused.lon_deg), 0.0);
}
