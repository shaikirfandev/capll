# User Manual
## TCU Validation Framework v2.0.0

---

## 1. Introduction

The `tcu_validator` binary is the primary entry point for running TCU validation suites. It initialises all modules, executes the requested test cases, generates reports, and exits with:
- `0` — all tests passed (or were skipped)
- `1` — one or more tests failed

---

## 2. Installation

### From DEB package
```bash
sudo dpkg -i TCU_Validation_Framework-2.0.0-Linux.deb
which tcu_validator    # /usr/local/bin/tcu_validator
```

### From source build
```bash
scripts/build.sh
# Binary at: build/Debug/bin/tcu_validator
```

---

## 3. Command-Line Reference

```
Usage: tcu_validator [OPTIONS]

Options:
  --config  <path>      Path to JSON config file  (default: configs/default.json)
  --profile <name>      Config profile overlay     (default: none)
  --suite   <tag>       Run only tests with this tag
  --output  <dir>       Report output directory    (default: reports/)
  --interface <name>    CAN interface override     (default: from config)
  --simulate            Force simulation mode (no hardware required)
  --verbose             Enable DEBUG log level
  --help                Show this help message
```

### Examples

#### Run all tests in simulation mode
```bash
tcu_validator --config configs/default.json --simulate
```

#### Run only CAN tests on physical hardware
```bash
tcu_validator \
    --config configs/default.json \
    --profile production \
    --suite can \
    --interface can0
```

#### Run with verbose logging and custom output dir
```bash
tcu_validator \
    --config configs/default.json \
    --simulate \
    --verbose \
    --output /tmp/reports
```

---

## 4. Configuration File Reference

The framework loads `configs/default.json` as the base and deep-merges the optional `--profile` overlay on top.

### Key sections

#### CAN interface
```json
{
  "can": {
    "interface": "vcan0",
    "bitrate": 500000,
    "enable_fd": false
  }
}
```

#### UDS diagnostics
```json
{
  "uds": {
    "tx_id": "0x7E0",
    "rx_id": "0x7E8",
    "p2_timeout_ms": 50,
    "p2_star_timeout_ms": 5000
  }
}
```

#### Telematics / OTA
```json
{
  "telematics": {
    "simulation_mode": true,
    "server_url": "mqtt://localhost:1883",
    "device_id": "TCU_DEV_001"
  }
}
```

#### Logging
```json
{
  "logging": {
    "level": "info",
    "file": "logs/tcu.log",
    "max_file_size_mb": 10,
    "max_files": 5
  }
}
```

#### Reporting
```json
{
  "reporting": {
    "output_dir": "reports/",
    "base_filename": "tcu_validation_report",
    "format": "all"
  }
}
```

---

## 5. Environment Variable Overrides

Any configuration value can be overridden at the OS level without editing JSON files:

```bash
export TCU_CFG_CAN_INTERFACE=can0
export TCU_CFG_TELEMATICS_SIMULATION_MODE=false
export TCU_CFG_LOGGING_LEVEL=warn

tcu_validator --config configs/default.json
```

Pattern: `TCU_CFG_<SECTION>_<KEY>` → `section.key`

---

## 6. Available Test Suites

The default suite includes these test cases:

| ID | Description | Tag | Critical |
|----|-------------|-----|---------|
| TC001 | CAN Interface Health | can | Yes |
| TC002 | Telematics SDK Connection | telematics | No |
| TC003 | Telemetry Publish | telematics | No |
| TC004 | OTA Package Detection | telematics, ota | No |
| TC005 | UDS Session Control | uds | No |
| TC006 | Fault Injection Recovery | fault | No |

Run a subset by tag:
```bash
tcu_validator --suite telematics --simulate
tcu_validator --suite uds --interface can0
```

---

## 7. Output Reports

After every run, three report files are created in the output directory:

| File | Format | Use |
|------|--------|-----|
| `tcu_validation_report.html` | HTML with dark theme | Human review, browser |
| `tcu_validation_report.json` | JSON structured data | Automation, dashboards |
| `tcu_validation_report.csv` | RFC 4180 CSV | Excel, Jira import |

Open the HTML report:
```bash
xdg-open reports/tcu_validation_report.html   # Linux
open reports/tcu_validation_report.html        # macOS
```

---

## 8. Log Files

Logs are written to `logs/tcu.log` (rotated at 10 MB, 5 files retained).  
The console always receives coloured output at the configured level.

Log levels (from most to least verbose):
```
trace → debug → info → warn → error → critical
```

Change level at runtime:
```bash
export TCU_CFG_LOGGING_LEVEL=debug
tcu_validator --simulate --verbose
```

---

## 9. Exit Codes

| Code | Meaning |
|------|---------|
| `0` | All tests passed or skipped |
| `1` | One or more tests failed |
| `2` | Initialisation error (bad config, CAN open failed) |
| `130` | Terminated by SIGINT (Ctrl-C) — graceful shutdown |

---

## 10. Stopping Gracefully

Press `Ctrl-C` or send `SIGTERM`:
```bash
kill -TERM $(pgrep tcu_validator)
```

The framework will:
1. Receive the signal
2. Call `Framework::request_shutdown()`
3. Stop all modules in reverse order
4. Flush logs and close report files
5. Exit with the appropriate code

---

## 11. Docker Usage

### Run in simulation mode
```bash
docker run --rm \
    -v $(pwd)/configs:/app/configs:ro \
    -v $(pwd)/reports:/app/reports \
    tcu-validation-framework:latest \
    --config /app/configs/default.json --simulate
```

### Run against physical CAN (host network)
```bash
docker run --rm \
    --cap-add=NET_ADMIN \
    --network=host \
    -v $(pwd)/configs:/app/configs:ro \
    -v $(pwd)/reports:/app/reports \
    tcu-validation-framework:latest \
    --config /app/configs/production.json \
    --interface can0
```

---

## 12. Common Workflows

### Daily smoke test (simulation)
```bash
tcu_validator --simulate --suite can,telematics
```

### Pre-release full validation
```bash
tcu_validator \
    --config configs/production.json \
    --interface can0 \
    --output reports/release-$(date +%Y%m%d)
```

### Firmware update workflow
```bash
# 1. Verify firmware file
python3 -c "import zlib,sys; d=open(sys.argv[1],'rb').read(); print(hex(zlib.crc32(d)&0xFFFFFFFF))" \
    firmware/tcu_v2.1.0.hex

# 2. Flash
FIRMWARE_FILE=firmware/tcu_v2.1.0.hex \
CAN_INTERFACE=can0 \
scripts/flash_firmware.sh

# 3. Validate post-flash
tcu_validator --config configs/production.json --suite uds
```
