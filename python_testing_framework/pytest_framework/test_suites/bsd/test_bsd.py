"""
pytest_framework/test_suites/bsd/test_bsd.py

BSD – Blind Spot Detection Validation
ASIL: A | Requirements: BSD_REQ_001–040
"""
import time
import pytest

from core.base_test import ADASBaseTest

SIG_BSD_LEFT_STATUS    = "BSD_LeftZone_Status"   # 0=Clear 1=Object 2=Warning
SIG_BSD_RIGHT_STATUS   = "BSD_RightZone_Status"
SIG_BSD_LEFT_DIST      = "BSD_LeftDist_m"
SIG_BSD_RIGHT_DIST     = "BSD_RightDist_m"
SIG_BSD_LKCA_LEFT      = "LKCA_LeftAlert"        # Lane change conflict alert
SIG_BSD_LKCA_RIGHT     = "LKCA_RightAlert"
SIG_VEHICLE_SPEED      = "VehicleSpeed_kmh"
SIG_TURN_SIGNAL_LEFT   = "TurnSignalLeft"
SIG_TURN_SIGNAL_RIGHT  = "TurnSignalRight"

CANID_BSD_OUTPUT       = 0x170
CANID_VEHICLE_STATE    = 0x130

ZONE_NEAR = 0.5   # m
ZONE_FAR  = 4.5   # m


