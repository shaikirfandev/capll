#!/usr/bin/env python3
"""
FILE:    04_bms_python_automation.py
PURPOSE: BMS HIL Test Automation using Python + CANoe COM API
         - Full BMS test suite with pytest framework
         - Automated test case execution via CANoe
         - Result reporting with HTML output
         - Test categories: Voltage, Temperature, SoC, Contactor, Balancing

DEPENDENCIES:
    pip install python-can pytest pytest-html openpyxl colorama

USAGE:
    pytest 04_bms_python_automation.py -v --html=bms_report.html

AUTHOR: BMS Validation Team
DATE:   2026-04-19
"""

import time
import logging
import subprocess
from dataclasses import dataclass, field
from typing import Optional
from enum import IntEnum

import pytest

# ── Logger setup ──────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)-8s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("BMS_TEST")


# ─────────────────────────────────────────────────────────────────────────────
# 1.  CANoe COM Interface Wrapper
# ─────────────────────────────────────────────────────────────────────────────
class CANoeInterface:
    """
    Thin wrapper around the Vector CANoe COM API.
    Provides: start/stop measurement, read/write system variables, wait for signals.
    """

    def __init__(self, cfg_path: str):
        self.cfg_path = cfg_path
        self._app = None
        self._measurement = None
        self._connected = False

    def connect(self) -> bool:
        try:
            import win32com.client  # pywin32
            self._app = win32com.client.Dispatch("CANoe.Application")
            self._app.Open(self.cfg_path)
            self._measurement = self._app.Measurement
            self._connected = True
            logger.info("CANoe connected: %s", self.cfg_path)
            return True
        except Exception as exc:
            logger.warning("CANoe COM not available (%s) — using SIMULATION mode", exc)
            self._connected = False
            return False

    def start_measurement(self):
        if self._connected:
            self._measurement.Start()
            time.sleep(2.0)
            logger.info("Measurement started")
        else:
            logger.info("[SIM] Measurement started")

    def stop_measurement(self):
        if self._connected:
            self._measurement.Stop()
            logger.info("Measurement stopped")

    def set_sysvar(self, namespace: str, variable: str, value) -> None:
        """Write a CANoe system variable."""
        if self._connected:
            ns = self._app.System.Namespaces(namespace)
            ns.Variables(variable).Value = value
        logger.debug("[SYSVAR] %s::%s = %s", namespace, variable, value)

    def get_sysvar(self, namespace: str, variable: str):
        """Read a CANoe system variable."""
        if self._connected:
            ns = self._app.System.Namespaces(namespace)
            return ns.Variables(variable).Value
        # Simulation: return a plausible default
        sim_defaults = {
            ("BMS_DTC", "LastDTC_Code"): 0x0000,
            ("BMS_UDS",  "SoC"):         75.0,
            ("BMS_UDS",  "PackVoltage"): 395.0,
            ("BMS_Sim",  "Precharge_Current"): 0.1,
            ("BMS_Sim",  "VDcLink"):     380.0,
        }
        return sim_defaults.get((namespace, variable), 0)

    def wait_for_sysvar(self, namespace: str, variable: str,
                        expected, timeout_s: float = 5.0) -> bool:
        """Poll until system variable reaches expected value or timeout."""
        deadline = time.time() + timeout_s
        while time.time() < deadline:
            val = self.get_sysvar(namespace, variable)
            if val == expected:
                logger.debug("[WAIT] %s::%s reached %s", namespace, variable, expected)
                return True
            time.sleep(0.05)
        logger.warning("[WAIT] Timeout waiting %s::%s == %s", namespace, variable, expected)
        return False

    def inject_cell_voltage(self, cell_index: int, voltage_v: float):
        """Inject a specific voltage into a simulated cell."""
        self.set_sysvar("BMS_Sim", f"Cell_Voltage_{cell_index:02d}", voltage_v)
        logger.info("[INJ] Cell[%d] voltage → %.3f V", cell_index, voltage_v)

    def inject_module_temperature(self, module_index: int, temp_c: float):
        """Inject a temperature into a battery module."""
        self.set_sysvar("BMS_Sim", f"Module_Temp_{module_index}", temp_c)
        logger.info("[INJ] Module[%d] temp → %.1f °C", module_index, temp_c)

    def restore_nominal_conditions(self, num_cells: int = 96, num_modules: int = 8):
        """Restore all cells to nominal voltage and temperature."""
        for i in range(num_cells):
            self.inject_cell_voltage(i, 3.65)
        for i in range(num_modules):
            self.inject_module_temperature(i, 25.0)
        logger.info("[RESTORE] All cells → 3.65 V, all modules → 25.0 °C")

    def get_last_dtc(self) -> int:
        """Return the last DTC code stored by the BMS."""
        return int(self.get_sysvar("BMS_DTC", "LastDTC_Code"))

    def get_contactor_state(self, name: str) -> int:
        """Return 0/1 state of named contactor."""
        return int(self.get_sysvar("BMS_Control", f"{name}_State"))

    def get_power_derate_pct(self) -> float:
        return float(self.get_sysvar("BMS_Control", "Power_Derate_Pct"))


