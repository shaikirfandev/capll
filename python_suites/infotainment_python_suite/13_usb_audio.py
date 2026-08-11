"""
13_usb_audio.py
Test IVI USB audio via CAN bus.
Connects USB media source (byte=2), verifies media state active,
track skip via SWC (byte=2), USB disconnect, and source fallback.
"""
import can
import time
import pytest

CHANNEL = 'PCAN_USBBUS1'
BUSTYPE = 'pcan'
BITRATE = 500_000
TIMEOUT = 5.0

IVI_MEDIA_SRC_ID = 0x401
IVI_STEERING_ID  = 0x406
IVI_ECU_RESP_ID  = 0x450

SOURCE_USB = 0x02
SOURCE_FM  = 0x00

SWC_NEXT = 0x02
SWC_PREV = 0x03

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


def step_usb_connect(bus):
    """Connect USB device and switch media source to USB."""
    send_msg(bus, IVI_MEDIA_SRC_ID, [SOURCE_USB, 0x01, 0x00, 0x00])  # byte1=1 USB connected
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("USB connect ACK received", resp is not None)
    if resp:
        check("USB source echoed byte0==0x02", resp.data[0] == SOURCE_USB)
        check("USB connect result OK", resp.data[1] == 0x00)


def step_verify_media_active(bus):
    """Verify USB media playback state is active."""
    send_msg(bus, IVI_MEDIA_SRC_ID, [SOURCE_USB, 0x02, 0x00, 0x00])  # byte1=2 playing
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("USB media active state ACK", resp is not None)
    if resp:
        check("Media playing state byte1==0x02", resp.data[1] == 0x02)


def step_track_skip_next(bus):
    """Skip to next track via SWC Next button (byte=2)."""
    send_msg(bus, IVI_STEERING_ID, [SWC_NEXT, 0x00, 0x00, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("Track skip next ACK received", resp is not None)
    if resp:
        check("SWC Next button byte0==0x02 echoed", resp.data[0] == SWC_NEXT)


def step_track_skip_prev(bus):
    """Skip to previous track via SWC Prev button (byte=3)."""
    send_msg(bus, IVI_STEERING_ID, [SWC_PREV, 0x00, 0x00, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("Track skip prev ACK received", resp is not None)
    if resp:
        check("SWC Prev button byte0==0x03 echoed", resp.data[0] == SWC_PREV)


def step_usb_disconnect(bus):
    """Disconnect USB device and verify source fallback."""
    send_msg(bus, IVI_MEDIA_SRC_ID, [SOURCE_USB, 0x00, 0x00, 0x00])  # byte1=0 disconnect
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("USB disconnect ACK received", resp is not None)
    if resp:
        check("USB disconnect result OK", resp.data[1] == 0x00)


def step_verify_source_fallback(bus):
    """After USB disconnect, source should fallback to FM."""
    send_msg(bus, IVI_MEDIA_SRC_ID, [SOURCE_FM, 0x00, 0x00, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("Source fallback to FM ACK received", resp is not None)
    if resp:
        check("FM fallback source byte0==0x00", resp.data[0] == SOURCE_FM)


def test_usb_audio(bus_session):
    bus = bus_session
    step_usb_connect(bus)
    step_verify_media_active(bus)
    step_track_skip_next(bus)
    step_track_skip_prev(bus)
    step_usb_disconnect(bus)
    step_verify_source_fallback(bus)
    assert fail_count == 0, f"{fail_count} check(s) failed in USB audio test"


if __name__ == "__main__":
    from conftest import create_bus

    bus = create_bus()
    try:
        test_usb_audio(bus)
    finally:
        bus.shutdown()
    print(f"\nResults: {pass_count} passed, {fail_count} failed")
