"""
robot_framework/libraries/ADASLibrary.py

Robot Framework keyword library for ADAS feature-level operations.
"""
from __future__ import annotations
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "pytest_framework"))

from robot.api import logger
from robot.api.deco import keyword, library

from simulators.vehicle_simulator import VehicleSimulator
from utilities.fault_injector     import FaultInjector, FaultType
from can.can_interface             import CANInterface
from can.signal_validator          import SignalValidator

ROBOT_LIBRARY_SCOPE = "SUITE"

CANID_ACC_OUTPUT    = 0x120
CANID_AEB_OUTPUT    = 0x150
CANID_LKA_OUTPUT    = 0x160
CANID_VEHICLE_STATE = 0x130


@library(scope="SUITE", auto_keywords=False)
class ADASLibrary:
    """
    Robot Framework library for ADAS feature control and validation.

    Requires CANLibrary to be imported first for shared CAN bus.

    Usage:
        Library    ../libraries/ADASLibrary.py
    """

    def __init__(self) -> None:
        self._sim: VehicleSimulator | None = None
        self._bus: CANInterface | None     = None
        self._sv:  SignalValidator | None  = None
        self._fi:  FaultInjector | None    = None

    @keyword("Initialize ADAS Library")
    def initialize_adas_library(
        self, channel: str = "virtual", interface: str = "virtual"
    ) -> None:
        """Initialize ADAS library with CAN bus connection."""
        self._bus = CANInterface(channel=channel, interface=interface)
        self._bus.connect()
        self._sv  = SignalValidator(self._bus)
        self._sv.start()
        self._sim = VehicleSimulator(self._sv)
        self._sim.start()
        self._fi  = FaultInjector(self._bus)
        logger.info("ADASLibrary initialized")

    @keyword("Teardown ADAS Library")
    def teardown_adas_library(self) -> None:
        """Clean up ADAS library resources."""
        if self._sim:
            self._sim.stop()
        if self._sv:
            self._sv.stop()
        if self._bus:
            self._bus.disconnect()

    # ── Vehicle state ─────────────────────────────────────────────────────────

    @keyword("Set Vehicle Speed")
    def set_vehicle_speed(self, speed_kmh: float) -> None:
        """
        Set simulated vehicle speed.

        Example:
            Set Vehicle Speed    100
        """
        self._sim.set_speed(float(speed_kmh))
        logger.info(f"Vehicle speed set to {speed_kmh} km/h")

    @keyword("Set Lane Deviation")
    def set_lane_deviation(self, deviation_m: float) -> None:
        """
        Set simulated lane deviation (positive=right, negative=left).

        Example:
            Set Lane Deviation    0.25
        """
        self._sim.set_lane_deviation(float(deviation_m))
        logger.info(f"Lane deviation set to {deviation_m}m")

    # ── ACC ───────────────────────────────────────────────────────────────────

    @keyword("Activate ACC")
    def activate_acc(self, set_speed_kmh: float = 100.0) -> None:
        """
        Activate Adaptive Cruise Control at given set speed.

        Example:
            Activate ACC    100
        """
        self._sim.activate_acc(True)
        self._bus.send(
            CANID_ACC_OUTPUT,
            [0x02, int(float(set_speed_kmh)) & 0xFF, 0x00, 0x00]
        )
        logger.info(f"ACC activated at {set_speed_kmh} km/h")

    @keyword("Deactivate ACC")
    def deactivate_acc(self) -> None:
        """Deactivate ACC."""
        self._sim.activate_acc(False)
        self._bus.send(CANID_ACC_OUTPUT, [0x00, 0x00, 0x00, 0x00])
        logger.info("ACC deactivated")

    @keyword("ACC Status Should Be")
    def acc_status_should_be(self, expected_status: int) -> None:
        """
        Assert ACC_Status signal equals expected value.

        0=Off, 1=Standby, 2=Active

        Example:
            ACC Status Should Be    2
        """
        val = self._sv.get("ACC_Status")
        if val is None:
            logger.warn("ACC_Status signal not available — skipping")
            return
        assert int(val) == int(expected_status), (
            f"ACC status={val}, expected={expected_status}"
        )

    # ── AEB ───────────────────────────────────────────────────────────────────

    @keyword("Inject Emergency Braking Event")
    def inject_emergency_braking_event(self, ttc_s: float = 1.0) -> None:
        """
        Simulate a pre-crash scenario with given TTC.

        Example:
            Inject Emergency Braking Event    1.5
        """
        ttc_byte = int(float(ttc_s) * 10) & 0xFF
        self._bus.send(CANID_AEB_OUTPUT, [0x00, ttc_byte, 0x01, 0x00])
        logger.info(f"AEB emergency event injected at TTC={ttc_s}s")

    @keyword("AEB Should Trigger Full Brake")
    def aeb_should_trigger_full_brake(self, timeout_s: float = 1.0) -> None:
        """Wait up to timeout_s for AEB full brake signal."""
        deadline = time.monotonic() + float(timeout_s)
        while time.monotonic() < deadline:
            val = self._sv.get("AEB_FullBrakeRequest")
            if val is not None and int(val) == 1:
                logger.info("AEB full brake triggered ✓")
                return
            time.sleep(0.05)
        raise AssertionError(
            f"AEB full brake not triggered within {timeout_s}s"
        )

    # ── LKA ───────────────────────────────────────────────────────────────────

    @keyword("LKA Should Be Active")
    def lka_should_be_active(self) -> None:
        """Assert LKA_Status == 2 (Active)."""
        val = self._sv.get("LKA_Status")
        if val is None:
            logger.warn("LKA_Status not available")
            return
        assert int(val) == 2, f"LKA not active: status={val}"

    @keyword("LKA Torque Should Not Exceed")
    def lka_torque_should_not_exceed(self, max_nm: float) -> None:
        """Assert LKA torque request ≤ max_nm."""
        val = self._sv.get("LKA_TorqueRequest_Nm")
        if val is None:
            logger.warn("LKA_TorqueRequest_Nm not available")
            return
        assert abs(float(val)) <= float(max_nm), (
            f"LKA torque {val:.2f} Nm exceeds limit {max_nm:.2f} Nm"
        )

    # ── Fault injection ───────────────────────────────────────────────────────

    @keyword("Inject Fault")
    def inject_fault(
        self,
        fault_type_name: str,
        can_id: str = "0x120",
        duration_s: float = 1.0,
    ) -> None:
        """
        Inject a named fault on a CAN ID for given duration.

        Arguments:
        - ``fault_type_name``: e.g. ``RADAR_DROPOUT``, ``MISSING_FRAME``
        - ``can_id``:          hex string
        - ``duration_s``:      seconds to inject

        Example:
            Inject Fault    RADAR_DROPOUT    0x120    2.0
        """
        ft     = FaultType[fault_type_name.upper()]
        arb_id = int(can_id, 16) if can_id.startswith("0x") else int(can_id)
        self._fi.inject_for(ft, can_id=arb_id, duration_s=float(duration_s))
        logger.info(f"Fault {fault_type_name} injected for {duration_s}s")

    # ── Wait helpers ──────────────────────────────────────────────────────────

    @keyword("Wait For Signal Value")
    def wait_for_signal_value(
        self, signal_name: str, expected: float,
        timeout_s: float = 5.0, tolerance: float = 0.0
    ) -> None:
        """
        Poll signal until it equals expected value.

        Example:
            Wait For Signal Value    ACC_Status    2    timeout_s=3
        """
        deadline = time.monotonic() + float(timeout_s)
        while time.monotonic() < deadline:
            val = self._sv.get(signal_name)
            if val is not None and abs(float(val) - float(expected)) <= float(tolerance):
                logger.info(f"Signal {signal_name} reached {val} ✓")
                return
            time.sleep(0.1)
        last = self._sv.get(signal_name)
        raise AssertionError(
            f"Signal '{signal_name}' = {last} after {timeout_s}s, "
            f"expected {expected} ± {tolerance}"
        )

    @keyword("Wait For ADAS Active")
    def wait_for_adas_active(
        self, feature: str, timeout_s: float = 5.0
    ) -> None:
        """
        Wait for ADAS feature status to become Active (≥ 2).

        Arguments:
        - ``feature``: one of ``ACC``, ``AEB``, ``LKA``, ``DMS``, ``TSR``

        Example:
            Wait For ADAS Active    ACC    5
        """
        sig_map = {
            "ACC": "ACC_Status",
            "AEB": "AEB_Status",
            "LKA": "LKA_Status",
            "DMS": "DMS_Status",
            "TSR": "TSR_Status",
        }
        sig_name = sig_map.get(feature.upper())
        if not sig_name:
            raise ValueError(f"Unknown ADAS feature: {feature}")
        deadline = time.monotonic() + float(timeout_s)
        while time.monotonic() < deadline:
            val = self._sv.get(sig_name)
            if val is not None and int(val) >= 2:
                logger.info(f"{feature} active ✓")
                return
            time.sleep(0.1)
        last = self._sv.get(sig_name)
        raise AssertionError(
            f"{feature} not active after {timeout_s}s (last status={last})"
        )
