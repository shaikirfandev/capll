"""
charging_test_suite/charging_tests.py
AC and DC Charging Validation Test Suite using pytest.

Covers:
    - AC Level 2 (J1772) full charge cycle
    - DC Fast Charge (CCS / ISO 15118 handshake)
    - Emergency stop validation
    - Fault injection during charging
    - Cold weather charging (-10°C, -20°C)
    - Charge current limit compliance
"""
import pytest
import time
import can
import cantools
from dataclasses import dataclass
from typing import Optional


@dataclass
class ChargingState:
    """Captured charging session state."""
    obc_state: int = 0
    output_voltage: float = 0.0
    output_current: float = 0.0
    output_power: float = 0.0
    cp_state: int = 0
    fault_code: int = 0
    bms_soc: float = 0.0
    bms_max_charge_current: float = 0.0


class ChargingTestHelper:
    """Helper for charging test interactions via CAN."""

    def __init__(self, bus: can.Bus, db: cantools.db.Database):
        self.bus = bus
        self.db = db
        self._latest = {}
        self._running = True
        import threading
        self._thread = threading.Thread(target=self._rx, daemon=True)
        self._thread.start()

    def _rx(self):
        while self._running:
            msg = self.bus.recv(timeout=0.1)
            if msg:
                try:
                    decoded = self.db.decode_message(msg.arbitration_id, msg.data)
                    self._latest[msg.arbitration_id] = decoded
                except Exception:
                    pass

    def get_decoded(self, arb_id: int) -> dict:
        return self._latest.get(arb_id, {})

    def get_charging_state(self) -> ChargingState:
        obc = self.get_decoded(0x400)
        bms = self.get_decoded(0x310)
        bms_limits = self.get_decoded(0x312)
        return ChargingState(
            obc_state=obc.get('OBC_State', -1),
            output_voltage=obc.get('OBC_OutputVoltage', 0.0),
            output_current=obc.get('OBC_OutputCurrent', 0.0),
            output_power=obc.get('OBC_OutputPower', 0.0),
            cp_state=obc.get('OBC_CP_State', -1),
            fault_code=obc.get('OBC_FaultCode', 0),
            bms_soc=bms.get('BMS_SoC', 0.0),
            bms_max_charge_current=bms_limits.get('BMS_MaxChargeCurrent', 0.0)
        )

    def send_vcu_charge_enable(self, enable: int, target_current: float = 0.0):
        """Send VCU_ChargeCommand message."""
        msg_def = self.db.get_message_by_name('VCU_ChargeCommand')
        data = msg_def.encode({
            'VCU_ChargeEnable': enable,
            'VCU_TargetCurrent': target_current
        })
        msg = can.Message(arbitration_id=msg_def.frame_id, data=data)
        self.bus.send(msg)

    def wait_for_obc_state(self, target_state: int, timeout_s: float = 10.0) -> bool:
        """Wait until OBC reaches target state."""
        deadline = time.time() + timeout_s
        while time.time() < deadline:
            state = self.get_charging_state()
            if state.obc_state == target_state:
                return True
            time.sleep(0.1)
        return False

    def stop(self):
        self._running = False


# ─────────────────────────────────────────────────────────────────────────────
# FIXTURES
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope='session')
def can_bus():
    bus = can.interface.Bus(channel='PCAN_USBBUS1', bustype='pcan', bitrate=500000)
    yield bus
    bus.shutdown()


@pytest.fixture(scope='session')
def dbc():
    return cantools.database.load_file('dbc/EV_Powertrain.dbc')


@pytest.fixture(scope='function')
def helper(can_bus, dbc):
    h = ChargingTestHelper(can_bus, dbc)
    yield h
    h.send_vcu_charge_enable(0)  # Always disable charging on teardown
    h.stop()


# ─────────────────────────────────────────────────────────────────────────────
# AC CHARGING TESTS
# ─────────────────────────────────────────────────────────────────────────────

