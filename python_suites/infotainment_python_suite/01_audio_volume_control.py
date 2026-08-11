"""
01_audio_volume_control.py
Test IVI audio volume control via CAN bus.
Sends volume levels 0,25,50,75,100 on IVI_Volume (0x400) and verifies ECU ACK.
Also tests mute (byte1=1) and unmute functionality.
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


def step_set_volume(bus, volume_level):
    """Send volume command and verify ACK byte0 echoes the volume value."""
    send_msg(bus, IVI_VOLUME_ID, [volume_level, 0x00, 0x00, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check(
        f"Volume set to {volume_level} – ACK received",
        resp is not None
    )
    if resp:
        check(
            f"Volume ACK echoes {volume_level} in byte0",
            resp.data[0] == volume_level
        )
        check(
            f"Volume ACK result byte1 == 0x00 (OK) for level {volume_level}",
            resp.data[1] == 0x00
        )


def step_mute_audio(bus):
    """Send mute command (byte1=1) and verify ACK indicates muted state."""
    send_msg(bus, IVI_VOLUME_ID, [0x32, 0x01, 0x00, 0x00])  # volume=50, mute=1
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("Mute command ACK received", resp is not None)
    if resp:
        check("Mute ACK result OK", resp.data[1] == 0x00)
        check("Mute state byte2=1 in response", resp.data[2] == 0x01)


def step_unmute_audio(bus):
    """Send unmute command (byte1=0) and verify audio is restored."""
    send_msg(bus, IVI_VOLUME_ID, [0x32, 0x00, 0x00, 0x00])  # volume=50, mute=0
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("Unmute command ACK received", resp is not None)
    if resp:
        check("Unmute ACK result OK", resp.data[1] == 0x00)
        check("Unmute state byte2=0 in response", resp.data[2] == 0x00)


def test_audio_volume_control(bus_session):
    bus = bus_session
    global pass_count, fail_count
    pass_count = 0
    fail_count = 0
    for level in [0, 25, 50, 75, 100]:
        step_set_volume(bus, level)
    step_mute_audio(bus)
    step_unmute_audio(bus)
    assert fail_count == 0, f"{fail_count} check(s) failed in audio volume control test"


if __name__ == "__main__":
    from conftest import create_bus

    bus = create_bus()
    try:
        test_audio_volume_control(bus)
    finally:
        bus.shutdown()
    print(f"\nResults: {pass_count} passed, {fail_count} failed")
