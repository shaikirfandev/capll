"""
11_display_brightness.py
Test IVI display brightness control via CAN bus.
Steps through 0,64,128,192,255 on IVI_Brightness (0x407).
Verifies ACK echo, auto mode (byte1=1), and auto-adjust on sensor change.
"""
import can
import time
import pytest

CHANNEL = 'PCAN_USBBUS1'
BUSTYPE = 'pcan'
BITRATE = 500_000
TIMEOUT = 5.0

IVI_BRIGHTNESS_ID = 0x407
IVI_ECU_RESP_ID   = 0x450

AUTO_OFF = 0x00
AUTO_ON  = 0x01

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


def step_set_brightness_level(bus, level):
    """Set brightness to a specific level and verify ACK echo."""
    send_msg(bus, IVI_BRIGHTNESS_ID, [level, AUTO_OFF, 0x00, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check(f"Brightness {level} ACK received", resp is not None)
    if resp:
        check(f"Brightness {level} echoed in byte0", resp.data[0] == level)
        check(f"Brightness {level} result OK", resp.data[1] == 0x00)


def step_enable_auto_brightness(bus):
    """Enable auto brightness mode (byte1=1) and verify ECU confirms."""
    send_msg(bus, IVI_BRIGHTNESS_ID, [0x80, AUTO_ON, 0x00, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("Auto brightness enable ACK received", resp is not None)
    if resp:
        check("Auto mode byte1==0x01 in response", resp.data[1] == AUTO_ON)


def step_simulate_sensor_change_bright(bus):
    """Simulate bright ambient light sensor: auto adjusts to max brightness."""
    send_msg(bus, IVI_BRIGHTNESS_ID, [0xFF, AUTO_ON, 0x64, 0x00])  # byte2=100 lux
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("Bright sensor auto-adjust ACK received", resp is not None)
    if resp:
        check("Auto bright-sensor level > 0x80", resp.data[0] > 0x80)


def step_simulate_sensor_change_dark(bus):
    """Simulate dark ambient light sensor: auto adjusts to low brightness."""
    send_msg(bus, IVI_BRIGHTNESS_ID, [0x20, AUTO_ON, 0x05, 0x00])  # byte2=5 lux
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("Dark sensor auto-adjust ACK received", resp is not None)
    if resp:
        check("Auto dark-sensor level <= 0x40", resp.data[0] <= 0x40)


def step_disable_auto_brightness(bus):
    """Disable auto brightness and revert to manual control."""
    send_msg(bus, IVI_BRIGHTNESS_ID, [0x80, AUTO_OFF, 0x00, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("Auto brightness disable ACK received", resp is not None)
    if resp:
        check("Auto mode byte1==0x00 after disable", resp.data[1] == AUTO_OFF)


def test_display_brightness(bus_session):
    bus = bus_session
    global pass_count, fail_count
    pass_count = 0
    fail_count = 0
    for level in [0, 64, 128, 192, 255]:
        step_set_brightness_level(bus, level)
    step_enable_auto_brightness(bus)
    step_simulate_sensor_change_bright(bus)
    step_simulate_sensor_change_dark(bus)
    step_disable_auto_brightness(bus)
    assert fail_count == 0, f"{fail_count} check(s) failed in display brightness test"


if __name__ == "__main__":
    from conftest import create_bus

    bus = create_bus()
    try:
        test_display_brightness(bus)
    finally:
        bus.shutdown()
    print(f"\nResults: {pass_count} passed, {fail_count} failed")
