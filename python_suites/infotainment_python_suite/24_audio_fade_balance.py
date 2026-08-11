"""
24_audio_fade_balance.py
Test IVI audio fade and balance control via CAN bus.
Tests fade front 100%/rear 100%/50-50 and balance L100/R100/centre.
Verifies ACK echoes for each configuration.
"""
import can
import time
import pytest

CHANNEL = 'PCAN_USBBUS1'
BUSTYPE = 'pcan'
BITRATE = 500_000
TIMEOUT = 5.0

IVI_VOLUME_ID   = 0x400
IVI_ECU_RESP_ID = 0x450

# Fade: byte2, Balance: byte3
# Fade: 0x00=all rear, 0x64=50-50, 0xFF=all front
# Balance: 0x00=all left, 0x64=centre, 0xFF=all right

FADE_FRONT = 0xFF
FADE_REAR  = 0x00
FADE_EQUAL = 0x64

BAL_LEFT   = 0x00
BAL_RIGHT  = 0xFF
BAL_CENTRE = 0x64

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


def step_set_fade(bus, fade_value, fade_name):
    """Set audio fade level and verify ACK echo."""
    send_msg(bus, IVI_VOLUME_ID, [0x32, 0x00, fade_value, BAL_CENTRE])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check(f"Fade {fade_name} (0x{fade_value:02X}) ACK received", resp is not None)
    if resp:
        check(f"Fade {fade_name} echoed in byte2", resp.data[2] == fade_value)


def step_set_balance(bus, balance_value, balance_name):
    """Set audio balance level and verify ACK echo."""
    send_msg(bus, IVI_VOLUME_ID, [0x32, 0x00, FADE_EQUAL, balance_value])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check(f"Balance {balance_name} (0x{balance_value:02X}) ACK received", resp is not None)
    if resp:
        check(f"Balance {balance_name} echoed in byte3", resp.data[3] == balance_value)


def step_combined_fade_balance(bus):
    """Set combined fade front + balance right and verify both bytes."""
    send_msg(bus, IVI_VOLUME_ID, [0x50, 0x00, FADE_FRONT, BAL_RIGHT])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("Combined fade+balance ACK received", resp is not None)
    if resp:
        check("Fade front echoed byte2==0xFF", resp.data[2] == FADE_FRONT)
        check("Balance right echoed byte3==0xFF", resp.data[3] == BAL_RIGHT)


def step_reset_to_default(bus):
    """Reset fade and balance to equal (50-50 centre) defaults."""
    send_msg(bus, IVI_VOLUME_ID, [0x32, 0x00, FADE_EQUAL, BAL_CENTRE])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("Default fade/balance reset ACK received", resp is not None)
    if resp:
        check("Default fade equal byte2==0x64", resp.data[2] == FADE_EQUAL)
        check("Default balance centre byte3==0x64", resp.data[3] == BAL_CENTRE)


def test_audio_fade_balance(bus_session):
    bus = bus_session
    global pass_count, fail_count
    pass_count = 0
    fail_count = 0
    step_set_fade(bus, FADE_FRONT, "Front100%")
    step_set_fade(bus, FADE_REAR,  "Rear100%")
    step_set_fade(bus, FADE_EQUAL, "50-50")
    step_set_balance(bus, BAL_LEFT,   "Left100%")
    step_set_balance(bus, BAL_RIGHT,  "Right100%")
    step_set_balance(bus, BAL_CENTRE, "Centre")
    step_combined_fade_balance(bus)
    step_reset_to_default(bus)
    assert fail_count == 0, f"{fail_count} check(s) failed in audio fade/balance test"


if __name__ == "__main__":
    from conftest import create_bus

    bus = create_bus()
    try:
        test_audio_fade_balance(bus)
    finally:
        bus.shutdown()
    print(f"\nResults: {pass_count} passed, {fail_count} failed")
