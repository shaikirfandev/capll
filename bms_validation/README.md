# BMS Validation — Complete Testing Repository

> **Domain:** Battery Management System (BMS) Validation Engineering
> **Target:** EV / HEV / PHEV Battery Packs (Li-Ion / LFP)
> **Coverage:** CAPL Scripts · Python Automation · UDS Diagnostics · HIL Framework

---

## Repository Structure

```
bms_validation/
│
├── 01_bms_cell_monitoring.capl        ← Cell V/T monitoring, OV/UV/OT protection (CAPL)
├── 02_bms_contactor_precharge.capl    ← Contactor FSM, precharge, weld detection (CAPL)
├── 03_bms_uds_diagnostics.capl        ← Full UDS service implementation (CAPL)
├── 04_bms_python_automation.py        ← pytest-based HIL test automation (Python)
├── 05_bms_python_uds.py               ← python-can + ISO-TP UDS client (Python)
├── 06_bms_hil_test_framework.py       ← HIL test orchestration + reporting (Python)
├── 07_bms_technical_reference.md      ← algorithms, signals, UDS, ISO standards
└── README.md                          ← This file
```

---

## File Descriptions

### CAPL Scripts (Vector CANoe)

| File | Purpose | Key Features |
|---|---|---|
| [01_bms_cell_monitoring.capl](01_bms_cell_monitoring.capl) | Cell voltage & temperature monitoring | OV/UV/OT protection, debounce, cell balancing, CAN Tx |
| [02_bms_contactor_precharge.capl](02_bms_contactor_precharge.capl) | Contactor state machine | Precharge FSM, inrush measurement, weld detection, emergency HV off |
| [03_bms_uds_diagnostics.capl](03_bms_uds_diagnostics.capl) | UDS diagnostics client | All ISO 14229 services, DID read/write, DTC, EOL sequence |

### Python Scripts

| File | Purpose | Key Features |
|---|---|---|
| [04_bms_python_automation.py](04_bms_python_automation.py) | pytest test suite for HIL | CANoe COM API wrapper, 28 test cases across all BMS functions |
| [05_bms_python_uds.py](05_bms_python_uds.py) | Standalone UDS diagnostic tool | python-can + ISOTP, full DID/DTC decode, EOL sequence, CLI |
| [06_bms_hil_test_framework.py](06_bms_hil_test_framework.py) | Test orchestration framework | Fault injection, simulation mode, HTML/JSON/Excel reports, CI/CD exit codes |

### Documentation

| File | Purpose |
|---|---|
| [07_bms_technical_reference.md](07_bms_technical_reference.md) | Complete technical reference — algorithms, OCV tables, protocols, standards |

---

## Quick Start

### Run HIL Test Framework (Simulation Mode — No Hardware Required)

```bash
# Full test suite
python 06_bms_hil_test_framework.py --suite full

# Individual suites
python 06_bms_hil_test_framework.py --suite voltage
python 06_bms_hil_test_framework.py --suite thermal
python 06_bms_hil_test_framework.py --suite soc
python 06_bms_hil_test_framework.py --suite isolation
python 06_bms_hil_test_framework.py --suite contactor
python 06_bms_hil_test_framework.py --suite balancing

# List all test cases
python 06_bms_hil_test_framework.py --list
```

### Run UDS Diagnostic Tool

```bash
# Read all live BMS data
python 05_bms_python_uds.py --mode read_all --sim

# Read stored DTCs
python 05_bms_python_uds.py --mode read_dtcs --sim

# Clear DTCs
python 05_bms_python_uds.py --mode clear_dtcs --sim

# Run EOL programming sequence
python 05_bms_python_uds.py --mode eol --vin "1BMSTST0000012345" --capacity 60 --sim

# Run all self-tests
python 05_bms_python_uds.py --mode self_test --sim

# Real hardware (Vector VN1610 on channel 0)
python 05_bms_python_uds.py --mode read_all --channel 0 --bustype vector
```

### Run pytest Test Suite (CANoe required for full execution)

```bash
pip install pytest pytest-html

# Full suite with HTML report
pytest 04_bms_python_automation.py -v --html=bms_report.html --self-contained-html

# Specific class
pytest 04_bms_python_automation.py::TestBMSCellVoltage -v
pytest 04_bms_python_automation.py::TestBMSSoC -v
pytest 04_bms_python_automation.py::TestBMSContactor -v
```

### Install Dependencies

```bash
pip install python-can udsoncan can-isotp pytest pytest-html openpyxl colorama rich
```

---

## CAPL Script Usage (Vector CANoe)

### Cell Monitoring Script (01)

1. Open CANoe configuration with BMS HIL simulation
2. Add `01_bms_cell_monitoring.capl` to the CAPL test module
3. Start measurement
4. Use keyboard shortcuts:
   - **`f`** — Inject OV2 fault (Cell 7 → 4.26 V)
   - **`u`** — Inject UV2 fault (Cell 50 → 2.45 V)
   - **`r`** — Reset all fault flags

System variables required:
```
BMS_Sim::Cell_Voltage[0..95]    (float, Volts)
BMS_Sim::Module_Temp[0..7]      (float, °C)
BMS_Control::MainPlus_Cmd       (int, 0/1)
BMS_Control::MainMinus_Cmd      (int, 0/1)
BMS_Control::Power_Derate_Pct   (float, %)
BMS_DTC::LastDTC_Code           (dword)
```

