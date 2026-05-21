/**
 * @file test_flight_plan_manager.cpp
 * @brief Unit tests for FlightPlanManager — @req SRS-FP-001..010
 */
#include <gtest/gtest.h>
#include "fms/FlightPlanManager.hpp"

class FlightPlanTest : public ::testing::Test {
protected:
    void SetUp() override {
        ASSERT_EQ(fpm_.init(nullptr), fms::FmsError::OK);
        fpm_.set_origin("EGLL");
        fpm_.set_destination("KSFO");
    }
    fms::FlightPlanManager fpm_;
};

/// @req SRS-FP-001: activate fails with fewer than 2 waypoints
TEST_F(FlightPlanTest, ActivateFailsLessThan2Wpts) {
    fms::Waypoint wpt{};
    ASSERT_TRUE(fpm_.find_waypoint("EGLL", wpt));
    fpm_.insert_waypoint(0U, wpt);
    EXPECT_NE(fpm_.activate(), fms::FmsError::OK);
}

/// @req SRS-FP-002: activate succeeds with ≥2 waypoints
TEST_F(FlightPlanTest, ActivateSucceedsWith2Wpts) {
    fms::Waypoint egll{}, ksfo{};
    ASSERT_TRUE(fpm_.find_waypoint("EGLL", egll));
    ASSERT_TRUE(fpm_.find_waypoint("KSFO", ksfo));
    fpm_.insert_waypoint(0U, egll);
    fpm_.insert_waypoint(1U, ksfo);
    EXPECT_EQ(fpm_.activate(), fms::FmsError::OK);
    EXPECT_EQ(fpm_.get_active_fp().state, fms::FlightPlanState::ACTIVE);
}

/// @req SRS-FP-003: find_waypoint returns false for unknown ident
TEST_F(FlightPlanTest, FindWaypointNotFound) {
    fms::Waypoint wpt{};
    EXPECT_FALSE(fpm_.find_waypoint("XXXX", wpt));
}

/// @req SRS-FP-004: find_waypoint returns true for known ident
TEST_F(FlightPlanTest, FindWaypointFound) {
    fms::Waypoint wpt{};
    EXPECT_TRUE(fpm_.find_waypoint("LAM", wpt));
}

/// @req SRS-FP-005: delete waypoint reduces wpt_count
TEST_F(FlightPlanTest, DeleteReducesCount) {
    fms::Waypoint egll{}, ksfo{};
    ASSERT_TRUE(fpm_.find_waypoint("EGLL", egll));
    ASSERT_TRUE(fpm_.find_waypoint("KSFO", ksfo));
    fpm_.insert_waypoint(0U, egll);
    fpm_.insert_waypoint(1U, ksfo);
    uint8_t before = fpm_.get_active_fp().wpt_count;
    fpm_.delete_waypoint(1U);
    EXPECT_EQ(fpm_.get_active_fp().wpt_count, before - 1U);
}

/// @req SRS-FP-006: direct_to skips ahead in flight plan
TEST_F(FlightPlanTest, DirectTo) {
    fms::Waypoint egll{}, wobun{}, ksfo{};
    ASSERT_TRUE(fpm_.find_waypoint("EGLL", egll));
    ASSERT_TRUE(fpm_.find_waypoint("WOBUN", wobun));
    ASSERT_TRUE(fpm_.find_waypoint("KSFO", ksfo));
    fpm_.insert_waypoint(0U, egll);
    fpm_.insert_waypoint(1U, wobun);
    fpm_.insert_waypoint(2U, ksfo);
    ASSERT_EQ(fpm_.activate(), fms::FmsError::OK);
    EXPECT_EQ(fpm_.direct_to("KSFO"), fms::FmsError::OK);
    EXPECT_STREQ(fpm_.get_active_fp().waypoints[fpm_.get_active_fp().active_wpt_idx].ident, "KSFO");
}

/// @req SRS-FP-007: sequence advances active waypoint index
TEST_F(FlightPlanTest, SequenceAdvancesIndex) {
    fms::Waypoint egll{}, wobun{}, ksfo{};
    ASSERT_TRUE(fpm_.find_waypoint("EGLL", egll));
    ASSERT_TRUE(fpm_.find_waypoint("WOBUN", wobun));
    ASSERT_TRUE(fpm_.find_waypoint("KSFO", ksfo));
    fpm_.insert_waypoint(0U, egll);
    fpm_.insert_waypoint(1U, wobun);
    fpm_.insert_waypoint(2U, ksfo);
    ASSERT_EQ(fpm_.activate(), fms::FmsError::OK);
    uint8_t idx_before = fpm_.get_active_fp().active_wpt_idx;
    fpm_.sequence_next_waypoint();
    EXPECT_GT(fpm_.get_active_fp().active_wpt_idx, idx_before);
}
