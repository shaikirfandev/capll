# ECU Test Suite

A modular, config-driven Python + pytest framework for multi-domain ECU validation
over a Vector CAN/CAN-FD interface using UDS diagnostic services (ISO 14229-1).

## Supported Domains

| Domain        | ECU Type             | Key Tests                                         |
|---------------|----------------------|---------------------------------------------------|
| ADAS          | Camera/Radar ECU     | Calibration DIDs, sensor DTCs, ACC/AEB signals    |
| Infotainment  | Head Unit (HU)       | BT/Wi-Fi DIDs, factory reset, display self-test   |
| Cluster       | Instrument Cluster   | Odometer, VIN, IO lamp control, gauge sweep       |
| Telematics    | TCU / TBOX           | SIM/GPS DIDs, connectivity self-test, eCall DTCs  |

---

## Architecture

```
ecu_test_suite/
├── cli/
│   └── main.py                  # Interactive domain selection + pytest launcher
├── core/
│   ├── vector_interface.py      # Mock + Real Vector VN device abstraction
│   ├── isotp_transport.py       # ISO-TP transport (can-isotp wrapper)
│   ├── uds_client.py            # UDS service layer (mock + udsoncan wrapper)
│   ├── security_access.py       # Pluggable seed/key algorithm registry
│   ├── dtc_manager.py           # Read/Clear/Diff DTC snapshots
│   ├── report_generator.py      # HTML + JSON report builder (Jinja2)
│   └── templates/
│       └── report_template.html # Jinja2 report template
├── config/
│   ├── adas_ecu.yaml            # CAN IDs, DIDs, DTCs, sessions for ADAS ECU
│   ├── infotainment_ecu.yaml
│   ├── cluster_ecu.yaml
│   └── telematics_ecu.yaml
├── tests/
│   ├── conftest.py              # Session/function fixtures + DTC snapshots + report
│   ├── common/
│   │   └── test_uds_common.py   # Generic UDS service tests (all domains)
│   ├── adas/
│   │   └── test_adas_features.py
│   ├── infotainment/
│   │   └── test_infotainment_features.py
│   ├── cluster/
│   │   └── test_cluster_features.py
│   └── telematics/
│       └── test_telematics_features.py
├── reports/                     # Generated HTML/JSON reports (git-ignored)
├── logs/                        # CAN trace and run logs (git-ignored)
├── requirements.txt
└── pytest.ini
```

---

## Quick Start

### 1. Prerequisites

