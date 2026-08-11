"""
12_screen_mirror.py
Test IVI screen mirroring via CAN bus.
Enables mirror mode, verifies app projection active, checks latency <1s,
turns mirror off, and verifies idle state.
"""
import can
import time
import pytest

CHANNEL = 'PCAN_USBBUS1'
BUSTYPE = 'pcan'
BITRATE = 500_000
TIMEOUT = 5.0
MIRROR_LATENCY_LIMIT = 1.0

IVI_MEDIA_SRC_ID = 0x401
IVI_ECU_RESP_ID  = 0x450

MIRROR_ON  = 0x01
MIRROR_OFF = 0x00
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


def step_enable_mirror_mode(bus):
    """Enable screen mirror mode byte=1 and verify ACK."""
    send_msg(bus, IVI_MEDIA_SRC_ID, [0x07, MIRROR_ON, 0x00, 0x00])  # source 7 = mirror
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("Mirror mode enable ACK received", resp is not None)
    if resp:
        check("Mirror mode byte1==0x01 in ACK", resp.data[1] == MIRROR_ON)


def step_verify_projection_latency(bus):
    """Measure app projection latency and assert < 1s."""
    t0 = time.time()
    send_msg(bus, IVI_MEDIA_SRC_ID, [0x07, MIRROR_ON, STATE_ACTIVE, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID, timeout=MIRROR_LATENCY_LIMIT + 1)
    latency = time.time() - t0
    check("Mirror projection ACK received within 2s", resp is not None)
    check(f"Mirror projection latency {latency:.3f}s < {MIRROR_LATENCY_LIMIT}s", latency < MIRROR_LATENCY_LIMIT)


def step_verify_projection_active(bus):
    """Verify projection state is Active during mirror session."""
    send_msg(bus, IVI_MEDIA_SRC_ID, [0x07, MIRROR_ON, STATE_ACTIVE, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("Mirror projection active ACK", resp is not None)
    if resp:
        check("Projection active byte2==0x02", resp.data[2] == STATE_ACTIVE)


def step_disable_mirror_mode(bus):
    """Disable screen mirror and verify return to idle."""
    send_msg(bus, IVI_MEDIA_SRC_ID, [0x07, MIRROR_OFF, 0x00, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("Mirror mode disable ACK received", resp is not None)
    if resp:
        check("Mirror off byte1==0x00 in ACK", resp.data[1] == MIRROR_OFF)


def step_verify_idle_state(bus):
    """After mirror off, verify IVI is in idle state."""
    send_msg(bus, IVI_MEDIA_SRC_ID, [0x00, 0x00, STATE_IDLE, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("Post-mirror idle state ACK received", resp is not None)
    if resp:
        check("Idle state byte2==0x00 after mirror off", resp.data[2] == STATE_IDLE)


def step_mirror_reconnect_stability(bus):
    """Reconnect mirror and verify stable re-entry."""
    send_msg(bus, IVI_MEDIA_SRC_ID, [0x07, MIRROR_ON, STATE_ACTIVE, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("Mirror reconnect stability ACK received", resp is not None)
    if resp:
        check("Mirror reconnect result OK", resp.data[1] == 0x00 or resp.data[1] == MIRROR_ON)


def test_screen_mirror(bus_session):
    bus = bus_session
    global pass_count, fail_count
    pass_count = 0
    fail_count = 0
    step_enable_mirror_mode(bus)
    step_verify_projection_latency(bus)
    step_verify_projection_active(bus)
    step_disable_mirror_mode(bus)
    step_verify_idle_state(bus)
    step_mirror_reconnect_stability(bus)
    assert fail_count == 0, f"{fail_count} check(s) failed in screen mirror test"


if __name__ == "__main__":
    from conftest import create_bus

    bus = create_bus()
    try:
        test_screen_mirror(bus)
    finally:
        bus.shutdown()
        print(f"\nResults: {pass_count} passed, {fail_count} failed")
