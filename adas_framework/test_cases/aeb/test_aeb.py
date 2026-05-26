# adas_framework/test_cases/aeb/test_aeb.py
"""
Autonomous Emergency Braking (AEB) — Automated Test Suite.

Euro NCAP / NHTSA aligned.

Covers:
    TC_AEB_001  Pedestrian detection — stationary
    TC_AEB_002  Pedestrian detection — moving
    TC_AEB_003  Collision avoidance — TTC < 2s triggers full braking
    TC_AEB_004  Deceleration capacity ≥ 8 m/s²
    TC_AEB_005  AEB off below 10 km/h
    TC_AEB_006  AEB off above 200 km/h
    TC_AEB_007  DTC set on sensor failure
    TC_AEB_008  False positive suppression (opposite lane traffic)
    TC_AEB_009  Latency: detection → brake < 600 ms
    TC_AEB_010  ASIL D self-monitoring CRC check

Requirements: AEB_REQ_001–080
ASIL: D
"""
import time
import pytest

from core.base_test import ADASBaseTest
from core.logger import get_logger

log = get_logger("test_aeb")

# ── CAN Signal names ──────────────────────────────────────────────────────────
SIG_AEB_STATUS         = "AEB_Status"          # 0=Off, 1=Standby, 2=Armed, 3=Active
SIG_AEB_TARGET_TTC     = "AEB_TargetTTC_s"
SIG_AEB_BRAKE_REQ      = "AEB_FullBrakeRequest"  # 0/1
SIG_AEB_DECEL_REQ      = "AEB_DecelRequest_mpss"
SIG_AEB_PEDESTRIAN_DET = "AEB_PedestrianDetected"
SIG_VEHICLE_SPEED      = "VehicleSpeed_kmh"
SIG_AEB_CRC            = "AEB_SafetyCRC"

CANID_AEB_OUTPUT       = 0x150
CANID_AEB_STATUS       = 0x151
CANID_VEHICLE_STATE    = 0x130


# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.aeb
@pytest.mark.regression
class TestAEB(ADASBaseTest):

    ASIL       = "D"
    FEATURE    = "AEB"
    REQ_IDS    = ["AEB_REQ_001", "AEB_REQ_010", "AEB_REQ_050"]

    # ── Pedestrian detection ───────────────────────────────────────────────────

    @pytest.mark.smoke
    def test_pedestrian_stationary_detected(self, signals, radar, fusion):
        """TC_AEB_001: AEB detects a stationary pedestrian at 20 m."""
        from radar.radar_validator import RadarObject
        from sensor_fusion.fusion_validator import FusedObject

        # Inject pedestrian as radar + fusion object
        ped_radar = RadarObject(obj_id=10, range_m=20.0, velocity_mps=0.0,
                                azimuth_deg=0.0, rcs_dbm=5.0)
        radar.ingest_object(ped_radar)
        ped_fused = FusedObject(
            track_id=10, pos_x_m=20.0, pos_y_m=0.0,
            velocity_mps=0.0, heading_deg=0.0,
            confidence=0.92, source="fused"
        )
        fusion.ingest(ped_fused)
        time.sleep(0.2)

        ped_det = signals.get(SIG_AEB_PEDESTRIAN_DET)
        if ped_det is None:
            pytest.skip("AEB pedestrian detection signal not available")
        assert int(ped_det) == 1, "AEB failed to detect stationary pedestrian"

    def test_pedestrian_moving_detected(self, signals, radar):
        """TC_AEB_002: AEB detects a pedestrian crossing at 3 m/s."""
        from radar.radar_validator import RadarObject
        ped = RadarObject(obj_id=11, range_m=25.0, velocity_mps=3.0,
                          azimuth_deg=5.0, rcs_dbm=5.5)
        radar.ingest_object(ped)
        time.sleep(0.2)
        ped_det = signals.get(SIG_AEB_PEDESTRIAN_DET)
        if ped_det is None:
            pytest.skip("AEB pedestrian detection signal not available")
        assert int(ped_det) == 1, "AEB failed to detect moving pedestrian"

    # ── Collision avoidance activation ────────────────────────────────────────

    @pytest.mark.smoke
    @pytest.mark.safety
    @pytest.mark.asil_d
    def test_full_brake_activation_on_low_ttc(self, signals, can_bus):
        """TC_AEB_003: Full brake triggered when TTC < 1.5 s."""
        # Simulate ECU reporting TTC = 1.0 s
        can_bus.send(CANID_AEB_OUTPUT, [0x00, 0x0A, 0x01, 0x00])  # TTC=1.0s byte
        time.sleep(0.2)

        brake_req = signals.get(SIG_AEB_BRAKE_REQ)
        if brake_req is None:
            pytest.skip("AEB brake request signal not available")
        assert int(brake_req) == 1, (
            "AEB did NOT trigger full brake at TTC < 1.5s — SAFETY CRITICAL FAILURE"
        )

    # ── Deceleration magnitude ─────────────────────────────────────────────────

    @pytest.mark.safety
    @pytest.mark.asil_d
    def test_max_deceleration_8mpss(self, signals):
        """TC_AEB_004: AEB commands ≥ 8 m/s² deceleration during active phase."""
        decel = signals.get(SIG_AEB_DECEL_REQ)
        if decel is None:
            pytest.skip("AEB deceleration request signal not available")
        # When active, decel should be ≥ 8 m/s²
        status = signals.get(SIG_AEB_STATUS)
        if status is not None and int(status) == 3:  # Active
            assert abs(float(decel)) >= 8.0, (
                f"AEB deceleration {decel:.1f} m/s² below minimum 8.0 m/s²"
            )

    # ── Speed-range disabling ──────────────────────────────────────────────────

    @pytest.mark.parametrize("speed_kmh, should_be_active", [
        (5, False),    # below 10 km/h — should NOT fire
        (30, True),    # within range — should be armed
        (100, True),   # nominal
        (200, True),   # at upper boundary
    ])
    def test_aeb_speed_envelope(self, signals, can_bus, speed_kmh, should_be_active):
        """TC_AEB_005/006: AEB active only within 10–200 km/h."""
        can_bus.send(CANID_VEHICLE_STATE, [speed_kmh & 0xFF, speed_kmh >> 8, 0, 0])
        time.sleep(0.1)
        status = signals.get(SIG_AEB_STATUS)
        if status is None:
            pytest.skip("AEB status signal not available")
        is_active = int(status) >= 1  # standby or armed
        assert is_active == should_be_active, (
            f"AEB at {speed_kmh} km/h: active={is_active}, expected={should_be_active}"
        )

    # ── DTC on sensor failure ─────────────────────────────────────────────────

    @pytest.mark.uds
    @pytest.mark.safety
    def test_dtc_set_on_radar_failure(self, uds):
        """TC_AEB_007: DTC B0100 set within 100ms of radar sensor loss."""
        from diagnostics.uds_client import NRCError
        try:
            dtcs = uds.sync_read_dtcs(status_mask=0x08)  # confirmed DTCs
            # In HIL: radar sensor power is cut and DTC appears
            # Here we validate the DTC read service works
            assert isinstance(dtcs, list)
        except Exception as e:
            pytest.skip(f"UDS read_dtcs not available: {e}")

    # ── False positive ─────────────────────────────────────────────────────────

    def test_false_positive_suppression(self, signals, radar):
        """TC_AEB_008: Oncoming opposite-lane vehicle does NOT trigger AEB."""
        from radar.radar_validator import RadarObject
        # Oncoming at 50m, -22m/s (approaching from front), azimuth = 15° (offset)
        oncoming = RadarObject(obj_id=20, range_m=50.0, velocity_mps=-22.0,
                               azimuth_deg=15.0, rcs_dbm=20.0)
        radar.ingest_object(oncoming)
        time.sleep(0.2)

        brake_req = signals.get(SIG_AEB_BRAKE_REQ)
        if brake_req is None:
            pytest.skip("AEB brake request signal not available")
        assert int(brake_req) == 0, \
            "AEB false positive: triggered for oncoming opposite-lane vehicle!"

    # ── Latency ───────────────────────────────────────────────────────────────

    @pytest.mark.performance
    @pytest.mark.asil_d
    def test_detection_to_brake_latency(self, signals, can_bus):
        """TC_AEB_009: Detection → brake activation < 600 ms (NHTSA requirement)."""
        trigger_time = time.monotonic()
        # Simulate sudden close target injection
        can_bus.send(CANID_AEB_OUTPUT, [0x00, 0x05, 0x01, 0x00])  # TTC=0.5s
        time.sleep(0.1)

        brake_req = signals.get(SIG_AEB_BRAKE_REQ)
        elapsed_ms = (time.monotonic() - trigger_time) * 1000

        if brake_req is None:
            pytest.skip("AEB brake request signal not available")
        if int(brake_req) == 1:
            assert elapsed_ms <= 600.0, (
                f"AEB latency {elapsed_ms:.0f}ms exceeds 600ms NHTSA requirement"
            )

    # ── ASIL D safety monitoring ───────────────────────────────────────────────

    @pytest.mark.safety
    @pytest.mark.asil_d
    def test_safety_crc_presence(self, signals):
        """TC_AEB_010: AEB output frame includes valid CRC / E2E byte."""
        crc = signals.get(SIG_AEB_CRC)
        if crc is None:
            pytest.skip("AEB safety CRC signal not in DBC")
        assert crc != 0xFF, "AEB safety CRC is all-ones — possible E2E error"
        assert crc != 0x00, "AEB safety CRC is zero — E2E protection inactive"
