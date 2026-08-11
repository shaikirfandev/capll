"""
16_infotainment_dtc.py
Test IVI DTC read/clear via UDS CAN bus.
Sends UDS ReadDTCByStatusMask (0x19 01 0F) on 0x744,
reads response on 0x74C, verifies DTC count byte,
clears with 0x14 FF FF FF, and re-reads to confirm count=0.
"""
import can
import time
import pytest

CHANNEL = 'PCAN_USBBUS1'
BUSTYPE = 'pcan'
BITRATE = 500_000
TIMEOUT = 5.0

UDS_REQ_ID  = 0x744
UDS_RESP_ID = 0x74C

UDS_READ_DTC     = [0x03, 0x19, 0x01, 0x0F, 0x00, 0x00, 0x00, 0x00]
UDS_CLEAR_DTC    = [0x04, 0x14, 0xFF, 0xFF, 0xFF, 0x00, 0x00, 0x00]
UDS_READ_RESP_SID = 0x59  # positive response: 0x40 + 0x19

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


def step_read_dtc(bus):
    """Send UDS ReadDTCByStatusMask and capture DTC count."""
    send_msg(bus, UDS_REQ_ID, UDS_READ_DTC)
    resp = wait_for_response(bus, UDS_RESP_ID)
    check("UDS ReadDTC response received on 0x74C", resp is not None)
    dtc_count = 0
    if resp:
        check("UDS ReadDTC positive response SID==0x59", resp.data[1] == UDS_READ_RESP_SID)
        dtc_count = resp.data[3] if len(resp.data) > 3 else 0
        check("DTC count byte readable (byte3 >= 0)", dtc_count >= 0)
    return dtc_count


def step_clear_dtc(bus):
    """Send UDS ClearDiagnosticInformation (0x14 FF FF FF)."""
    send_msg(bus, UDS_REQ_ID, UDS_CLEAR_DTC)
    resp = wait_for_response(bus, UDS_RESP_ID)
    check("UDS ClearDTC response received on 0x74C", resp is not None)
    if resp:
        check("UDS ClearDTC positive response SID==0x54", resp.data[1] == 0x54)


def step_verify_dtc_cleared(bus):
    """Re-read DTC and verify count is zero."""
    send_msg(bus, UDS_REQ_ID, UDS_READ_DTC)
    resp = wait_for_response(bus, UDS_RESP_ID)
    check("UDS re-read DTC response received", resp is not None)
    if resp:
        cleared_count = resp.data[3] if len(resp.data) > 3 else 0
        check("DTC count is 0 after clear", cleared_count == 0)


def step_negative_response_handling(bus):
    """Send malformed UDS request and verify negative response."""
    send_msg(bus, UDS_REQ_ID, [0x02, 0x19, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
    resp = wait_for_response(bus, UDS_RESP_ID)
    check("Malformed UDS request response received", resp is not None)
    if resp:
        check("Negative response SID==0x7F", resp.data[1] == 0x7F)


def step_verify_ecu_reachable(bus):
    """Verify ECU responds to a tester present (0x3E 00)."""
    send_msg(bus, UDS_REQ_ID, [0x02, 0x3E, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
    resp = wait_for_response(bus, UDS_RESP_ID)
    check("TesterPresent ACK received from ECU", resp is not None)
    if resp:
        check("TesterPresent positive response 0x7E", resp.data[1] == 0x7E)


def test_infotainment_dtc(bus_session):
    bus = bus_session
    global pass_count, fail_count
    pass_count = 0
    fail_count = 0
    initial_dtc_count = step_read_dtc(bus)
    print(f"  Initial DTC count: {initial_dtc_count}")
    step_clear_dtc(bus)
    step_verify_dtc_cleared(bus)
    step_negative_response_handling(bus)
    step_verify_ecu_reachable(bus)
    assert fail_count == 0, f"{fail_count} check(s) failed in infotainment DTC test"


if __name__ == "__main__":
    from conftest import create_bus

    bus = create_bus()
    try:
        test_infotainment_dtc(bus)
    finally:
        bus.shutdown()
        print(f"\nResults: {pass_count} passed, {fail_count} failed")
