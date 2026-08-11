"""
29_ambient_lighting_control.py
Test IVI ambient lighting RGB control via CAN bus.
Sets RGB colors for red/green/blue, controls zones 1/2/3,
tests dim/bright brightness levels, and auto-follow interior mode.
"""
import can
import time
import pytest

CHANNEL = 'PCAN_USBBUS1'
BUSTYPE = 'pcan'
BITRATE = 500_000
TIMEOUT = 5.0

# Ambient lighting uses IVI_Brightness extended with zone bytes
IVI_BRIGHTNESS_ID = 0x407
IVI_ECU_RESP_ID   = 0x450

# byte0=R, byte1=G, byte2=B, byte3=zone (1/2/3)
ZONE_1 = 0x01
ZONE_2 = 0x02
ZONE_3 = 0x03

COLOR_RED   = (0xFF, 0x00, 0x00)
COLOR_GREEN = (0x00, 0xFF, 0x00)
COLOR_BLUE  = (0x00, 0x00, 0xFF)
COLOR_WHITE = (0xFF, 0xFF, 0xFF)
COLOR_OFF   = (0x00, 0x00, 0x00)

AUTO_FOLLOW_ON  = 0x01
AUTO_FOLLOW_OFF = 0x00

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


def step_set_rgb_color(bus, r, g, b, zone, color_name):
    """Set RGB ambient color for a zone and verify ACK."""
    send_msg(bus, IVI_BRIGHTNESS_ID, [r, g, b, zone])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check(f"Ambient {color_name} zone {zone} ACK received", resp is not None)
    if resp:
        check(f"R byte0=={r:#04x} echoed", resp.data[0] == r)
        check(f"Zone byte3=={zone:#04x} echoed", resp.data[3] == zone)


def step_brightness_dim(bus):
    """Set ambient brightness to dim (all channels 20%) and verify."""
    DIM_LEVEL = 0x33
    send_msg(bus, IVI_BRIGHTNESS_ID, [DIM_LEVEL, DIM_LEVEL, DIM_LEVEL, ZONE_1])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("Ambient dim brightness ACK received", resp is not None)
    if resp:
        check(f"Dim level {DIM_LEVEL} echoed in byte0", resp.data[0] == DIM_LEVEL)


def step_brightness_bright(bus):
    """Set ambient brightness to full (all channels max) and verify."""
    send_msg(bus, IVI_BRIGHTNESS_ID, [0xFF, 0xFF, 0xFF, ZONE_1])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("Ambient full brightness ACK received", resp is not None)
    if resp:
        check("Full brightness byte0==0xFF echoed", resp.data[0] == 0xFF)


def step_auto_follow_interior(bus):
    """Enable auto-follow interior theme mode and verify ACK."""
    # Use byte2 as auto-follow flag since zone is byte3
    send_msg(bus, IVI_BRIGHTNESS_ID, [0x80, 0x80, AUTO_FOLLOW_ON, ZONE_1])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("Auto-follow interior mode ACK received", resp is not None)
    if resp:
        check("Auto-follow flag byte2==0x01 echoed", resp.data[2] == AUTO_FOLLOW_ON)


def step_disable_auto_follow(bus):
    """Disable auto-follow and return to manual color control."""
    send_msg(bus, IVI_BRIGHTNESS_ID, [0x80, 0x80, AUTO_FOLLOW_OFF, ZONE_1])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("Auto-follow disable ACK received", resp is not None)
    if resp:
        check("Auto-follow off byte2==0x00", resp.data[2] == AUTO_FOLLOW_OFF)


def test_ambient_lighting_control(bus_session):
    bus = bus_session
    global pass_count, fail_count
    pass_count = 0
    fail_count = 0
    step_set_rgb_color(bus, *COLOR_RED, ZONE_1, "Red")
    step_set_rgb_color(bus, *COLOR_GREEN, ZONE_2, "Green")
    step_set_rgb_color(bus, *COLOR_BLUE, ZONE_3, "Blue")
    step_set_rgb_color(bus, *COLOR_WHITE, ZONE_1, "White")
    step_brightness_dim(bus)
    step_brightness_bright(bus)
    step_auto_follow_interior(bus)
    step_disable_auto_follow(bus)
    assert fail_count == 0, f"{fail_count} check(s) failed in ambient lighting test"


if __name__ == "__main__":
    from conftest import create_bus

    bus = create_bus()
    try:
        test_ambient_lighting_control(bus)
    finally:
        bus.shutdown()
    print(f"\nResults: {pass_count} passed, {fail_count} failed")
