/**
 * @file test_fms_integration.cpp
 * @brief Full FMS integration — EGLL→KSFO scenario @req SRS-INT-001..005
 */
#include <gtest/gtest.h>
#include "fms/FlightPlanManager.hpp"
#include "fms/NavigationEngine.hpp"
#include "fms/GuidanceComputer.hpp"
#include "fms/FuelManagement.hpp"
#include "fms/PerformanceComputer.hpp"
#include "safety/FaultManager.hpp"
#include "sensors/AirDataSystem.hpp"
#include "sensors/GpsReceiver.hpp"
#include "sensors/InertialNavSystem.hpp"

class FmsIntegrationTest : public ::testing::Test {
protected:
    void SetUp() override {
        fms::LatLon egll{51.4775, -0.4614};
        fms::Position3D egll_pos{51.4775, -0.4614, 0.0};
        ASSERT_EQ(adc_.init(), fms::FmsError::OK);
        ASSERT_EQ(gps_.init(), fms::FmsError::OK);
        ASSERT_EQ(ins_.init(egll_pos), fms::FmsError::OK);
        ASSERT_EQ(nav_.init(egll), fms::FmsError::OK);
        ASSERT_EQ(gc_.init(), fms::FmsError::OK);
        ASSERT_EQ(fpm_.init(nullptr), fms::FmsError::OK);
        ASSERT_EQ(fuel_.init(), fms::FmsError::OK);
        perf_.init();
        fault_.init();
        fpm_.set_origin("EGLL"); fpm_.set_destination("KSFO");
        fms::Waypoint egll_w{}, wobun{}, ksfo{};
        fpm_.find_waypoint("EGLL", egll_w);
        fpm_.find_waypoint("WOBUN", wobun);
        fpm_.find_waypoint("KSFO", ksfo);
        fpm_.insert_waypoint(0U, egll_w);
        fpm_.insert_waypoint(1U, wobun);
        fpm_.insert_waypoint(2U, ksfo);
        ASSERT_EQ(fpm_.activate(), fms::FmsError::OK);
        nav_.set_rnp_requirement(2.0f);
        gc_.set_lnav_mode(fms::LnavMode::LNAV);
        gc_.set_vnav_mode(fms::VnavMode::VNAV_PTH);
    }

    fms::sensors::AirDataSystem     adc_;
    fms::sensors::GpsReceiver       gps_;
    fms::sensors::InertialNavSystem ins_;
    fms::NavigationEngine           nav_;
    fms::GuidanceComputer           gc_;
    fms::FlightPlanManager          fpm_;
    fms::FuelManagement             fuel_;
    fms::PerformanceComputer        perf_;
    fms::safety::FaultManager       fault_;
};

/// @req SRS-INT-001: 30-cycle loop executes without fault
TEST_F(FmsIntegrationTest, ThirtyCyclesNoFault) {
    for (int i = 0; i < 30; ++i) {
        adc_.update(); gps_.update(); ins_.update();
        const auto& g = gps_.get_data();
        if (g.valid)
            nav_.update_gps(g.lat_deg, g.lon_deg, g.alt_wgs84_m,
                             g.vel_north_ms, g.vel_east_ms, g.num_satellites, g.hdop);
        const auto& a = adc_.get_data();
        if (a.valid)
            nav_.update_adc(a.tas_kt, a.cas_kt, a.mach, a.pressure_alt_ft, a.isa_deviation_c);
        perf_.update(nav_.get_nav_state(), fuel_.get_fuel_state(), fpm_.get_active_fp());
        fuel_.update(perf_.get_perf_data(), nav_.get_nav_state());
        gc_.update(nav_.get_nav_state(), fpm_.get_active_fp(), perf_.get_perf_data());
    }
    EXPECT_EQ(fault_.get_worst_status(), fms::SystemStatus::NORMAL);
}

/// @req SRS-INT-002: flight plan remains ACTIVE after 30 cycles
TEST_F(FmsIntegrationTest, FlightPlanStaysActive) {
    for (int i = 0; i < 30; ++i) {
        adc_.update(); gps_.update();
        const auto& g = gps_.get_data();
        if (g.valid)
            nav_.update_gps(g.lat_deg, g.lon_deg, g.alt_wgs84_m,
                             g.vel_north_ms, g.vel_east_ms, g.num_satellites, g.hdop);
        gc_.update(nav_.get_nav_state(), fpm_.get_active_fp(), perf_.get_perf_data());
    }
    EXPECT_EQ(fpm_.get_active_fp().state, fms::FlightPlanState::ACTIVE);
}

/// @req SRS-INT-003: fuel decreases over 30 cycles
TEST_F(FmsIntegrationTest, FuelDecreases) {
    double initial = fuel_.get_fuel_state().total_fuel_kg;
    for (int i = 0; i < 30; ++i) {
        adc_.update();
        const auto& a = adc_.get_data();
        if (a.valid)
            nav_.update_adc(a.tas_kt, a.cas_kt, a.mach, a.pressure_alt_ft, a.isa_deviation_c);
        perf_.update(nav_.get_nav_state(), fuel_.get_fuel_state(), fpm_.get_active_fp());
        fuel_.update(perf_.get_perf_data(), nav_.get_nav_state());
    }
    EXPECT_LT(fuel_.get_fuel_state().total_fuel_kg, initial);
}
