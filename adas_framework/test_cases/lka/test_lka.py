# adas_framework/test_cases/lka/test_lka.py
"""
Lane Keep Assist (LKA) / Lane Departure Warning (LDW) — Automated Test Suite.

Covers:
    TC_LKA_001  Lane centering — straight road, 100 km/h
    TC_LKA_002  Torque output within ±5 Nm spec
    TC_LKA_003  Left drift correction
    TC_LKA_004  Right drift correction
    TC_LKA_005  LKA inactive when turn signal active
    TC_LKA_006  LDW warning triggered at lane line crossing
    TC_LKA_007  LKA off below 60 km/h
    TC_LKA_008  Camera input — lane detection confidence ≥ 0.85
    TC_LKA_009  Curvature compensation on motorway curve
    TC_LKA_010  Driver override — hands-on torque suppression

Requirements: LKA_REQ_001–060
ASIL: B
"""
import time
import pytest

from core.base_test import ADASBaseTest
from core.logger import get_logger

log = get_logger("test_lka")

# ── CAN Signal names ──────────────────────────────────────────────────────────
SIG_LKA_STATUS         = "LKA_Status"           # 0=Off, 1=Standby, 2=Active
SIG_LKA_TORQUE_REQ     = "LKA_TorqueRequest_Nm"
SIG_LKA_LANE_CONF      = "LKA_LaneConfidence"
SIG_LKA_OFFSET_M       = "LKA_LateralOffset_m"
SIG_LKA_TURN_SIGNAL    = "TurnSignalActive"      # 0=Off, 1=Left, 2=Right
SIG_LDW_WARNING        = "LDW_WarningActive"
SIG_VEHICLE_SPEED      = "VehicleSpeed_kmh"
SIG_DRIVER_TORQUE      = "SteeringDriverTorque_Nm"

CANID_LKA_OUTPUT       = 0x160
CANID_VEHICLE_STATE    = 0x130
CANID_TURN_SIGNAL      = 0x170


