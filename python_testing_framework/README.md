# Enterprise ADAS Hybrid Test Framework

**PyTest + Robot Framework | 25 ADAS Features | ASIL A–D | OEM/Tier-1 Grade**

Production-ready automotive validation platform covering:
CAN/CAN-FD, UDS, Radar, Camera, LiDAR, Sensor Fusion, HIL/SIL/CI,
SOME/IP, Cybersecurity, ISO 26262, ASPICE, Euro NCAP, NHTSA.

---

## Architecture

```
python_testing_framework/
├── pytest_framework/           # pytest layer (feature + system tests)
│   ├── core/                   # Config, logging, base class, retry
│   ├── can/                    # CAN/CAN-FD interface + signal validator
│   ├── diagnostics/            # UDS client (ISO 14229) + DTC handler
│   ├── radar/                  # Radar object validator
│   ├── camera/                 # OpenCV camera validator
│   ├── lidar/                  # LiDAR point cloud validator
│   ├── sensor_fusion/          # Multi-sensor fusion validator
│   ├── simulators/             # SIL/CI data generators
│   ├── utilities/              # Fault injector (FMEA), report generator
│   ├── ai_analytics/           # Flaky test detector
│   ├── ethernet/               # SOME/IP client
│   ├── replay_tools/           # BLF/ASC CAN replay
│   ├── test_suites/            # Test cases by ADAS feature
│   │   ├── acc/                # Adaptive Cruise Control
│   │   ├── aeb/                # Autonomous Emergency Braking
│   │   ├── lka/                # Lane Keep Assist
│   │   ├── bsd/                # Blind Spot Detection
│   │   ├── tsr/                # Traffic Sign Recognition
│   │   ├── dms/                # Driver Monitoring System
│   │   ├── parking/            # Parking Assist + Auto Park
│   │   ├── sensor_fusion/      # Fusion validation
│   │   ├── performance/        # Timing + load tests
│   │   └── cybersecurity/      # Security validation
│   └── conftest.py             # Root fixtures + markers + hooks
│
├── robot_framework/            # Robot Framework keyword-driven layer
│   ├── libraries/              # Python keyword libraries
│   │   ├── CANLibrary.py       # CAN bus keywords
│   │   ├── UDSLibrary.py       # UDS diagnostic keywords
│   │   ├── ADASLibrary.py      # ADAS feature keywords
│   │   └── SensorLibrary.py    # Sensor validation keywords
│   ├── resources/
│   │   └── common.resource     # Shared setup/teardown/assertions
│   ├── variables/
│   │   └── global_vars.py      # Framework-wide variable definitions
│   └── test_suites/            # .robot test suites
│       ├── ACC_TestSuite.robot
│       ├── AEB_TestSuite.robot
│       ├── LKA_TestSuite.robot
│       └── ADAS_E2E_TestSuite.robot
│
├── ci_cd/
│   ├── Jenkinsfile             # 8-stage Jenkins pipeline
│   └── github_actions.yml      # GitHub Actions matrix CI
│
├── docker/
│   ├── Dockerfile              # Multi-stage container (non-root, slim)
│   └── docker-compose.yml      # Allure + InfluxDB + Grafana stack
│
├── kubernetes/
│   ├── deployment.yaml         # K8s deployment (3 replicas)
│   └── service.yaml            # Services + namespace
│
├── configs/
│   └── framework_config.yaml   # Master YAML configuration
│
└── requirements/
    └── requirements.txt        # Pinned Python dependencies
```

---

## Quick Start

### CI / Headless (no hardware)

```bash
cd python_testing_framework
pip install -r requirements/requirements.txt

# pytest — smoke
python3 -m pytest pytest_framework/test_suites/ -m smoke --no-hardware -v

# pytest — full regression (parallel)
python3 -m pytest pytest_framework/test_suites/ \
    -m "regression and not hil" \
    --no-hardware \
    -n auto \
    --alluredir=allure-results \
    -v

# Robot Framework
python3 -m robot \
    --variable ENVIRONMENT:ci \
    --exclude hil \
    robot_framework/test_suites/
```

### With Real Hardware (HIL/SIL)

```bash
python3 -m pytest pytest_framework/test_suites/ \
    --hil \
    --channel=PCAN0 \
    --interface=pcan \
    --bitrate=500000 \
    --dbc=dbc_arxml_files/adas_system.dbc \
    --env=hil \
    --sw-version=2.5.1 \
    -m regression \
    --alluredir=allure-results \
    -v
```

### Docker

```bash
cd python_testing_framework
docker build -f docker/Dockerfile -t adas-test-framework:1.0.0 .
docker run --rm adas-test-framework:1.0.0
```

### Full Observability Stack

```bash
cd python_testing_framework
SW_VERSION=2.5.1 docker-compose -f docker/docker-compose.yml up

# Allure UI:  http://localhost:5252
# Grafana:    http://localhost:3000   (admin / adas_grafana_secure)
# InfluxDB:   http://localhost:8086
```

---

## CLI Reference

| Option | Default | Description |
|--------|---------|-------------|
| `--channel` | `virtual` | CAN channel (virtual/PCAN0/vcan0) |
| `--interface` | `virtual` | CAN interface driver |
| `--bitrate` | `500000` | CAN bitrate in bps |
| `--dbc` | `` | Path to .dbc file |
| `--ecu` | `ADAS_ECU` | Target ECU name |
| `--env` | `ci` | Test environment (ci/sil/hil) |
| `--sw-version` | `` | SW version under test |
| `--hil` | `False` | Enable HIL bench |
| `--no-hardware` | `False` | Headless CI mode |
| `--config-file` | `` | Custom YAML config path |

---

## Test Markers