# ─────────────────────────────────────────────────────────────────────────────
# 2.  Test Result Data Class
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class TestResult:
    tc_id: str
    description: str
    passed: bool
    actual_value: str = ""
    expected_value: str = ""
    notes: str = ""
    duration_ms: float = 0.0


# ─────────────────────────────────────────────────────────────────────────────
# 3.  pytest Fixtures
# ─────────────────────────────────────────────────────────────────────────────
@pytest.fixture(scope="session")
def canoe():
    """Session-wide CANoe connection."""
    interface = CANoeInterface(r"C:\CANoe_Projects\BMS_HIL\BMS_HIL.cfg")
    interface.connect()
    interface.start_measurement()
    time.sleep(1.0)
    yield interface
    interface.stop_measurement()


@pytest.fixture(autouse=True)
def restore_conditions(canoe):
    """Restore nominal conditions before every test."""
    canoe.restore_nominal_conditions()
    time.sleep(0.3)
    yield
    canoe.restore_nominal_conditions()
    time.sleep(0.1)


# ─────────────────────────────────────────────────────────────────────────────
# 4.  Cell Voltage Tests
# ─────────────────────────────────────────────────────────────────────────────
class TestBMSCellVoltage:
    """Test suite: TC_BMS_OV & TC_BMS_UV"""

    def test_TC_BMS_OV_001_ov1_warning(self, canoe):
        """OV1 warning: inject 4.21 V on Cell 7 → DTC P0A0D logged, 80% derating."""
        canoe.inject_cell_voltage(6, 4.21)     # Cell index 6 = Cell 7
        time.sleep(0.5)

        dtc   = canoe.get_last_dtc()
        derate = canoe.get_power_derate_pct()

        assert dtc == 0x0A0D, f"Expected DTC 0x0A0D, got 0x{dtc:04X}"
        assert derate <= 80.0, f"Expected power derate ≤ 80%, got {derate:.1f}%"
        logger.info("PASS | DTC=0x%04X | Derate=%.1f%%", dtc, derate)

    def test_TC_BMS_OV_002_ov2_contactor_open(self, canoe):
        """OV2 critical: inject 4.26 V → contactor opens within 100 ms."""
        t_start = time.time()
        canoe.inject_cell_voltage(6, 4.26)

        opened = canoe.wait_for_sysvar("BMS_Control", "MainPlus_State", 0, timeout_s=0.5)
        elapsed_ms = (time.time() - t_start) * 1000

        assert opened, "Main+ contactor did not open after OV2 fault"
        assert elapsed_ms <= 100, f"Contactor open time {elapsed_ms:.1f} ms > 100 ms"
        assert canoe.get_last_dtc() == 0x0A0E, "DTC P0A0E not logged"
        logger.info("PASS | Contactor opened in %.1f ms", elapsed_ms)

    def test_TC_BMS_OV_003_ov2_single_cell_in_pack(self, canoe):
        """OV2 with 95 cells at nominal — only Cell 1 at 4.26 V → same OV2 response."""
        # All cells are already nominal from fixture; just inject one cell
        canoe.inject_cell_voltage(0, 4.26)
        time.sleep(0.2)

        assert canoe.get_last_dtc() == 0x0A0E, "DTC P0A0E not logged for single-cell OV2"

    def test_TC_BMS_OV_004_noise_spike_no_fault(self, canoe):
        """Short OV spike (4.24 V for 5 ms) — should not trigger fault (below debounce)."""
        canoe.inject_cell_voltage(10, 4.24)
        time.sleep(0.005)                          # 5 ms — less than debounce
        canoe.inject_cell_voltage(10, 3.75)        # Restore
        time.sleep(0.3)

        dtc = canoe.get_last_dtc()
        assert dtc not in (0x0A0D, 0x0A0E), \
            f"Spurious DTC 0x{dtc:04X} logged for sub-debounce spike"
        logger.info("PASS | No DTC logged for noise spike")

    def test_TC_BMS_OV_005_ov2_recovery(self, canoe):
        """After OV2 recovery, DTC should clear and contactors can re-close."""
        canoe.inject_cell_voltage(6, 4.26)
        time.sleep(0.3)
        canoe.inject_cell_voltage(6, 3.75)         # Restore below OV1
        time.sleep(1.0)                             # Wait for debounce clear + hysteresis

        assert canoe.get_sysvar("BMS_Control", "MainPlus_State") == 1, \
            "Main+ contactor did not re-close after OV2 recovery"

    def test_TC_BMS_UV_001_uv1_warning(self, canoe):
        """UV1 warning: inject 2.95 V → DTC logged, 50% derating."""
        canoe.inject_cell_voltage(20, 2.95)
        time.sleep(0.5)

        dtc    = canoe.get_last_dtc()
        derate = canoe.get_power_derate_pct()

        assert dtc in (0x0A0F,), f"Expected UV1 DTC, got 0x{dtc:04X}"
        assert derate <= 50.0, f"Expected derate ≤ 50%, got {derate:.1f}%"

    def test_TC_BMS_UV_002_uv2_contactor_open(self, canoe):
        """UV2 critical: inject 2.45 V → contactor opens."""
        canoe.inject_cell_voltage(20, 2.45)
        opened = canoe.wait_for_sysvar("BMS_Control", "MainPlus_State", 0, timeout_s=0.5)
        assert opened, "Contactor did not open for UV2 fault"


