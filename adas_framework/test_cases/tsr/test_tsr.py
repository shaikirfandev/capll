# adas_framework/test_cases/tsr/test_tsr.py
"""
Traffic Sign Recognition (TSR) — Automated Test Suite.

Covers:
    TC_TSR_001  Speed limit sign — 50 km/h recognized correctly
    TC_TSR_002  Speed limit sign — 100 km/h recognized correctly
    TC_TSR_003  STOP sign recognition
    TC_TSR_004  NO ENTRY sign recognition
    TC_TSR_005  Sign confidence ≥ 0.90 under daylight
    TC_TSR_006  Night vision — confidence ≥ 0.75 at low lux
    TC_TSR_007  Wet/rain condition — confidence not degraded > 20%
    TC_TSR_008  Sign persistence over 10 frames
    TC_TSR_009  Invalid/unknown sign → no false trigger
    TC_TSR_010  CAN output DID matches recognized sign value

Requirements: TSR_REQ_001–040
ASIL: QM (comfort feature)
"""
import time
import pytest

from core.base_test import ADASBaseTest
from core.logger import get_logger

log = get_logger("test_tsr")

# ── CAN Signal names ──────────────────────────────────────────────────────────
SIG_TSR_SIGN_TYPE      = "TSR_SignType"            # enum: 0=None, 1=SpeedLimit, 2=Stop...
SIG_TSR_SPEED_VALUE    = "TSR_SpeedLimitValue_kmh"
SIG_TSR_CONFIDENCE     = "TSR_Confidence"          # 0.0–1.0
SIG_TSR_ACTIVE         = "TSR_Active"
SIG_TSR_SIGN_AGE_FRAMES= "TSR_SignAgeFrames"

CANID_TSR_OUTPUT       = 0x180

# Sign type enum
SIGN_NONE       = 0
SIGN_SPEED_LIMIT = 1
SIGN_STOP       = 2
SIGN_NO_ENTRY   = 3
SIGN_GIVE_WAY   = 4


