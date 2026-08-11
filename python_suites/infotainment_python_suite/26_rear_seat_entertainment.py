"""
26_rear_seat_entertainment.py
Test IVI rear seat entertainment (RSE) zone controls via CAN bus.
RSE zone enable byte, content routing to rear screens,
and independent volume control for rear zones.
"""
import can
import time
import pytest

CHANNEL = 'PCAN_USBBUS1'
BUSTYPE = 'pcan'
BITRATE = 500_000
TIMEOUT = 5.0

IVI_VOLUME_ID   = 0x400
IVI_MEDIA_SRC_ID = 0x401
IVI_ECU_RESP_ID = 0x450

RSE_ZONE_DISABLE = 0x00
RSE_ZONE_1       = 0x01
RSE_ZONE_2       = 0x02
RSE_ZONE_BOTH    = 0x03

RSE_CONTENT_HDMI   = 0x01
RSE_CONTENT_MIRROR = 0x02
RSE_CONTENT_USB    = 0x03

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


def step_enable_rse_zone1(bus):
    """Enable RSE zone 1 (rear left screen) and verify ACK."""
    send_msg(bus, IVI_MEDIA_SRC_ID, [0x02, RSE_ZONE_1, 0x00, 0x00])  # USB + zone1
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("RSE Zone 1 enable ACK received", resp is not None)
    if resp:
        check("RSE Zone 1 byte1==0x01 echoed", resp.data[1] == RSE_ZONE_1)


def step_enable_rse_zone2(bus):
    """Enable RSE zone 2 (rear right screen) and verify ACK."""
    send_msg(bus, IVI_MEDIA_SRC_ID, [0x02, RSE_ZONE_2, 0x00, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("RSE Zone 2 enable ACK received", resp is not None)
    if resp:
        check("RSE Zone 2 byte1==0x02 echoed", resp.data[1] == RSE_ZONE_2)


def step_route_content_to_rear(bus):
    """Route USB content to both rear screens and verify ACK."""
    send_msg(bus, IVI_MEDIA_SRC_ID, [0x02, RSE_ZONE_BOTH, RSE_CONTENT_USB, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("Content routing to both zones ACK received", resp is not None)
    if resp:
        check("Both zones byte1==0x03", resp.data[1] == RSE_ZONE_BOTH)
        check("USB content byte2==0x03", resp.data[2] == RSE_CONTENT_USB)


def step_independent_volume_zone1(bus):
    """Set independent volume for zone 1 (rear left) to 40."""
    ZONE1_VOL = 40
    send_msg(bus, IVI_VOLUME_ID, [ZONE1_VOL, 0x00, RSE_ZONE_1, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("Zone 1 independent volume ACK received", resp is not None)
    if resp:
        check(f"Zone 1 volume {ZONE1_VOL} echoed in byte0", resp.data[0] == ZONE1_VOL)


def step_independent_volume_zone2(bus):
    """Set independent volume for zone 2 (rear right) to 60."""
    ZONE2_VOL = 60
    send_msg(bus, IVI_VOLUME_ID, [ZONE2_VOL, 0x00, RSE_ZONE_2, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("Zone 2 independent volume ACK received", resp is not None)
    if resp:
        check(f"Zone 2 volume {ZONE2_VOL} echoed in byte0", resp.data[0] == ZONE2_VOL)


def step_disable_rse(bus):
    """Disable RSE zones and verify zones off."""
    send_msg(bus, IVI_MEDIA_SRC_ID, [0x02, RSE_ZONE_DISABLE, 0x00, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("RSE disable ACK received", resp is not None)
    if resp:
        check("RSE disabled byte1==0x00", resp.data[1] == RSE_ZONE_DISABLE)


def test_rear_seat_entertainment(bus_session):
    bus = bus_session
    global pass_count, fail_count
    pass_count = 0
    fail_count = 0
    step_enable_rse_zone1(bus)
    step_enable_rse_zone2(bus)
    step_route_content_to_rear(bus)
    step_independent_volume_zone1(bus)
    step_independent_volume_zone2(bus)
    step_disable_rse(bus)
    assert fail_count == 0, f"{fail_count} check(s) failed in rear seat entertainment test"


if __name__ == "__main__":
    from conftest import create_bus

    bus = create_bus()
    try:
        test_rear_seat_entertainment(bus)
    finally:
        bus.shutdown()
        print(f"\nResults: {pass_count} passed, {fail_count} failed")
