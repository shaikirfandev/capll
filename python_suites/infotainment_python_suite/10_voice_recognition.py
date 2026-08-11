"""
10_voice_recognition.py
Test IVI voice recognition via CAN bus.
Simulates SWC Voice button (byte=7) press, wake word detection,
command byte transmission, and verifies action response.
"""
import can
import time
import pytest

CHANNEL = 'PCAN_USBBUS1'
BUSTYPE = 'pcan'
BITRATE = 500_000
TIMEOUT = 5.0

IVI_STEERING_ID = 0x406
IVI_ECU_RESP_ID = 0x450

SWC_VOICE_BTN = 0x07

VOICE_WAKE_WORD = 0x01
VOICE_CMD_NAV   = 0x02
VOICE_CMD_CALL  = 0x03
VOICE_CMD_MUSIC = 0x04

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


def step_voice_button_press(bus):
    """Press Voice button on SWC (byte=7) and verify IVI acknowledges."""
    send_msg(bus, IVI_STEERING_ID, [SWC_VOICE_BTN, 0x00, 0x00, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("Voice button press ACK received", resp is not None)
    if resp:
        check("Voice button byte0==0x07 echoed", resp.data[0] == SWC_VOICE_BTN)
        check("Voice button result OK", resp.data[1] == 0x00)


def step_wake_word_detected(bus):
    """Simulate wake word detection and verify voice session starts."""
    send_msg(bus, IVI_STEERING_ID, [SWC_VOICE_BTN, VOICE_WAKE_WORD, 0x00, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("Wake word detection ACK received", resp is not None)
    if resp:
        check("Wake word byte1==0x01 echoed", resp.data[1] == VOICE_WAKE_WORD)


def step_send_nav_command(bus):
    """Send navigation voice command and verify action response."""
    send_msg(bus, IVI_STEERING_ID, [SWC_VOICE_BTN, VOICE_CMD_NAV, 0x01, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("Nav voice command ACK received", resp is not None)
    if resp:
        check("Nav command byte1==0x02 echoed", resp.data[1] == VOICE_CMD_NAV)
        check("Nav action triggered byte2==0x01", resp.data[2] == 0x01)


def step_send_call_command(bus):
    """Send call voice command and verify call session initiated."""
    send_msg(bus, IVI_STEERING_ID, [SWC_VOICE_BTN, VOICE_CMD_CALL, 0x01, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("Call voice command ACK received", resp is not None)
    if resp:
        check("Call command byte1==0x03 echoed", resp.data[1] == VOICE_CMD_CALL)


def step_send_music_command(bus):
    """Send music voice command and verify media playback triggered."""
    send_msg(bus, IVI_STEERING_ID, [SWC_VOICE_BTN, VOICE_CMD_MUSIC, 0x01, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("Music voice command ACK received", resp is not None)
    if resp:
        check("Music command byte1==0x04 echoed", resp.data[1] == VOICE_CMD_MUSIC)


def step_voice_session_end(bus):
    """End voice session and verify IVI returns to normal state."""
    send_msg(bus, IVI_STEERING_ID, [SWC_VOICE_BTN, 0x00, 0x00, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("Voice session end ACK received", resp is not None)
    if resp:
        check("Voice session ended byte1==0x00", resp.data[1] == 0x00)


def test_voice_recognition(bus_session):
    bus = bus_session
    global pass_count, fail_count
    pass_count = 0
    fail_count = 0
    step_voice_button_press(bus)
    step_wake_word_detected(bus)
    step_send_nav_command(bus)
    step_send_call_command(bus)
    step_send_music_command(bus)
    step_voice_session_end(bus)
    assert fail_count == 0, f"{fail_count} check(s) failed in voice recognition test"


if __name__ == "__main__":
    from conftest import create_bus

    bus = create_bus()
    try:
        test_voice_recognition(bus)
    finally:
        bus.shutdown()
    print(f"\nResults: {pass_count} passed, {fail_count} failed")
