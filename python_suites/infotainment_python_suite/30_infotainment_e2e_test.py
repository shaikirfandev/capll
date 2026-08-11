"""
30_infotainment_e2e_test.py
End-to-end IVI infotainment test via CAN bus.
Full sequence:
  power_on → boot <10s → volume_set → source_BT → nav_route
  → call_handle → OTA_download → privacy → power_off
Verifies the complete IVI lifecycle in a single integrated test.
"""
import can
import time
import pytest

CHANNEL = 'PCAN_USBBUS1'
BUSTYPE = 'pcan'
BITRATE = 500_000
TIMEOUT = 5.0
BOOT_TIME_LIMIT = 10.0

IVI_POWER_ID    = 0x402
IVI_VOLUME_ID   = 0x400
IVI_MEDIA_SRC_ID = 0x401
IVI_NAV_ID      = 0x403
IVI_PHONE_ID    = 0x405
IVI_OTA_ID      = 0x408
IVI_PRIVACY_ID  = 0x40D
IVI_ECU_RESP_ID = 0x450

POWER_OFF     = 0x00
POWER_STANDBY = 0x01
POWER_ON      = 0x02
POWER_BOOTING = 0x03

SOURCE_BT = 0x03

NAV_ROUTING = 0x01
NAV_ARRIVED = 0x03

CALL_RINGING = 0x01
CALL_ACTIVE  = 0x02
CALL_IDLE    = 0x00

OTA_IDLE        = 0x00
OTA_DOWNLOADING = 0x01
OTA_COMPLETE    = 0x03

PRIVACY_ON  = 0x01
PRIVACY_OFF = 0x00

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


def e2e_step_power_on_and_boot(bus):
    """E2E Step 1: Power on IVI and verify boot completes within 10s."""
    print("\n[E2E] Step 1: Power On & Boot")
    send_msg(bus, IVI_POWER_ID, [POWER_BOOTING, 0x00, 0x00, 0x00])
    t0 = time.time()
    send_msg(bus, IVI_POWER_ID, [POWER_ON, 0x00, 0x00, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID, timeout=BOOT_TIME_LIMIT + 2)
    boot_time = time.time() - t0
    check("E2E: IVI booted to On state", resp is not None and (resp.data[0] == POWER_ON if resp else False))
    check(f"E2E: Boot time {boot_time:.2f}s < {BOOT_TIME_LIMIT}s", boot_time < BOOT_TIME_LIMIT)


def e2e_step_volume_set(bus):
    """E2E Step 2: Set volume to 50 and verify ACK."""
    print("\n[E2E] Step 2: Volume Set to 50")
    send_msg(bus, IVI_VOLUME_ID, [50, 0x00, 0x00, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("E2E: Volume 50 ACK received", resp is not None)
    if resp:
        check("E2E: Volume 50 echoed in ACK byte0", resp.data[0] == 50)


def e2e_step_source_bluetooth(bus):
    """E2E Step 3: Switch to Bluetooth source and verify connected."""
    print("\n[E2E] Step 3: Source → Bluetooth")
    send_msg(bus, IVI_MEDIA_SRC_ID, [SOURCE_BT, 0x00, 0x00, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("E2E: BT source ACK received", resp is not None)
    if resp:
        check("E2E: BT source byte0==0x03 echoed", resp.data[0] == SOURCE_BT)


def e2e_step_nav_route(bus):
    """E2E Step 4: Start navigation route and verify active."""
    print("\n[E2E] Step 4: Navigation Route Active")
    send_msg(bus, IVI_NAV_ID, [NAV_ROUTING, 0x1E, 0x00, 0x00])  # ETA=30min
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("E2E: Nav routing ACK received", resp is not None)
    if resp:
        check("E2E: Nav Routing state byte0==0x01", resp.data[0] == NAV_ROUTING)


def e2e_step_call_handle(bus):
    """E2E Step 5: Handle incoming call → answer → end."""
    print("\n[E2E] Step 5: Phone Call – Ring → Answer → End")
    send_msg(bus, IVI_PHONE_ID, [CALL_RINGING, 0x04, 0x00, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("E2E: Incoming ring ACK received", resp is not None)
    send_msg(bus, IVI_PHONE_ID, [CALL_ACTIVE, 0x04, 0x00, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("E2E: Call answered ACK received", resp is not None)
    send_msg(bus, IVI_PHONE_ID, [CALL_IDLE, 0x00, 0x00, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("E2E: Call ended ACK received", resp is not None)
    if resp:
        check("E2E: Call idle state byte0==0x00", resp.data[0] == CALL_IDLE)


def e2e_step_ota_download(bus):
    """E2E Step 6: OTA download 0→100% progress."""
    print("\n[E2E] Step 6: OTA Download 0% → 100%")
    for progress in [0, 50, 100]:
        send_msg(bus, IVI_OTA_ID, [OTA_DOWNLOADING, progress, 0x00, 0x00])
        resp = wait_for_response(bus, IVI_ECU_RESP_ID)
        check(f"E2E: OTA {progress}% ACK received", resp is not None)
    send_msg(bus, IVI_OTA_ID, [OTA_COMPLETE, 0x64, 0x00, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("E2E: OTA Complete ACK received", resp is not None)
    if resp:
        check("E2E: OTA Complete byte0==0x03", resp.data[0] == OTA_COMPLETE)


def e2e_step_privacy_mode(bus):
    """E2E Step 7: Enable then disable privacy mode."""
    print("\n[E2E] Step 7: Privacy Mode ON → OFF")
    send_msg(bus, IVI_PRIVACY_ID, [PRIVACY_ON, 0x00, 0x00, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("E2E: Privacy ON ACK received", resp is not None)
    time.sleep(0.1)
    send_msg(bus, IVI_PRIVACY_ID, [PRIVACY_OFF, 0x00, 0x00, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("E2E: Privacy OFF ACK received", resp is not None)
    if resp:
        check("E2E: Privacy OFF byte0==0x00", resp.data[0] == PRIVACY_OFF)


def e2e_step_power_off(bus):
    """E2E Step 8: Power off IVI and verify shutdown."""
    print("\n[E2E] Step 8: Power Off")
    send_msg(bus, IVI_POWER_ID, [POWER_OFF, 0x00, 0x00, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("E2E: Power Off ACK received", resp is not None)
    if resp:
        check("E2E: IVI shut down byte0==0x00", resp.data[0] == POWER_OFF)


def test_infotainment_e2e(bus_session):
    bus = bus_session
    global pass_count, fail_count
    pass_count = 0
    fail_count = 0
    e2e_step_power_on_and_boot(bus)
    e2e_step_volume_set(bus)
    e2e_step_source_bluetooth(bus)
    e2e_step_nav_route(bus)
    e2e_step_call_handle(bus)
    e2e_step_ota_download(bus)
    e2e_step_privacy_mode(bus)
    e2e_step_power_off(bus)
    print(f"\n[E2E Summary] {pass_count} passed, {fail_count} failed")
    assert fail_count == 0, f"{fail_count} check(s) failed in E2E infotainment test"


if __name__ == "__main__":
    from conftest import create_bus

    bus = create_bus()
    try:
        test_infotainment_e2e(bus)
    finally:
        bus.shutdown()
        print(f"\nFinal Results: {pass_count} passed, {fail_count} failed")