@pytest.mark.lka
@pytest.mark.regression
class TestLKA(ADASBaseTest):

    ASIL       = "B"
    FEATURE    = "LKA"
    REQ_IDS    = ["LKA_REQ_001", "LKA_REQ_010", "LKA_REQ_030"]

    # ── Lane centering ─────────────────────────────────────────────────────────

    @pytest.mark.smoke
    def test_lane_centering_100kmh(self, signals, can_bus):
        """TC_LKA_001: LKA maintains lateral offset < 0.3 m from centre."""
        can_bus.send(CANID_VEHICLE_STATE, [100, 0, 0, 0])  # 100 km/h
        time.sleep(0.5)

        offset = signals.get(SIG_LKA_OFFSET_M)
        if offset is None:
            pytest.skip("LKA lateral offset signal not available")

        self.assert_signal_in_range(abs(float(offset)), 0.0, 0.3)

    # ── Torque limits ─────────────────────────────────────────────────────────

    @pytest.mark.safety
    @pytest.mark.asil_b
    def test_torque_within_spec(self, signals):
        """TC_LKA_002: LKA torque request within ±5 Nm ISO 11270 limit."""
        torque = signals.get(SIG_LKA_TORQUE_REQ)
        if torque is None:
            pytest.skip("LKA torque request signal not available")
        self.assert_signal_in_range(float(torque), -5.0, 5.0)

    # ── Drift correction ──────────────────────────────────────────────────────

    @pytest.mark.parametrize("direction", ["left", "right"])
    def test_drift_correction(self, signals, can_bus, direction):
        """TC_LKA_003/004: LKA corrects lateral drift from both sides."""
        offset_val = -0.4 if direction == "left" else 0.4
        # Simulate vehicle offset signal
        can_bus.send(CANID_LKA_OUTPUT,
                     [0x02, int(abs(offset_val) * 100), 0x01 if direction == "right" else 0x00, 0x00])
        time.sleep(0.3)

        torque = signals.get(SIG_LKA_TORQUE_REQ)
        if torque is None:
            pytest.skip("LKA torque request signal not available")

        if direction == "left":
            assert float(torque) > 0.0, \
                f"Expected positive torque for left drift correction, got {torque}"
        else:
            assert float(torque) < 0.0, \
                f"Expected negative torque for right drift correction, got {torque}"

    # ── Turn signal inhibition ────────────────────────────────────────────────

    @pytest.mark.safety
    def test_lka_inactive_during_turn_signal(self, signals, can_bus):
        """TC_LKA_005: LKA must NOT intervene when turn signal is active."""
        # Activate left turn signal
        can_bus.send(CANID_TURN_SIGNAL, [0x01, 0x00, 0x00, 0x00])
        time.sleep(0.2)

        torque = signals.get(SIG_LKA_TORQUE_REQ)
        if torque is None:
            pytest.skip("LKA torque request signal not available")

        assert abs(float(torque)) < 0.5, (
            f"LKA torque {torque:.2f}Nm active during turn signal — "
            f"driver intention not respected!"
        )

        # Restore turn signal off
        can_bus.send(CANID_TURN_SIGNAL, [0x00, 0x00, 0x00, 0x00])

    # ── LDW warning ───────────────────────────────────────────────────────────

    @pytest.mark.smoke
    def test_ldw_warning_at_line_crossing(self, signals, can_bus):
        """TC_LKA_006: LDW triggers warning when lane line crossed without signal."""
        # Simulate large lateral offset (crossing line)
        can_bus.send(CANID_LKA_OUTPUT, [0x02, 0x50, 0x01, 0x00])  # 0.8m offset
        time.sleep(0.3)

        ldw = signals.get(SIG_LDW_WARNING)
        if ldw is None:
            pytest.skip("LDW warning signal not available")
        assert int(ldw) == 1, "LDW warning did not activate at lane line crossing"

    # ── Speed envelope ────────────────────────────────────────────────────────

    @pytest.mark.parametrize("speed_kmh, should_assist", [
        (40,  False),   # below 60 km/h threshold
        (60,  True),    # at activation boundary
        (100, True),    # nominal
        (180, True),    # high speed
    ])
    def test_lka_speed_envelope(self, signals, can_bus, speed_kmh, should_assist):
        """TC_LKA_007: LKA only active ≥ 60 km/h."""
        can_bus.send(CANID_VEHICLE_STATE, [speed_kmh & 0xFF, 0, 0, 0])
        time.sleep(0.2)

        status = signals.get(SIG_LKA_STATUS)
        if status is None:
            pytest.skip("LKA status signal not available")
        is_active = int(status) >= 2  # 2 = Active
        assert is_active == should_assist, (
            f"LKA at {speed_kmh} km/h: active={is_active}, expected={should_assist}"
        )

    # ── Camera lane confidence ────────────────────────────────────────────────

    def test_camera_lane_confidence(self, signals, camera):
        """TC_LKA_008: Camera lane detection confidence ≥ 0.85 during LKA."""
        frame  = camera.capture_frame()
        result = camera.detect_lanes(frame)

        lka_conf = signals.get(SIG_LKA_LANE_CONF)
        if lka_conf is not None:
            assert float(lka_conf) >= 0.85, (
                f"LKA lane confidence {lka_conf:.2f} below 0.85 minimum"
            )

    # ── Driver override ───────────────────────────────────────────────────────

    @pytest.mark.safety
    def test_driver_torque_override(self, signals, can_bus):
        """TC_LKA_010: LKA suppresses when driver applies ≥ 3 Nm steering torque."""
        # Simulate driver steering torque
        can_bus.send(CANID_VEHICLE_STATE, [100, 0, 0x03, 0x00])  # 3Nm driver torque
        time.sleep(0.2)

        lka_torque = signals.get(SIG_LKA_TORQUE_REQ)
        driver_torque = signals.get(SIG_DRIVER_TORQUE)

        if lka_torque is None or driver_torque is None:
            pytest.skip("LKA or driver torque signals not available")

        if abs(float(driver_torque)) >= 3.0:
            assert abs(float(lka_torque)) < 0.5, (
                f"LKA not suppressed despite {driver_torque:.1f}Nm driver torque"
            )
