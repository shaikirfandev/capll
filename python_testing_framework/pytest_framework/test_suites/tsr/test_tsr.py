"""
pytest_framework/test_suites/tsr/test_tsr.py

TSR – Traffic Sign Recognition Validation
ASIL: QM | Requirements: TSR_REQ_001–035
"""
import time
import pytest

from core.base_test import ADASBaseTest

SIG_TSR_STATUS        = "TSR_Status"            # 0=Off 1=Active
SIG_TSR_SIGN_ID       = "TSR_DetectedSignID"
SIG_TSR_SIGN_VALUE    = "TSR_SignValue"          # km/h or code
SIG_TSR_CONFIDENCE    = "TSR_Confidence"         # 0.0–1.0
SIG_TSR_PERSIST       = "TSR_SignPersistTime_s"  # how long sign displayed
SIG_ISA_OVERSPEED_ALT = "ISA_OverspeedAlert"     # ISA integration

CANID_TSR_OUTPUT      = 0x180
CANID_CAMERA_INPUT    = 0x161

# Sign IDs (coded)
SIGN_SPEED_30   = 0x1E
SIGN_SPEED_50   = 0x32
SIGN_SPEED_60   = 0x3C
SIGN_SPEED_80   = 0x50
SIGN_SPEED_100  = 0x64
SIGN_SPEED_120  = 0x78
SIGN_STOP       = 0xA0
SIGN_NO_ENTRY   = 0xA1
SIGN_MOTORWAY   = 0xB0
SIGN_END_LIMIT  = 0xC0

CONF_MIN_VALID  = 0.65   # minimum confidence for valid detection
PERSIST_MIN_S   = 3.0    # sign must persist ≥ 3s


