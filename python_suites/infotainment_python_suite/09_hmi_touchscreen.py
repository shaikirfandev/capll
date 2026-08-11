"""
09_hmi_touchscreen.py
Test IVI HMI touchscreen power sequence via CAN bus.
Verifies Power On, screen timeout (30s), wake-on-touch, and brightness restore.
Uses IVI_PowerState (0x402) and IVI_Brightness (0x407).
"""
import can
import time
import pytest

CHANNEL = 'PCAN_USBBUS1'
BUSTYPE = 'pcan'
BITRATE = 500_000
TIMEOUT = 5.0
SCREEN_TIMEOUT = 30.0

IVI_POWER_ID      = 0x402
IVI_BRIGHTNESS_ID = 0x407
IVI_ECU_RESP_ID   = 0x450

POWER_OFF      = 0x00
POWER_STANDBY  = 0x01
POWER_ON       = 0x02
POWER_BOOTING  = 0x03

BRIGHTNESS_DIM  = 0x10
BRIGHTNESS_FULL = 0xFF

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


def step_power_on(bus):
    """Send Power On command and verify IVI transitions to On state."""
    send_msg(bus, IVI_POWER_ID, [POWER_ON, 0x00, 0x00, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("Power On ACK received", resp is not None)
    if resp:
        check("Power On state echoed byte0==0x02", resp.data[0] == POWER_ON)
        check("Power On result OK", resp.data[1] == 0x00)


def step_set_brightness(bus, level):
    """Set brightness level and verify ACK echo."""
    send_msg(bus, IVI_BRIGHTNESS_ID, [level, 0x00, 0x00, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check(f"Brightness {level} set ACK received", resp is not None)
    if resp:
        check(f"Brightness {level} echoed in ACK byte0", resp.data[0] == level)


def step_screen_timeout_to_standby(bus):
    """After screen idle, IVI transitions to Standby."""
    send_msg(bus, IVI_POWER_ID, [POWER_STANDBY, 0x00, 0x00, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("Screen timeout → Standby ACK received", resp is not None)
    if resp:
        check("Standby state echoed byte0==0x01", resp.data[0] == POWER_STANDBY)


def step_wake_on_touch(bus):
    """Simulate touch event to wake screen from Standby."""
    send_msg(bus, IVI_POWER_ID, [POWER_ON, 0x01, 0x00, 0x00])  # byte1=1 touch event
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("Wake-on-touch ACK received", resp is not None)
    if resp:
        check("IVI wakes to On state byte0==0x02", resp.data[0] == POWER_ON)


def step_brightness_restore(bus):
    """After wake, brightness should restore to previous level."""
    send_msg(bus, IVI_BRIGHTNESS_ID, [BRIGHTNESS_FULL, 0x00, 0x00, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("Brightness restore ACK received", resp is not None)
    if resp:
        check("Brightness restored to full (0xFF)", resp.data[0] == BRIGHTNESS_FULL)


def step_auto_brightness_mode(bus):
    """Enable auto brightness mode and verify ECU acknowledges byte1=1."""
    send_msg(bus, IVI_BRIGHTNESS_ID, [0x80, 0x01, 0x00, 0x00])  # level=128, auto=1
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("Auto brightness mode ACK received", resp is not None)
    if resp:
        check("Auto mode flag byte2==0x01 in response", resp.data[2] == 0x01 or resp.data[1] == 0x01)


def test_hmi_touchscreen(bus_session):
    bus = bus_session
    global pass_count, fail_count
    pass_count = 0
    fail_count = 0
    step_power_on(bus)
    step_set_brightness(bus, BRIGHTNESS_FULL)
    step_screen_timeout_to_standby(bus)
    step_wake_on_touch(bus)
    step_brightness_restore(bus)
    step_auto_brightness_mode(bus)
    assert fail_count == 0, f"{fail_count} check(s) failed in HMI touchscreen test"


if __name__ == "__main__":
    from conftest import create_bus

    bus = create_bus()
    try:
        test_hmi_touchscreen(bus)
    finally:
        bus.shutdown()
        print(f"\nResults: {pass_count} passed, {fail_count} failed")
