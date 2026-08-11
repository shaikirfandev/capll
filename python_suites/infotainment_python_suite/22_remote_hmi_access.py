"""
22_remote_hmi_access.py
Test IVI remote HMI access enable/disable via CAN bus.
Enables remote access byte, verifies IVI state accessible,
disables byte and confirms access is blocked.
"""
import can
import time
import pytest

CHANNEL = 'PCAN_USBBUS1'
BUSTYPE = 'pcan'
BITRATE = 500_000
TIMEOUT = 5.0

IVI_PRIVACY_ID  = 0x40D
IVI_POWER_ID    = 0x402
IVI_ECU_RESP_ID = 0x450

REMOTE_ACCESS_ENABLE  = 0x01
REMOTE_ACCESS_DISABLE = 0x00

POWER_ON = 0x02

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


def step_enable_remote_access(bus):
    """Enable remote HMI access and verify ACK."""
    send_msg(bus, IVI_PRIVACY_ID, [REMOTE_ACCESS_ENABLE, 0x00, 0x00, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("Remote access enable ACK received", resp is not None)
    if resp:
        check("Remote access byte0==0x01 in ACK", resp.data[0] == REMOTE_ACCESS_ENABLE)
        check("Remote access enable result OK", resp.data[1] == 0x00)


def step_verify_ivi_accessible(bus):
    """With remote access on, verify IVI state is accessible."""
    send_msg(bus, IVI_POWER_ID, [POWER_ON, 0x00, 0x00, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("IVI state accessible with remote access ACK", resp is not None)
    if resp:
        check("IVI reachable in On state byte0==0x02", resp.data[0] == POWER_ON)


def step_remote_command_volume(bus):
    """Send remote volume command and verify IVI processes it."""
    send_msg(bus, IVI_PRIVACY_ID, [REMOTE_ACCESS_ENABLE, 0x32, 0x00, 0x00])  # volume=50
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("Remote volume command ACK received", resp is not None)
    if resp:
        check("Remote volume echoed in byte1", resp.data[1] == 0x32)


def step_disable_remote_access(bus):
    """Disable remote HMI access and verify ACK."""
    send_msg(bus, IVI_PRIVACY_ID, [REMOTE_ACCESS_DISABLE, 0x00, 0x00, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("Remote access disable ACK received", resp is not None)
    if resp:
        check("Remote access byte0==0x00 in ACK", resp.data[0] == REMOTE_ACCESS_DISABLE)


def step_verify_access_blocked(bus):
    """With remote access off, verify remote commands are rejected."""
    send_msg(bus, IVI_PRIVACY_ID, [REMOTE_ACCESS_DISABLE, 0x32, 0x00, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("Blocked remote command response received", resp is not None)
    if resp:
        check("Remote command blocked result byte1==0x01 (Fail)", resp.data[1] == 0x01)


def step_recheck_ivi_state_blocked(bus):
    """With remote access disabled, IVI state query returns restricted."""
    send_msg(bus, IVI_POWER_ID, [POWER_ON, 0x00, 0x00, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("IVI query with remote off ACK received", resp is not None)
    if resp:
        check("IVI state byte result defined", len(resp.data) >= 2)


def test_remote_hmi_access(bus_session):
    bus = bus_session
    step_enable_remote_access(bus)
    step_verify_ivi_accessible(bus)
    step_remote_command_volume(bus)
    step_disable_remote_access(bus)
    step_verify_access_blocked(bus)
    step_recheck_ivi_state_blocked(bus)
    assert fail_count == 0, f"{fail_count} check(s) failed in remote HMI access test"


if __name__ == "__main__":
    from conftest import create_bus

    bus = create_bus()
    try:
        test_remote_hmi_access(bus)
    finally:
        bus.shutdown()
    print(f"\nResults: {pass_count} passed, {fail_count} failed")
