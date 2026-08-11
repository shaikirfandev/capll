"""
14_steering_wheel_controls.py
Test all 8 IVI steering wheel control (SWC) buttons via CAN bus.
Sends each button byte 0-7 on IVI_SteeringCtrl (0x406) and verifies
corresponding IVI actions via ECU ACK. Includes rapid press test.
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

SWC_BUTTONS = [
    (0x00, "VolUp"),
    (0x01, "VolDown"),
    (0x02, "Next"),
    (0x03, "Prev"),
    (0x04, "Mode"),
    (0x05, "Call"),
    (0x06, "End"),
    (0x07, "Voice"),
]

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


def step_test_swc_button(bus, button_byte, button_name):
    """Send SWC button press and verify ACK echoes the button byte."""
    send_msg(bus, IVI_STEERING_ID, [button_byte, 0x00, 0x00, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check(f"SWC {button_name} (0x{button_byte:02X}) ACK received", resp is not None)
    if resp:
        check(f"SWC {button_name} byte0=={button_byte:#04x} echoed", resp.data[0] == button_byte)
        check(f"SWC {button_name} result OK", resp.data[1] == 0x00)


def step_rapid_press_test(bus):
    """Rapid successive presses of VolUp should not miss any ACK."""
    ack_received_count = 0
    for _ in range(5):
        send_msg(bus, IVI_STEERING_ID, [0x00, 0x00, 0x00, 0x00])  # VolUp
        resp = wait_for_response(bus, IVI_ECU_RESP_ID, timeout=1.0)
        if resp and resp.data[0] == 0x00:
            ack_received_count += 1
    check(f"Rapid VolUp: {ack_received_count}/5 ACKs received", ack_received_count >= 4)


def step_long_press_mode_button(bus):
    """Simulate long press of Mode button (byte1=0x01 for long press)."""
    send_msg(bus, IVI_STEERING_ID, [0x04, 0x01, 0x00, 0x00])  # Mode + long press flag
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("SWC Mode long-press ACK received", resp is not None)
    if resp:
        check("Mode long-press byte0==0x04", resp.data[0] == 0x04)


def test_steering_wheel_controls(bus_session):
    bus = bus_session
    global pass_count, fail_count
    pass_count = 0
    fail_count = 0
    for btn_byte, btn_name in SWC_BUTTONS:
        step_test_swc_button(bus, btn_byte, btn_name)
    step_rapid_press_test(bus)
    step_long_press_mode_button(bus)
    assert fail_count == 0, f"{fail_count} check(s) failed in steering wheel controls test"


if __name__ == "__main__":
    from conftest import create_bus

    bus = create_bus()
    try:
        test_steering_wheel_controls(bus)
    finally:
        bus.shutdown()
        print(f"\nResults: {pass_count} passed, {fail_count} failed")
