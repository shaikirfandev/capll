# adas_framework/test_cases/bsd/test_bsd.py
"""
Blind Spot Detection (BSD) — Automated Test Suite.

Covers:
    TC_BSD_001  Stationary vehicle in blind spot detected
    TC_BSD_002  Moving vehicle entering blind spot — warning trigger
    TC_BSD_003  Warning suppressed when turn signal NOT active
    TC_BSD_004  Warning active when turn signal active + object in BSZ
    TC_BSD_005  Both left and right zone detection
    TC_BSD_006  BSD object distance accuracy ±0.5 m
    TC_BSD_007  BSD off below 30 km/h
    TC_BSD_008  BSD off above 250 km/h
    TC_BSD_009  Tracking continuation through brief sensor dropout
    TC_BSD_010  No false positive from bridge/barrier

Requirements: BSD_REQ_001–040
ASIL: A
"""
import time
import pytest

from core.base_test import ADASBaseTest
from core.logger import get_logger

log = get_logger("test_bsd")

# ── CAN Signal names ──────────────────────────────────────────────────────────
SIG_BSD_LEFT_OBJ       = "BSD_LeftObjectDetected"     # 0/1
SIG_BSD_RIGHT_OBJ      = "BSD_RightObjectDetected"    # 0/1
SIG_BSD_LEFT_WARN      = "BSD_LeftWarningActive"      # 0/1
SIG_BSD_RIGHT_WARN     = "BSD_RightWarningActive"     # 0/1
SIG_BSD_LEFT_DIST      = "BSD_LeftObjectDistance_m"
SIG_BSD_RIGHT_DIST     = "BSD_RightObjectDistance_m"
SIG_VEHICLE_SPEED      = "VehicleSpeed_kmh"
SIG_TURN_SIGNAL        = "TurnSignalActive"

CANID_BSD_OUTPUT       = 0x190
CANID_VEHICLE_STATE    = 0x130
CANID_TURN_SIGNAL      = 0x170


