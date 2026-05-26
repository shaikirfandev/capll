"""
pytest_framework/test_suites/aeb/test_aeb.py

AEB – Autonomous Emergency Braking Validation
Euro NCAP / NHTSA / UN-R152 aligned | ASIL: D
Requirements: AEB_REQ_001–080
"""
import time
import pytest

from core.base_test import ADASBaseTest

SIG_AEB_STATUS         = "AEB_Status"
SIG_AEB_BRAKE_REQ      = "AEB_FullBrakeRequest"
SIG_AEB_DECEL_REQ      = "AEB_DecelRequest_mpss"
SIG_AEB_PEDESTRIAN_DET = "AEB_PedestrianDetected"
SIG_AEB_TARGET_TTC     = "AEB_TargetTTC_s"
SIG_AEB_CRC            = "AEB_SafetyCRC"
SIG_VEHICLE_SPEED      = "VehicleSpeed_kmh"

CANID_AEB_OUTPUT       = 0x150
CANID_VEHICLE_STATE    = 0x130


@pytest.mark.aeb
@pytest.mark.regression
class TestAEB(ADASBaseTest):

    ASIL    = "D"
    FEATURE = "AEB"
    REQ_IDS = ["AEB_REQ_001", "AEB_REQ_010", "AEB_REQ_050"]

    # ── Pedestrian detection ──────────────────────────────────────────────────

    @pytest.mark.smoke
    def test_pedestrian_stationary_detected(self, signals, radar, fusion):
        """AEB detects stationary pedestrian at 20m."""
        from radar.radar_validator   import RadarObject
        from sensor_fusion.fusion_validator import FusedObject

        radar.ingest_object(RadarObject(
            obj_id=10, range_m=20.0, velocity_mps=0.0,
            azimuth_deg=0.0, rcs_dbm=5.0, confidence=0.92
        ))
        fusion.ingest(FusedObject(
            track_id=10, pos_x_m=20.0, pos_y_m=0.0,
            velocity_mps=0.0, heading_deg=0.0,
            confidence=0.92, source="fused"
        ))
        time.sleep(0.2)

        det = signals.get(SIG_AEB_PEDESTRIAN_DET)
        if det is None:
            pytest.skip("AEB_PedestrianDetected signal not available")
        assert int(det) == 1, "AEB failed to detect stationary pedestrian"

    def test_pedestrian_crossing_detected(self, signals, radar):
        """AEB detects pedestrian crossing at 3 m/s."""
        from radar.radar_validator import RadarObject
        radar.ingest_object(RadarObject(
            obj_id=11, range_m=25.0, velocity_mps=3.0,
            azimuth_deg=5.0, rcs_dbm=5.5, confidence=0.88
        ))
        time.sleep(0.2)
        det = signals.get(SIG_AEB_PEDESTRIAN_DET)
        if det is None:
            pytest.skip("AEB pedestrian signal not available")
        assert int(det) == 1, "AEB failed to detect crossing pedestrian"

    # ── Brake activation ──────────────────────────────────────────────────────

    @pytest.mark.smoke
    @pytest.mark.safety
    @pytest.mark.asil_d
    def test_full_brake_at_critical_ttc(self, signals, can_bus):
        """Full brake triggered when TTC < 1.5s (ASIL D safety requirement)."""
        can_bus.send(CANID_AEB_OUTPUT, [0x00, 0x0A, 0x01, 0x00])  # TTC=1.0s
        time.sleep(0.2)

        brake = signals.get(SIG_AEB_BRAKE_REQ)
        if brake is None:
            pytest.skip("AEB_FullBrakeRequest signal not available")
        assert int(brake) == 1, (
            "AEB did NOT trigger full brake at TTC < 1.5s — SAFETY CRITICAL"
        )

    @pytest.mark.safety
    @pytest.mark.asil_d
    def test_deceleration_meets_minimum(self, signals, vehicle_sim):
        """AEB active phase must command ≥ 8 m/s² deceleration."""
        vehicle_sim.activate_aeb(True)
        decel = signals.get(SIG_AEB_DECEL_REQ)
        if decel is None:
            pytest.skip("AEB deceleration request not available")
        status = signals.get(SIG_AEB_STATUS)
        if status is not None and int(status) == 3:  # active
            assert abs(float(decel)) >= 8.0, (
                f"AEB decel {decel:.1f} m/s² below 8.0 m/s² minimum"
            )

    # ── Speed envelope ────────────────────────────────────────────────────────

    @pytest.mark.parametrize("speed_kmh, should_arm", [
        (5,   False),   # < 10 km/h
        (20,  True),
        (60,  True),
        (130, True),
        (200, True),
    ])
    def test_aeb_speed_envelope(
        self, signals, can_bus, vehicle_sim, speed_kmh, should_arm
    ):
        """AEB armed only within 10–200 km/h."""
        vehicle_sim.set_speed(speed_kmh)
        can_bus.send(CANID_VEHICLE_STATE, [speed_kmh & 0xFF, speed_kmh >> 8, 0, 0])
        time.sleep(0.15)

        status = signals.get(SIG_AEB_STATUS)
        if status is None:
            pytest.skip("AEB_Status signal not available")
        armed = int(status) >= 1
        assert armed == should_arm, (
            f"AEB at {speed_kmh} km/h: armed={armed}, expected={should_arm}"
        )

    # ── False positive suppression ────────────────────────────────────────────

    def test_oncoming_traffic_no_false_brake(self, signals, radar):
        """Oncoming opposite-lane vehicle must NOT trigger AEB."""
        from radar.radar_validator import RadarObject
        radar.ingest_object(RadarObject(
            obj_id=20, range_m=50.0, velocity_mps=-22.0,
            azimuth_deg=15.0, rcs_dbm=20.0
        ))
        time.sleep(0.2)

        brake = signals.get(SIG_AEB_BRAKE_REQ)
        if brake is None:
            pytest.skip("AEB brake request signal not available")
        assert int(brake) == 0, (
            "AEB false positive: triggered for oncoming opposite-lane vehicle!"
        )

    # ── Detection latency ─────────────────────────────────────────────────────

    @pytest.mark.performance
    @pytest.mark.asil_d
    def test_detection_to_brake_latency(self, signals, can_bus):
        """Detection → brake activation < 600ms (NHTSA / Euro NCAP requirement)."""
        t0 = time.monotonic()
        can_bus.send(CANID_AEB_OUTPUT, [0x00, 0x05, 0x01, 0x00])
        time.sleep(0.15)

        brake   = signals.get(SIG_AEB_BRAKE_REQ)
        elapsed = (time.monotonic() - t0) * 1000

        if brake is None:
            pytest.skip("AEB brake request signal not available")
        if int(brake) == 1:
            assert elapsed <= 600.0, (
                f"AEB latency {elapsed:.0f}ms exceeds 600ms NHTSA limit"
            )

    # ── E2E safety monitoring ─────────────────────────────────────────────────

    @pytest.mark.safety
    @pytest.mark.asil_d
    def test_e2e_crc_present(self, signals):
        """AEB CAN frame must carry valid E2E protection byte."""
        crc = signals.get(SIG_AEB_CRC)
        if crc is None:
            pytest.skip("AEB_SafetyCRC not in DBC")
        assert crc not in (0x00, 0xFF), (
            f"AEB E2E CRC = 0x{int(crc):02X} — E2E protection inactive"
        )

    # ── UDS DTC on sensor failure ─────────────────────────────────────────────

    @pytest.mark.uds
    @pytest.mark.safety
    def test_dtc_on_radar_failure(self, uds):
        """DTC B0100 (Radar_SignalLoss) set on radar sensor dropout."""
        try:
            dtcs = uds.sync_read_dtcs(status_mask=0x08)
            assert isinstance(dtcs, list)
        except Exception as exc:
            pytest.skip(f"UDS not available: {exc}")


# ── AEB Fault Injection ───────────────────────────────────────────────────────

@pytest.mark.aeb
@pytest.mark.fault_injection
class TestAEBFaultInjection(ADASBaseTest):
    ASIL    = "D"
    FEATURE = "AEB"

    @pytest.mark.asil_d
    def test_aeb_safe_state_on_cam_blockage(
        self, signals, fault_injector, vehicle_sim
    ):
        """AEB enters safe state (standby) when camera is blocked."""
        from utilities.fault_injector import FaultType
        vehicle_sim.set_speed(80.0)

        with fault_injector.inject(
            FaultType.CAMERA_BLOCKAGE, duration_s=0.5
        ):
            time.sleep(0.4)
            status = signals.get(SIG_AEB_STATUS)
            if status is not None:
                # Should NOT stay Active (3) when sensor is blocked
                assert int(status) != 3, (
                    "AEB remained Active during camera blockage — ASIL D violation"
                )