# ─────────────────────────────────────────────────────────────────────────────
# 5.  Temperature Tests
# ─────────────────────────────────────────────────────────────────────────────
class TestBMSTemperature:

    def test_TC_BMS_TEMP_001_ot1_warning(self, canoe):
        """OT1 warning: inject 52°C on Module 0 → DTC P0A1A, cooling max."""
        canoe.inject_module_temperature(0, 52.0)
        time.sleep(0.5)

        dtc     = canoe.get_last_dtc()
        cooling = canoe.get_sysvar("BMS_Control", "Cooling_Duty_Pct")
        derate  = canoe.get_power_derate_pct()

        assert dtc == 0x0A1A, f"Expected DTC 0x0A1A, got 0x{dtc:04X}"
        assert cooling == 100, f"Cooling not at 100%, got {cooling}%"
        assert derate <= 50, f"Expected power derate ≤ 50%, got {derate:.1f}%"

    def test_TC_BMS_TEMP_002_ot2_emergency_shutdown(self, canoe):
        """OT2 emergency: inject 62°C → contactor open, DTC P1A00."""
        canoe.inject_module_temperature(2, 62.0)
        opened = canoe.wait_for_sysvar("BMS_Control", "MainPlus_State", 0, timeout_s=1.0)

        assert opened, "Contactor not opened for OT2 emergency"
        assert canoe.get_last_dtc() == 0x1A00, "DTC P1A00 not logged"

    def test_TC_BMS_TEMP_003_temp_sensor_open_circuit(self, canoe):
        """Temperature sensor open circuit (invalid value) → fail-safe response."""
        # Inject invalid temperature (e.g. -50°C = sensor open circuit on hardware)
        canoe.inject_module_temperature(1, -50.0)
        time.sleep(0.5)

        dtc = canoe.get_last_dtc()
        assert dtc == 0x0A1C, f"Expected sensor fault DTC 0x0A1C, got 0x{dtc:04X}"

    def test_TC_BMS_TEMP_004_low_temp_charge_inhibit(self, canoe):
        """Under-temperature: -25°C → charge inhibited."""
        canoe.inject_module_temperature(0, -25.0)
        time.sleep(0.5)
        charge_allowed = canoe.get_sysvar("BMS_Control", "Charge_Allowed")
        assert charge_allowed == 0, "Charge not inhibited at -25°C"