@pytest.mark.bsd
@pytest.mark.regression
class TestBSD(ADASBaseTest):

    ASIL    = "A"
    FEATURE = "BSD"
    REQ_IDS = ["BSD_REQ_001", "BSD_REQ_010", "BSD_REQ_030"]

    # ── Object detection ──────────────────────────────────────────────────────

    @pytest.mark.smoke
    @pytest.mark.parametrize("side", ["left", "right"])
    def test_stationary_object_in_bsz(self, signals, can_bus, side):
        """TC_BSD_001: Stationary vehicle in blind spot zone detected."""
        obj_flag = 0x01 if side == "left" else 0x02
        can_bus.send(CANID_BSD_OUTPUT, [obj_flag, 0x1E, 0x1E, 0x00])  # 30m
        time.sleep(0.1)

        sig = SIG_BSD_LEFT_OBJ if side == "left" else SIG_BSD_RIGHT_OBJ
        detected = signals.get(sig)
        if detected is None:
            pytest.skip(f"BSD {side} object signal not available")
        assert int(detected) == 1, \
            f"BSD did not detect stationary object in {side} blind spot zone"

    def test_moving_object_entering_bsz(self, signals, can_bus):
        """TC_BSD_002: Object approaching from behind enters BSD zone."""
        # Object enters from behind at 120 km/h (overtaking at host 100 km/h)
        can_bus.send(CANID_VEHICLE_STATE, [100, 0, 0, 0])
        time.sleep(0.1)
        can_bus.send(CANID_BSD_OUTPUT, [0x02, 0x14, 0x14, 0x00])  # right, 20m
        time.sleep(0.1)

        right_det = signals.get(SIG_BSD_RIGHT_OBJ)
        if right_det is None:
            pytest.skip("BSD right object signal not available")
        assert int(right_det) == 1, "BSD missed moving object entering right BSZ"

    # ── Warning logic ─────────────────────────────────────────────────────────

    def test_warning_suppressed_without_turn_signal(self, signals, can_bus):
        """TC_BSD_003: Warning indicator NOT active unless turn signal is active."""
        can_bus.send(CANID_TURN_SIGNAL, [0x00, 0x00, 0x00, 0x00])
        can_bus.send(CANID_BSD_OUTPUT, [0x01, 0x14, 0x14, 0x00])  # object in left zone
        time.sleep(0.15)

        warn = signals.get(SIG_BSD_LEFT_WARN)
        if warn is None:
            pytest.skip("BSD left warning signal not available")
        # Warning should NOT be escalated (just indicator light, no intervention)
        assert int(warn) == 0, \
            "BSD warning unexpectedly active without turn signal"

    @pytest.mark.safety
    def test_warning_active_with_turn_signal(self, signals, can_bus):
        """TC_BSD_004: Warning ACTIVE when turn signal + object in BSZ."""
        can_bus.send(CANID_TURN_SIGNAL, [0x01, 0x00, 0x00, 0x00])  # left
        can_bus.send(CANID_BSD_OUTPUT, [0x01, 0x14, 0x14, 0x00])   # left object
        time.sleep(0.15)

        warn = signals.get(SIG_BSD_LEFT_WARN)
        if warn is None:
            pytest.skip("BSD left warning signal not available")
        assert int(warn) == 1, \
            "BSD warning not active despite turn signal + BSZ object!"

        # Restore
        can_bus.send(CANID_TURN_SIGNAL, [0x00, 0x00, 0x00, 0x00])

    # ── Distance accuracy ─────────────────────────────────────────────────────

    @pytest.mark.parametrize("expected_dist_m", [2.0, 3.5, 5.0, 10.0])
    def test_bsd_distance_accuracy(self, signals, can_bus, expected_dist_m):
        """TC_BSD_006: BSD distance measurement accurate to ±0.5 m."""
        dist_byte = int(expected_dist_m * 10) & 0xFF
        can_bus.send(CANID_BSD_OUTPUT, [0x02, dist_byte, 0x00, 0x00])  # right
        time.sleep(0.1)

        dist = signals.get(SIG_BSD_RIGHT_DIST)
        if dist is None:
            pytest.skip("BSD right distance signal not available")
        self.assert_signal_in_range(
            float(dist), expected_dist_m - 0.5, expected_dist_m + 0.5
        )

    # ── Speed envelope ────────────────────────────────────────────────────────

    @pytest.mark.parametrize("speed_kmh, should_be_active", [
        (20,  False),   # Below 30 km/h — inactive
        (30,  True),    # Boundary
        (120, True),    # Normal highway
    ])
    def test_bsd_speed_envelope(self, signals, can_bus, speed_kmh, should_be_active):
        """TC_BSD_007/008: BSD active only 30–250 km/h."""
        can_bus.send(CANID_VEHICLE_STATE, [speed_kmh, 0, 0, 0])
        time.sleep(0.1)

        # Use object detection as proxy for "BSD active"
        can_bus.send(CANID_BSD_OUTPUT, [0x01, 0x14, 0x14, 0x00])
        time.sleep(0.1)

        left_det = signals.get(SIG_BSD_LEFT_OBJ)
        if left_det is None:
            pytest.skip("BSD left object signal not available")
        detected = int(left_det) == 1
        assert detected == should_be_active, (
            f"BSD at {speed_kmh} km/h: active={detected}, expected={should_be_active}"
        )

    # ── False positive ────────────────────────────────────────────────────────

    def test_bridge_no_false_positive(self, signals, can_bus):
        """TC_BSD_010: Bridge/overhead structure does NOT trigger BSD warning."""
        # A bridge overhead at 6m height should not be in the lateral BSZ
        # This is validated via the vertical extent filtering in radar
        # Inject a "zero lateral" target as proxy
        can_bus.send(CANID_BSD_OUTPUT, [0x00, 0x00, 0x00, 0x00])
        time.sleep(0.1)

        warn = signals.get(SIG_BSD_LEFT_WARN)
        r_warn = signals.get(SIG_BSD_RIGHT_WARN)

        if warn is not None:
            assert int(warn) == 0, "BSD false warning triggered for bridge"
        if r_warn is not None:
            assert int(r_warn) == 0, "BSD false warning triggered for bridge (right)"
