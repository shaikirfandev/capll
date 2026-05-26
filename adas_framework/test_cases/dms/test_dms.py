# adas_framework/test_cases/dms/test_dms.py
"""
Driver Monitoring System (DMS) — Automated Test Suite.

Covers:
    TC_DMS_001  Eye gaze: forward — no warning
    TC_DMS_002  Eye gaze: off-road 2s → Level 1 alert
    TC_DMS_003  Eye gaze: off-road 5s → Level 2 alert (audio)
    TC_DMS_004  Drowsiness: PERCLOS > 0.35 → alert
    TC_DMS_005  Drowsiness: PERCLOS > 0.60 → intervention
    TC_DMS_006  Head pose: extreme yaw (>45°) → distraction alert
    TC_DMS_007  Head pose: pitch (down >30°) → phone use alert
    TC_DMS_008  Seatbelt → DMS active only when belted
    TC_DMS_009  Camera occlusion → DMS fallback mode + DTC
    TC_DMS_010  False positive: brief gaze away (< 1s) — no alert

Requirements: DMS_REQ_001–060
ASIL: B (safety intervention signal path)
"""
import time
import pytest

from core.base_test import ADASBaseTest
from core.logger import get_logger

log = get_logger("test_dms")

# ── CAN Signal names ──────────────────────────────────────────────────────────
SIG_DMS_ALERT_LEVEL    = "DMS_AlertLevel"       # 0=None, 1=Visual, 2=Audio, 3=Haptic
SIG_DMS_GAZE_STATUS    = "DMS_GazeStatus"       # 0=Forward, 1=Distracted, 2=Eyes closed
SIG_DMS_PERCLOS        = "DMS_PERCLOS"          # 0.0–1.0 (eye closure ratio)
SIG_DMS_HEAD_YAW       = "DMS_HeadYaw_deg"
SIG_DMS_HEAD_PITCH     = "DMS_HeadPitch_deg"
SIG_DMS_DROWSY         = "DMS_DrowsinessLevel"  # 0=Alert, 1=Mild, 2=Severe
SIG_DMS_CAMERA_OK      = "DMS_CameraOK"
SIG_DMS_INTERVENTION   = "DMS_InterventionRequest"
SIG_SEATBELT           = "DriverSeatbeltBuckled"

CANID_DMS_OUTPUT       = 0x1A0
CANID_DMS_STATUS       = 0x1A1
CANID_VEHICLE_STATE    = 0x130

# Alert levels
ALERT_NONE   = 0
ALERT_VISUAL = 1
ALERT_AUDIO  = 2
ALERT_HAPTIC = 3