# ─────────────────────────────────────────────────────────────────────────────
# 6.  State of Charge (SoC) Tests
# ─────────────────────────────────────────────────────────────────────────────
class TestBMSSoC:

    def test_TC_BMS_SOC_001_initial_soc_from_ocv(self, canoe):
        """SoC should be estimated correctly from OCV at startup."""
        # At 3.75 V per cell (nominal open circuit), SoC should be ~75%
        canoe.set_sysvar("BMS_Sim", "Pack_OCV_Mode", 1)
        time.sleep(1.0)
        soc = canoe.get_sysvar("BMS_UDS", "SoC")
        assert 70.0 <= soc <= 80.0, f"Initial SoC from OCV incorrect: {soc:.1f}%"

    def test_TC_BMS_SOC_002_full_charge_soc_100(self, canoe):
        """SoC must reach 100% when all cells reach 4.15 V (CC-CV charge end)."""
        for i in range(96):
            canoe.inject_cell_voltage(i, 4.15)
        canoe.set_sysvar("BMS_Sim", "Pack_Current", -2.0)   # 2A charge current
        time.sleep(2.0)
        soc = canoe.get_sysvar("BMS_UDS", "SoC")
        assert soc >= 99.0, f"SoC at full charge should be 100%, got {soc:.1f}%"

    def test_TC_BMS_SOC_003_deep_discharge_soc_zero(self, canoe):
        """When any cell hits UV2, SoC must be forced to 0%."""
        canoe.inject_cell_voltage(5, 2.45)
        time.sleep(0.5)
        soc = canoe.get_sysvar("BMS_UDS", "SoC")
        assert soc <= 2.0, f"SoC should be ~0% at UV2 cutoff, got {soc:.1f}%"

    def test_TC_BMS_SOC_004_coulomb_counting_accuracy(self, canoe):
        """
        Coulomb counting accuracy over a 60-second constant discharge.
        At 0.5C = 30A, capacity removed = 30 × (60/3600) = 0.5 Ah.
        SoC error must be ≤ ±3%.
        """
        initial_soc = canoe.get_sysvar("BMS_UDS", "SoC")
        nominal_capacity_ah = 60.0
        discharge_current   = 30.0   # 0.5C
        duration_s          = 60.0

        canoe.set_sysvar("BMS_Sim", "Pack_Current", discharge_current)
        time.sleep(duration_s)
        canoe.set_sysvar("BMS_Sim", "Pack_Current", 0.0)

        expected_soc_drop = (discharge_current * duration_s / 3600) / nominal_capacity_ah * 100
        final_soc         = canoe.get_sysvar("BMS_UDS", "SoC")
        actual_drop       = initial_soc - final_soc
        error             = abs(actual_drop - expected_soc_drop)

        assert error <= 3.0, \
            f"SoC error {error:.2f}% exceeds ±3% limit | expected drop={expected_soc_drop:.1f}% actual={actual_drop:.1f}%"
        logger.info("PASS | SoC drop: expected=%.1f%% actual=%.1f%% error=%.2f%%",
                    expected_soc_drop, actual_drop, error)


# ─────────────────────────────────────────────────────────────────────────────
# 7.  Contactor & Precharge Tests
# ─────────────────────────────────────────────────────────────────────────────
class TestBMSContactor:

    def test_TC_BMS_CTR_001_normal_hv_on_sequence(self, canoe):
        """Normal HV ON: DC link must reach ≥95% of battery voltage before Main+ closes."""
        canoe.set_sysvar("VCU_Control", "HV_Request", 1)

        # Wait for HV Ready state
        hv_ready = canoe.wait_for_sysvar("BMS_Control", "HV_Ready", 1, timeout_s=5.0)
        v_dclink  = canoe.get_sysvar("BMS_Sim", "VDcLink")
        v_battery = canoe.get_sysvar("BMS_Sim", "VBattery")

        assert hv_ready, "HV Ready state not reached"
        ratio = v_dclink / v_battery if v_battery > 0 else 0
        assert ratio >= 0.95, \
            f"DC Link ratio {ratio:.3f} < 0.95 — precharge incomplete when Main+ closed"

    def test_TC_BMS_CTR_002_precharge_timeout(self, canoe):
        """Precharge timeout: block V_dclink rise → expect fault and DTC P0A3B."""
        canoe.set_sysvar("BMS_Sim", "Block_VDcLink_Rise", 1)  # Inject block
        canoe.set_sysvar("VCU_Control", "HV_Request", 1)
        time.sleep(3.0)   # Wait beyond 2 s timeout

        assert canoe.get_last_dtc() == 0x0A3B, "DTC P0A3B not logged for precharge timeout"
        main_plus = canoe.get_contactor_state("MainPlus")
        assert main_plus == 0, "Main+ should remain open on precharge timeout"

    def test_TC_BMS_CTR_004_contactor_weld_detection(self, canoe):
        """Weld detection: residual current after precharge open → DTC P0A3A."""
        canoe.set_sysvar("BMS_Sim", "Precharge_Current", 2.5)   # Simulate weld
        canoe.set_sysvar("VCU_Control", "HV_Request", 1)
        time.sleep(1.5)

        assert canoe.get_last_dtc() == 0x0A3A, "DTC P0A3A not logged for weld"

    def test_TC_BMS_CTR_005_emergency_hv_off(self, canoe):
        """Crash signal → all contactors open within 50 ms."""
        canoe.set_sysvar("VCU_Control", "HV_Request", 1)
        canoe.wait_for_sysvar("BMS_Control", "HV_Ready", 1, timeout_s=5.0)

        t_start = time.time()
        canoe.set_sysvar("VCU_Control", "Crash_Signal", 1)
        opened = canoe.wait_for_sysvar("BMS_Control", "MainPlus_State", 0, timeout_s=0.1)
        elapsed_ms = (time.time() - t_start) * 1000

        assert opened, "Main+ contactor not opened on crash signal"
        assert elapsed_ms <= 50, f"Emergency open time {elapsed_ms:.1f} ms > 50 ms"
        logger.info("PASS | Emergency open in %.1f ms", elapsed_ms)


