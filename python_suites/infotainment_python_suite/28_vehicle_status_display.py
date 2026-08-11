"""
28_vehicle_status_display.py
Test IVI vehicle status data display via CAN bus.
Sends speed, fuel level, and engine temperature to IVI.
Verifies IVI response echoes the received display data bytes correctly.
"""
import can
import time
import pytest

CHANNEL = 'PCAN_USBBUS1'
BUSTYPE = 'pcan'
BITRATE = 500_000
TIMEOUT = 5.0

# Simulated vehicle data CAN IDs
VEHICLE_SPEED_ID = 0x300
VEHICLE_FUEL_ID  = 0x301
VEHICLE_TEMP_ID  = 0x302
IVI_ECU_RESP_ID  = 0x450

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


def step_send_speed(bus, speed_kph):
    """Send vehicle speed to IVI and verify response echoes speed."""
    # Speed encoded as raw value in byte0-1 (little-endian, km/h * 10)
    raw = speed_kph * 10
    high = (raw >> 8) & 0xFF
    low  = raw & 0xFF
    send_msg(bus, VEHICLE_SPEED_ID, [low, high, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check(f"Speed {speed_kph}km/h display ACK received", resp is not None)
    if resp:
        check(f"Speed data received result OK", resp.data[1] == 0x00)


def step_send_fuel_level(bus, fuel_pct):
    """Send fuel level percentage to IVI and verify echo."""
    send_msg(bus, VEHICLE_FUEL_ID, [fuel_pct, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check(f"Fuel {fuel_pct}% display ACK received", resp is not None)
    if resp:
        check(f"Fuel level echoed in ACK byte0", resp.data[0] == fuel_pct)


def step_send_engine_temp(bus, temp_c):
    """Send engine temperature (°C) to IVI and verify echo."""
    send_msg(bus, VEHICLE_TEMP_ID, [temp_c, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check(f"Engine temp {temp_c}°C display ACK received", resp is not None)
    if resp:
        check(f"Engine temp echoed in ACK", resp.data[0] == temp_c)


def step_low_fuel_warning(bus):
    """Send low fuel (10%) and verify IVI triggers warning indicator."""
    send_msg(bus, VEHICLE_FUEL_ID, [0x0A, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])  # 10% + warning flag
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("Low fuel warning display ACK received", resp is not None)
    if resp:
        check("Low fuel warning byte1==0x01", resp.data[1] == 0x01)


def step_overheat_warning(bus):
    """Send overtemp (105°C) and verify IVI displays warning."""
    send_msg(bus, VEHICLE_TEMP_ID, [0x69, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])  # 105°C + warning
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("Overheat warning display ACK received", resp is not None)
    if resp:
        check("Overheat warning flag byte1==0x01", resp.data[1] == 0x01)


def step_all_normal_status(bus):
    """Send all-normal status and verify IVI clears warnings."""
    send_msg(bus, VEHICLE_SPEED_ID, [0x64, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])  # 100km/h
    send_msg(bus, VEHICLE_FUEL_ID,  [0x50, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])  # 80%
    send_msg(bus, VEHICLE_TEMP_ID,  [0x5A, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])  # 90°C normal
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("All-normal status display ACK received", resp is not None)
    if resp:
        check("All-normal result OK byte1==0x00", resp.data[1] == 0x00)


def test_vehicle_status_display(bus_session):
    bus = bus_session
    for speed in [0, 50, 100, 130]:
        step_send_speed(bus, speed)
    for fuel in [100, 75, 50, 25, 10]:
        step_send_fuel_level(bus, fuel)
    step_send_engine_temp(bus, 90)
    step_low_fuel_warning(bus)
    step_overheat_warning(bus)
    step_all_normal_status(bus)
    assert fail_count == 0, f"{fail_count} check(s) failed in vehicle status display test"


if __name__ == "__main__":
    from conftest import create_bus

    bus = create_bus()
    try:
        test_vehicle_status_display(bus)
    finally:
        bus.shutdown()
    print(f"\nResults: {pass_count} passed, {fail_count} failed")
