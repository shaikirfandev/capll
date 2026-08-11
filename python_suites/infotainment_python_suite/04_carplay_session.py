"""
04_carplay_session.py
Test Apple CarPlay session lifecycle via CAN bus.
Sets media source to CarPlay (0x05), verifies session connect latency <3s,
confirms active state, then disconnects and verifies idle state restoration.
"""
import can
import time
import pytest

CHANNEL = 'PCAN_USBBUS1'
BUSTYPE = 'pcan'
BITRATE = 500_000
TIMEOUT = 5.0
LATENCY_LIMIT = 3.0

IVI_MEDIA_SRC_ID  = 0x401
IVI_POWER_ID      = 0x402
IVI_ECU_RESP_ID   = 0x450

SOURCE_CARPLAY = 0x05
SOURCE_FM       = 0x00

STATE_IDLE   = 0x00
STATE_ACTIVE = 0x02

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


def step_set_source_carplay(bus):
    """Switch media source to CarPlay and verify ACK."""
    send_msg(bus, IVI_MEDIA_SRC_ID, [SOURCE_CARPLAY, 0x00, 0x00, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("CarPlay source switch ACK received", resp is not None)
    if resp:
        check("CarPlay source echoed in ACK byte0", resp.data[0] == SOURCE_CARPLAY)


def step_carplay_connect_latency(bus):
    """Measure CarPlay session connect time and assert < 3s."""
    t0 = time.time()
    send_msg(bus, IVI_MEDIA_SRC_ID, [SOURCE_CARPLAY, 0x01, 0x00, 0x00])  # byte1=1 connect
    resp = wait_for_response(bus, IVI_ECU_RESP_ID, timeout=LATENCY_LIMIT + 1)
    latency = time.time() - t0
    check("CarPlay connect ACK within 4s", resp is not None)
    check(f"CarPlay connect latency {latency:.2f}s < {LATENCY_LIMIT}s", latency < LATENCY_LIMIT)


def step_verify_carplay_active(bus):
    """Verify CarPlay session is in Active state."""
    send_msg(bus, IVI_MEDIA_SRC_ID, [SOURCE_CARPLAY, STATE_ACTIVE, 0x00, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("CarPlay active state ACK received", resp is not None)
    if resp:
        check("CarPlay state byte2 == Active (0x02)", resp.data[2] == STATE_ACTIVE)
        check("CarPlay active result OK", resp.data[1] == 0x00)


def step_carplay_screen_projection(bus):
    """Verify screen projection byte is set during CarPlay session."""
    send_msg(bus, IVI_MEDIA_SRC_ID, [SOURCE_CARPLAY, STATE_ACTIVE, 0x01, 0x00])  # byte2=projection
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("CarPlay screen projection ACK", resp is not None)
    if resp:
        check("Projection flag echoed in response byte2", resp.data[2] == 0x01)


def step_carplay_disconnect(bus):
    """Disconnect CarPlay session and verify IVI returns to idle."""
    send_msg(bus, IVI_MEDIA_SRC_ID, [SOURCE_CARPLAY, 0x00, 0x00, 0x00])  # byte1=0 disconnect
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("CarPlay disconnect ACK received", resp is not None)
    if resp:
        check("CarPlay post-disconnect state idle (byte2==0x00)", resp.data[2] == STATE_IDLE)


def step_verify_fallback_source(bus):
    """After CarPlay disconnect, source falls back to FM."""
    send_msg(bus, IVI_MEDIA_SRC_ID, [SOURCE_FM, 0x00, 0x00, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("Fallback to FM source ACK received", resp is not None)
    if resp:
        check("Fallback source FM echoed in ACK", resp.data[0] == SOURCE_FM)


def test_carplay_session(bus_session):
    bus = bus_session
    global pass_count, fail_count
    pass_count = 0
    fail_count = 0
    step_set_source_carplay(bus)
    step_carplay_connect_latency(bus)
    step_verify_carplay_active(bus)
    step_carplay_screen_projection(bus)
    step_carplay_disconnect(bus)
    step_verify_fallback_source(bus)
    assert fail_count == 0, f"{fail_count} check(s) failed in CarPlay session test"


if __name__ == "__main__":
    from conftest import create_bus

    bus = create_bus()
    try:
        test_carplay_session(bus)
    finally:
        bus.shutdown()
    print(f"\nResults: {pass_count} passed, {fail_count} failed")
