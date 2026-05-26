# ADAS Enterprise Test Framework

> Production-grade automated test framework for ADAS (Advanced Driver Assistance Systems) validation.  
> OEM / Tier-1 standard. ISO 26262-aligned. CI/CD ready.

---

## Architecture

```
adas_framework/
├── core/                        # Framework infrastructure
│   ├── config.py                # YAML-driven config singleton (ENV override)
│   ├── logger.py                # Structured JSON + colour console logging
│   ├── retry.py                 # @retry / @flaky decorators + FlakyTracker
│   └── base_test.py             # ADASBaseTest class — ASIL, assertions, timing
│
├── can/                         # CAN bus layer
│   ├── can_interface.py         # Thread-safe CAN abstraction (PCAN/Vector/virtual)
│   └── signal_validator.py      # DBC signal decoding + range/timeout checks
│
├── diagnostics/                 # UDS layer
│   ├── uds_client.py            # Full async ISO 14229 client (14 services)
│   └── dtc_handler.py           # DTC lifecycle management
│
├── radar/
│   └── radar_validator.py       # Object detection, SNR, update rate, ghost detection
│
├── camera/
│   └── camera_validator.py      # Lane detection, image quality, distortion
│
├── lidar/
│   └── lidar_validator.py       # Point cloud validation, range, density
│
├── sensor_fusion/
│   └── fusion_validator.py      # Timestamp sync, object correlation, tracking
│
├── test_cases/                  # ADAS test suites
│   ├── acc/test_acc.py          # Adaptive Cruise Control  (ASIL B)
│   ├── aeb/test_aeb.py          # Autonomous Emergency Braking (ASIL D)
│   ├── lka/test_lka.py          # Lane Keep Assist (ASIL B)
│   ├── tsr/test_tsr.py          # Traffic Sign Recognition (QM)
│   ├── bsd/test_bsd.py          # Blind Spot Detection (ASIL A)
│   └── dms/test_dms.py          # Driver Monitoring System (ASIL B)
│
├── utilities/
│   ├── fault_injector.py        # CAN/sensor/ECU fault injection
│   └── report_generator.py      # Allure + HTML + Excel reports
│
├── replay_tools/
│   └── can_replay.py            # BLF / ASC log replay engine
│
├── ai_analytics/
│   └── flaky_detector.py        # Statistical flaky test detection + smart selection
│
├── ci_cd/
│   ├── Jenkinsfile              # Declarative Jenkins pipeline
│   └── github_actions.yml       # GitHub Actions workflow
│
├── docker/
│   ├── Dockerfile               # Multi-stage container build
│   └── docker-compose.yml       # Full stack: runner + Allure + Grafana + InfluxDB
│
├── configs/
│   └── test_config.yaml         # Master configuration (all sub-configs)
│
├── requirements/
│   └── requirements.txt         # Pinned Python dependencies
│
└── conftest.py                  # Root pytest fixtures (CAN, UDS, sensors, reports)
```

---

## Quick Start

### 1. Install dependencies

```bash
cd adas_framework
pip install -r requirements/requirements.txt
```

### 2. Run smoke tests (headless, no hardware)

```bash
pytest test_cases/ -m smoke --no-hardware -v
```

### 3. Run full regression (headless)

```bash
pytest test_cases/ -m "regression and not hardware" --no-hardware -v \
    --html=test_reports/report.html --self-contained-html
```

### 4. Run with real hardware (PCAN USB)

```bash
pytest test_cases/ -m "smoke" \
    --channel PCAN_USBBUS1 \
    --interface pcan \
    --ecu ADAS_ECU \
    --sw-version 1.4.2 \
    -v
```

### 5. Docker (fully isolated CI)

```bash
docker build -t adas-test-framework .
docker run --rm adas-test-framework

# Full stack with Allure + Grafana:
docker-compose up -d allure grafana influxdb
docker-compose run --rm test-runner pytest test_cases/ -m regression --no-hardware
```