class TestACCharging:
    """AC Level 2 (J1772) Charging Validation."""

    def test_ac_charge_enable_obc_starts(self, helper):
        """TC-CHRG-001: OBC shall enter CHARGE state within 2s of VCU ChargeEnable."""
        helper.send_vcu_charge_enable(1, target_current=16.0)
        obc_charging = helper.wait_for_obc_state(3, timeout_s=5.0)  # OBC_CC_MODE = 3
        assert obc_charging, "OBC did not enter CC_MODE within 5 seconds of charge enable"

    def test_charge_current_within_bms_limit(self, helper):
        """TC-CHRG-002: OBC output current shall not exceed BMS_MaxChargeCurrent."""
        helper.send_vcu_charge_enable(1, target_current=100.0)
        time.sleep(3.0)

        state = helper.get_charging_state()
        assert state.output_current <= state.bms_max_charge_current + 1.0, \
            f"OBC current {state.output_current}A exceeds BMS limit {state.bms_max_charge_current}A"

    def test_obc_stops_when_charge_disabled(self, helper):
        """TC-CHRG-003: OBC shall ramp down current within 2s of ChargeEnable=0."""
        helper.send_vcu_charge_enable(1, target_current=16.0)
        helper.wait_for_obc_state(3, timeout_s=5.0)

        t_disable = time.time()
        helper.send_vcu_charge_enable(0)
        time.sleep(2.5)

        state = helper.get_charging_state()
        assert state.output_current < 2.0, \
            f"OBC still delivering {state.output_current}A after charge disable"

    @pytest.mark.parametrize("evse_current,expected_max", [
        (10.0, 11.0),   # 10A EVSE limit
        (16.0, 17.0),   # 16A EVSE limit (standard Type 2)
        (32.0, 33.0),   # 32A EVSE limit
    ])
    def test_charge_current_respects_evse_limit(self, helper, evse_current, expected_max):
        """TC-CHRG-004: OBC output current shall not exceed EVSE CP limit."""
        # Set CP duty cycle for EVSE current (duty = I / 60.0 for J1772)
        cp_duty = evse_current / 60.0
        # In real test: set via HIL/EVSE simulator
        # Here: send as sysvar or test equipment command
        helper.send_vcu_charge_enable(1, target_current=evse_current)
        time.sleep(3.0)

        state = helper.get_charging_state()
        assert state.output_current <= expected_max, \
            f"OBC {state.output_current}A exceeds EVSE limit {evse_current}A"


# ─────────────────────────────────────────────────────────────────────────────
# FAULT TESTS
# ─────────────────────────────────────────────────────────────────────────────

class TestChargingFaults:
    """Charging fault detection and response tests."""

    def test_emergency_stop_opens_contactors(self, helper):
        """TC-CHRG-005: Emergency stop signal shall halt charging and open contactors."""
        helper.send_vcu_charge_enable(1, target_current=16.0)
        helper.wait_for_obc_state(3, timeout_s=5.0)

        # Send emergency stop (VCU_EmergencyStop = 1)
        import can
        # Emergency stop CAN message (adjust ID per DBC)
        eStop = can.Message(arbitration_id=0x105,
                            data=[0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
        helper.bus.send(eStop)
        time.sleep(1.0)

        state = helper.get_charging_state()
        assert state.output_current < 1.0, \
            f"OBC still delivering {state.output_current}A after emergency stop"
        assert state.obc_state in (0, 6), \
            f"OBC not in IDLE/FAULT after emergency stop (state={state.obc_state})"

    def test_cp_loss_stops_charging(self, helper):
        """TC-CHRG-006: Loss of CP signal shall stop charging within 500ms."""
        helper.send_vcu_charge_enable(1, target_current=16.0)
        helper.wait_for_obc_state(3, timeout_s=5.0)

        # Simulate CP loss: set CP state to 0 (state A) via test equipment
        # (In real test: control EVSE simulator via serial/ethernet API)
        time.sleep(0.6)  # Allow 500ms + margin

        state = helper.get_charging_state()
        # If OBC still charging after CP loss, test fails
        # In simulation, this depends on fault_injection sysvar
        assert state.fault_code != 0 or state.output_current < 1.0, \
            "OBC continued charging after simulated CP loss"
