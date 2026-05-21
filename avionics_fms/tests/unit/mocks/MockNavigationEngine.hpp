/**
 * @file MockNavigationEngine.hpp
 */
#pragma once
#include "fms/INavigationEngine.hpp"
#include <gmock/gmock.h>

struct MockNavigationEngine : fms::INavigationEngine {
    MOCK_METHOD(fms::FmsError, init,   (fms::LatLon), (noexcept, override));
    MOCK_METHOD(void, shutdown,        (),             (noexcept, override));
    MOCK_METHOD(void, update_gps, (double,double,double,double,double,uint8_t,float), (noexcept, override));
    MOCK_METHOD(void, update_adc, (float,float,float,float,float), (noexcept, override));
    MOCK_METHOD(void, set_rnp_requirement, (float), (noexcept, override));
    MOCK_METHOD(bool, is_rnp_satisfied, (), (const, noexcept, override));
    MOCK_METHOD(const fms::NavState&, get_nav_state, (), (const, noexcept, override));
    MOCK_METHOD(double, compute_bearing_deg, (const fms::Position3D&, const fms::Position3D&), (const, noexcept, override));
    MOCK_METHOD(double, compute_distance_nm, (const fms::Position3D&, const fms::Position3D&), (const, noexcept, override));
    MOCK_METHOD(double, compute_xte_nm, (const fms::Position3D&, const fms::Position3D&, const fms::Position3D&), (const, noexcept, override));
    MOCK_METHOD(fms::SystemStatus, get_status, (), (const, noexcept, override));
};
