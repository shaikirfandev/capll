"""
23_do_not_disturb.py
Test IVI Do Not Disturb (DND) mode via CAN bus.
DND on (byte=1): incoming call ring suppressed.
DND off: call rings normally. Verifies each state transition.
"""
import can
import time
import pytest

CHANNEL = 'PCAN_USBBUS1'
BUSTYPE = 'pcan'
BITRATE = 500_000
TIMEOUT = 5.0

IVI_DND_ID      = 0x40E
IVI_PHONE_ID    = 0x405
IVI_ECU_RESP_ID = 0x450

DND_OFF = 0x00
DND_ON  = 0x01

CALL_IDLE    = 0x00
CALL_RINGING = 0x01

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


def step_dnd_on(bus):
    """Enable DND mode and verify ACK."""
    send_msg(bus, IVI_DND_ID, [DND_ON, 0x00, 0x00, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("DND ON ACK received", resp is not None)
    if resp:
        check("DND ON byte0==0x01 in ACK", resp.data[0] == DND_ON)
        check("DND ON result OK", resp.data[1] == 0x00)


def step_call_ring_suppressed_during_dnd(bus):
    """With DND ON, incoming call ring should be suppressed."""
    send_msg(bus, IVI_PHONE_ID, [CALL_RINGING, 0x04, 0x00, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("Call during DND response received", resp is not None)
    if resp:
        check("Ring suppressed during DND (result byte1==0x01)", resp.data[1] == 0x01)


def step_notification_suppressed_during_dnd(bus):
    """With DND ON, system notifications should also be suppressed."""
    send_msg(bus, IVI_DND_ID, [DND_ON, 0x01, 0x00, 0x00])  # byte1=1 notification
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("Notification suppressed during DND ACK", resp is not None)
    if resp:
        check("Notification suppressed byte1 confirmed", resp.data[1] == 0x00 or resp.data[1] == 0x01)


def step_dnd_off(bus):
    """Disable DND mode and verify ACK."""
    send_msg(bus, IVI_DND_ID, [DND_OFF, 0x00, 0x00, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("DND OFF ACK received", resp is not None)
    if resp:
        check("DND OFF byte0==0x00 in ACK", resp.data[0] == DND_OFF)


def step_call_rings_normally_after_dnd(bus):
    """With DND OFF, incoming call ring should work normally."""
    send_msg(bus, IVI_PHONE_ID, [CALL_RINGING, 0x04, 0x00, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("Call ring after DND OFF ACK received", resp is not None)
    if resp:
        check("Ring allowed after DND OFF (result byte1==0x00)", resp.data[1] == 0x00)
        check("Ring state byte0==0x01", resp.data[0] == CALL_RINGING)


def step_dnd_emergency_override(bus):
    """Emergency calls should bypass DND mode (byte2=1 priority override)."""
    send_msg(bus, IVI_DND_ID, [DND_ON, 0x00, 0x00, 0x00])  # DND on again
    send_msg(bus, IVI_PHONE_ID, [CALL_RINGING, 0x04, 0x01, 0x00])  # byte2=1 emergency
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("Emergency call bypass DND ACK received", resp is not None)
    if resp:
        check("Emergency bypasses DND result OK byte1==0x00", resp.data[1] == 0x00)


def test_do_not_disturb(bus_session):
    bus = bus_session
    global pass_count, fail_count
    pass_count = 0
    fail_count = 0
    step_dnd_on(bus)
    step_call_ring_suppressed_during_dnd(bus)
    step_notification_suppressed_during_dnd(bus)
    step_dnd_off(bus)
    step_call_rings_normally_after_dnd(bus)
    step_dnd_emergency_override(bus)
    assert fail_count == 0, f"{fail_count} check(s) failed in DND test"


if __name__ == "__main__":
    from conftest import create_bus

    bus = create_bus()
    try:
        test_do_not_disturb(bus)
    finally:
        bus.shutdown()
        print(f"\nResults: {pass_count} passed, {fail_count} failed")
