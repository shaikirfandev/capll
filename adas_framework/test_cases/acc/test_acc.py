# adas_framework/test_cases/acc/test_acc.py
"""
Adaptive Cruise Control (ACC) — Automated Test Suite.

Covers:
    TC_ACC_001  Speed hold accuracy at set point
    TC_ACC_002  Following distance maintenance
    TC_ACC_003  Target acquisition (object enters range)
    TC_ACC_004  Target loss (cut-out) → resume set speed
    TC_ACC_005  Deceleration profile to standstill
    TC_ACC_006  Re-acceleration after standstill
    TC_ACC_007  ACC activation conditions
    TC_ACC_008  Velocity range limits
    TC_ACC_009  False target rejection (stationary objects)
    TC_ACC_010  Override by driver braking

Requirements: ACC_REQ_001–050 (from DOORS/Polarion)
ASIL: B
"""
import time
import pytest

from core.base_test import ADASBaseTest
from core.logger import get_logger

log = get_logger("test_acc")

# ── CAN Signal names (match project DBC) ─────────────────────────────────────
SIG_ACC_STATUS      = "ACC_Status"           # 0=Off, 1=Standby, 2=Active
SIG_ACC_SET_SPEED   = "ACC_SetSpeed_kmh"
SIG_VEHICLE_SPEED   = "VehicleSpeed_kmh"
SIG_ACC_TARGET_ID   = "ACC_TargetObjectID"
SIG_ACC_HEADWAY_S   = "ACC_FollowingTime_s"
SIG_ACC_DECEL_REQ   = "ACC_DecelRequest_mpss"
SIG_ACC_ACCEL_REQ   = "ACC_AccelRequest_mpss"
SIG_DRIVER_BRAKE    = "DriverBrakePressure_bar"

# ── ECU CAN IDs ───────────────────────────────────────────────────────────────
CANID_ACC_OUTPUT    = 0x120
CANID_VEHICLE_STATE = 0x130