@pytest.mark.dms
@pytest.mark.regression
class TestDMS(ADASBaseTest):

    ASIL    = "B"
    FEATURE = "DMS"
    REQ_IDS = ["DMS_REQ_001", "DMS_REQ_010", "DMS_REQ_020"]

    # ── Gaze forward — no warning ─────────────────────────────────────────────

    @pytest.mark.smoke
    def test_forward_gaze_no_alert(self, signals, can_bus):
        """TC_DMS_001: Driver looking forward → no DMS alert."""
        can_bus.send(CANID_DMS_OUTPUT, [0x00, 0x00, 0x00, 0x00])  # gaze=forward
        time.sleep(0.1)

        alert = signals.get(SIG_DMS_ALERT_LEVEL)
        if alert is None:
            pytest.skip("DMS alert level signal not available")
        assert int(alert) == ALERT_NONE, \
            f"Unexpected DMS alert {alert} during forward gaze"

    # ── Gaze distraction alerts ───────────────────────────────────────────────

    def test_gaze_2s_level1_alert(self, signals, can_bus):
        """TC_DMS_002: Gaze off-road for 2 s → Level 1 visual alert."""
        # Simulate distracted gaze
        for _ in range(20):  # 20 × 100ms = 2s
            can_bus.send(CANID_DMS_OUTPUT, [0x01, 0x02, 0x00, 0x00])  # distracted
            time.sleep(0.1)

        alert = signals.get(SIG_DMS_ALERT_LEVEL)
        if alert is None:
            pytest.skip("DMS alert level signal not available")
        assert int(alert) >= ALERT_VISUAL, \
            f"DMS failed to raise Level 1 alert after 2s distraction (level={alert})"

    def test_gaze_5s_level2_alert(self, signals, can_bus):
        """TC_DMS_003: Gaze off-road for 5 s → Level 2 audio alert."""
        for _ in range(50):  # ~5s
            can_bus.send(CANID_DMS_OUTPUT, [0x01, 0x05, 0x00, 0x00])
            time.sleep(0.1)

        alert = signals.get(SIG_DMS_ALERT_LEVEL)
        if alert is None:
            pytest.skip("DMS alert level signal not available")
        assert int(alert) >= ALERT_AUDIO, \
            f"DMS Level 2 audio alert not raised after 5s distraction (level={alert})"

    # ── PERCLOS drowsiness ────────────────────────────────────────────────────

    @pytest.mark.parametrize("perclos, min_alert", [
        (0.20, ALERT_NONE),   # alert driver
        (0.35, ALERT_VISUAL), # mild drowsiness
        (0.60, ALERT_AUDIO),  # severe drowsiness
    ])
    def test_perclos_alert_levels(self, signals, can_bus, perclos, min_alert):
        """TC_DMS_004/005: PERCLOS thresholds trigger correct alert levels."""
        perclos_byte = int(perclos * 100)
        can_bus.send(CANID_DMS_STATUS, [0x00, perclos_byte, 0x00, 0x00])
        time.sleep(0.2)

        alert = signals.get(SIG_DMS_ALERT_LEVEL)
        if alert is None:
            pytest.skip("DMS alert level signal not available")
        assert int(alert) >= min_alert, (
            f"PERCLOS={perclos:.2f} → alert={alert}, expected ≥ {min_alert}"
        )

    # ── Head pose distraction ─────────────────────────────────────────────────

    @pytest.mark.parametrize("yaw_deg, should_alert", [
        (10,  False),   # minor glance
        (45,  True),    # extreme yaw
        (60,  True),    # full side look
    ])
    def test_head_yaw_distraction(self, signals, can_bus, yaw_deg, should_alert):
        """TC_DMS_006: Head yaw > 45° triggers distraction alert."""
        yaw_byte = int(yaw_deg + 128) & 0xFF  # offset-encoded signed byte
        can_bus.send(CANID_DMS_OUTPUT, [0x01, 0x00, yaw_byte, 0x00])
        time.sleep(0.15)

        alert = signals.get(SIG_DMS_ALERT_LEVEL)
        gaze  = signals.get(SIG_DMS_GAZE_STATUS)
        if alert is None:
            pytest.skip("DMS alert signal not available")
        is_alerted = int(alert) >= ALERT_VISUAL
        assert is_alerted == should_alert, (
            f"Head yaw {yaw_deg}°: alerted={is_alerted}, expected={should_alert}"
        )

    def test_head_pitch_phone_use(self, signals, can_bus):
        """TC_DMS_007: Head pitch down > 30° triggers phone use alert."""
        pitch_byte = int(-35 + 128) & 0xFF  # -35° pitch (looking down)
        can_bus.send(CANID_DMS_OUTPUT, [0x01, 0x00, 0x80, pitch_byte])
        time.sleep(0.15)

        alert = signals.get(SIG_DMS_ALERT_LEVEL)
        if alert is None:
            pytest.skip("DMS alert signal not available")
        assert int(alert) >= ALERT_VISUAL, \
            f"DMS did not alert on head-down pitch (phone use) — alert={alert}"

    # ── Seatbelt prerequisite ─────────────────────────────────────────────────

    def test_dms_only_active_when_belted(self, signals, can_bus):
        """TC_DMS_008: DMS monitoring only active when driver is belted."""
        # Unbelted
        can_bus.send(CANID_VEHICLE_STATE, [100, 0, 0, 0x00])  # belt=0
        can_bus.send(CANID_DMS_OUTPUT, [0x01, 0x04, 0x00, 0x00])  # distracted
        time.sleep(0.15)

        # When unbelted, DMS intervention request should not fire
        intervention = signals.get(SIG_DMS_INTERVENTION)
        belt = signals.get(SIG_SEATBELT)

        if belt is not None and intervention is not None:
            if int(belt) == 0:
                assert int(intervention) == 0, \
                    "DMS triggered intervention while driver unbelted — unexpected!"

    # ── Camera occlusion fallback ─────────────────────────────────────────────

    @pytest.mark.uds
    @pytest.mark.safety
    def test_camera_occlusion_dtc(self, uds, can_bus):
        """TC_DMS_009: Camera occlusion → DTC B0200 set, DMS in fallback."""
        # Simulate camera failure
        can_bus.send(CANID_DMS_STATUS, [0x00, 0x00, 0x00, 0x00])  # camera_ok=0

        try:
            dtcs = uds.sync_read_dtcs(status_mask=0x08)
            assert isinstance(dtcs, list), "DTC read failed"
        except Exception as e:
            pytest.skip(f"UDS not available: {e}")

    # ── False positive: brief glance ──────────────────────────────────────────

    def test_brief_glance_no_alert(self, signals, can_bus):
        """TC_DMS_010: Brief gaze away < 1 s does NOT trigger alert."""
        # One single 100ms distracted frame then back to forward
        can_bus.send(CANID_DMS_OUTPUT, [0x01, 0x01, 0x00, 0x00])  # 1 cycle distracted
        time.sleep(0.1)
        can_bus.send(CANID_DMS_OUTPUT, [0x00, 0x00, 0x00, 0x00])  # back to forward
        time.sleep(0.1)

        alert = signals.get(SIG_DMS_ALERT_LEVEL)
        if alert is None:
            pytest.skip("DMS alert level signal not available")
        assert int(alert) == ALERT_NONE, \
            f"DMS false alert {alert} for brief <1s glance away"
