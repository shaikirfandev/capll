"""
regression_framework/conftest.py
Shared pytest fixtures for the EV Powertrain regression framework.

Provides:
    - can_bus: session-scoped CAN bus connection
    - uds_client: function-scoped UDS client (always starts fresh session)
    - can_helper: shared CAN message send/receive helper
    - bms_state / vcu_state: latest decoded signal snapshots
"""
import pytest
import can
import isotp
import udsoncan
import cantools
import threading
from typing import Optional
from collections import defaultdict


# ─────────────────────────────────────────────────────────────────────────────
# CONFIG (override via pytest.ini or command line)
# ─────────────────────────────────────────────────────────────────────────────

def pytest_addoption(parser):
    parser.addoption('--channel',    default='PCAN_USBBUS1')
    parser.addoption('--interface',  default='pcan')
    parser.addoption('--bitrate',    default='500000', type=int)
    parser.addoption('--dbc',        default='dbc/EV_Powertrain.dbc')
    parser.addoption('--bms-tx',     default='0x741')
    parser.addoption('--bms-rx',     default='0x749')


# ─────────────────────────────────────────────────────────────────────────────
# CAN BUS (session scope — one connection for all tests)
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope='session')
def can_bus(request):
    ch  = request.config.getoption('--channel')
    ifc = request.config.getoption('--interface')
    btr = request.config.getoption('--bitrate')
    bus = can.interface.Bus(channel=ch, bustype=ifc, bitrate=btr)
    yield bus
    bus.shutdown()


@pytest.fixture(scope='session')
def dbc(request):
    path = request.config.getoption('--dbc')
    return cantools.database.load_file(path)


# ─────────────────────────────────────────────────────────────────────────────
# LIVE SIGNAL RECEIVER (session scope)
# ─────────────────────────────────────────────────────────────────────────────

class SignalReceiver:
    """Continuously receives and decodes CAN messages into a signal dict."""

    def __init__(self, bus: can.Bus, db: cantools.db.Database):
        self._bus = bus
        self._db = db
        self._latest: dict = {}
        self._lock = threading.Lock()
        self._running = True
        self._thread = threading.Thread(target=self._rx_loop, daemon=True)
        self._thread.start()

    def _rx_loop(self):
        while self._running:
            msg = self._bus.recv(timeout=0.1)
            if msg and not msg.is_error_frame:
                try:
                    decoded = self._db.decode_message(
                        msg.arbitration_id, msg.data, decode_choices=False
                    )
                    with self._lock:
                        self._latest.update(decoded)
                except Exception:
                    pass

    def get(self, signal: str, default=None):
        with self._lock:
            return self._latest.get(signal, default)

    def get_all(self) -> dict:
        with self._lock:
            return dict(self._latest)

    def stop(self):
        self._running = False


@pytest.fixture(scope='session')
def signals(can_bus, dbc):
    rx = SignalReceiver(can_bus, dbc)
    yield rx
    rx.stop()


# ─────────────────────────────────────────────────────────────────────────────
# UDS CLIENT (function scope — fresh connection per test)
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope='function')
def uds_client(can_bus, request):
    tx_id = int(request.config.getoption('--bms-tx'), 16)
    rx_id = int(request.config.getoption('--bms-rx'), 16)

    addr = isotp.Address(
        isotp.AddressingMode.Normal_11bits,
        txid=tx_id, rxid=rx_id
    )
    conn = udsoncan.connections.PythonIsoTpConnection(can_bus, addr)
    conn.open()

    client_config = {
        'request_timeout': 3.0,
        'p2_timeout': 2.0,
        'p2_star_timeout': 25.0,
    }
    client = udsoncan.client.Client(conn, client_config=client_config)
    client.__enter__()

    # Start in default session
    client.change_session(0x01)

    yield client

    # Cleanup: return to default session, close connection
    try:
        client.change_session(0x01)
    except Exception:
        pass
    client.__exit__(None, None, None)


# ─────────────────────────────────────────────────────────────────────────────
# PYTEST MARKS
# ─────────────────────────────────────────────────────────────────────────────

def pytest_configure(config):
    config.addinivalue_line("markers", "smoke: quick smoke test (< 30s)")
    config.addinivalue_line("markers", "regression: full regression test")
    config.addinivalue_line("markers", "safety: ISO 26262 safety-related test")
    config.addinivalue_line("markers", "slow: test takes > 60 seconds")
    config.addinivalue_line("markers", "hardware: requires physical hardware")
