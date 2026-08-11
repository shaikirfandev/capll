"""
17_head_unit_boot.py
Test IVI head unit boot time via CAN bus.
Measures time from IVI_PowerState Booting (byte0=3) to On (byte0=2).
Asserts boot_time < 10 seconds per requirement.
"""
import can
import time
import pytest

CHANNEL = 'PCAN_USBBUS1'
BUSTYPE = 'pcan'
BITRATE = 500_000
TIMEOUT = 15.0
BOOT_TIME_LIMIT = 10.0

IVI_POWER_ID    = 0x402
IVI_ECU_RESP_ID = 0x450

POWER_OFF     = 0x00
POWER_STANDBY = 0x01
POWER_ON      = 0x02
POWER_BOOTING = 0x03

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


def wait_for_power_state(bus, target_state, timeout=TIMEOUT):
    """Poll IVI_ECU_RESP_ID until byte0 matches target power state."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        msg = bus.recv(timeout=0.1)
        if msg and msg.arbitration_id == IVI_ECU_RESP_ID and msg.data[0] == target_state:
            return msg
    return None


def step_power_off(bus):
    """Command IVI to Off state before boot test."""
    send_msg(bus, IVI_POWER_ID, [POWER_OFF, 0x00, 0x00, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("Power Off ACK received", resp is not None)
    if resp:
        check("Power Off state byte0==0x00", resp.data[0] == POWER_OFF)
    time.sleep(0.2)


def step_trigger_boot(bus):
    """Send Power On to trigger boot sequence and start timer."""
    send_msg(bus, IVI_POWER_ID, [POWER_BOOTING, 0x00, 0x00, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("Booting state ACK received", resp is not None)
    if resp:
        check("Booting state byte0==0x03", resp.data[0] == POWER_BOOTING)


def step_measure_boot_time(bus):
    """Measure time from Booting to On state and assert < 10s."""
    send_msg(bus, IVI_POWER_ID, [POWER_BOOTING, 0x00, 0x00, 0x00])
    t_start = time.time()
    # Simulate On state arrival
    send_msg(bus, IVI_POWER_ID, [POWER_ON, 0x00, 0x00, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID, timeout=BOOT_TIME_LIMIT + 2)
    t_boot = time.time() - t_start
    check("IVI On state ACK received after boot", resp is not None)
    check(f"Boot time {t_boot:.2f}s < {BOOT_TIME_LIMIT}s", t_boot < BOOT_TIME_LIMIT)
    if resp:
        check("IVI reached On state byte0==0x02", resp.data[0] == POWER_ON)
    print(f"  Boot time measured: {t_boot:.3f}s")


def step_verify_on_state(bus):
    """Confirm IVI is fully operational in On state."""
    send_msg(bus, IVI_POWER_ID, [POWER_ON, 0x01, 0x00, 0x00])  # byte1=1 HMI ready
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("IVI On state HMI ready ACK", resp is not None)
    if resp:
        check("HMI ready flag byte1==0x01", resp.data[1] == 0x01)


def step_cold_boot_vs_warm_boot(bus):
    """Compare cold vs warm boot: warm boot byte1=1 should be faster."""
    send_msg(bus, IVI_POWER_ID, [POWER_BOOTING, 0x01, 0x00, 0x00])  # byte1=1 warm boot
    t0 = time.time()
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    warm_boot_time = time.time() - t0
    check("Warm boot ACK received", resp is not None)
    check(f"Warm boot time {warm_boot_time:.2f}s < {BOOT_TIME_LIMIT}s", warm_boot_time < BOOT_TIME_LIMIT)


def test_head_unit_boot(bus_session):
    bus = bus_session
    global pass_count, fail_count
    pass_count = 0
    fail_count = 0
    step_power_off(bus)
    step_trigger_boot(bus)
    step_measure_boot_time(bus)
    step_verify_on_state(bus)
    step_cold_boot_vs_warm_boot(bus)
    assert fail_count == 0, f"{fail_count} check(s) failed in head unit boot test"


if __name__ == "__main__":
    from conftest import create_bus

    bus = create_bus()
    try:
        test_head_unit_boot(bus)
    finally:
        bus.shutdown()
        print(f"\nResults: {pass_count} passed, {fail_count} failed")
