# TCU Validation Framework

[![Build Status](https://github.com/your-org/tcu_validation_framework/actions/workflows/ci.yml/badge.svg)](https://github.com/your-org/tcu_validation_framework/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![C++17](https://img.shields.io/badge/C%2B%2B-17-blue.svg)](https://en.cppreference.com/w/cpp/17)
[![CMake 3.18+](https://img.shields.io/badge/CMake-3.18%2B-green.svg)](https://cmake.org)
[![Platform: Linux](https://img.shields.io/badge/Platform-Linux-lightgrey.svg)]()

A **production-grade, enterprise-level C/C++ platform** for end-to-end validation of Telematics Control Units (TCU). Covers CAN/CAN-FD communication, UDS diagnostics (ISO 14229), OTA firmware updates, telematics SDK integration, fault injection, and automated test reporting — all driven by a single configurable binary.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     TCU Validation Framework                         │
│                                                                       │
│  Layer 1: CLI (main.cpp) ──── Layer 9: Config (JSON + hot-reload)   │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │               Framework (Singleton lifecycle)                │    │
│  └─────┬───────────────────────────────────────────────────────┘    │
│        │                                                              │
│  ┌─────┴────────────────────────────────────────────────────────┐   │
│  │                     Module Layer                              │   │
│  │                                                               │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │   │
│  │  │  Layer 2 │  │  Layer 3 │  │  Layer 4 │  │  Layer 5 │    │   │
│  │  │  CAN     │  │  UDS     │  │  Firmware│  │ Telematics│   │   │
│  │  │ Manager  │  │  Client  │  │  Flasher │  │  Adapter │    │   │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │   │
│  │                                                               │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │   │
│  │  │  Layer 6 │  │  Layer 6 │  │  Layer 7 │  │  Layer 8 │    │   │
│  │  │   Test   │  │  Fault   │  │  Logger  │  │ Reporter │    │   │
│  │  │  Engine  │  │ Injector │  │ (spdlog) │  │HTML+JSON+│    │   │
│  │  └──────────┘  └──────────┘  └──────────┘  │   CSV    │    │   │
│  │                                              └──────────┘    │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                       │
│  External: SocketCAN │ MQTT (mTLS) │ OEM SDK │ Renesas RFP CLI      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Quick Start (3 Commands)

```bash
scripts/setup.sh          # Install dependencies
scripts/setup_vcan.sh     # Create virtual CAN interface
scripts/build.sh && build/Debug/bin/tcu_validator --simulate
```

---

## Features

| Feature | Details |
|---------|---------|
| **CAN/CAN-FD** | SocketCAN raw socket, Rx callback dispatch, error frames, statistics |
| **UDS (ISO 14229)** | Software ISO-TP, all services (0x10–0x3E), NRC 0x78 handling |
| **Firmware Flash** | UDS 0x34/0x36/0x37 block transfer + Renesas RFP CLI, pre-flash CRC-32 |
| **OTA** | OEM SDK abstraction, MQTT telemetry, acknowledge/progress flow |
| **Test Engine** | Sequential & parallel execution, preconditions, retries, timeouts, RAII fault injection |
| **Fault Injection** | 13 fault types: CAN drop, network loss, UDS malformed, OTA interrupted, security attack, memory pressure |
| **Logging** | spdlog async, rotating file + colour console, `ScopedTimer` RAII |
| **Reporting** | Dark-theme HTML, structured JSON, RFC 4180 CSV |
| **Config** | nlohmann::json, dot-path get/set, env overrides (`TCU_CFG_*`), hot reload |
| **Testing** | GoogleTest unit + integration + stress, vcan0 conditional skip |
| **DevOps** | GitHub Actions, Jenkins, Docker, cppcheck, clang-tidy, SonarQube |

---

## Requirements

- Linux (Ubuntu 22.04 recommended) — SocketCAN requires Linux kernel ≥ 5.4
- CMake ≥ 3.18
- GCC ≥ 10 or Clang ≥ 12 (C++17 required)
- Ninja (recommended) or Make
- Internet access for first CMake build (FetchContent downloads dependencies)

---

## Full Build Instructions

### Debug build (with sanitizers + tests)
```bash
cmake -S . -B build/Debug \
    -G Ninja \
    -DCMAKE_BUILD_TYPE=Debug \
    -DBUILD_TESTS=ON \
    -DCMAKE_EXPORT_COMPILE_COMMANDS=ON

cmake --build build/Debug --parallel $(nproc)
```

### Release build (optimised, no tests)
```bash
cmake -S . -B build/Release \
    -G Ninja \
    -DCMAKE_BUILD_TYPE=Release \
    -DBUILD_TESTS=OFF

cmake --build build/Release --parallel $(nproc)
```

### Using the build script
```bash
scripts/build.sh                       # Debug (default)
BUILD_TYPE=Release scripts/build.sh    # Release
```

### CMake options
| Option | Default | Description |
|--------|---------|-------------|
| `BUILD_TESTS` | `ON` | Include GoogleTest binaries |
| `ENABLE_SANITIZERS` | ON in Debug | ASan + UBSan |
| `CMAKE_EXPORT_COMPILE_COMMANDS` | `ON` | Required by clang-tidy |

---

## Test Execution

```bash
# Setup virtual CAN interface
scripts/setup_vcan.sh

# Run all tests with XML reports
scripts/run_tests.sh

# Individual test binaries
build/Debug/bin/unit_tests
build/Debug/bin/integration_tests
build/Debug/bin/stress_tests

# Filter by test name
build/Debug/bin/unit_tests --gtest_filter="CANManagerTest.*"

# With coverage report
COVERAGE=1 scripts/run_tests.sh
open reports/coverage.html
```

---

## Running tcu_validator

```bash
# Simulation mode (no hardware)
./build/Debug/bin/tcu_validator \
    --config configs/default.json \
    --simulate \
    --verbose

# Physical CAN + production config
./build/Release/bin/tcu_validator \
    --config configs/default.json \
    --profile production \
    --interface can0

# Run only telematics tests
./build/Release/bin/tcu_validator \
    --config configs/default.json \
    --suite telematics \
    --simulate

# Custom report output
./build/Release/bin/tcu_validator \
    --simulate \
    --output /tmp/my_reports
```

---

## Firmware Flashing

### UDS path (via CAN)
```bash
FIRMWARE_FILE=firmware/tcu_v2.1.0.hex \
CAN_INTERFACE=can0 \
FLASH_METHOD=uds \
scripts/flash_firmware.sh
```

### Renesas RFP CLI path
```bash
FIRMWARE_FILE=firmware/tcu_v2.1.0.mot \
FLASH_METHOD=rfp \
scripts/flash_firmware.sh
```

### Manual CRC-32 check
```bash
python3 -c "
import zlib, sys
data = open(sys.argv[1], 'rb').read()
print(hex(zlib.crc32(data) & 0xFFFFFFFF))
" firmware/tcu_v2.1.0.hex
```

---

## CAN Simulation

```bash
# Start virtual CAN
scripts/setup_vcan.sh

# Send a frame
cansend vcan0 7E0#022710FF00000000

# Capture traffic
candump -l vcan0

# Replay a capture
python3 tools/can_replay.py \
    --file candump.log \
    --interface vcan0 \
    --speed 1.0 \
    --loop
```

---

## Configuration Profiles

| Profile | Config | Use case |
|---------|--------|---------|
| Default | `configs/default.json` | Development, simulation |
| Production | `configs/production.json` | Physical hardware, mTLS |
| Test | `configs/test.json` | CI, short timeouts |

Apply a profile:
```bash
tcu_validator --config configs/default.json --profile production
```

Override any key via environment:
```bash
export TCU_CFG_CAN_INTERFACE=can0
export TCU_CFG_TELEMATICS_SIMULATION_MODE=false
tcu_validator --config configs/default.json
```

---

## Docker

```bash
# Build runtime image
docker build --target runtime -t tcu-validation-framework:latest .

# Run in simulation mode
docker run --rm \
    -v $(pwd)/configs:/app/configs:ro \
    -v $(pwd)/reports:/app/reports \
    tcu-validation-framework:latest \
    --config /app/configs/default.json --simulate

# Full stack with MQTT broker
docker-compose up tcu-validator mqtt-broker

# Run tests in Docker
docker-compose --profile test up tcu-test
```

---

## Project Layout

```
tcu_validation_framework/
├── CMakeLists.txt
├── include/                   Public C++ headers
│   ├── core/        can/    diagnostics/    firmware/
│   ├── telematics/  validation/    logging/
│   └── reporting/   config/
├── src/                       Implementations
├── tests/
│   ├── unit/                  GoogleTest unit tests
│   ├── integration/           Multi-module tests (needs vcan0)
│   └── stress/                Throughput + concurrency
├── configs/
│   ├── default.json           Base configuration
│   ├── production.json        Production overlay
│   └── test.json              CI overlay
├── scripts/
│   ├── setup.sh               Install dependencies
│   ├── setup_vcan.sh          Create virtual CAN
│   ├── build.sh               CMake configure + build
│   ├── run_tests.sh           Run all tests with reports
│   └── flash_firmware.sh      Firmware flash workflow
├── tools/
│   └── can_replay.py          CAN log replay tool
├── docs/
│   ├── architecture/SAD.md    Software Architecture Document
│   ├── design/LLD.md          Low-Level Design
│   ├── api/API.md             Full API Reference
│   ├── integration/           OEM SDK integration guide
│   └── guides/                Build, Flash, CAN, Tests, CI/CD...
├── Dockerfile
├── docker-compose.yml
├── .github/workflows/ci.yml   GitHub Actions
├── Jenkinsfile                Jenkins declarative pipeline
├── .clang-tidy
├── .clang-format
└── sonar-project.properties
```

---

## Documentation

| Document | Description |
|----------|-------------|
| [SAD](docs/architecture/SAD.md) | Software Architecture Document — component overview, threading model, data flows |
| [LLD](docs/design/LLD.md) | Low-Level Design — class diagrams, sequence diagrams, state machines |
| [API Reference](docs/api/API.md) | Full public API for all 9 modules |
| [Integration Guide](docs/integration/Integration_Guide.md) | Replace simulation with real OEM SDK |
| [Build & Deploy](docs/guides/Build_Deploy.md) | CMake, CPack, Docker deployment |
| [TCU Flashing](docs/guides/TCU_Flashing.md) | UDS + RFP firmware flash guide |
| [CAN Configuration](docs/guides/CAN_Config.md) | Interface setup, filtering, DBC usage |
| [Test Execution](docs/guides/Test_Execution.md) | Running tests, interpreting reports |
| [Troubleshooting](docs/guides/Troubleshooting.md) | Common issues and fixes |
| [Developer Onboarding](docs/guides/Developer_Onboarding.md) | New developer setup, conventions |
| [CI/CD Setup](docs/guides/CICD_Setup.md) | GitHub Actions + Jenkins configuration |
| [User Manual](docs/guides/User_Manual.md) | tcu_validator usage reference |

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Run tests and static analysis before committing:
   ```bash
   scripts/run_tests.sh
   cmake --build build/Debug --target cppcheck clang-tidy
   find src/ include/ -name '*.cpp' -o -name '*.h' | xargs clang-format -i
   ```
4. Commit with descriptive messages: `feat(can): add CAN-FD filter mask support`
5. Open a Pull Request — CI must be green before merge

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

## Authors

TCU Validation Framework — automotive test & validation platform.  
Built with spdlog, nlohmann/json, GoogleTest, and the Linux SocketCAN subsystem.
