# Bluetooth Firmware

A production-representative **Bluetooth stack implementation in Modern C++17** targeting automotive infotainment, wearable, and IoT/telematics ECUs.

[![CI](https://github.com/yourorg/bluetooth_firmware/actions/workflows/ci.yml/badge.svg)](https://github.com/yourorg/bluetooth_firmware/actions)
[![Coverage](https://codecov.io/gh/yourorg/bluetooth_firmware/branch/main/graph/badge.svg)](https://codecov.io/gh/yourorg/bluetooth_firmware)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Application Layer                   │
│   ConnectionManager │ OtaManager │ DiagnosticsModule │
├─────────────────────────────────────────────────────┤
│               BT Profile Layer                       │
│      A2dpSimulator │ HfpSimulator │ HidDevice        │
├─────────────────────────────────────────────────────┤
│                  BT Stack Layer                      │
│  BleAdvertiser  │  BleScanner   │  GattServer        │
│  GattClient     │  PairingMgr   │  SecurityManager   │
│  L2capManager   │  AttProtocol  │  RfcommSimulator   │
│  EventBus       │  ConnectionStateMachine            │
│  BluetoothController (Singleton, HCI transport)     │
├─────────────────────────────────────────────────────┤
│              HAL / Transport Layer                   │
│   UartDriver │ SpiDriver │ GpioDriver │ PowerManager │
├─────────────────────────────────────────────────────┤
│              RTOS Abstraction Layer                  │
│  StdThreadTask │ StdMutex │ StdQueue │ StdSemaphore  │
└─────────────────────────────────────────────────────┘
```

---

## Features

| Feature | Status |
|---|---|
| BLE Advertising / Scanning | ✅ |
| GATT Server (services, chars, CCCD) | ✅ |
| GATT Client (discovery, read/write, notify) | ✅ |
| Pairing (Just Works / Passkey / Numeric Comp) | ✅ |
| Bond storage (in-memory, 8 bonds max) | ✅ |
| Security Manager (LTK, IRK, encryption) | ✅ |
| A2DP streaming simulation | ✅ |
| HFP AT command handling | ✅ |
| HID keyboard report descriptor | ✅ |
| OTA firmware update (CRC-32, chunked DFU) | ✅ |
| Lock-free SPSC RingBuffer | ✅ |
| CRTP StateMachine template | ✅ |
| Connection FSM (10-state, 11-event) | ✅ |
| EventBus (sync + async dispatch) | ✅ |
| Diagnostics & health stats | ✅ |
| HAL: UART / SPI / GPIO / Power | ✅ |
| RTOS: Thread / Mutex / Queue / Semaphore | ✅ |
| GoogleTest unit + integration tests | ✅ |
| GitHub Actions CI (Debug/Release/ASan/TSan) | ✅ |
| Docker multi-stage build | ✅ |

---

## Quick Start

### Prerequisites
- CMake 3.18+
- GCC 11+ or Clang 13+ with C++17 support
- Ninja (recommended) or Make
- Internet access (FetchContent downloads spdlog, nlohmann_json, GoogleTest)

### Build

```bash
# Default Debug build with tests
./scripts/build.sh

# Release build without sanitizers
BUILD_TYPE=Release ./scripts/build.sh

# ASan build
ENABLE_ASAN=ON ./scripts/build.sh
```

### Run tests

```bash
./scripts/run_tests.sh
```

### Run firmware binary

```bash
./build/bt_firmware
```

### Docker build

```bash
docker build --target runtime -t bt_firmware:latest .
docker run --rm bt_firmware:latest
```

---

## Project Structure

```
bluetooth_firmware/
├── CMakeLists.txt            # Top-level build
├── Dockerfile                # 3-stage: builder → analyzer → runtime
├── config/
│   ├── bt_config.json        # Runtime configuration
│   └── device_config.hpp     # Compile-time constants
├── include/
│   ├── bt/                   # BT stack interfaces (I-prefixed pure virtual)
│   ├── hal/                  # HAL interfaces
│   ├── rtos/                 # RTOS abstraction interfaces
│   ├── app/                  # Application layer interfaces
│   └── common/               # Logger, RingBuffer, StateMachine, ErrorCodes
├── src/
│   ├── bt/                   # Stack implementations + profiles/
│   ├── hal/                  # HAL simulated drivers
│   ├── rtos/                 # std:: based RTOS wrappers
│   ├── app/                  # Application modules
│   └── main.cpp              # Entry point
├── tests/
│   ├── unit/                 # GoogleTest unit tests + GMock mocks
│   └── integration/          # Integration tests (full stack)
├── scripts/                  # build.sh, run_tests.sh, generate_docs.sh
└── docs/                     # Architecture, SDD, SRS, Interview Q&A
```

---

## Design Patterns Used

| Pattern | Where |
|---|---|
| **Pimpl** (compile-time firewall) | Every concrete class (`struct Impl + unique_ptr`) |
| **Singleton** | `BluetoothController::instance()` |
| **Observer** | `IEventBus / EventBus` with shared_mutex |
| **State Machine (CRTP)** | `StateMachine<D,S,E>` → `ConnectionStateMachine` |
| **Factory / Strategy** | `IBleAdvertiser::make_automotive_adv()` |
| **Interface Segregation** | All layers depend on `I`-prefixed pure virtual interfaces |
| **RAII** | All resources released in destructors, no naked new/delete |

---

## Automotive Industry Context

| Target Platform | Mapping |
|---|---|
| Qualcomm QCC5171 | `BluetoothController` ↔ HCI UART @ 3 Mbaud |
| Texas Instruments CC2642R | `GattServer` ↔ TI BLE5-Stack GATT APIs |
| NXP KW45 | `PowerManager` ↔ XCVR power modes |
| STMicro BlueNRG-LP | `SpiDriver` ↔ SPI HCI transport |
| FreeRTOS (production) | Replace `StdThread*` with `FreeRTOS*` implementations |

---

## License

MIT — see [LICENSE](LICENSE)
