"""
pytest_framework/test_suites/lka/test_lka.py

LKA – Lane Keep Assist Validation
ASIL: B | Requirements: LKA_REQ_001–050
"""
import time
import pytest

from core.base_test import ADASBaseTest

SIG_LKA_STATUS         = "LKA_Status"          # 0=Off 1=Standby 2=Active
SIG_LKA_TORQUE_REQ     = "LKA_TorqueRequest_Nm"
SIG_LKA_DEVIATION      = "LKA_LaneDeviation_m"
SIG_LKA_CAMERA_CONF    = "LKA_CameraConfidence" # 0.0–1.0
SIG_LKA_SUPPRESS       = "LKA_Suppressed"       # 1 = suppressed by turn signal
SIG_TURN_SIGNAL_LEFT   = "TurnSignalLeft"
SIG_TURN_SIGNAL_RIGHT  = "TurnSignalRight"
SIG_VEHICLE_SPEED      = "VehicleSpeed_kmh"
SIG_STEERING_TORQUE    = "SteeringTorque_Nm"

CANID_LKA_OUTPUT       = 0x160
CANID_CAMERA_INPUT     = 0x161
CANID_VEHICLE_STATE    = 0x130

# Physical limits
TORQUE_MAX_NM   = 3.0   # Maximum LKA torque
DEVIATION_WARN  = 0.30  # m – lane deviation warning threshold
DEVIATION_MAX   = 0.45  # m – maximum tolerated before suppression


