"""
05_android_auto_session.py
Test Android Auto session lifecycle via CAN bus.
Sets media source to AndroidAuto (0x06), verifies active state,
screen projection byte, and disconnect/idle restoration.
"""
import can
import time
import pytest

CHANNEL = 'PCAN_USBBUS1'
BUSTYPE = 'pcan'
BITRATE = 500_000
TIMEOUT = 5.0
LATENCY_LIMIT = 3.0

IVI_MEDIA_SRC_ID = 0x401
IVI_ECU_RESP_ID  = 0x450

SOURCE_ANDROID_AUTO = 0x06
SOURCE_FM            = 0x00

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


def step_set_source_android_auto(bus):
    """Switch media source to AndroidAuto and verify ACK."""
    send_msg(bus, IVI_MEDIA_SRC_ID, [SOURCE_ANDROID_AUTO, 0x00, 0x00, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("AndroidAuto source switch ACK received", resp is not None)
    if resp:
        check("AndroidAuto source echoed in ACK byte0", resp.data[0] == SOURCE_ANDROID_AUTO)
        check("AndroidAuto source ACK result OK", resp.data[1] == 0x00)


def step_android_auto_connect(bus):
    """Initiate AndroidAuto session and measure connect latency."""
    t0 = time.time()
    send_msg(bus, IVI_MEDIA_SRC_ID, [SOURCE_ANDROID_AUTO, 0x01, 0x00, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID, timeout=LATENCY_LIMIT + 1)
    latency = time.time() - t0
    check("AndroidAuto connect ACK received", resp is not None)
    check(f"AndroidAuto connect latency {latency:.2f}s < {LATENCY_LIMIT}s", latency < LATENCY_LIMIT)


def step_verify_android_auto_active(bus):
    """Verify AndroidAuto session state is Active."""
    send_msg(bus, IVI_MEDIA_SRC_ID, [SOURCE_ANDROID_AUTO, STATE_ACTIVE, 0x00, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("AndroidAuto active state ACK received", resp is not None)
    if resp:
        check("AndroidAuto active state echoed byte2==0x02", resp.data[2] == STATE_ACTIVE)


def step_android_auto_screen_projection(bus):
    """Verify screen projection byte reflects AndroidAuto projection active."""
    send_msg(bus, IVI_MEDIA_SRC_ID, [SOURCE_ANDROID_AUTO, STATE_ACTIVE, 0x01, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("AndroidAuto projection ACK received", resp is not None)
    if resp:
        check("Projection active flag byte2==0x01 in response", resp.data[2] == 0x01)


def step_android_auto_voice_assistant(bus):
    """Trigger Google Assistant through AndroidAuto and verify ack."""
    send_msg(bus, IVI_MEDIA_SRC_ID, [SOURCE_ANDROID_AUTO, STATE_ACTIVE, 0x02, 0x00])  # byte2=2 voice
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("AndroidAuto voice assistant trigger ACK", resp is not None)
    if resp:
        check("Voice assistant byte2 echoed as 0x02", resp.data[2] == 0x02)


def step_android_auto_disconnect(bus):
    """Disconnect AndroidAuto session and verify idle state."""
    send_msg(bus, IVI_MEDIA_SRC_ID, [SOURCE_ANDROID_AUTO, 0x00, 0x00, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("AndroidAuto disconnect ACK received", resp is not None)
    if resp:
        check("Post-disconnect state idle byte2==0x00", resp.data[2] == STATE_IDLE)


def step_verify_source_fallback(bus):
    """After AndroidAuto, source reverts to FM."""
    send_msg(bus, IVI_MEDIA_SRC_ID, [SOURCE_FM, 0x00, 0x00, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("FM fallback source ACK received", resp is not None)
    if resp:
        check("FM source echoed correctly in ACK", resp.data[0] == SOURCE_FM)


def test_android_auto_session(bus_session):
    bus = bus_session
    global pass_count, fail_count
    pass_count = 0
    fail_count = 0
    step_set_source_android_auto(bus)
    step_android_auto_connect(bus)
    step_verify_android_auto_active(bus)
    step_android_auto_screen_projection(bus)
    step_android_auto_voice_assistant(bus)
    step_android_auto_disconnect(bus)
    step_verify_source_fallback(bus)
    assert fail_count == 0, f"{fail_count} check(s) failed in AndroidAuto session test"


if __name__ == "__main__":
    from conftest import create_bus

    bus = create_bus()
    try:
        test_android_auto_session(bus)
    finally:
        bus.shutdown()
        print(f"\nResults: {pass_count} passed, {fail_count} failed")
