# ECU Regression Suite

A Python + pytest framework for per-release UDS/DID/RID/NRC regression testing
of ADAS and Infotainment ECUs. Every test run is tagged with the ECU software
version under test and automatically compared against the last known-good
baseline to detect regressions before release sign-off.

> **MOCK/SIMULATED mode** — The suite ships with a full simulated UDS engine so
> it can run on any CI machine without Vector hardware. Set `--no-mock` and
> configure `--channel` to connect to real hardware.

---

## Project Structure

```
ecu_regression_suite/
├── core/
│   ├── vector_interface.py      # Real/Mock CAN interface
│   ├── isotp_transport.py       # ISO 15765-2 transport layer
│   ├── uds_client.py            # UDS client + full mock ECU engine
│   ├── security_access.py       # Pluggable seed/key interface
│   ├── nrc_catalog.py           # ISO 14229-1 NRC catalog
│   ├── baseline_manager.py      # Save/load/diff baseline results
│   └── report_generator.py      # HTML + JSON release report
├── config/
│   ├── adas/
│   │   ├── did_matrix.yaml
│   │   ├── rid_matrix.yaml
│   │   ├── nrc_expected_matrix.yaml
│   │   └── sessions_security.yaml
│   └── infotainment/
│       └── (same files)
├── baselines/
│   ├── adas/v1.2.0_baseline.json
│   └── infotainment/v2.0.4_baseline.json
├── tests/
│   ├── conftest.py              # Fixtures, parametrisation, CLI options
│   ├── uds_services/            # 0x10, 0x11, 0x14, 0x19, 0x22, 0x27…
│   ├── nrc_matrix/              # Data-driven NRC coverage
│   └── regression/              # Baseline diff: DID, RID, NRC, service
├── reports/                     # Auto-generated HTML + JSON reports
├── logs/
├── requirements.txt
└── pytest.ini
```

---

## Installation

```bash
cd ecu_regression_suite
pip install -r requirements.txt
```

---

## Running the Suite

### Mock mode (no hardware — default)

```bash
# Run full ADAS suite
pytest --ecu=adas --version=v1.3.0

# Run infotainment suite
pytest --ecu=infotainment --version=v2.1.0

# Run against specific baseline
pytest --ecu=adas --version=v1.3.0 --baseline-version=v1.2.0

# Run only regression comparison tests
pytest --ecu=adas --version=v1.3.0 -m regression

# Run smoke subset
pytest --ecu=adas --version=v1.3.0 -m smoke

# Parallel execution (requires pytest-xdist)
pytest --ecu=adas --version=v1.3.0 -n 4
```

### Real hardware mode

```bash
# Connect to Vector hardware on channel 1, 500 kbps
pytest --ecu=adas --version=v1.3.0 --no-mock --channel=VECTOR::0 --bitrate=500000
```

---

## Establishing the First Baseline

The first time you run the suite against a new ECU or version, there is no
prior baseline to compare against. The suite detects this automatically:

1. All tests run normally; results are collected.
2. `pytest_sessionfinish` saves the results to
   `baselines/<ecu>/<version>_baseline.json`.
3. The report notes "first baseline run — no comparison available".

**Command:**
```bash
pytest --ecu=adas --version=v1.2.0
# → baselines/adas/v1.2.0_baseline.json created automatically
```

---

## Updating the Baseline After an Accepted Release

When a new release is validated and accepted:

1. Run the full suite against the new version:
   ```bash
   pytest --ecu=adas --version=v1.3.0
   ```
2. Review the report in `reports/adas_v1.3.0_<timestamp>.html`.
3. If the sign-off recommendation is **GO**, the baseline is already saved
   automatically as `baselines/adas/v1.3.0_baseline.json`.
4. Future runs will automatically use the most recent baseline.

To explicitly pin a comparison baseline:
```bash
pytest --ecu=adas --version=v1.4.0 --baseline-version=v1.3.0
```

---

## Adding New DIDs, RIDs, or NRC Scenarios

