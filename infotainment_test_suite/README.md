# Infotainment ECU Test Automation Suite

A standalone, production-grade Python + pytest framework for full validation of an
Infotainment Head Unit (HU) ECU via UDS diagnostics over a Vector CAN interface.

---

## Project Structure

```
infotainment_test_suite/
├── core/
│   ├── vector_interface.py       Mock + Real Vector CAN abstraction
│   ├── isotp_transport.py        ISO-TP transport (can-isotp)
│   ├── uds_client.py             UDS service layer + transaction_log
│   ├── security_access.py        Pluggable seed/key algorithm registry
│   ├── dtc_manager.py            DTC read / clear / diff / freeze-frame
│   ├── report_generator.py       HTML + JSON report with DTC summary
│   └── templates/
│       └── report_template.html  Jinja2 report template (Bootstrap-styled)
├── config/
│   ├── infotainment_dids.yaml    36 DIDs — id, length, session, writable, decode
│   ├── infotainment_dtcs.yaml    30 DTCs — code, severity, fault_type, system
│   ├── infotainment_routines.yaml 14 routines — id, session, security, timeout
│   └── ecu_sessions.yaml         CAN, ISO-TP, session timing, security access
├── tests/
│   ├── conftest.py               All fixtures + hooks + report generation
│   ├── uds/                      7 files — 35 tests covering every UDS service
│   ├── dtc/                      3 files — 13 tests covering 0x19/0x14
│   └── features/                10 files — 49 tests across all HU features
├── reports/                      Generated reports (git-ignored)
├── logs/                         CAN trace + pytest logs (git-ignored)
├── requirements.txt
└── pytest.ini
```

---

## Setup

### 1. Python environment

```bash
cd infotainment_test_suite
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Vector XL Driver (real hardware only)

1. Download **Vector Driver Setup** from vector.com → downloads.
2. Install on Windows.  The `xlwrap.dll` is deployed automatically.
3. Open **Vector Hardware Config**, assign your VN1610/VN1630 channel to
   the app name `InfotainmentTestSuite` (matches `config/ecu_sessions.yaml`).

---

## Running the Suite

### Mock mode (no hardware — CI / offline development)

`MOCK_HARDWARE=1` is the **default**.  All UDS responses are simulated.
The HTML report shows a prominent simulation banner.

```bash
cd infotainment_test_suite

# Full regression — all tests
MOCK_HARDWARE=1 pytest tests/ --html=reports/full_$(date +%Y%m%d_%H%M%S).html --self-contained-html -v

# Smoke tests only
MOCK_HARDWARE=1 pytest tests/ -m smoke --html=reports/smoke.html --self-contained-html -v

# Single feature area
MOCK_HARDWARE=1 pytest tests/features/test_bluetooth.py -v

# Single UDS service
MOCK_HARDWARE=1 pytest tests/uds/test_session_control.py -v
```

### Real hardware mode

```bash
export MOCK_HARDWARE=0
export VECTOR_CHANNEL=1     # match Vector Hardware Config
export CAN_BITRATE=500000