### Feature markers
`acc`, `aeb`, `lka`, `ldw`, `bsd`, `tsr`, `dms`, `parking`,
`surround_view`, `rcta`, `fcw`, `pedestrian`, `sensor_fusion`,
`highway_pilot`, `esa`, `night_vision`, `isa`

### Type markers
`smoke`, `sanity`, `regression`, `performance`, `cybersecurity`,
`uds`, `can`, `ethernet`, `hil`, `sil`, `e2e`, `fault_injection`

### Safety markers
`asil_a`, `asil_b`, `asil_c`, `asil_d`, `safety`

**Example:**
```bash
# Run only ASIL D safety tests
pytest -m "asil_d and safety" --no-hardware -v

# Run AEB + ACC regression, excluding HIL
pytest -m "(aeb or acc) and regression and not hil" -n 4 -v
```

---

## ADAS Feature Coverage

| Feature | ASIL | Tests | Key Validations |
|---------|------|-------|-----------------|
| ACC | B | ~20 | Speed hold, headway, target tracking, brake override |
| AEB | D | ~18 | Pedestrian/vehicle, latency <600ms, E2E CRC, DTC |
| LKA | B | ~15 | Torque ≤3Nm, turn signal inhibit, camera fallback |
| BSD | A | ~12 | Zone detection, LKCA, distance accuracy ±0.25m |
| TSR | QM | ~12 | Speed signs, confidence filter, ISA integration |
| DMS | B | ~14 | Gaze, PERCLOS, head pose, alert escalation |
| Parking | QM | ~10 | Distance alerts, auto-park, surround cameras |
| Sensor Fusion | B | ~12 | Timestamp sync, object fusion, latency, failover |
| Performance | QM | ~12 | Cycle times, bus load, concurrent features |
| Cybersecurity | QM | ~10 | UDS auth, replay attack, VIN protection |

---

## Robot Framework Keywords

### CANLibrary
- `Connect To CAN Bus` / `Disconnect From CAN Bus`
- `Send CAN Frame` / `Send CAN Frame Periodically`
- `Wait For CAN Frame`
- `Signal Should Be In Range` / `Signal Should Equal`
- `Wait For Signal Change`

### UDSLibrary
- `Open UDS Session` / `Close UDS Session` / `Switch To UDS Session`
- `Read DID` / `Write DID` / `DID Value Should Be`
- `Read DTCs` / `DTC Should Be Set` / `No DTCs Should Be Present`
- `Clear DTCs` / `Reset ECU` / `Unlock Security Access`
- `Read VIN` / `VIN Should Be`

### ADASLibrary
- `Set Vehicle Speed` / `Set Lane Deviation`
- `Activate ACC` / `Deactivate ACC` / `ACC Status Should Be`
- `Inject Emergency Braking Event` / `AEB Should Trigger Full Brake`
- `LKA Should Be Active` / `LKA Torque Should Not Exceed`
- `Inject Fault` / `Wait For Signal Value` / `Wait For ADAS Active`

### SensorLibrary
- `Inject Radar Object` / `Radar Should Detect Target`
- `Camera Should Detect Lane` / `Camera Image Quality Should Meet Spec`
- `LiDAR Should Detect Obstacle` / `LiDAR Should Have Minimum Points`
- `Inject Fused Object` / `Fusion Should Track Object`
- `Fusion Timestamps Should Be Synced` / `Fusion Latency Should Be Under`

---

## CI/CD Pipeline

### Jenkins (8 Stages)
```
Setup → Lint → Flash ECU → Smoke → Regression → Safety → Performance → Report
```
Supports: Docker agent, email notifications, Allure publishing, HIL self-hosted runner.

### GitHub Actions
- **Matrix regression**: Each ADAS feature in parallel
- **Nightly schedule** at 02:00 UTC
- **HIL self-hosted runner** for `release/**` branches
- **Allure → GitHub Pages** for main branch
- **Failure notifications** via email

---

## Safety Compliance Metadata

All tests carry ASIL metadata propagated to Allure:

```python
@pytest.mark.asil_d
@pytest.mark.safety
class TestAEB(ADASBaseTest):
    ASIL    = "D"
    FEATURE = "AEB"
    REQ_IDS = ["AEB_REQ_001", "AEB_REQ_050"]
```

This enables:
- Allure test categorisation by ASIL level
- CI gating: ASIL D failures block release
- ASPICE traceability: requirement → test → result
- ISO 26262 evidence generation

---

## Configuration Priority (highest first)

1. CLI argument (`--channel=PCAN0`)
2. Environment variable (`CAN_CHANNEL=PCAN0`)
3. YAML config file (`configs/framework_config.yaml`)
4. Built-in defaults

---

## Extending the Framework

### Add a new ADAS feature
1. Create `pytest_framework/test_suites/<feature>/test_<feature>.py`
2. Add marker in `conftest.py` `pytest_configure`
3. Create `robot_framework/test_suites/<Feature>_TestSuite.robot`
4. Add signal constants and limits to `configs/framework_config.yaml`

### Add a new keyword library
1. Implement `robot_framework/libraries/<Name>Library.py`
2. Decorate with `@library` and `@keyword`
3. Import in `robot_framework/resources/common.resource`

---

## Standards Compliance

| Standard | Coverage |
|----------|----------|
| ISO 26262 ASIL A–D | ASIL metadata, safety test gating |
| UN-R152 AEB | Pedestrian/vehicle detection, latency limits |
| Euro NCAP AEB | Pedestrian, cyclist, CCR scenarios |
| NHTSA FMVSS 127 | Forward collision, AEB activation |
| ISO 21434 (Cybersecurity) | UDS auth, replay, seed entropy |
| ASPICE SWE.4/SWE.5 | Requirement traceability in test metadata |
| AUTOSAR | DID naming, DTC handling conventions |
