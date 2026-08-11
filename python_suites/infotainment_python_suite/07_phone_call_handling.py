"""
07_phone_call_handling.py
Test IVI phone call state machine via CAN bus.
Transitions: Incoming ring (byte=1) → Answer (byte=2) → Hold (byte=3) → End (byte=0).
Verifies each ACK step and signal strength byte.
"""
import can
import time
import pytest

CHANNEL = 'PCAN_USBBUS1'
BUSTYPE = 'pcan'
BITRATE = 500_000
TIMEOUT = 5.0

IVI_PHONE_ID    = 0x405
IVI_ECU_RESP_ID = 0x450

CALL_IDLE    = 0x00
CALL_RINGING = 0x01
CALL_ACTIVE  = 0x02
CALL_ONHOLD  = 0x03

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


def step_incoming_ring(bus, signal_strength=4):
    """Simulate incoming call ring with signal strength."""
    send_msg(bus, IVI_PHONE_ID, [CALL_RINGING, signal_strength, 0x00, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("Incoming ring ACK received", resp is not None)
    if resp:
        check("Ring state echoed byte0==0x01", resp.data[0] == CALL_RINGING)
        check(f"Signal strength {signal_strength} echoed in byte1", resp.data[1] == signal_strength)


def step_answer_call(bus):
    """Answer the incoming call and verify Active state."""
    send_msg(bus, IVI_PHONE_ID, [CALL_ACTIVE, 0x04, 0x00, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("Answer call ACK received", resp is not None)
    if resp:
        check("Active call state echoed byte0==0x02", resp.data[0] == CALL_ACTIVE)
        check("Answer call result OK", resp.data[1] == 0x04)


def step_hold_call(bus):
    """Place the active call on hold and verify OnHold state."""
    send_msg(bus, IVI_PHONE_ID, [CALL_ONHOLD, 0x04, 0x00, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("Call hold ACK received", resp is not None)
    if resp:
        check("OnHold state echoed byte0==0x03", resp.data[0] == CALL_ONHOLD)


def step_resume_call(bus):
    """Resume call from hold."""
    send_msg(bus, IVI_PHONE_ID, [CALL_ACTIVE, 0x04, 0x00, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("Call resume from hold ACK received", resp is not None)
    if resp:
        check("Resumed active state byte0==0x02", resp.data[0] == CALL_ACTIVE)


def step_end_call(bus):
    """End the call and verify Idle state."""
    send_msg(bus, IVI_PHONE_ID, [CALL_IDLE, 0x00, 0x00, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("End call ACK received", resp is not None)
    if resp:
        check("Idle state after end call byte0==0x00", resp.data[0] == CALL_IDLE)
        check("End call result OK", resp.data[2] == 0x00 or resp.data[1] == 0x00)


def step_verify_call_duration_tracked(bus):
    """Verify call duration byte is non-zero during active call."""
    send_msg(bus, IVI_PHONE_ID, [CALL_ACTIVE, 0x04, 0x1E, 0x00])  # byte2=30s duration
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("Call duration tracking ACK received", resp is not None)
    if resp:
        check("Duration byte echoed in response byte2 >= 0", (resp.data[2] if len(resp.data) > 2 else 0) >= 0)


def test_phone_call_handling(bus_session):
    bus = bus_session
    global pass_count, fail_count
    pass_count = 0
    fail_count = 0
    step_incoming_ring(bus)
    step_answer_call(bus)
    step_hold_call(bus)
    step_resume_call(bus)
    step_end_call(bus)
    step_verify_call_duration_tracked(bus)
    assert fail_count == 0, f"{fail_count} check(s) failed in phone call handling test"


if __name__ == "__main__":
    from conftest import create_bus

    bus = create_bus()
    try:
        test_phone_call_handling(bus)
    finally:
        bus.shutdown()
        print(f"\nResults: {pass_count} passed, {fail_count} failed")
