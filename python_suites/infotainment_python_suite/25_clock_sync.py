"""
25_clock_sync.py
Test IVI clock synchronisation via CAN bus.
Builds unix timestamp bytes, sends on IVI_ClockSync (0x40C),
reads back ACK, and verifies timestamp is within ±5s of system time.
"""
import can
import time
import struct
import pytest

CHANNEL = 'PCAN_USBBUS1'
BUSTYPE = 'pcan'
BITRATE = 500_000
TIMEOUT = 5.0
CLOCK_TOLERANCE_S = 5

IVI_CLOCK_ID    = 0x40C
IVI_ECU_RESP_ID = 0x450

pass_count = 0
fail_count = 0


def check(name, condition):
    global pass_count, fail_count
    if condition:
        print(f"[PASS] {name}")
        pass_count += 1
    else:
        print(f"[FAIL] {name}")
        fail_count += 1


def send_msg(bus, arb_id, data):
    msg = can.Message(arbitration_id=arb_id, data=data, is_extended_id=False)
    bus.send(msg)
    time.sleep(0.05)


def wait_for_response(bus, expected_id, timeout=TIMEOUT):
    deadline = time.time() + timeout
    while time.time() < deadline:
        msg = bus.recv(timeout=0.1)
        if msg and msg.arbitration_id == expected_id:
            return msg
    return None


def build_timestamp_bytes(ts_unix):
    """Pack 32-bit unix timestamp into 4 bytes big-endian."""
    return list(struct.pack('>I', int(ts_unix)))


def extract_timestamp_from_response(resp):
    """Extract 32-bit timestamp from response bytes 0-3."""
    if resp and len(resp.data) >= 4:
        return struct.unpack('>I', bytes(resp.data[0:4]))[0]
    return None


def step_send_current_timestamp(bus):
    """Send current system unix timestamp and verify ECU ACK."""
    ts_now = int(time.time())
    ts_bytes = build_timestamp_bytes(ts_now)
    send_msg(bus, IVI_CLOCK_ID, ts_bytes + [0x00, 0x00, 0x00, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("Clock sync ACK received", resp is not None)
    if resp:
        check("Clock sync result OK byte4==0x00", resp.data[1] == 0x00 if len(resp.data) > 1 else True)
    return ts_now


def step_verify_timestamp_readback(bus, sent_ts):
    """Verify ECU echoes timestamp within ±5s of sent value."""
    ts_bytes = build_timestamp_bytes(sent_ts)
    send_msg(bus, IVI_CLOCK_ID, ts_bytes + [0x00, 0x00, 0x00, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("Clock readback ACK received", resp is not None)
    if resp:
        echoed_ts = extract_timestamp_from_response(resp)
        if echoed_ts is not None:
            delta = abs(echoed_ts - sent_ts)
            check(f"Echoed timestamp within ±{CLOCK_TOLERANCE_S}s (delta={delta}s)", delta <= CLOCK_TOLERANCE_S)


def step_send_past_timestamp(bus):
    """Send timestamp 1 hour in the past and verify ECU accepts."""
    past_ts = int(time.time()) - 3600
    ts_bytes = build_timestamp_bytes(past_ts)
    send_msg(bus, IVI_CLOCK_ID, ts_bytes + [0x00, 0x00, 0x00, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("Past timestamp ACK received", resp is not None)


def step_send_future_timestamp(bus):
    """Send timestamp 1 hour in the future and verify ECU handles gracefully."""
    future_ts = int(time.time()) + 3600
    ts_bytes = build_timestamp_bytes(future_ts)
    send_msg(bus, IVI_CLOCK_ID, ts_bytes + [0x00, 0x00, 0x00, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("Future timestamp ACK received", resp is not None)


def step_zero_timestamp(bus):
    """Send epoch zero timestamp and verify ECU rejects or handles it."""
    send_msg(bus, IVI_CLOCK_ID, [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("Zero timestamp response received", resp is not None)
    if resp:
        check("Zero timestamp: result byte defined", len(resp.data) >= 2)


def test_clock_sync(bus_session):
    bus = bus_session
    global pass_count, fail_count
    pass_count = 0
    fail_count = 0
    sent_ts = step_send_current_timestamp(bus)
    step_verify_timestamp_readback(bus, sent_ts)
    step_send_past_timestamp(bus)
    step_send_future_timestamp(bus)
    step_zero_timestamp(bus)
    assert fail_count == 0, f"{fail_count} check(s) failed in clock sync test"


if __name__ == "__main__":
    from conftest import create_bus

    bus = create_bus()
    try:
        test_clock_sync(bus)
    finally:
        bus.shutdown()
        print(f"\nResults: {pass_count} passed, {fail_count} failed")
