"""
18_privacy_mode.py
Test IVI privacy mode via CAN bus.
Enables Privacy ON (byte=1), verifies navigation disabled and mic muted.
Disables Privacy OFF and confirms navigation/mic restored.
"""
import can
import time
import pytest

CHANNEL = 'PCAN_USBBUS1'
BUSTYPE = 'pcan'
BITRATE = 500_000
TIMEOUT = 5.0

IVI_PRIVACY_ID  = 0x40D
IVI_NAV_ID      = 0x403
IVI_ECU_RESP_ID = 0x450

PRIVACY_OFF = 0x00
PRIVACY_ON  = 0x01

NAV_IDLE    = 0x00
NAV_ROUTING = 0x01

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


def step_enable_privacy(bus):
    """Enable privacy mode and verify ACK."""
    send_msg(bus, IVI_PRIVACY_ID, [PRIVACY_ON, 0x00, 0x00, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("Privacy ON ACK received", resp is not None)
    if resp:
        check("Privacy ON byte0==0x01 in ACK", resp.data[0] == PRIVACY_ON)
        check("Privacy ON result OK", resp.data[1] == 0x00)


def step_verify_navigation_disabled(bus):
    """With privacy ON, attempt to start navigation - should return error."""
    send_msg(bus, IVI_NAV_ID, [NAV_ROUTING, 0x1E, 0x00, 0x00])  # ETA=30
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("Nav request during privacy ACK received", resp is not None)
    if resp:
        check("Nav blocked during privacy (result byte1==0x01 Fail)", resp.data[1] == 0x01)


def step_verify_mic_muted(bus):
    """Verify microphone is muted during privacy mode (mic status byte2=0)."""
    send_msg(bus, IVI_PRIVACY_ID, [PRIVACY_ON, 0x01, 0x00, 0x00])  # byte1=1 check mic
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("Mic mute status ACK received", resp is not None)
    if resp:
        check("Mic muted byte2==0x00 during privacy", resp.data[2] == 0x00)


def step_disable_privacy(bus):
    """Disable privacy mode and verify ACK."""
    send_msg(bus, IVI_PRIVACY_ID, [PRIVACY_OFF, 0x00, 0x00, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("Privacy OFF ACK received", resp is not None)
    if resp:
        check("Privacy OFF byte0==0x00 in ACK", resp.data[0] == PRIVACY_OFF)


def step_verify_navigation_restored(bus):
    """After privacy OFF, navigation should be accessible again."""
    send_msg(bus, IVI_NAV_ID, [NAV_ROUTING, 0x1E, 0x00, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("Nav restored after privacy OFF ACK", resp is not None)
    if resp:
        check("Nav accessible result OK byte1==0x00", resp.data[1] == 0x00)


def step_verify_mic_restored(bus):
    """After privacy OFF, microphone should be active."""
    send_msg(bus, IVI_PRIVACY_ID, [PRIVACY_OFF, 0x01, 0x00, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("Mic restore status ACK received", resp is not None)
    if resp:
        check("Mic active byte2==0x01 after privacy off", resp.data[2] == 0x01)


def test_privacy_mode(bus_session):
    bus = bus_session
    global pass_count, fail_count
    pass_count = 0
    fail_count = 0
    step_enable_privacy(bus)
    step_verify_navigation_disabled(bus)
    step_verify_mic_muted(bus)
    step_disable_privacy(bus)
    step_verify_navigation_restored(bus)
    step_verify_mic_restored(bus)
    assert fail_count == 0, f"{fail_count} check(s) failed in privacy mode test"


if __name__ == "__main__":
    from conftest import create_bus

    bus = create_bus()
    try:
        test_privacy_mode(bus)
    finally:
        bus.shutdown()
        print(f"\nResults: {pass_count} passed, {fail_count} failed")
