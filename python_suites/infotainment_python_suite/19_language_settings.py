"""
19_language_settings.py
Test IVI language and locale settings via CAN bus.
Cycles EN→DE→FR→ZH on IVI_Language (0x40B).
Verifies ACK, units metric/imperial toggle, and date format change.
"""
import can
import time
import pytest

CHANNEL = 'PCAN_USBBUS1'
BUSTYPE = 'pcan'
BITRATE = 500_000
TIMEOUT = 5.0

IVI_LANGUAGE_ID = 0x40B
IVI_ECU_RESP_ID = 0x450

LANG_EN = 0x00
LANG_DE = 0x01
LANG_FR = 0x02
LANG_ZH = 0x03
LANG_AR = 0x04

UNITS_METRIC   = 0x00
UNITS_IMPERIAL = 0x01

DATE_FORMAT_DMY = 0x00
DATE_FORMAT_MDY = 0x01
DATE_FORMAT_YMD = 0x02

LANGUAGES = [
    (LANG_EN, "English"),
    (LANG_DE, "German"),
    (LANG_FR, "French"),
    (LANG_ZH, "Chinese"),
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


def step_set_language(bus, lang_byte, lang_name):
    """Set language and verify ACK echoes language byte."""
    send_msg(bus, IVI_LANGUAGE_ID, [lang_byte, 0x00, 0x00, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check(f"Language {lang_name} ACK received", resp is not None)
    if resp:
        check(f"Language {lang_name} byte0=={lang_byte:#04x} echoed", resp.data[0] == lang_byte)
        check(f"Language {lang_name} result OK", resp.data[1] == 0x00)
    time.sleep(0.05)


def step_set_units_metric(bus):
    """Set units to metric and verify ACK."""
    send_msg(bus, IVI_LANGUAGE_ID, [LANG_EN, UNITS_METRIC, 0x00, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("Units metric ACK received", resp is not None)
    if resp:
        check("Units metric byte1==0x00 in ACK", resp.data[1] == UNITS_METRIC)


def step_set_units_imperial(bus):
    """Set units to imperial and verify ACK."""
    send_msg(bus, IVI_LANGUAGE_ID, [LANG_EN, UNITS_IMPERIAL, 0x00, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("Units imperial ACK received", resp is not None)
    if resp:
        check("Units imperial byte1==0x01 in ACK", resp.data[1] == UNITS_IMPERIAL)


def step_set_date_format(bus, fmt_byte, fmt_name):
    """Set date format and verify ACK."""
    send_msg(bus, IVI_LANGUAGE_ID, [LANG_EN, UNITS_METRIC, fmt_byte, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check(f"Date format {fmt_name} ACK received", resp is not None)
    if resp:
        check(f"Date format {fmt_name} byte2=={fmt_byte:#04x} echoed", resp.data[2] == fmt_byte)


def test_language_settings(bus_session):
    bus = bus_session
    for lang_byte, lang_name in LANGUAGES:
        step_set_language(bus, lang_byte, lang_name)
    step_set_units_metric(bus)
    step_set_units_imperial(bus)
    step_set_date_format(bus, DATE_FORMAT_DMY, "DD/MM/YYYY")
    step_set_date_format(bus, DATE_FORMAT_MDY, "MM/DD/YYYY")
    assert fail_count == 0, f"{fail_count} check(s) failed in language settings test"


if __name__ == "__main__":
    from conftest import create_bus

    bus = create_bus()
    try:
        test_language_settings(bus)
    finally:
        bus.shutdown()
    print(f"\nResults: {pass_count} passed, {fail_count} failed")