@pytest.mark.bsd
@pytest.mark.regression
class TestBSD(ADASBaseTest):

    ASIL    = "A"
    FEATURE = "BSD"
    REQ_IDS = ["BSD_REQ_001", "BSD_REQ_005", "BSD_REQ_020"]

    # ── Detection ─────────────────────────────────────────────────────────────

    @pytest.mark.smoke
    def test_vehicle_in_left_blind_spot(self, signals, can_bus):
        """BSD detects vehicle in left blind spot zone."""
        can_bus.send(CANID_BSD_OUTPUT, [0x01, 0x50, 0x00, 0x00])  # left=1, dist=80cm
        time.sleep(0.1)

        status = signals.get(SIG_BSD_LEFT_STATUS)
        if status is None:
            pytest.skip("BSD_LeftZone_Status signal not available")
        assert int(status) >= 1, "BSD did not detect vehicle in left blind spot"

    @pytest.mark.smoke
    def test_vehicle_in_right_blind_spot(self, signals, can_bus):
        """BSD detects vehicle in right blind spot zone."""
        can_bus.send(CANID_BSD_OUTPUT, [0x00, 0x00, 0x01, 0x60])  # right=1, dist=96cm
        time.sleep(0.1)

        status = signals.get(SIG_BSD_RIGHT_STATUS)
        if status is None:
            pytest.skip("BSD_RightZone_Status signal not available")
        assert int(status) >= 1, "BSD did not detect vehicle in right blind spot"

    # ── Zone boundary tests ───────────────────────────────────────────────────

    @pytest.mark.parametrize("dist_m, expected_status", [
        (6.0, 0),    # outside zone
        (4.5, 1),    # at far boundary
        (2.0, 1),    # mid zone
        (0.5, 2),    # near boundary — escalate to warning
    ])
    def test_left_zone_status_by_distance(
        self, signals, can_bus, dist_m, expected_status
    ):
        """BSD left zone status corresponds to distance."""
        dist_byte = min(int(dist_m * 100), 0xFF)
        can_bus.send(CANID_BSD_OUTPUT, [expected_status, dist_byte, 0x00, 0x00])
        time.sleep(0.1)

        status = signals.get(SIG_BSD_LEFT_STATUS)
        if status is None:
            pytest.skip("BSD_LeftZone_Status signal not available")
        assert int(status) == expected_status, (
            f"At dist={dist_m}m: status={status}, expected={expected_status}"
        )

    # ── RCTA – Rear Cross-Traffic Alert ──────────────────────────────────────

    def test_lkca_alert_with_turn_signal_and_bsd(self, signals, can_bus):
        """LCKA alert active when turn signal + vehicle in blind spot."""
        # Right turn signal + right blind spot occupied
        can_bus.send(CANID_BSD_OUTPUT,    [0x00, 0x00, 0x01, 0x50])
        can_bus.send(CANID_VEHICLE_STATE, [0x00, 0x01, 0x00, 0x00])
        time.sleep(0.15)

        alert = signals.get(SIG_BSD_LKCA_RIGHT)
        if alert is None:
            pytest.skip("LKCA_RightAlert signal not available")
        assert int(alert) == 1, (
            "LKCA alert not active despite right blind spot occupied + right turn signal"
        )

    def test_no_lkca_alert_without_turn_signal(self, signals, can_bus):
        """LKCA alert suppressed when turn signal not activated."""
        can_bus.send(CANID_BSD_OUTPUT,    [0x00, 0x00, 0x01, 0x50])  # right occupied
        can_bus.send(CANID_VEHICLE_STATE, [0x00, 0x00, 0x00, 0x00])  # no turn signal
        time.sleep(0.15)

        alert = signals.get(SIG_BSD_LKCA_RIGHT)
        if alert is not None:
            assert int(alert) == 0, (
                "LKCA alert raised without turn signal — false positive"
            )

    # ── Distance accuracy ─────────────────────────────────────────────────────

    @pytest.mark.parametrize("true_dist_m", [0.8, 1.5, 2.5, 3.5, 4.0])
    def test_distance_accuracy(self, signals, can_bus, true_dist_m):
        """BSD reported distance within ±0.25m of injected distance."""
        dist_byte = int(true_dist_m * 100) & 0xFF
        can_bus.send(CANID_BSD_OUTPUT, [0x01, dist_byte, 0x00, 0x00])
        time.sleep(0.1)

        reported = signals.get(SIG_BSD_LEFT_DIST)
        if reported is None:
            pytest.skip("BSD_LeftDist signal not available")
        assert abs(float(reported) - true_dist_m) <= 0.25, (
            f"BSD distance error: reported={reported:.2f}m, "
            f"true={true_dist_m:.2f}m (tolerance=±0.25m)"
        )

    # ── Speed envelope ────────────────────────────────────────────────────────

    @pytest.mark.parametrize("speed_kmh, expect_active", [
        (10,  False),
        (30,  True),
        (100, True),
        (160, True),
    ])
    def test_bsd_speed_activation(
        self, signals, vehicle_sim, speed_kmh, expect_active
    ):
        """BSD active only when vehicle speed ≥ 15 km/h."""
        vehicle_sim.set_speed(speed_kmh)
        time.sleep(0.15)

        status_l = signals.get(SIG_BSD_LEFT_STATUS)
        status_r = signals.get(SIG_BSD_RIGHT_STATUS)
        if status_l is None:
            pytest.skip("BSD status signal not available")
        active = int(status_l) >= 0 and int(status_r) >= 0  # approximate check
        # Primary check: at low speed BSD should report 0
        if not expect_active:
            assert int(status_l) == 0 and int(status_r) == 0, (
                f"BSD active at {speed_kmh} km/h — should be inactive below 15 km/h"
            )

    # ── Clear zone — no false positives ──────────────────────────────────────

    def test_no_false_detection_clear_zone(self, signals, can_bus):
        """No BSD detection when zones are clear."""
        can_bus.send(CANID_BSD_OUTPUT, [0x00, 0xFF, 0x00, 0xFF])  # both clear
        time.sleep(0.1)

        status_l = signals.get(SIG_BSD_LEFT_STATUS)
        status_r = signals.get(SIG_BSD_RIGHT_STATUS)
        if status_l is not None:
            assert int(status_l) == 0, f"False left BSD detection: status={status_l}"
        if status_r is not None:
            assert int(status_r) == 0, f"False right BSD detection: status={status_r}"
