"""
15_equalizer_settings.py
Test IVI equalizer settings via CAN bus.
Cycles EQ Flat→Bass→Treble→Custom on IVI_EQ (0x40A).
Verifies ACK preset echo and bass gain byte in Custom mode.
"""
import can
import time
import pytest

CHANNEL = 'PCAN_USBBUS1'
BUSTYPE = 'pcan'
BITRATE = 500_000
TIMEOUT = 5.0

IVI_EQ_ID       = 0x40A
IVI_ECU_RESP_ID = 0x450

EQ_FLAT   = 0x00
EQ_BASS   = 0x01
EQ_TREBLE = 0x02
EQ_CUSTOM = 0x03

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


def step_set_eq_preset(bus, preset_byte, preset_name):
    """Set EQ preset and verify ACK echoes the preset."""
    send_msg(bus, IVI_EQ_ID, [preset_byte, 0x00, 0x00, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check(f"EQ {preset_name} ACK received", resp is not None)
    if resp:
        check(f"EQ {preset_name} preset echoed byte0=={preset_byte:#04x}", resp.data[0] == preset_byte)
        check(f"EQ {preset_name} result OK", resp.data[1] == 0x00)


def step_custom_eq_bass_gain(bus):
    """In Custom mode, set bass gain byte1=+6dB and verify."""
    BASS_GAIN = 0x06
    send_msg(bus, IVI_EQ_ID, [EQ_CUSTOM, BASS_GAIN, 0x00, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("Custom EQ bass gain ACK received", resp is not None)
    if resp:
        check(f"Custom EQ bass gain {BASS_GAIN} echoed in byte1", resp.data[1] == BASS_GAIN)


def step_custom_eq_treble_gain(bus):
    """In Custom mode, set treble gain byte2=+4dB and verify."""
    TREBLE_GAIN = 0x04
    send_msg(bus, IVI_EQ_ID, [EQ_CUSTOM, 0x06, TREBLE_GAIN, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("Custom EQ treble gain ACK received", resp is not None)
    if resp:
        check(f"Custom EQ treble gain {TREBLE_GAIN} echoed in byte2", resp.data[2] == TREBLE_GAIN)


def step_revert_to_flat(bus):
    """Revert EQ to Flat preset after custom adjustments."""
    send_msg(bus, IVI_EQ_ID, [EQ_FLAT, 0x00, 0x00, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("EQ revert to Flat ACK received", resp is not None)
    if resp:
        check("EQ Flat preset restored byte0==0x00", resp.data[0] == EQ_FLAT)
        check("EQ Flat gain bytes cleared", resp.data[1] == 0x00)


def test_equalizer_settings(bus_session):
    bus = bus_session
    for preset_byte, preset_name in [(EQ_FLAT, "Flat"), (EQ_BASS, "Bass"),
                                      (EQ_TREBLE, "Treble"), (EQ_CUSTOM, "Custom")]:
        step_set_eq_preset(bus, preset_byte, preset_name)
    step_custom_eq_bass_gain(bus)
    step_custom_eq_treble_gain(bus)
    step_revert_to_flat(bus)
    assert fail_count == 0, f"{fail_count} check(s) failed in equalizer settings test"


if __name__ == "__main__":
    from conftest import create_bus

    bus = create_bus()
    try:
        test_equalizer_settings(bus)
    finally:
        bus.shutdown()
    print(f"\nResults: {pass_count} passed, {fail_count} failed")
