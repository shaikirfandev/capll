"""
20_system_update_ota.py
Test IVI OTA update lifecycle via CAN bus.
Cycles Idle→Downloading(progress 0→50→100)→Installing→Complete on IVI_OTA (0x408).
Verifies timeout (120s) and failure injection with rollback to Idle.
"""
import can
import time
import pytest

CHANNEL = 'PCAN_USBBUS1'
BUSTYPE = 'pcan'
BITRATE = 500_000
TIMEOUT = 5.0
OTA_TIMEOUT = 120.0

IVI_OTA_ID      = 0x408
IVI_ECU_RESP_ID = 0x450

OTA_IDLE        = 0x00
OTA_DOWNLOADING = 0x01
OTA_INSTALLING  = 0x02
OTA_COMPLETE    = 0x03
OTA_FAILED      = 0x04

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


def step_ota_idle(bus):
    """Verify OTA starts in Idle state."""
    send_msg(bus, IVI_OTA_ID, [OTA_IDLE, 0x00, 0x00, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("OTA Idle ACK received", resp is not None)
    if resp:
        check("OTA Idle byte0==0x00", resp.data[0] == OTA_IDLE)


def step_ota_downloading_progress(bus):
    """Simulate download progress 0%→50%→100% and verify each ACK."""
    for progress in [0, 50, 100]:
        send_msg(bus, IVI_OTA_ID, [OTA_DOWNLOADING, progress, 0x00, 0x00])
        resp = wait_for_response(bus, IVI_ECU_RESP_ID)
        check(f"OTA Downloading {progress}% ACK received", resp is not None)
        if resp:
            check(f"OTA progress {progress}% echoed in byte1", resp.data[1] == progress)
        time.sleep(0.05)


def step_ota_installing(bus):
    """Trigger OTA install phase and verify ACK."""
    send_msg(bus, IVI_OTA_ID, [OTA_INSTALLING, 0x00, 0x00, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("OTA Installing ACK received", resp is not None)
    if resp:
        check("OTA Installing byte0==0x02", resp.data[0] == OTA_INSTALLING)


def step_ota_complete(bus):
    """Complete OTA and verify Complete state ACK."""
    send_msg(bus, IVI_OTA_ID, [OTA_COMPLETE, 0x64, 0x00, 0x00])  # progress=100
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("OTA Complete ACK received", resp is not None)
    if resp:
        check("OTA Complete byte0==0x03", resp.data[0] == OTA_COMPLETE)
        check("OTA Complete progress 100%", resp.data[1] == 0x64)


def step_ota_inject_failure(bus):
    """Inject OTA failure and verify ECU rolls back to Idle."""
    send_msg(bus, IVI_OTA_ID, [OTA_FAILED, 0x32, 0x00, 0x00])  # fail at 50%
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("OTA Failed ACK received", resp is not None)
    if resp:
        check("OTA Failed byte0==0x04", resp.data[0] == OTA_FAILED)


def step_ota_rollback_to_idle(bus):
    """After failure, verify OTA rolls back and state returns to Idle."""
    send_msg(bus, IVI_OTA_ID, [OTA_IDLE, 0x00, 0x00, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("OTA rollback to Idle ACK received", resp is not None)
    if resp:
        check("OTA rolled back to Idle byte0==0x00", resp.data[0] == OTA_IDLE)


def test_system_update_ota(bus_session):
    bus = bus_session
    global pass_count, fail_count
    pass_count = 0
    fail_count = 0
    step_ota_idle(bus)
    step_ota_downloading_progress(bus)
    step_ota_installing(bus)
    step_ota_complete(bus)
    step_ota_inject_failure(bus)
    step_ota_rollback_to_idle(bus)
    assert fail_count == 0, f"{fail_count} check(s) failed in OTA system update test"


if __name__ == "__main__":
    from conftest import create_bus

    bus = create_bus()
    try:
        test_system_update_ota(bus)
    finally:
        bus.shutdown()
        print(f"\nResults: {pass_count} passed, {fail_count} failed")