### Contactor Script (02)

Keyboard shortcuts:
- **`h`** — HV ON request (starts precharge sequence)
- **`o`** — HV OFF request
- **`c`** — Simulate crash → Emergency HV OFF
- **`w`** — Simulate precharge contactor weld

### UDS Diagnostics Script (03)

Keyboard shortcuts:
- **`1`** — Open Default Session
- **`2`** — Open Extended Session
- **`3`** — Request Security Seed
- **`4-7`** — Read SoC, Voltage, Max Cell V, Temperature
- **`8`** — Read all DTCs
- **`9`** — Clear all DTCs
- **`0`** — ECU Hard Reset
- **`s`** — Run BMS Self-Test routine
- **`b`** — Start Cell Balancing routine
- **`i`** — Run IMD Self-Test

---

## UDS DID Map (Quick Reference)

### Read DIDs (0x22)

| DID | Parameter | Resolution | Range |
|---|---|---|---|
| 0xF190 | SoC | 0.5 % | 0–100% |
| 0xF191 | SoH | 0.5 % | 0–100% |
| 0xF192 | Pack Voltage | 0.1 V | 0–655 V |
| 0xF193 | Pack Current | 0.1 A | -3276 to +3276 A |
| 0xF194 | Max Cell Voltage | 0.001 V | 0–6.5 V |
| 0xF195 | Min Cell Voltage | 0.001 V | 0–6.5 V |
| 0xF196 | Max Temperature | 1°C, offset -40 | -40 to +215°C |
| 0xF197 | Min Temperature | 1°C, offset -40 | -40 to +215°C |
| 0xF198 | Cell Delta | 1 mV | 0–65535 mV |
| 0xF199 | BMS State | Enum | 0=INIT…7=SLEEP |
| 0xF19A | Fault Level | 0–3 | 0=None, 3=Emergency |
| 0xF19B | Cycle Count | 1 | 0–65535 |
| 0xF19D | SW Version | BCD x.xx.xx | — |
| 0xF19E | Isolation Resistance | 10 Ω | 0–655350 Ω |

### Write DIDs (0x2E) — Require Security Level 1

| DID | Parameter | Bytes |
|---|---|---|
| 0xF17F | VIN | 17 (ASCII) |
| 0xF1A0 | Nominal Capacity [Ah] | 2 |
| 0xF1A1 | SoC Initialisation [%] | 1 |
| 0xF1A3 | OV1 Threshold | 2 |
| 0xF1A4 | OV2 Threshold | 2 |
| 0xF1A5 | UV1 Threshold | 2 |
| 0xF1A6 | UV2 Threshold | 2 |
| 0xF1FF | EOL Completion Flag | 2 |

---

## Test Case Summary

| Category | TC Count | Key Validations |
|---|---|---|
| Cell Voltage (OV/UV) | 6 | Debounce, response time < 100 ms, DTC logging |
| Temperature | 3 | OT1/OT2, sensor OC, cooling activation |
| SoC Accuracy | 3 | OCV init, full charge = 100%, UV2 = 0% |
| Isolation (IMD) | 3 | All 3 fault levels, ISO 6469-3 compliance |
| Contactor / Precharge | 2 | 95% precharge ratio, weld detection |
| Cell Balancing | 1 | 10 mV activation, suspension at high discharge |
| **Total** | **18** | |

---

## CI/CD Integration

The HIL test framework returns exit code `0` for pass (≥ 95% pass rate) and `1` for fail.

```yaml
# GitHub Actions / Jenkins snippet
- name: Run BMS Validation Suite
  run: python 06_bms_hil_test_framework.py --suite full
  
- name: Upload Test Report
  uses: actions/upload-artifact@v3
  with:
    name: bms-validation-report
    path: bms_reports/
```

---

## Protection Threshold Summary

| Fault | Level 1 (Warning) | Level 2 (Critical) |
|---|---|---|
| Over-Voltage | ≥ 4.20 V → 80% derate | ≥ 4.25 V → Contactor open |
| Under-Voltage | ≤ 3.00 V → 50% derate | ≤ 2.50 V → Contactor open |
| Over-Temperature | ≥ 50°C → Cooling 100% | ≥ 60°C → Contactor open |
| Under-Temperature | ≤ 0°C → Limit charge | ≤ -20°C → Block charge |
| Isolation | ≤ 500 Ω/V → Warning | ≤ 100 Ω/V → HV off |

---

## Standards Compliance

| Standard | Requirement | Coverage |
|---|---|---|
| ISO 6469-3 | R_iso ≥ 500 Ω/V | `tc_bms_iso_001–003` |
| ISO 26262 ASIL B | DC ≥ 90% for OV function | Safety mechanism POST test |
| ISO 14229 (UDS) | All diagnostic services | `03_bms_uds_diagnostics.capl` + `05_bms_python_uds.py` |
| IEC 62619 | Cell abuse test reference | External cell qualification |
| UN R100 | HV isolation monitoring | IMD tests |

---

*Generated: 2026-04-19 | BMS Validation Team*