pytest tests/ --html=reports/hw_$(date +%Y%m%d_%H%M%S).html --self-contained-html -v
```

---

## Selective Marker Runs

All markers are defined in `pytest.ini`.

| Goal | Command |
|------|---------|
| Smoke only | `pytest tests/ -m smoke` |
| Regression | `pytest tests/ -m regression` |
| UDS layer only | `pytest tests/uds/` |
| DTC tests only | `pytest tests/dtc/` |
| Bluetooth | `pytest tests/ -m bluetooth` |
| Display + IO | `pytest tests/ -m "display or io_control"` |
| Negative-response tests | `pytest tests/ -m negative` |
| All DTC-related | `pytest tests/ -m dtc` |
| Parametrized DID coverage | `pytest tests/uds/test_read_write_did.py -m parametrize` |

### Run specific test by name

```bash
pytest tests/ -k "test_read_bluetooth_module_status_did" -v
```

---

## Parallel execution

```bash
pip install pytest-xdist
pytest tests/ -n 4          # 4 worker processes
```

Note: parallel runs require `MOCK_HARDWARE=1` or separate Vector channels per worker.

---

## How to Add a New DID

1. **`config/infotainment_dids.yaml`** — add an entry:
   ```yaml
   my_new_feature_status:
     id: "0x30C0"       # from ODX / supplier DID catalogue
     length: 2
     writable: false
     session: extended
     description: "My new feature state"
     decode: { type: enum, values: { 0x00: "off", 0x01: "on" } }
   ```

2. **In any test file** — use the `did` fixture:
   ```python
   def test_my_feature(uds_client, did):
       resp = uds_client.read_data_by_identifier(did("my_new_feature_status"))
       assert resp.positive
   ```

---

## How to Add a New DTC

1. **`config/infotainment_dtcs.yaml`**:
   ```yaml
   my_new_fault:
     code: "0xB1A001"
     iso_code: "B1A001"
     description: "My new hardware fault"
     severity: major
     fault_type: hardware
     system: my_subsystem
     expected_on_clean: false
   ```

2. **In a feature test**:
   ```python
   def test_no_my_new_fault(uds_client, dtc_manager, dtc_code):
       uds_client.clear_dtc(group=0xFFFFFF)
       snapshot = dtc_manager.read_all()
       code = dtc_code("my_new_fault")
       assert all(r.dtc_code != code for r in snapshot.confirmed_dtcs)
   ```

---

## How to Add a New Feature Test File

1. Create `tests/features/test_my_feature.py`.
2. Add a pytest marker in `pytest.ini`:
   ```ini
   my_feature: My new feature validation tests
   ```
3. Write tests using fixtures `uds_client`, `did`, `routine`, `dtc_manager`, `dtc_code`.

---

## Switching to Real OEM Security Algorithm

The default `xor_placeholder` algorithm **will fail on real hardware** (NRC 0x35).

```python
# In a separate file (keep out of VCS if proprietary)
from core.security_access import SecurityAlgorithmBase, register_algorithm

class MyHUAlgorithm(SecurityAlgorithmBase):
    def compute_key(self, seed: bytes, level: int) -> bytes:
        # ← insert OEM derivation
        return derived_key

register_algorithm("hu_level1", MyHUAlgorithm())
```

Then in `config/ecu_sessions.yaml`:
```yaml
security_access:
  level_1:
    algorithm: hu_level1
```

Import the registration module at the top of `tests/conftest.py`.

---

## Report Output

Two files are written to `reports/` after each session:

| File | Description |
|------|-------------|
| `infotainment_<run_id>_report.html` | Self-contained HTML with pass/fail table + DTC summary |
| `infotainment_<run_id>_report.json` | Machine-readable JSON sidecar |

The HTML report includes a **DTC Summary** section listing every DTC that was
set, cleared, or present at the end of the run, cross-referenced with the
`infotainment_dtcs.yaml` catalogue (description + severity).

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MOCK_HARDWARE` | `1` | `1`=mock, `0`=real Vector hardware |
| `VECTOR_CHANNEL` | from YAML | Vector 1-based channel number |
| `CAN_BITRATE` | from YAML | CAN bitrate in bps |

---

## Assumptions

| Assumption | Value | Override |
|------------|-------|----------|
| CAN bitrate | 500 kbps | `CAN_BITRATE` env or `can.bitrate` in YAML |
| Addressing | 11-bit normal ISO-TP | `isotp.addressing_mode` in YAML |
| TX/RX IDs | 0x730 / 0x738 | `can.tx_id` / `can.rx_id` in YAML |
| Security algo | XOR placeholder | Implement `SecurityAlgorithmBase` |
| Session timeout | 5 s (extended) | `sessions.extended.session_timeout_s` |
