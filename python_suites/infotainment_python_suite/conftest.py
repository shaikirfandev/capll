"""
conftest.py - pytest configuration for infotainment_python_suite
Shared fixtures and session-level setup/teardown.
"""
import pytest
import can

CHANNEL = 'PCAN_USBBUS1'
BUSTYPE = 'pcan'
BITRATE = 500_000


def create_bus():
    """Create CAN bus with PCAN primary and vcan0 fallback."""
    try:
        return can.interface.Bus(channel=CHANNEL, bustype=BUSTYPE, bitrate=BITRATE)
    except Exception:
        return can.interface.Bus(channel='vcan0', bustype='socketcan')


@pytest.fixture(scope="session")
def bus_session():
    """Session-scoped shared CAN bus fixture for infotainment tests."""
    bus = create_bus()
    yield bus
    bus.shutdown()