### 6. View Allure Report

```bash
allure serve allure-results/
# Or via Docker: http://localhost:4040
```

---

## Test Markers

| Marker         | Description                                   |
|----------------|-----------------------------------------------|
| `smoke`        | Fast sanity check (< 5 min)                   |
| `regression`   | Full regression suite                         |
| `safety`       | ISO 26262 safety-critical path                |
| `asil_a/b/c/d` | ASIL severity tag                             |
| `hardware`     | Requires physical HIL bench                   |
| `acc`          | Adaptive Cruise Control tests                 |
| `aeb`          | Autonomous Emergency Braking tests            |
| `lka`          | Lane Keep Assist tests                        |
| `tsr`          | Traffic Sign Recognition tests                |
| `bsd`          | Blind Spot Detection tests                    |
| `dms`          | Driver Monitoring System tests                |
| `uds`          | UDS diagnostic tests                          |
| `can`          | CAN network tests                             |
| `fault_injection` | Fault injection scenarios                  |
| `performance`  | Timing / latency tests                        |

---

## CLI Options

```
--channel        CAN channel (PCAN_USBBUS1 | virtual | socketcan)
--interface      CAN interface type (pcan | vector | virtual)
--bitrate        CAN bitrate (default: 500000)
--dbc            DBC file path
--ecu            Target ECU for UDS (ADAS_ECU | BMS | VCU ...)
--env            Environment name (HIL_LAB_01 | SIL_DEV ...)
--sw-version     SW version under test
--hil            Enable HIL bench integration
--no-hardware    Skip hardware-dependent tests (for CI)
```

---

## Configuration

All settings in `configs/test_config.yaml`. Override via environment:

```bash
export ADAS_CAN_CHANNEL=PCAN_USBBUS1
export ADAS_ENV_NAME=HIL_LAB_01
export ADAS_UDS_TX_ID=0x741
```

---

## CI/CD Integration

### Jenkins
Use `ci_cd/Jenkinsfile`. Stages:
1. Setup → 2. Lint → 3. Flash ECU → 4. Smoke → 5. Regression → 6. Safety → 7. Reports

### GitHub Actions
Use `ci_cd/github_actions.yml`. Jobs:
- `lint`: flake8 + mypy on every push
- `smoke`: headless smoke on every push
- `regression`: per-feature matrix on push to main
- `hardware-tests`: self-hosted HIL runner (tagged: `hil-bench`)
- `allure-report`: published to GitHub Pages

---

## ASIL Coverage

| Feature | ASIL | Safety Tests |
|---------|------|--------------|
| AEB     | D    | TC_AEB_003, TC_AEB_004, TC_AEB_009, TC_AEB_010 |
| ACC     | B    | TC_ACC_008, TC_ACC_009 |
| LKA     | B    | TC_LKA_002, TC_LKA_005, TC_LKA_010 |
| BSD     | A    | TC_BSD_004 |
| DMS     | B    | TC_DMS_003, TC_DMS_009 |
| TSR     | QM   | N/A |

---

## Extending the Framework

### Add a new test suite
1. Create `test_cases/<feature>/test_<feature>.py`
2. Inherit from `ADASBaseTest`
3. Set `ASIL`, `FEATURE`, `REQ_IDS` class attributes
4. Apply appropriate pytest marks

### Add a new sensor validator
1. Create `<sensor>/<sensor>_validator.py`
2. Accept config dataclass from `core.config`
3. Implement `assert_*` methods
4. Add fixture in `conftest.py`

### Custom signal timeout/range
Edit `configs/test_config.yaml` → `signal_timeouts` or `timing_limits`.

---

## Requirements Traceability

Each test case maps directly to requirement IDs via `REQ_IDS` and `req_ids` fixture.  
Allure reports include direct links to the Jira/Polarion requirement system.

---

## License

Internal proprietary framework — OEM/Tier-1 use only.  
Not for distribution.
