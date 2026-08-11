"""
21_power_mode_infotainment.py
Test IVI power mode transitions via CAN bus.
IGN off→Standby(30s)→IGN on→boot→accessory mode (audio only)→full on with navigation.
Uses IVI_PowerState (0x402).
"""
import can
import time
import pytest

CHANNEL = 'PCAN_USBBUS1'
BUSTYPE = 'pcan'
BITRATE = 500_000
TIMEOUT = 5.0

IVI_POWER_ID    = 0x402
IVI_MEDIA_SRC_ID = 0x401
IVI_NAV_ID      = 0x403
IVI_ECU_RESP_ID = 0x450

POWER_OFF     = 0x00
POWER_STANDBY = 0x01
POWER_ON      = 0x02
POWER_BOOTING = 0x03

SOURCE_FM   = 0x00
NAV_ROUTING = 0x01

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


def step_ign_off_to_standby(bus):
    """IGN off → IVI transitions to Standby after idle delay."""
    send_msg(bus, IVI_POWER_ID, [POWER_OFF, 0x00, 0x00, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("IGN off Power Off ACK received", resp is not None)
    send_msg(bus, IVI_POWER_ID, [POWER_STANDBY, 0x00, 0x00, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("Standby after IGN off ACK received", resp is not None)
    if resp:
        check("Standby state byte0==0x01", resp.data[0] == POWER_STANDBY)


def step_ign_on_boot_sequence(bus):
    """IGN on → IVI boots from Standby to On."""
    send_msg(bus, IVI_POWER_ID, [POWER_BOOTING, 0x00, 0x00, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("IGN on Booting ACK received", resp is not None)
    send_msg(bus, IVI_POWER_ID, [POWER_ON, 0x00, 0x00, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("IGN on → Power On ACK received", resp is not None)
    if resp:
        check("Power On state byte0==0x02", resp.data[0] == POWER_ON)


def step_accessory_mode_audio_only(bus):
    """In accessory mode, only audio is available (FM source active, nav blocked)."""
    send_msg(bus, IVI_POWER_ID, [POWER_ON, 0x01, 0x00, 0x00])  # byte1=1 accessory
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("Accessory mode ACK received", resp is not None)
    # Audio should work
    send_msg(bus, IVI_MEDIA_SRC_ID, [SOURCE_FM, 0x00, 0x00, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("FM audio in accessory mode ACK", resp is not None)
    if resp:
        check("FM available in accessory mode byte0==0x00", resp.data[0] == SOURCE_FM)


def step_full_on_with_navigation(bus):
    """Full power on: navigation and all features available."""
    send_msg(bus, IVI_POWER_ID, [POWER_ON, 0x02, 0x00, 0x00])  # byte1=2 full on
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("Full On state ACK received", resp is not None)
    send_msg(bus, IVI_NAV_ID, [NAV_ROUTING, 0x1E, 0x00, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("Navigation available in full on mode ACK", resp is not None)
    if resp:
        check("Nav routing available result OK", resp.data[1] == 0x00)


def step_power_off_verification(bus):
    """Power off and verify IVI shutdown state."""
    send_msg(bus, IVI_POWER_ID, [POWER_OFF, 0x00, 0x00, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("Power Off shutdown ACK received", resp is not None)
    if resp:
        check("Shutdown state byte0==0x00", resp.data[0] == POWER_OFF)


def test_power_mode_infotainment(bus_session):
    bus = bus_session
    step_ign_off_to_standby(bus)
    step_ign_on_boot_sequence(bus)
    step_accessory_mode_audio_only(bus)
    step_full_on_with_navigation(bus)
    step_power_off_verification(bus)
    assert fail_count == 0, f"{fail_count} check(s) failed in power mode test"


if __name__ == "__main__":
    from conftest import create_bus

    bus = create_bus()
    try:
        test_power_mode_infotainment(bus)
    finally:
        bus.shutdown()
    print(f"\nResults: {pass_count} passed, {fail_count} failed")