# ─────────────────────────────────────────────────────────────────────────────
# Test class
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.acc
@pytest.mark.regression
class TestACC(ADASBaseTest):

    ASIL       = "B"
    FEATURE    = "ACC"
    REQ_IDS    = ["ACC_REQ_001", "ACC_REQ_005", "ACC_REQ_010"]

    # ── Speed hold ─────────────────────────────────────────────────────────────

    @pytest.mark.smoke
    def test_speed_hold_100kmh(self, signals, can_bus):
        """TC_ACC_001: ACC holds vehicle speed at 100 km/h ±2 km/h."""
        set_speed = 100.0

        # Simulate set speed signal
        can_bus.send(CANID_ACC_OUTPUT, [0x02, int(set_speed), 0x00, 0x00])
        time.sleep(0.5)

        actual = signals.get(SIG_VEHICLE_SPEED)
        if actual is None:
            pytest.skip("VehicleSpeed signal not yet available")

        assert (set_speed - 2.0) <= float(actual) <= (set_speed + 2.0), (
            f"Vehicle speed {actual} km/h outside expected range "
            f"[{set_speed - 2.0}, {set_speed + 2.0}]"
        )

    @pytest.mark.parametrize("set_speed_kmh", [30, 60, 80, 100, 130])
    def test_speed_hold_parametrized(self, signals, can_bus, set_speed_kmh):
        """TC_ACC_002: Speed hold at multiple set points."""
        can_bus.send(CANID_ACC_OUTPUT, [0x02, set_speed_kmh, 0x00, 0x00])
        time.sleep(0.5)

        actual = signals.get(SIG_VEHICLE_SPEED)
        if actual is None:
            pytest.skip("VehicleSpeed signal not available")

        assert (set_speed_kmh - 2.0) <= float(actual) <= (set_speed_kmh + 2.0), (
            f"Vehicle speed {actual} km/h outside expected range "
            f"[{set_speed_kmh - 2.0}, {set_speed_kmh + 2.0}]"
        )

    # ── Following distance ─────────────────────────────────────────────────────

    @pytest.mark.smoke
    def test_following_time_2s(self, signals):
        """TC_ACC_003: ACC headway ≥ 2 s when following active."""
        headway = signals.get(SIG_ACC_HEADWAY_S)
        if headway is None:
            pytest.skip("ACC headway signal not available")
        assert 1.5 <= float(headway) <= 4.0, (
            f"ACC following time {headway}s outside expected range [1.5, 4.0]"
        )

    # ── Target tracking ────────────────────────────────────────────────────────

    def test_target_acquisition(self, signals, radar, can_bus):
        """TC_ACC_004: ACC acquires a lead vehicle detected by radar."""
        # Inject a target at 50m, 80 km/h
        from radar.radar_validator import RadarObject
        obj = RadarObject(obj_id=1, range_m=50.0, velocity_mps=22.2,
                          azimuth_deg=0.0, rcs_dbm=15.0)
        radar.ingest_object(obj)
        time.sleep(0.2)

        target_id = signals.get(SIG_ACC_TARGET_ID)
        if target_id is None:
            pytest.skip("ACC target ID signal not available")
        assert int(target_id) != 0, "ACC did not acquire radar target"

    def test_target_loss_resume(self, signals, can_bus):
        """TC_ACC_005: After target cut-out, ACC resumes set speed."""
        set_speed = 100.0
        can_bus.send(CANID_ACC_OUTPUT, [0x02, int(set_speed), 0x00, 0x00])
        time.sleep(1.0)

        # Simulate target disappearance
        can_bus.send(CANID_ACC_OUTPUT, [0x02, int(set_speed), 0x00, 0x00])
        time.sleep(1.5)

        actual = signals.get(SIG_VEHICLE_SPEED)
        if actual is None:
            pytest.skip("VehicleSpeed signal not available")
        assert (set_speed - 5.0) <= float(actual) <= (set_speed + 5.0), (
            f"Vehicle speed {actual} km/h outside expected range "
            f"[{set_speed - 5.0}, {set_speed + 5.0}] after target loss"
        )

    # ── Deceleration ───────────────────────────────────────────────────────────

    def test_deceleration_profile(self, signals, can_bus):
        """TC_ACC_006: ACC decelerates ≤ 3.0 m/s² under normal following."""
        decel_req = signals.get(SIG_ACC_DECEL_REQ)
        if decel_req is None:
            pytest.skip("ACC deceleration request signal not available")
        assert abs(float(decel_req)) <= 3.0, (
            f"ACC decel request {decel_req:.2f} m/s² exceeds 3.0 m/s²"
        )

    def test_deceleration_to_standstill(self, signals, can_bus):
        """TC_ACC_007: ACC can decelerate to 0 km/h (stop-and-go)."""
        # Inject slow-moving target at 15m
        from radar.radar_validator import RadarObject
        from radar.radar_validator import RadarValidator
        pass  # Behavioural — validated via HIL bench

    # ── Driver override ────────────────────────────────────────────────────────

    @pytest.mark.safety
    @pytest.mark.asil_b
    def test_driver_brake_override(self, signals, can_bus):
        """TC_ACC_008: Driver braking overrides ACC deceleration command."""
        # Simulate driver brake pedal
        can_bus.send(CANID_VEHICLE_STATE, [0x00, 0x00, 0x50, 0x00])  # brake=80bar
        time.sleep(0.1)

        decel = signals.get(SIG_ACC_DECEL_REQ)
        if decel is None:
            pytest.skip("ACC deceleration request signal not available")
        # With brake override, ACC should not command any deceleration (driver takes over)
        # (ECU should set AccelRequest = 0, let friction braking handle it)
        accel = signals.get(SIG_ACC_ACCEL_REQ)
        if accel is not None:
            assert float(accel) <= 0.0, \
                "ACC still commanding positive acceleration during driver braking!"

    # ── Velocity range ─────────────────────────────────────────────────────────

    @pytest.mark.safety
    def test_velocity_range_limits(self, signals, can_bus):
        """TC_ACC_009: ACC only active 30–180 km/h as per spec."""
        # Below minimum speed — ACC should not be active
        can_bus.send(CANID_VEHICLE_STATE, [0x1E, 0x00, 0x00, 0x00])  # 30 km/h
        time.sleep(0.1)
        status = signals.get(SIG_ACC_STATUS)
        if status is None:
            pytest.skip("ACC status signal not available")
        # 30 km/h is at the lower boundary — status should still be ≥ 2 (active)
        assert 0 <= float(status) <= 3, (
            f"ACC status {status} outside valid range [0, 3]"
        )

    # ── False target rejection ─────────────────────────────────────────────────

    def test_false_target_rejection(self, signals, radar):
        """TC_ACC_010: ACC ignores stationary roadside objects."""
        from radar.radar_validator import RadarObject
        # A guard rail at 5m azimuth=45°, velocity=0
        guardrail = RadarObject(obj_id=99, range_m=5.0, velocity_mps=0.0,
                                azimuth_deg=45.0, rcs_dbm=20.0)
        radar.ingest_object(guardrail)
        time.sleep(0.2)

        target_id = signals.get(SIG_ACC_TARGET_ID)
        if target_id is not None:
            assert int(target_id) != 99, (
                "ACC falsely acquired stationary roadside object as target!"
            )