### Adding a DID

Edit `config/<ecu>/did_matrix.yaml` and append a new entry:

```yaml
- id: "0xD099"
  name: "NewFeatureStatus"
  description: "Status byte for new feature XYZ"
  length: 1
  data_type: "uint8"
  readable: true
  writable: true
  sessions: [extended]
  security_level: 1
  mock_value: "00"
  write_test_value: "01"
```

No test code changes needed. `pytest_generate_tests` picks up the new entry
automatically on the next run.

### Adding an RID

Edit `config/<ecu>/rid_matrix.yaml`:

```yaml
- id: "0x0208"
  name: "NewSensorCalibration"
  description: "Calibration routine for new sensor"
  supports_start: true
  supports_stop: false
  supports_results: true
  sessions: [extended]
  security_level: 1
  expected_duration_ms: 1000
  max_duration_ms: 5000
  mock_result: "0100"
```

### Adding an NRC Scenario

Edit `config/<ecu>/nrc_expected_matrix.yaml`:

```yaml
- scenario: "read_new_did_in_wrong_session"
  service_id: "0x22"
  trigger_action: "read_did_0xD099_no_security"
  setup_session: "extended"
  setup_security: 0
  expected_nrc: "0x33"
  description: "Read new DID without security access"
```

Then add the trigger mapping to
`tests/nrc_matrix/test_nrc_responses.py::_trigger_nrc_scenario` if the
`trigger_action` string is new.

---

## CI/CD Pipeline Integration

The suite outputs a machine-readable JSON report alongside every HTML report.
Use the JSON sign-off field as a pipeline gate:

### GitHub Actions example

```yaml
- name: Run ECU Regression Suite
  run: |
    cd ecu_regression_suite
    pytest --ecu=adas --version=${{ env.SW_VERSION }} --mock \
           --baseline-version=${{ env.LAST_GOOD_VERSION }} \
           --tb=short -q

- name: Check sign-off
  run: |
    python - <<'EOF'
    import json, glob, sys
    reports = sorted(glob.glob("ecu_regression_suite/reports/adas_*.json"))
    if not reports:
        print("No report found"); sys.exit(1)
    data = json.load(open(reports[-1]))
    cmp = data.get("baseline_comparison", {})
    if cmp.get("has_regressions"):
        print(f"REGRESSIONS DETECTED: {cmp['regressions']} regressions")
        sys.exit(1)
    print("Sign-off:", cmp.get("sign_off", "N/A"))
    EOF
```

### Jenkins / dSPACE VEOS integration

Point the JSON report path at your QA dashboard tool. The JSON schema:

```json
{
  "baseline_comparison": {
    "has_regressions": false,
    "regressions": 0,
    "sign_off": "GO — no regressions detected"
  }
}
```

---

## Security Access Algorithm

The suite ships with an XOR placeholder algorithm that works with the mock ECU
engine. For real hardware, replace it by:

1. Subclassing `core.security_access.SecurityAlgorithmBase`.
2. Implementing `compute_key(seed, level)` using the OEM algorithm.
3. Registering it: `register_algorithm("my_ecu_algo", MyAlgo())`.
4. Referencing the name in `sessions_security.yaml`:
   ```yaml
   security:
     levels:
       "1":
         algorithm: "my_ecu_algo"
   ```

> The OEM algorithm must **never** be committed to source control.
> Load it at runtime from a secure vault or DLL.

---

## Assumptions & Defaults

| Parameter | Default | Basis |
|-----------|---------|-------|
| CAN bitrate | 500 kbps | ISO 14229 default |
| P2 server timeout | 50 ms | ISO 14229-1 §7.2 |
| P2* extended timeout | 5000 ms | ISO 14229-1 §7.2 |
| Security lockout attempts | 3 | Typical OEM |
| Security lockout delay | 10 s | Typical OEM |
| Timing regression threshold | 50 ms or 100% drift | Configurable in YAML |

Adjust per ECU requirements in `config/<ecu>/sessions_security.yaml`.
