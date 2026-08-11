"""
27_wifi_hotspot.py
Test IVI Wi-Fi hotspot lifecycle via CAN bus.
Transitions WiFi Off→Connecting→Connected on IVI_WiFi (0x409).
Verifies signal bars 0→3→5, connected state, and disconnect back to Off.
"""
import can
import time
import pytest

CHANNEL = 'PCAN_USBBUS1'
BUSTYPE = 'pcan'
BITRATE = 500_000
TIMEOUT = 5.0

IVI_WIFI_ID     = 0x409
IVI_ECU_RESP_ID = 0x450

WIFI_OFF        = 0x00
WIFI_CONNECTING = 0x01
WIFI_CONNECTED  = 0x02

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


def step_wifi_off(bus):
    """Set WiFi state to Off and verify ACK."""
    send_msg(bus, IVI_WIFI_ID, [WIFI_OFF, 0x00, 0x00, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("WiFi Off ACK received", resp is not None)
    if resp:
        check("WiFi Off byte0==0x00", resp.data[0] == WIFI_OFF)


def step_wifi_connecting(bus):
    """Initiate WiFi connection and verify Connecting state."""
    send_msg(bus, IVI_WIFI_ID, [WIFI_CONNECTING, 0x00, 0x00, 0x00])  # bars=0 during connecting
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("WiFi Connecting ACK received", resp is not None)
    if resp:
        check("WiFi Connecting byte0==0x01", resp.data[0] == WIFI_CONNECTING)
        check("WiFi bars 0 during connecting byte1==0x00", resp.data[1] == 0x00)


def step_wifi_signal_bars_3(bus):
    """WiFi connected with 3 signal bars."""
    send_msg(bus, IVI_WIFI_ID, [WIFI_CONNECTED, 0x03, 0x00, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("WiFi 3 bars ACK received", resp is not None)
    if resp:
        check("WiFi Connected byte0==0x02", resp.data[0] == WIFI_CONNECTED)
        check("WiFi 3 bars byte1==0x03", resp.data[1] == 0x03)


def step_wifi_signal_bars_5(bus):
    """WiFi at full signal 5 bars."""
    send_msg(bus, IVI_WIFI_ID, [WIFI_CONNECTED, 0x05, 0x00, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("WiFi 5 bars ACK received", resp is not None)
    if resp:
        check("WiFi full signal byte1==0x05", resp.data[1] == 0x05)
        check("WiFi Connected state maintained", resp.data[0] == WIFI_CONNECTED)


def step_verify_hotspot_active(bus):
    """Verify hotspot sharing byte2=1 is active."""
    send_msg(bus, IVI_WIFI_ID, [WIFI_CONNECTED, 0x05, 0x01, 0x00])  # byte2=1 hotspot on
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("Hotspot active ACK received", resp is not None)
    if resp:
        check("Hotspot active byte2==0x01 echoed", resp.data[2] == 0x01)


def step_wifi_disconnect(bus):
    """Disconnect WiFi and verify state returns to Off."""
    send_msg(bus, IVI_WIFI_ID, [WIFI_OFF, 0x00, 0x00, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("WiFi disconnect ACK received", resp is not None)
    if resp:
        check("WiFi Off after disconnect byte0==0x00", resp.data[0] == WIFI_OFF)
        check("WiFi signal bars 0 after disconnect", resp.data[1] == 0x00)


def test_wifi_hotspot(bus_session):
    bus = bus_session
    step_wifi_off(bus)
    step_wifi_connecting(bus)
    step_wifi_signal_bars_3(bus)
    step_wifi_signal_bars_5(bus)
    step_verify_hotspot_active(bus)
    step_wifi_disconnect(bus)
    assert fail_count == 0, f"{fail_count} check(s) failed in WiFi hotspot test"


if __name__ == "__main__":
    from conftest import create_bus

    bus = create_bus()
    try:
        test_wifi_hotspot(bus)
    finally:
        bus.shutdown()
    print(f"\nResults: {pass_count} passed, {fail_count} failed")