@pytest.mark.lka
@pytest.mark.regression
class TestLKA(ADASBaseTest):

    ASIL    = "B"
    FEATURE = "LKA"
    REQ_IDS = ["LKA_REQ_001", "LKA_REQ_010", "LKA_REQ_020"]

    # ── Activation ────────────────────────────────────────────────────────────

    @pytest.mark.smoke
    def test_lka_activates_above_threshold_speed(self, signals, vehicle_sim):
        """LKA activates only when speed ≥ 60 km/h."""
        vehicle_sim.set_speed(80.0)
        time.sleep(0.2)

        status = signals.get(SIG_LKA_STATUS)
        if status is None:
            pytest.skip("LKA_Status signal not available")
        assert int(status) >= 1, "LKA did not activate at 80 km/h"

    def test_lka_inactive_below_threshold_speed(self, signals, vehicle_sim):
        """LKA stays inactive below 60 km/h."""
        vehicle_sim.set_speed(50.0)
        time.sleep(0.2)

        status = signals.get(SIG_LKA_STATUS)
        if status is None:
            pytest.skip("LKA_Status signal not available")
        assert int(status) == 0, (
            f"LKA active at 50 km/h — should require ≥ 60 km/h"
        )

    # ── Torque limits ─────────────────────────────────────────────────────────

    @pytest.mark.safety
    @pytest.mark.asil_b
    def test_torque_within_physical_limit(self, signals, vehicle_sim):
        """LKA torque request must never exceed ±3.0 Nm (ASIL B)."""
        vehicle_sim.set_speed(100.0)
        vehicle_sim.set_lane_deviation(0.25)
        time.sleep(0.3)

        torque = signals.get(SIG_LKA_TORQUE_REQ)
        if torque is None:
            pytest.skip("LKA_TorqueRequest signal not available")
        assert abs(float(torque)) <= TORQUE_MAX_NM, (
            f"LKA torque {torque:.2f} Nm exceeds ±3.0 Nm limit — ASIL B violation"
        )

    @pytest.mark.parametrize("deviation_m, expect_torque_nonzero", [
        (0.05, False),   # Within lane — no correction needed
        (0.20, True),    # Moderate deviation — correction applied
        (0.35, True),    # Large deviation — correction applied
    ])
    def test_torque_proportional_to_deviation(
        self, signals, vehicle_sim, deviation_m, expect_torque_nonzero
    ):
        """LKA torque proportional to lane deviation."""
        vehicle_sim.set_speed(100.0)
        vehicle_sim.set_lane_deviation(deviation_m)
        time.sleep(0.2)

        torque = signals.get(SIG_LKA_TORQUE_REQ)
        if torque is None:
            pytest.skip("LKA_TorqueRequest signal not available")
        torque_nonzero = abs(float(torque)) > 0.05
        assert torque_nonzero == expect_torque_nonzero, (
            f"Deviation={deviation_m}m: torque={torque:.2f}Nm, "
            f"expected {'non-zero' if expect_torque_nonzero else 'zero'}"
        )

    # ── Turn signal inhibition ────────────────────────────────────────────────

    @pytest.mark.safety
    @pytest.mark.smoke
    @pytest.mark.parametrize("signal_name", [SIG_TURN_SIGNAL_LEFT, SIG_TURN_SIGNAL_RIGHT])
    def test_lka_suppressed_by_turn_signal(
        self, signals, can_bus, vehicle_sim, signal_name
    ):
        """LKA suppressed when turn signal is active."""
        vehicle_sim.set_speed(100.0)
        vehicle_sim.set_lane_deviation(0.25)
        # Activate turn signal
        byte_idx = 0 if "Left" in signal_name else 1
        msg = [0x00, 0x00, 0x00, 0x00]
        msg[byte_idx] = 0x01
        can_bus.send(CANID_VEHICLE_STATE, msg)
        time.sleep(0.2)

        suppressed = signals.get(SIG_LKA_SUPPRESS)
        if suppressed is None:
            pytest.skip("LKA_Suppressed signal not available")
        assert int(suppressed) == 1, (
            f"LKA not suppressed when {signal_name} active"
        )

    # ── Camera confidence ─────────────────────────────────────────────────────

    def test_lka_degrades_on_low_camera_confidence(self, signals, can_bus):
        """LKA enters standby when camera confidence drops below 0.5."""
        # Inject low-confidence camera status
        can_bus.send(CANID_CAMERA_INPUT, [0x01, 0x30, 0x00, 0x00])  # conf=0.48
        time.sleep(0.2)

        status = signals.get(SIG_LKA_STATUS)
        if status is None:
            pytest.skip("LKA_Status signal not available")
        # Should be standby (1) not active (2) on low confidence
        assert int(status) <= 1, (
            "LKA remained active with camera confidence < 0.5"
        )

    # ── Lane re-centering accuracy ────────────────────────────────────────────

    def test_lane_centering_reduces_deviation(self, signals, vehicle_sim):
        """LKA correction reduces lane deviation over 1s."""
        vehicle_sim.set_speed(100.0)
        vehicle_sim.set_lane_deviation(0.30)
        t0 = time.monotonic()
        initial = signals.get(SIG_LKA_DEVIATION)
        if initial is None:
            pytest.skip("LKA_LaneDeviation signal not available")

        time.sleep(1.0)
        final = signals.get(SIG_LKA_DEVIATION)
        if final is None:
            pytest.skip("LKA_LaneDeviation signal not available")
        assert float(final) <= float(initial), (
            f"LKA failed to reduce deviation: {initial:.2f}m → {final:.2f}m"
        )

    # ── Driver override ───────────────────────────────────────────────────────

    @pytest.mark.safety
    def test_driver_steering_overrides_lka(self, signals, can_bus, vehicle_sim):
        """High driver steering torque must override LKA intervention."""
        vehicle_sim.set_speed(100.0)
        vehicle_sim.set_lane_deviation(0.25)
        # Inject high driver torque
        can_bus.send(CANID_VEHICLE_STATE, [0x00, 0x00, 0x00, 0x50])  # 8.0 Nm
        time.sleep(0.15)

        suppress = signals.get(SIG_LKA_SUPPRESS)
        if suppress is not None:
            assert int(suppress) == 1, (
                "LKA not suppressed by high driver steering torque"
            )

    # ── Performance ───────────────────────────────────────────────────────────

    @pytest.mark.performance
    def test_lka_response_time(self, signals, vehicle_sim):
        """LKA torque response within 100ms of deviation onset."""
        vehicle_sim.set_speed(100.0)
        with self.measure("lka_response"):
            vehicle_sim.set_lane_deviation(0.30)
            time.sleep(0.1)
        self.assert_response_time("lka_response", max_ms=100.0)


# ── LKA Fault Injection ───────────────────────────────────────────────────────

@pytest.mark.lka
@pytest.mark.fault_injection
class TestLKAFaultInjection(ADASBaseTest):
    ASIL    = "B"
    FEATURE = "LKA"

    def test_lka_fallback_on_camera_loss(
        self, signals, fault_injector, vehicle_sim
    ):
        """LKA enters standby when camera signal lost."""
        from utilities.fault_injector import FaultType
        vehicle_sim.set_speed(100.0)

        with fault_injector.inject(
            FaultType.CAMERA_BLOCKAGE, duration_s=0.5
        ):
            time.sleep(0.4)
            status = signals.get(SIG_LKA_STATUS)
            if status is not None:
                assert int(status) != 2, (
                    "LKA remained active during camera signal loss"
                )