#### Vector XL Driver (real hardware only)
1. Download **Vector Driver Setup** from [vector.com/downloads](https://www.vector.com/int/en/products/products-a-z/software/vector-driver-setup/)
2. Install on Windows (xlwrap.dll is deployed automatically).
3. Open **Vector Hardware Config**, assign your VN1610/VN1630/CANcaseXL channel to the
   `ECU_Test_Suite` application.

#### Python environment
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r ecu_test_suite/requirements.txt
```

### 2. Run in mock mode (no hardware required — default)

```bash
cd ecu_test_suite

# All ADAS tests (mock mode active by default)
MOCK_HARDWARE=1 ECU_DOMAIN=ADAS pytest tests/adas tests/common \
    --html=reports/adas_smoke.html --self-contained-html -v -m smoke

# All Cluster regression tests
MOCK_HARDWARE=1 ECU_DOMAIN=Cluster pytest tests/cluster tests/common \
    --html=reports/cluster_regression.html --self-contained-html -v -m regression
```

### 3. Run via the interactive CLI

```bash
cd ecu_test_suite
python -m cli.main
```

The CLI will prompt for:
- ECU domain (ADAS / Infotainment / Cluster / Telematics)
- Vector channel and CAN bitrate (pre-filled from YAML config)
- Run mode (smoke / regression / all)

### 4. Run against real Vector hardware

```bash
# Disable mock mode
export MOCK_HARDWARE=0
export ECU_DOMAIN=ADAS
export VECTOR_CHANNEL=1        # match Vector Hardware Config
export CAN_BITRATE=500000

cd ecu_test_suite
pytest tests/adas tests/common \
    --html=reports/adas_$(date +%Y%m%d_%H%M%S).html \
    --self-contained-html -v
```

---

## Running Domain Suites

| Domain        | Command                                               |
|---------------|-------------------------------------------------------|
| ADAS          | `ECU_DOMAIN=ADAS pytest tests/adas tests/common`      |
| Infotainment  | `ECU_DOMAIN=Infotainment pytest tests/infotainment tests/common` |
| Cluster       | `ECU_DOMAIN=Cluster pytest tests/cluster tests/common`|
| Telematics    | `ECU_DOMAIN=Telematics pytest tests/telematics tests/common`|

### Filter by marker

```bash
# Only smoke tests for ADAS
ECU_DOMAIN=ADAS pytest tests/adas tests/common -m "adas and smoke"

# All regression DTC tests across all domains
pytest tests/ -m "dtc and regression"
```

### Parallel execution (optional)

```bash
pip install pytest-xdist
ECU_DOMAIN=ADAS pytest tests/adas tests/common -n 4   # 4 worker processes
```

---

## Environment Variables Reference

| Variable         | Default | Description                                        |
|------------------|---------|----------------------------------------------------|
| `ECU_DOMAIN`     | `ADAS`  | Active domain (ADAS / Infotainment / Cluster / Telematics) |
| `MOCK_HARDWARE`  | `1`     | `1` = mock mode (no hardware); `0` = real hardware |
| `VECTOR_CHANNEL` | `1`     | Vector 1-based channel number                      |
| `CAN_BITRATE`    | `500000`| CAN bitrate in bps                                 |

---

## Adding a New ECU Domain

1. **Create a YAML config** in `config/my_new_ecu.yaml` following the structure of
   `config/adas_ecu.yaml` — fill in CAN IDs, DIDs, routines, and DTCs from the
   supplier ODX / DBC.

2. **Create a test module** `tests/my_domain/test_my_domain_features.py` with at
   least 5 test functions marked `@pytest.mark.my_domain`.

3. **Register the domain** in `cli/main.py` by adding an entry to `DOMAIN_MAP`.

4. **Register the domain config** in `tests/conftest.py` → `ecu_config` fixture
   `config_map` dict.

5. **Add the pytest marker** in `pytest.ini` under `markers`.

---

## Adding a Real OEM Security Access Algorithm

The placeholder XOR algorithm **will not work** with a real ECU.  Replace it:

```python
# In a separate file (e.g. my_oem_algo.py — keep out of VCS if proprietary)
from core.security_access import SecurityAlgorithmBase, register_algorithm

class MyECUAlgorithm(SecurityAlgorithmBase):
    def compute_key(self, seed: bytes, level: int) -> bytes:
        # ← Insert your OEM derivation here
        return derived_key

register_algorithm("my_ecu_algo", MyECUAlgorithm())
```

Then in `config/adas_ecu.yaml`:
```yaml
security_access:
  algorithm: my_ecu_algo
```

Import the registration module in `conftest.py` before the `uds_client` fixture runs.

---

## Report Output

After each test session two files are written to `reports/`:

| File | Format | Contents |
|------|--------|----------|
| `<domain>_<timestamp>_report.html` | HTML (self-contained) | Pass/fail table, DTC snapshots, timing |
| `<domain>_<timestamp>_report.json` | JSON | Machine-readable version of the same data |

pytest-html also produces its own report when `--html` is passed to pytest.

---

## Assumptions & Defaults

| Assumption | Value | Override |
|------------|-------|----------|
| CAN bitrate | 500 kbps (classic CAN) | Set `can.bitrate` in YAML or `CAN_BITRATE` env |
| Addressing | 11-bit normal (ISO 15765-2) | Change `addressing_mode` in `IsoTpConfig` |
| Security algorithm | XOR placeholder | Implement `SecurityAlgorithmBase` |
| TX CAN ID | 0x7DF (functional) | Set `can.tx_id` in ECU YAML |
| Hardware mode | Mock (MOCK_HARDWARE=1) | Set `MOCK_HARDWARE=0` for real hardware |

---

## License

MIT — see LICENSE file for details.