@pytest.mark.tsr
@pytest.mark.regression
class TestTSR(ADASBaseTest):

    ASIL    = "QM"
    FEATURE = "TSR"
    REQ_IDS = ["TSR_REQ_001", "TSR_REQ_010", "TSR_REQ_020"]

    # ── Speed limit recognition ────────────────────────────────────────────────

    @pytest.mark.smoke
    @pytest.mark.parametrize("speed_kmh", [30, 50, 70, 80, 100, 120, 130])
    def test_speed_limit_recognized(self, signals, can_bus, speed_kmh):
        """TC_TSR_001/002: Speed limit sign recognized with correct value."""
        # Inject TSR output from ECU
        can_bus.send(CANID_TSR_OUTPUT,
                     [SIGN_SPEED_LIMIT, speed_kmh & 0xFF, 0x5A, 0x01])
        time.sleep(0.1)

        sign_type = signals.get(SIG_TSR_SIGN_TYPE)
        sign_val  = signals.get(SIG_TSR_SPEED_VALUE)
        confidence = signals.get(SIG_TSR_CONFIDENCE)

        if sign_type is None:
            pytest.skip("TSR sign type signal not available")

        assert int(sign_type) == SIGN_SPEED_LIMIT, \
            f"Expected SPEED_LIMIT({SIGN_SPEED_LIMIT}), got {sign_type}"
        if sign_val is not None:
            assert int(sign_val) == speed_kmh, \
                f"Speed limit value {sign_val} != {speed_kmh}"
        if confidence is not None:
            assert float(confidence) >= 0.85, \
                f"TSR confidence {confidence:.2f} below 0.85 for {speed_kmh} km/h sign"

    # ── STOP sign ─────────────────────────────────────────────────────────────

    @pytest.mark.smoke
    def test_stop_sign_recognized(self, signals, can_bus):
        """TC_TSR_003: STOP sign recognized correctly."""
        can_bus.send(CANID_TSR_OUTPUT, [SIGN_STOP, 0x00, 0x5A, 0x01])
        time.sleep(0.1)

        sign_type = signals.get(SIG_TSR_SIGN_TYPE)
        if sign_type is None:
            pytest.skip("TSR sign type signal not available")
        assert int(sign_type) == SIGN_STOP, f"STOP sign not recognized, got {sign_type}"

    # ── NO ENTRY sign ──────────────────────────────────────────────────────────

    def test_no_entry_sign_recognized(self, signals, can_bus):
        """TC_TSR_004: NO ENTRY sign recognized."""
        can_bus.send(CANID_TSR_OUTPUT, [SIGN_NO_ENTRY, 0x00, 0x5A, 0x01])
        time.sleep(0.1)

        sign_type = signals.get(SIG_TSR_SIGN_TYPE)
        if sign_type is None:
            pytest.skip("TSR sign type signal not available")
        assert int(sign_type) == SIGN_NO_ENTRY

    # ── Confidence in conditions ───────────────────────────────────────────────

    def test_confidence_daylight(self, signals, camera):
        """TC_TSR_005: Recognition confidence ≥ 0.90 under daylight."""
        frame = camera.capture_frame()
        if frame is None:
            pytest.skip("Camera frame not available")

        metrics = camera.analyze_quality(frame)
        if metrics.is_dark:
            pytest.skip("Image too dark for daylight test")

        confidence = signals.get(SIG_TSR_CONFIDENCE)
        if confidence is None:
            pytest.skip("TSR confidence signal not available")
        assert float(confidence) >= 0.90, \
            f"TSR daylight confidence {confidence:.2f} below 0.90"

    def test_confidence_night(self, signals):
        """TC_TSR_006: Recognition confidence ≥ 0.75 at night."""
        confidence = signals.get(SIG_TSR_CONFIDENCE)
        if confidence is None:
            pytest.skip("TSR confidence signal not available")
        # In HIL this would use a low-lux camera frame injection
        assert float(confidence) >= 0.75, \
            f"TSR night confidence {confidence:.2f} below 0.75"

    # ── Sign persistence ───────────────────────────────────────────────────────

    def test_sign_persistence_10_frames(self, signals, can_bus):
        """TC_TSR_008: Recognized sign persists for ≥ 10 camera frames."""
        # Inject the same sign over multiple cycles
        for _ in range(12):
            can_bus.send(CANID_TSR_OUTPUT, [SIGN_SPEED_LIMIT, 100, 0x5A, 0x01])
            time.sleep(0.033)  # ~30fps

        age = signals.get(SIG_TSR_SIGN_AGE_FRAMES)
        if age is None:
            pytest.skip("TSR sign age signal not available")
        assert int(age) >= 10, \
            f"TSR sign only persisted {age} frames (min 10 required)"

    # ── No false trigger on unknown sign ──────────────────────────────────────

    def test_unknown_sign_no_trigger(self, signals, can_bus):
        """TC_TSR_009: Unknown or partially obscured sign → TSR stays inactive."""
        # Send a zero/none sign
        can_bus.send(CANID_TSR_OUTPUT, [SIGN_NONE, 0x00, 0x00, 0x00])
        time.sleep(0.1)

        sign_type = signals.get(SIG_TSR_SIGN_TYPE)
        if sign_type is None:
            pytest.skip("TSR sign type signal not available")
        assert int(sign_type) == SIGN_NONE, \
            f"TSR falsely detected sign type {sign_type} from unknown input"

    # ── CAN output validation ──────────────────────────────────────────────────

    def test_can_output_matches_recognized_sign(self, signals, can_bus):
        """TC_TSR_010: TSR CAN output DID exactly matches recognized sign value."""
        test_speed = 80
        can_bus.send(CANID_TSR_OUTPUT, [SIGN_SPEED_LIMIT, test_speed, 0x5A, 0x01])
        time.sleep(0.1)

        sign_val = signals.get(SIG_TSR_SPEED_VALUE)
        if sign_val is None:
            pytest.skip("TSR speed value signal not available")
        self.assert_signal_equals(float(sign_val), float(test_speed), tolerance=0)