# ─────────────────────────────────────────────────────────────────────────────
# 8.  Cell Balancing Tests
# ─────────────────────────────────────────────────────────────────────────────
class TestBMSCellBalancing:

    def test_TC_BMS_BAL_001_balancing_activation(self, canoe):
        """Balance activates when cell delta > 10 mV."""
        # Set all cells to 3.75 V, then raise one by 50 mV
        for i in range(96):
            canoe.inject_cell_voltage(i, 3.75)
        canoe.inject_cell_voltage(0, 3.80)
        time.sleep(0.5)

        balance_active = canoe.get_sysvar("BMS_Control", "Balance_Enable")
        assert balance_active == 1, "Balancing should be active for 50 mV delta"

    def test_TC_BMS_BAL_002_balancing_deactivation(self, canoe):
        """Balance deactivates once delta drops below 5 mV."""
        for i in range(96):
            canoe.inject_cell_voltage(i, 3.75)
        time.sleep(0.5)
        balance_active = canoe.get_sysvar("BMS_Control", "Balance_Enable")
        assert balance_active == 0, "Balancing should be inactive for <5 mV delta"

    def test_TC_BMS_BAL_003_balance_not_active_during_fast_discharge(self, canoe):
        """Balancing must be suspended above 0.5C discharge current."""
        for i in range(96):
            canoe.inject_cell_voltage(i, 3.75)
        canoe.inject_cell_voltage(5, 3.80)
        canoe.set_sysvar("BMS_Sim", "Pack_Current", 40.0)  # ~0.67C for 60 Ah pack
        time.sleep(0.5)

        balance_active = canoe.get_sysvar("BMS_Control", "Balance_Enable")
        assert balance_active == 0, "Balancing must not be active during high discharge"


# ─────────────────────────────────────────────────────────────────────────────
# 9.  Isolation Monitoring Tests
# ─────────────────────────────────────────────────────────────────────────────
class TestBMSIsolation:

    def test_TC_BMS_ISO_001_normal_isolation(self, canoe):
        """R_iso > 500 Ω/V → no action."""
        canoe.set_sysvar("BMS_Sim", "IsolationResistance_Ohm", 250000)  # 625 Ω/V at 400V
        time.sleep(0.5)
        dtc = canoe.get_last_dtc()
        assert dtc not in (0x1B00, 0x1B01, 0x1B02), \
            f"Unexpected isolation DTC 0x{dtc:04X} at normal R_iso"

    def test_TC_BMS_ISO_002_warning_level(self, canoe):
        """R_iso between 200–500 Ω/V → DTC P1B00 warning."""
        canoe.set_sysvar("BMS_Sim", "IsolationResistance_Ohm", 120000)  # 300 Ω/V at 400V
        time.sleep(0.5)
        assert canoe.get_last_dtc() == 0x1B00, "DTC P1B00 not logged for warning isolation"

    def test_TC_BMS_ISO_003_emergency_shutdown(self, canoe):
        """R_iso < 100 Ω/V → immediate HV off, DTC P1B02."""
        canoe.set_sysvar("BMS_Sim", "IsolationResistance_Ohm", 30000)   # 75 Ω/V at 400V
        canoe.set_sysvar("VCU_Control", "HV_Request", 1)
        canoe.wait_for_sysvar("BMS_Control", "HV_Ready", 1, timeout_s=5.0)

        canoe.set_sysvar("BMS_Sim", "IsolationResistance_Ohm", 30000)   # Re-confirm
        opened = canoe.wait_for_sysvar("BMS_Control", "MainPlus_State", 0, timeout_s=1.0)

        assert opened, "Contactor not opened for critical isolation fault"
        assert canoe.get_last_dtc() == 0x1B02, "DTC P1B02 not logged"


