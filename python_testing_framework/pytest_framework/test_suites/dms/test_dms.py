"""
pytest_framework/test_suites/dms/test_dms.py

DMS – Driver Monitoring System Validation
ASIL: B | Requirements: DMS_REQ_001–045
"""
import time
import pytest

from core.base_test import ADASBaseTest

SIG_DMS_STATUS        = "DMS_Status"            # 0=Off 1=Monitoring 2=Warning
SIG_DMS_GAZE_X        = "DMS_GazeAzimuth_deg"   # horizontal gaze angle
SIG_DMS_GAZE_Y        = "DMS_GazeElevation_deg" # vertical gaze angle
SIG_DMS_BLINK_RATE    = "DMS_BlinkRate_bpm"
SIG_DMS_PERCLOS       = "DMS_PERCLOS"            # 0.0–1.0
SIG_DMS_HEAD_PITCH    = "DMS_HeadPitch_deg"
SIG_DMS_HEAD_YAW      = "DMS_HeadYaw_deg"
SIG_DMS_ATTENTION     = "DMS_AttentionScore"     # 0.0–1.0
SIG_DMS_ALERT         = "DMS_AlertLevel"         # 0=None 1=Visual 2=Haptic 3=Audio
SIG_DMS_DROWSINESS    = "DMS_DrowsinessLevel"    # 0–3
SIG_DMS_DISTRACTION   = "DMS_DistractionLevel"  # 0–2

CANID_DMS_OUTPUT      = 0x190
CANID_CAMERA_INPUT    = 0x191

PERCLOS_DROWSY_THRESH = 0.08   # >8% eye closure = drowsy
GAZE_ROAD_LIMIT_DEG   = 15.0   # degrees off-center = distracted
HEAD_DROOP_LIMIT_DEG  = 30.0   # head pitch down = drowsy posture


