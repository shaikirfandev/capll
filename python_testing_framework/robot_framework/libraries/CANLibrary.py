"""
robot_framework/libraries/CANLibrary.py

Robot Framework keyword library for CAN/CAN-FD bus operations.
Wraps pytest_framework/can/can_interface.py and signal_validator.py.
"""
from __future__ import annotations
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "pytest_framework"))

from robot.api import logger
from robot.api.deco import keyword, library

from can.can_interface    import CANInterface
from can.signal_validator import SignalValidator

ROBOT_LIBRARY_SCOPE = "SUITE"


@library(scope="SUITE", auto_keywords=False)
class CANLibrary:
    """
    Robot Framework library for CAN/CAN-FD vehicle bus interaction.

    Usage in robot file:
        Library    ../libraries/CANLibrary.py
    """

    def __init__(
        self,
        channel:   str = "virtual",
        interface: str = "virtual",
        bitrate:   int = 500_000,
        dbc_path:  str = "",
    ):
        self._channel   = channel
        self._interface = interface
        self._bitrate   = bitrate
        self._dbc_path  = dbc_path
        self._bus: CANInterface | None   = None
        self._sv:  SignalValidator | None = None

    # ── Setup / Teardown ──────────────────────────────────────────────────────

    @keyword("Connect To CAN Bus")
    def connect_to_can_bus(self) -> None:
        """Open CAN bus connection."""
        self._bus = CANInterface(
            channel=self._channel,
            interface=self._interface,
            bitrate=self._bitrate,
            dbc_path=self._dbc_path,
        )
        self._bus.connect()
        self._sv = SignalValidator(self._bus)
        self._sv.start()
        logger.info(f"CAN bus connected: {self._interface}/{self._channel}")

    @keyword("Disconnect From CAN Bus")
    def disconnect_from_can_bus(self) -> None:
        """Close CAN bus connection."""
        if self._sv:
            self._sv.stop()
        if self._bus:
            self._bus.disconnect()
        logger.info("CAN bus disconnected")

    # ── Send ──────────────────────────────────────────────────────────────────

    @keyword("Send CAN Frame")
    def send_can_frame(self, can_id: str, data: str) -> None:
        """
        Send a CAN frame.

        Arguments:
        - ``can_id``: hex string e.g. ``0x120``
        - ``data``:   space-separated hex bytes e.g. ``02 64 00 00``

        Example:
            Send CAN Frame    0x120    02 64 00 00
        """
        arb_id   = int(can_id, 16) if can_id.startswith("0x") else int(can_id)
        payload  = bytes(int(b, 16) for b in data.split())
        self._bus.send(arb_id, list(payload))
        logger.debug(f"Sent CAN {can_id} data={data}")

    @keyword("Send CAN Frame Periodically")
    def send_can_frame_periodically(
        self, can_id: str, data: str, interval_ms: int = 10
    ) -> None:
        """
        Start periodic CAN transmission.

        Arguments:
        - ``can_id``:      hex string
        - ``data``:        space-separated hex bytes
        - ``interval_ms``: transmit period in ms (default: 10)
        """
        arb_id  = int(can_id, 16) if can_id.startswith("0x") else int(can_id)
        payload = bytes(int(b, 16) for b in data.split())
        self._bus.send_periodic(arb_id, list(payload), interval_ms / 1000.0)
        logger.info(f"Periodic CAN {can_id} @ {interval_ms}ms started")

    # ── Receive ───────────────────────────────────────────────────────────────

    @keyword("Wait For CAN Frame")
    def wait_for_can_frame(
        self, can_id: str, timeout_ms: int = 1000
    ) -> dict:
        """
        Wait for a CAN frame with the given arbitration ID.

        Returns a dict with keys: ``id``, ``data``, ``timestamp``.
        Fails if not received within timeout.
        """
        arb_id = int(can_id, 16) if can_id.startswith("0x") else int(can_id)
        frame  = self._bus.wait_for_id(arb_id, timeout_ms=timeout_ms)
        if frame is None:
            raise AssertionError(
                f"CAN frame {can_id} not received within {timeout_ms}ms"
            )
        logger.info(f"Received CAN {can_id}: {list(frame.data)}")
        return {"id": frame.can_id, "data": list(frame.data), "timestamp": frame.timestamp}

    # ── Signals ───────────────────────────────────────────────────────────────

    @keyword("Get Signal Value")
    def get_signal_value(self, signal_name: str) -> float | None:
        """
        Return the latest decoded value for a DBC signal.

        Returns ``None`` if signal has not been received.
        """
        val = self._sv.get(signal_name)
        logger.debug(f"Signal {signal_name} = {val}")
        return val

    @keyword("Signal Should Be In Range")
    def signal_should_be_in_range(
        self, signal_name: str, minimum: float, maximum: float
    ) -> None:
        """
        Assert that a signal value is within [minimum, maximum].

        Example:
            Signal Should Be In Range    VehicleSpeed_kmh    90    110
        """
        val = self._sv.get(signal_name)
        if val is None:
            raise AssertionError(
                f"Signal '{signal_name}' has no value (not received)"
            )
        assert float(minimum) <= float(val) <= float(maximum), (
            f"Signal '{signal_name}' = {val} outside [{minimum}, {maximum}]"
        )
        logger.info(f"Signal {signal_name} = {val} ∈ [{minimum}, {maximum}] ✓")

    @keyword("Signal Should Equal")
    def signal_should_equal(
        self, signal_name: str, expected: float, tolerance: float = 0.0
    ) -> None:
        """
        Assert signal equals expected value within optional tolerance.

        Example:
            Signal Should Equal    ACC_Status    2    0
        """
        val = self._sv.get(signal_name)
        if val is None:
            raise AssertionError(f"Signal '{signal_name}' not received")
        assert abs(float(val) - float(expected)) <= float(tolerance), (
            f"Signal '{signal_name}' = {val}, expected {expected} ± {tolerance}"
        )

    @keyword("Signal Should Not Change For")
    def signal_should_not_change_for(
        self, signal_name: str, duration_s: float, tolerance: float = 0.01
    ) -> None:
        """Assert signal value is stable for given duration (no change > tolerance)."""
        self._sv.assert_stable(
            signal_name, duration_s=float(duration_s), tolerance=float(tolerance)
        )

    @keyword("Wait For Signal Change")
    def wait_for_signal_change(
        self, signal_name: str, timeout_s: float = 5.0
    ) -> float:
        """Wait until signal changes from its current value. Returns new value."""
        initial = self._sv.get(signal_name)
        deadline = time.monotonic() + float(timeout_s)
        while time.monotonic() < deadline:
            current = self._sv.get(signal_name)
            if current is not None and current != initial:
                return current
            time.sleep(0.05)
        raise AssertionError(
            f"Signal '{signal_name}' did not change within {timeout_s}s"
        )

    @keyword("CAN Bus Should Be Active")
    def can_bus_should_be_active(self) -> None:
        """Assert that at least one CAN frame has been received recently."""
        frames = self._bus.receive_all(max_count=1)
        if not frames:
            raise AssertionError("No CAN frames received — bus may be inactive")