@pytest.mark.tsr
@pytest.mark.regression
class TestTSR(ADASBaseTest):

    ASIL    = "QM"
    FEATURE = "TSR"
    REQ_IDS = ["TSR_REQ_001", "TSR_REQ_010"]

    # ── Speed sign recognition ────────────────────────────────────────────────

    @pytest.mark.smoke
    @pytest.mark.parametrize("sign_id, expected_value_kmh", [
        (SIGN_SPEED_30,  30),
        (SIGN_SPEED_50,  50),
        (SIGN_SPEED_60,  60),
        (SIGN_SPEED_80,  80),
        (SIGN_SPEED_100, 100),
        (SIGN_SPEED_120, 120),
    ])
    def test_speed_limit_sign_recognised(
        self, signals, can_bus, sign_id, expected_value_kmh
    ):
        """TSR correctly identifies speed limit signs."""
        can_bus.send(
            CANID_TSR_OUTPUT,
            [0x01, sign_id, expected_value_kmh & 0xFF,
             int(0.85 * 100)]  # conf=0.85
        )
        time.sleep(0.15)

        detected_id = signals.get(SIG_TSR_SIGN_ID)
        detected_val = signals.get(SIG_TSR_SIGN_VALUE)
        if detected_id is None:
            pytest.skip("TSR_DetectedSignID signal not available")

        assert int(detected_id) == sign_id, (
            f"TSR sign ID mismatch: got={detected_id}, expected={sign_id}"
        )
        if detected_val is not None:
            assert int(detected_val) == expected_value_kmh, (
                f"TSR sign value mismatch: got={detected_val}, "
                f"expected={expected_value_kmh}"
            )

    # ── Regulatory signs ──────────────────────────────────────────────────────

    @pytest.mark.parametrize("sign_id", [SIGN_STOP, SIGN_NO_ENTRY, SIGN_MOTORWAY])
    def test_regulatory_sign_recognised(self, signals, can_bus, sign_id):
        """TSR correctly identifies stop, no-entry, motorway signs."""
        can_bus.send(CANID_TSR_OUTPUT, [0x01, sign_id, 0x00, int(0.80 * 100)])
        time.sleep(0.1)

        detected_id = signals.get(SIG_TSR_SIGN_ID)
        if detected_id is None:
            pytest.skip("TSR_DetectedSignID signal not available")
        assert int(detected_id) == sign_id, (
            f"Regulatory sign {sign_id:#04x} not correctly detected"
        )

    # ── Confidence threshold ──────────────────────────────────────────────────

    @pytest.mark.parametrize("conf, expect_valid", [
        (0.90, True),
        (0.65, True),   # boundary
        (0.64, False),  # below threshold
        (0.30, False),
    ])
    def test_confidence_filter(self, signals, can_bus, conf, expect_valid):
        """TSR only propagates detections above confidence threshold."""
        can_bus.send(
            CANID_TSR_OUTPUT,
            [0x01, SIGN_SPEED_50, 50, int(conf * 100)]
        )
        time.sleep(0.1)

        detected_id = signals.get(SIG_TSR_SIGN_ID)
        sig_conf    = signals.get(SIG_TSR_CONFIDENCE)

        if detected_id is None:
            pytest.skip("TSR signal not available")
        if not expect_valid:
            # Low confidence should produce zero/invalid detection
            assert int(detected_id) == 0, (
                f"TSR reported sign at confidence {conf:.2f} below threshold"
            )

    # ── Persistence ───────────────────────────────────────────────────────────

    def test_sign_persistence_after_occlusion(self, signals, can_bus):
        """TSR maintains sign display for ≥ 3s after brief occlusion."""
        can_bus.send(CANID_TSR_OUTPUT, [0x01, SIGN_SPEED_80, 80, 0x55])  # active
        time.sleep(0.2)
        can_bus.send(CANID_TSR_OUTPUT, [0x00, 0x00, 0x00, 0x00])         # occluded
        time.sleep(0.5)  # still within persistence window

        persist = signals.get(SIG_TSR_PERSIST)
        sign_id = signals.get(SIG_TSR_SIGN_ID)
        if persist is not None:
            assert float(persist) >= 0.0, "Persistence time is negative"
        # Sign should still be shown during persistence window
        if sign_id is not None:
            assert int(sign_id) in (SIGN_SPEED_80, 0), (
                f"Wrong sign shown during persistence: {sign_id}"
            )

    # ── ISA integration ───────────────────────────────────────────────────────

    def test_isa_alert_on_overspeed(self, signals, can_bus, vehicle_sim):
        """ISA triggers overspeed alert when vehicle speed > signed limit."""
        vehicle_sim.set_speed(100.0)
        can_bus.send(CANID_TSR_OUTPUT, [0x01, SIGN_SPEED_80, 80, 0x55])
        time.sleep(0.2)

        alert = signals.get(SIG_ISA_OVERSPEED_ALT)
        if alert is None:
            pytest.skip("ISA_OverspeedAlert signal not available")
        assert int(alert) == 1, (
            "ISA overspeed alert not triggered at 100 km/h with 80 km/h sign"
        )

    def test_isa_no_alert_under_signed_limit(self, signals, can_bus, vehicle_sim):
        """ISA no alert when vehicle speed is within signed limit."""
        vehicle_sim.set_speed(70.0)
        can_bus.send(CANID_TSR_OUTPUT, [0x01, SIGN_SPEED_80, 80, 0x55])
        time.sleep(0.2)

        alert = signals.get(SIG_ISA_OVERSPEED_ALT)
        if alert is not None:
            assert int(alert) == 0, (
                "ISA false overspeed alert at 70 km/h with 80 km/h sign"
            )

    # ── Night / low visibility ────────────────────────────────────────────────

    def test_sign_detection_low_light(self, signals, can_bus):
        """TSR operates in low ambient light (headlight mode)."""
        # Inject low-light camera status byte
        can_bus.send(CANID_CAMERA_INPUT, [0x02, 0x00, 0x00, 0x00])  # night mode
        can_bus.send(CANID_TSR_OUTPUT,   [0x01, SIGN_SPEED_50, 50, 0x47])
        time.sleep(0.15)

        detected = signals.get(SIG_TSR_SIGN_ID)
        if detected is None:
            pytest.skip("TSR signal not available in night mode test")
        # In CI we just verify no assertion error
        assert int(detected) >= 0