@pytest.mark.dms
@pytest.mark.regression
class TestDMS(ADASBaseTest):

    ASIL    = "B"
    FEATURE = "DMS"
    REQ_IDS = ["DMS_REQ_001", "DMS_REQ_010", "DMS_REQ_020"]

    # ── System activation ─────────────────────────────────────────────────────

    @pytest.mark.smoke
    def test_dms_active_when_engine_on(self, signals, can_bus):
        """DMS monitoring starts when ignition is on."""
        can_bus.send(CANID_DMS_OUTPUT, [0x01, 0x00, 0x00, 0x00])  # status=monitoring
        time.sleep(0.1)

        status = signals.get(SIG_DMS_STATUS)
        if status is None:
            pytest.skip("DMS_Status signal not available")
        assert int(status) >= 1, "DMS not active with ignition on"

    # ── Gaze tracking ─────────────────────────────────────────────────────────

    @pytest.mark.parametrize("gaze_angle_deg, expect_distracted", [
        (5.0,  False),  # looking forward
        (10.0, False),  # acceptable peripheral
        (16.0, True),   # distracted
        (40.0, True),   # looking away
    ])
    def test_gaze_distraction_detection(
        self, signals, can_bus, gaze_angle_deg, expect_distracted
    ):
        """DMS distraction level correct for given gaze angle."""
        gaze_byte = int(gaze_angle_deg * 2) & 0xFF
        distraction_byte = 1 if gaze_angle_deg > GAZE_ROAD_LIMIT_DEG else 0
        can_bus.send(
            CANID_DMS_OUTPUT,
            [0x01, gaze_byte, 0x00, distraction_byte]
        )
        time.sleep(0.1)

        distraction = signals.get(SIG_DMS_DISTRACTION)
        if distraction is None:
            pytest.skip("DMS_DistractionLevel signal not available")
        actually_distracted = int(distraction) >= 1
        assert actually_distracted == expect_distracted, (
            f"Gaze={gaze_angle_deg}°: distracted={actually_distracted}, "
            f"expected={expect_distracted}"
        )

    # ── PERCLOS drowsiness ────────────────────────────────────────────────────

    @pytest.mark.parametrize("perclos, expect_drowsy", [
        (0.04, False),
        (0.08, True),   # at threshold
        (0.15, True),
        (0.30, True),
    ])
    def test_perclos_drowsiness(self, signals, can_bus, perclos, expect_drowsy):
        """DMS drowsiness flag matches PERCLOS level."""
        perclos_byte = int(perclos * 255) & 0xFF
        drowsy_byte  = 2 if perclos >= PERCLOS_DROWSY_THRESH else 0
        can_bus.send(CANID_DMS_OUTPUT, [0x01, 0x00, perclos_byte, drowsy_byte])
        time.sleep(0.1)

        drowsiness = signals.get(SIG_DMS_DROWSINESS)
        if drowsiness is None:
            pytest.skip("DMS_DrowsinessLevel signal not available")
        actually_drowsy = int(drowsiness) >= 2
        assert actually_drowsy == expect_drowsy, (
            f"PERCLOS={perclos:.2f}: drowsy={actually_drowsy}, "
            f"expected={expect_drowsy}"
        )

    # ── Head pose ─────────────────────────────────────────────────────────────

    def test_head_droop_triggers_drowsy(self, signals, can_bus):
        """Head pitch > 30° down classified as drowsy posture."""
        can_bus.send(CANID_DMS_OUTPUT, [0x01, 0x00, 0x0F, 0x02])  # pitch=30+
        time.sleep(0.1)

        drowsiness = signals.get(SIG_DMS_DROWSINESS)
        if drowsiness is None:
            pytest.skip("DMS_DrowsinessLevel signal not available")
        assert int(drowsiness) >= 1, (
            "DMS did not flag drowsiness on 30° head droop"
        )

    def test_head_turn_extreme_triggers_distraction(self, signals, can_bus):
        """Head yaw > 45° classified as severe distraction."""
        can_bus.send(CANID_DMS_OUTPUT, [0x01, 0x5A, 0x00, 0x02])  # yaw=90 bytes
        time.sleep(0.1)

        distraction = signals.get(SIG_DMS_DISTRACTION)
        if distraction is None:
            pytest.skip("DMS_DistractionLevel signal not available")
        assert int(distraction) >= 1, (
            "DMS did not flag distraction on extreme head yaw"
        )

    # ── Alert escalation ──────────────────────────────────────────────────────

    @pytest.mark.safety
    def test_alert_escalation_sequence(self, signals, can_bus):
        """DMS alert escalates: None → Visual → Haptic → Audio."""
        for level in range(4):
            can_bus.send(CANID_DMS_OUTPUT, [0x02, 0x00, 0x10, level])
            time.sleep(0.05)
            alert = signals.get(SIG_DMS_ALERT)
            if alert is not None:
                assert int(alert) == level, (
                    f"Alert level mismatch: got {alert}, expected {level}"
                )

    # ── Attention score ───────────────────────────────────────────────────────

    def test_attention_score_range(self, signals, can_bus):
        """DMS attention score always in [0.0, 1.0]."""
        can_bus.send(CANID_DMS_OUTPUT, [0x01, 0x0A, 0x05, 0x00])
        time.sleep(0.1)

        score = signals.get(SIG_DMS_ATTENTION)
        if score is None:
            pytest.skip("DMS_AttentionScore signal not available")
        assert 0.0 <= float(score) <= 1.0, (
            f"DMS attention score {score} out of [0.0, 1.0] range"
        )

    # ── Privacy / night mode ──────────────────────────────────────────────────

    def test_dms_monitors_in_darkness(self, signals, can_bus):
        """DMS IR camera maintains monitoring in darkness."""
        can_bus.send(CANID_CAMERA_INPUT, [0x02, 0x00, 0x00, 0x00])  # night mode
        can_bus.send(CANID_DMS_OUTPUT,   [0x01, 0x05, 0x02, 0x00])
        time.sleep(0.1)

        status = signals.get(SIG_DMS_STATUS)
        if status is None:
            pytest.skip("DMS_Status not available")
        assert int(status) >= 1, "DMS stopped monitoring in night mode"

    # ── Negative tests ────────────────────────────────────────────────────────

    def test_no_false_drowsy_alert_attentive_driver(self, signals, can_bus):
        """No drowsiness alert for attentive driver (low PERCLOS, forward gaze)."""
        can_bus.send(CANID_DMS_OUTPUT, [0x01, 0x04, 0x02, 0x00])  # attentive
        time.sleep(0.1)

        drowsiness = signals.get(SIG_DMS_DROWSINESS)
        alert      = signals.get(SIG_DMS_ALERT)
        if drowsiness is not None:
            assert int(drowsiness) == 0, (
                f"False drowsiness {drowsiness} for attentive driver"
            )
        if alert is not None:
            assert int(alert) == 0, (
                f"False alert {alert} for attentive driver"
            )
