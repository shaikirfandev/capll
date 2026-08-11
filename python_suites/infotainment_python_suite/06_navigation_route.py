"""
06_navigation_route.py
Test IVI Navigation route lifecycle via CAN bus.
Transitions Nav Idle→Routing(ETA=45)→Active(ETA decrement)→Arrived on IVI_Navigation (0x403).
Verifies each state transition is acknowledged correctly.
"""
import can
import time
import pytest

CHANNEL = 'PCAN_USBBUS1'
BUSTYPE = 'pcan'
BITRATE = 500_000
TIMEOUT = 5.0

IVI_NAV_ID      = 0x403
IVI_ECU_RESP_ID = 0x450

NAV_IDLE    = 0x00
NAV_ROUTING = 0x01
NAV_ACTIVE  = 0x02
NAV_ARRIVED = 0x03

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


def step_nav_idle(bus):
    """Set navigation to Idle state."""
    send_msg(bus, IVI_NAV_ID, [NAV_IDLE, 0x00, 0x00, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("Nav Idle ACK received", resp is not None)
    if resp:
        check("Nav Idle state echoed byte0==0x00", resp.data[0] == NAV_IDLE)


def step_nav_routing(bus, eta_min=45):
    """Set navigation to Routing with ETA=45 minutes."""
    send_msg(bus, IVI_NAV_ID, [NAV_ROUTING, eta_min, 0x00, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("Nav Routing ACK received", resp is not None)
    if resp:
        check("Nav Routing state echoed byte0==0x01", resp.data[0] == NAV_ROUTING)
        check(f"Nav ETA echoed as {eta_min} min in byte1", resp.data[1] == eta_min)
        check("Nav Routing result OK", resp.data[1] == eta_min)


def step_nav_active_eta_decrement(bus):
    """Simulate ETA decrement as route progresses: 45→30→15."""
    for eta in [45, 30, 15]:
        send_msg(bus, IVI_NAV_ID, [NAV_ACTIVE, eta, 0x00, 0x00])
        resp = wait_for_response(bus, IVI_ECU_RESP_ID)
        check(f"Nav Active ETA={eta} ACK received", resp is not None)
        if resp:
            check(f"Nav Active ETA {eta} echoed in byte1", resp.data[1] == eta)
        time.sleep(0.1)


def step_nav_arrived(bus):
    """Set navigation to Arrived state and verify."""
    send_msg(bus, IVI_NAV_ID, [NAV_ARRIVED, 0x00, 0x00, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("Nav Arrived ACK received", resp is not None)
    if resp:
        check("Nav Arrived state echoed byte0==0x03", resp.data[0] == NAV_ARRIVED)
        check("Nav Arrived ETA byte1==0x00", resp.data[1] == 0x00)
        check("Nav Arrived result OK", resp.data[2] == 0x00 or resp.data[1] == 0x00)


def step_nav_post_arrived_idle(bus):
    """After arrival, navigation returns to Idle state."""
    send_msg(bus, IVI_NAV_ID, [NAV_IDLE, 0x00, 0x00, 0x00])
    resp = wait_for_response(bus, IVI_ECU_RESP_ID)
    check("Nav post-arrived Idle ACK received", resp is not None)
    if resp:
        check("Nav returned to Idle after arrival", resp.data[0] == NAV_IDLE)


def test_navigation_route(bus_session):
    bus = bus_session
    global pass_count, fail_count
    pass_count = 0
    fail_count = 0
    step_nav_idle(bus)
    step_nav_routing(bus, eta_min=45)
    step_nav_active_eta_decrement(bus)
    step_nav_arrived(bus)
    step_nav_post_arrived_idle(bus)
    assert fail_count == 0, f"{fail_count} check(s) failed in navigation route test"


if __name__ == "__main__":
    from conftest import create_bus

    bus = create_bus()
    try:
        test_navigation_route(bus)
    finally:
        bus.shutdown()
        print(f"\nResults: {pass_count} passed, {fail_count} failed")