# ─────────────────────────────────────────────────────────────────────────────
# 10. CAN Communication Tests
# ─────────────────────────────────────────────────────────────────────────────
class TestBMSCANCommunication:

    def test_TC_BMS_CAN_001_bms_status_cycle_time(self, canoe):
        """
        BMS_Status (0x3A0) cycle time must be 10 ms ± 1 ms.
        Measure 100 consecutive frames and check average and max jitter.
        """
        # In a real test this would be captured via CANoe trace object
        # Here we simulate by checking the system variable updated flag
        timestamps = []
        for _ in range(100):
            canoe.wait_for_sysvar("BMS_Monitor", "BmsStatus_NewFrame", 1, timeout_s=0.05)
            ts = canoe.get_sysvar("BMS_Monitor", "BmsStatus_Timestamp")
            timestamps.append(ts)
            canoe.set_sysvar("BMS_Monitor", "BmsStatus_NewFrame", 0)

        if len(timestamps) < 10:
            pytest.skip("Not enough timestamps in simulation mode")

        intervals = [timestamps[i+1] - timestamps[i] for i in range(len(timestamps)-1)]
        avg_interval = sum(intervals) / len(intervals)
        max_interval = max(intervals)

        assert 9.0 <= avg_interval <= 11.0, \
            f"Average cycle time {avg_interval:.1f} ms outside 9–11 ms"
        assert max_interval <= 12.0, \
            f"Max jitter {max_interval:.1f} ms > 12 ms"

    def test_TC_BMS_CAN_002_pack_voltage_signal_range(self, canoe):
        """Pack voltage in BMS_Voltage message must be between 200–500 V."""
        v = canoe.get_sysvar("BMS_UDS", "PackVoltage")
        assert 200.0 <= v <= 500.0, f"Pack voltage {v:.1f} V out of plausible range"

    def test_TC_BMS_CAN_003_no_missing_frames_under_load(self, canoe):
        """No BMS_Status frames missing in 10 seconds under simulated load."""
        missing = canoe.get_sysvar("BMS_Monitor", "BmsStatus_MissingCount")
        time.sleep(10.0)
        missing_after = canoe.get_sysvar("BMS_Monitor", "BmsStatus_MissingCount")
        new_missing = missing_after - missing
        assert new_missing == 0, f"{new_missing} BMS_Status frames missing in 10 s"


# ─────────────────────────────────────────────────────────────────────────────
# 11. Regression Test Summary Reporter
# ─────────────────────────────────────────────────────────────────────────────
class BMSTestReporter:
    """Collects and prints a formatted pass/fail summary."""

    def __init__(self):
        self.results: list[TestResult] = []

    def add(self, result: TestResult):
        self.results.append(result)

    def print_summary(self):
        passed = [r for r in self.results if r.passed]
        failed = [r for r in self.results if not r.passed]
        total  = len(self.results)

        print("\n" + "="*70)
        print(" BMS REGRESSION TEST SUMMARY")
        print("="*70)
        print(f" Total   : {total}")
        print(f" Passed  : {len(passed)}")
        print(f" Failed  : {len(failed)}")
        print(f" Pass Rate: {len(passed)/total*100:.1f}%" if total else " Pass Rate: N/A")
        print("-"*70)

        if failed:
            print("\n FAILURES:")
            for r in failed:
                print(f"  ✗ [{r.tc_id}] {r.description}")
                print(f"      Expected: {r.expected_value}")
                print(f"      Actual  : {r.actual_value}")
                if r.notes:
                    print(f"      Note    : {r.notes}")

        print("="*70)


# ─────────────────────────────────────────────────────────────────────────────
# Entry point for standalone execution
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    sys.exit(
        pytest.main([
            __file__,
            "-v",
            "--tb=short",
            "--html=bms_regression_report.html",
            "--self-contained-html",
        ])
    )
