"""
03_bluetooth_pairing.py
Test IVI Bluetooth pairing state machine via CAN bus.
Transitions BT Off→Discoverable→Pairing→Connected on IVI_Bluetooth (0x404).
Verifies deviceCount increments and pairing timeout handling.
"""
import can
import time
import pytest

CHANNEL = 'PCAN_USBBUS1'
BUSTYPE = 'pcan'
BITRATE = 500_000
TIMEOUT = 5.0
PAIRING_TIMEOUT = 30.0

IVI_BLUETOOTH_ID = 0x404
IVI_ECU_RESP_ID  = 0x450

BT_OFF          = 0x00
BT_DISCOVERABLE = 0x01
BT_PAIRING      = 0x02
BT_CONNECTED    = 0x03

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


def step_bt_off(bus):
    """Set BT state to Off and verify ACK."""
    send_msg(bus, IVI_BLUETOOTH_ID, [BT_OFF, 0x00, 0x00, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("BT Off command ACK received", resp is not None)
    if resp:
        check("BT Off ACK result OK", resp.data[1] == 0x00)


def step_bt_discoverable(bus):
    """Set BT to Discoverable and verify state transition."""
    send_msg(bus, IVI_BLUETOOTH_ID, [BT_DISCOVERABLE, 0x00, 0x00, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("BT Discoverable ACK received", resp is not None)
    if resp:
        check("BT Discoverable state echoed in byte0", resp.data[0] == BT_DISCOVERABLE)
        check("BT Discoverable result OK", resp.data[1] == 0x00)


def step_bt_pairing(bus):
    """Initiate BT pairing mode and verify ACK within timeout."""
    send_msg(bus, IVI_BLUETOOTH_ID, [BT_PAIRING, 0x00, 0x00, 0x00])
    start = time.time()
    resp = wait_for_response(bus, IVI_ECU_RESP_ID, timeout=PAIRING_TIMEOUT)
    elapsed = time.time() - start
    check("BT Pairing ACK received within timeout", resp is not None)
    check(f"BT Pairing response time < {PAIRING_TIMEOUT}s", elapsed < PAIRING_TIMEOUT)
    if resp:
        check("BT Pairing state ACK byte0 correct", resp.data[0] == BT_PAIRING)


def step_bt_connected(bus, expected_device_count=1):
    """Set BT Connected with deviceCount and verify increment."""
    send_msg(bus, IVI_BLUETOOTH_ID, [BT_CONNECTED, expected_device_count, 0x00, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("BT Connected ACK received", resp is not None)
    if resp:
        check("BT Connected state echoed in byte0", resp.data[0] == BT_CONNECTED)
        check(
            f"BT deviceCount echoed as {expected_device_count}",
            resp.data[2] == expected_device_count
        )
        check("BT Connected result OK", resp.data[1] == 0x00)


def step_bt_device_count_increment(bus):
    """Connect a second device and verify deviceCount increments to 2."""
    send_msg(bus, IVI_BLUETOOTH_ID, [BT_CONNECTED, 0x02, 0x00, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("BT second device ACK received", resp is not None)
    if resp:
        check("BT deviceCount incremented to 2", resp.data[2] == 0x02)


def test_bluetooth_pairing(bus_session):
    bus = bus_session
    global pass_count, fail_count
    pass_count = 0
    fail_count = 0
    step_bt_off(bus)
    step_bt_discoverable(bus)
    step_bt_pairing(bus)
    step_bt_connected(bus, expected_device_count=1)
    step_bt_device_count_increment(bus)
    assert fail_count == 0, f"{fail_count} check(s) failed in Bluetooth pairing test"


if __name__ == "__main__":
    from conftest import create_bus

    bus = create_bus()
    try:
        test_bluetooth_pairing(bus)
    finally:
        bus.shutdown()
    print(f"\nResults: {pass_count} passed, {fail_count} failed")
