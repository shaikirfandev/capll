# Software Architecture Document (SAD)
## TCU Validation Framework v2.0.0

---

## 1. Introduction

### 1.1 Purpose
This document describes the software architecture of the **TCU Validation Framework** — a production-grade platform for automated testing and validation of Telematics Control Units (TCU) in automotive systems.

### 1.2 Scope
The framework covers:
- CAN/CAN-FD bus communication (SocketCAN)
- UDS diagnostics (ISO 14229 over ISO-TP ISO 15765-2)
- OTA firmware update orchestration (UDS + Renesas RFP CLI)
- Telematics SDK abstraction (MQTT, OEM SDK)
- Test engine with fault injection
- Structured logging, HTML/JSON/CSV reporting
- JSON configuration with hot reload

### 1.3 Definitions
| Term | Meaning |
|------|---------|
| TCU | Telematics Control Unit |
| UDS | Unified Diagnostic Services (ISO 14229) |
| ISO-TP | ISO Transport Protocol (ISO 15765-2) |
| CAN-FD | CAN Flexible Data-rate |
| OTA | Over-The-Air update |
| DTC | Diagnostic Trouble Code |
| ECU | Electronic Control Unit |

---

## 2. Architectural Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                     TCU Validation Framework                         │
│                                                                       │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────────────────┐   │
│  │  CLI / main │   │  Config     │   │  Logging (spdlog async) │   │
│  │  (main.cpp) │   │  Manager    │   │  rotating + console     │   │
│  └──────┬──────┘   └──────┬──────┘   └─────────────────────────┘   │
│         │                 │                                           │
│  ┌──────▼─────────────────▼──────────────────────────────────────┐  │
│  │               Framework (Singleton lifecycle manager)          │  │
│  │  register_module() → start() → wait_for_shutdown()            │  │
│  └──────┬────────────────────────────────────────────────────────┘  │
│         │                                                             │
│    ┌────┴─────────────────────────────────────┐                      │
│    │               Module Layer                │                      │
│    │  ┌──────────┐  ┌──────────┐  ┌────────┐ │                      │
│    │  │CAN       │  │Telematics│  │Firmware│ │                      │
│    │  │Manager   │  │SDK Adapter│ │Flasher │ │                      │
│    │  └────┬─────┘  └────┬─────┘  └───┬────┘ │                      │
│    │       │             │             │       │                      │
│    │  ┌────▼─────┐  ┌────▼──────┐ ┌───▼────┐ │                      │
│    │  │UDS Client│  │CRC Valid. │ │Report  │ │                      │
│    │  └──────────┘  └───────────┘ │Generat.│ │                      │
│    │                               └────────┘ │                      │
│    │  ┌──────────────────────┐                │                      │
│    │  │ Test Engine          │                │                      │
│    │  │ FaultInjector        │                │                      │
│    │  └──────────────────────┘                │                      │
│    └──────────────────────────────────────────┘                      │
│                                                                       │
│  External Interfaces:                                                 │
│  ┌────────────┐  ┌────────────┐  ┌─────────────┐                    │
│  │ SocketCAN  │  │ MQTT Broker│  │ OEM SDK /   │                    │
│  │ (vcan0/    │  │ (port 1883 │  │ RFP CLI     │                    │
│  │  can0)     │  │  /8883 TLS)│  │ popen()     │                    │
│  └────────────┘  └────────────┘  └─────────────┘                    │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. Layer Descriptions

### Layer 1 — Core Framework (`core/`)
**Class:** `tcu::Framework` (Singleton)

Responsibilities:
- Module lifecycle management (register → start → health-check → shutdown)
- SIGINT/SIGTERM graceful shutdown via `request_shutdown()`
- Ordered startup (registration order) and reverse-ordered teardown
- Periodic health check callbacks per module

Key interactions:
- Owns `std::vector<ModuleEntry>` with name, start/stop/health callbacks
- `wait_for_shutdown()` blocks on a `condition_variable` until `request_shutdown()` fires

### Layer 2 — CAN Communication (`can/`)
**Class:** `tcu::CANManager`

Responsibilities:
- SocketCAN socket lifecycle: `socket(PF_CAN, SOCK_RAW, CAN_RAW)` → `bind()`
- CAN-FD optional: `setsockopt(CAN_RAW_FD_FRAMES)`
- Error frame mask subscription
- Dedicated Rx thread with `select()` 100 ms timeout loop
- Mutex-protected Tx queue
- Frame callback registry (can_id mask matching)
- Statistics: rx_count, tx_count, error_count

### Layer 3 — UDS Diagnostics (`diagnostics/`)
**Class:** `tcu::UDSClient`

Responsibilities:
- Software ISO-TP (ISO 15765-2) framing: SF/FF/CF/FC
- P2/P2* timer management
- NRC 0x78 `responsePending` loop (up to 150 × P2*)
- Full service coverage: 0x10 SessionControl, 0x11 ECUReset, 0x22 ReadByID, 0x27 SecurityAccess, 0x14 ClearDTC, 0x19 ReadDTC, 0x2E WriteByID, 0x31 RoutineControl, 0x34/0x36/0x37 Download, 0x28 CommControl, 0x3E TesterPresent

### Layer 4 — Firmware Flashing (`firmware/`)
**Classes:** `tcu::FirmwareFlasher`, `tcu::CRCValidator`

Responsibilities:
- Pre-flash CRC-32/ISO-HDLC integrity check
- UDS path: Programming Session → Seed/Key → Erase → `0x34` RequestDownload → `0x36` TransferData blocks → `0x37` TransferExit → Checksum Routine → ECU Reset
- RFP CLI path: `popen()` subprocess with progress parsing
- Progress callbacks per block transfer

### Layer 5 — Telematics (`telematics/`)
**Class:** `tcu::TelematicsSDKAdapter`

Responsibilities:
- OEM SDK abstraction (concrete SDK hidden behind interface)
- `connect()` with exponential backoff (max 30 s)
- Heartbeat thread (30 s interval keep-alive)
- `publish_telemetry(json)` serialisation to MQTT topic
- OTA flow: `check_for_updates()` → `acknowledge_ota()` → `report_ota_progress()`
- Simulation mode: all traffic stored in-memory for test inspection

### Layer 6 — Validation (`validation/`)
**Classes:** `tcu::TestEngine`, `tcu::FaultInjector`

Responsibilities:
- Test case lifecycle: precondition → execute (with retries) → cleanup
- Sequential and parallel (std::async) execution modes
- Observer pattern via `IResultListener`
- RAII fault activation: inject → scope ends → auto-clear
- 13 fault types covering CAN, network, UDS, firmware, OTA, security, OS-level

### Layer 7 — Logging (`logging/`)
**Class:** `tcu::Logger`

Responsibilities:
- spdlog async thread pool (8192-message queue)
- Two sinks: rotating file (10 MB × 5 files) + stdout colour
- `get(name)` factory — returns async_logger; falls back to null_sink pre-init
- `ScopedTimer` RAII: logs µs elapsed on destruction

### Layer 8 — Reporting (`reporting/`)
**Class:** `tcu::ReportGenerator`

Responsibilities:
- HTML: dark-theme, colour-coded verdicts, progress bar, summary cards, results table
- JSON: structured nlohmann::json dump
- CSV: RFC 4180-compliant, quote-escaped special characters
- `ReportFormat::ALL` creates all three in one call

### Layer 9 — Configuration (`config/`)
**Class:** `tcu::ConfigManager`

Responsibilities:
- JSON load/overlay merge (deep merge recursion)
- Dot-path `get<T>()` navigation with default fallback
- Environment override: `TCU_CFG_KEY_SUBKEY` → `key.subkey`
- Mtime-based hot reload thread (polling every 1 s)
- Thread-safe reads via `shared_mutex`

---

## 4. Threading Model

```
Main thread
├── Framework::start() → calls module start() callbacks sequentially
│
├── CANManager Rx thread (detached)
│   └── select() loop → dispatch Rx callbacks on Rx thread
│
├── TelematicsSDKAdapter heartbeat thread
│   └── sleep 30s → ping OEM SDK
│
├── ConfigManager hot-reload thread
│   └── poll file mtime every 1s → reload+merge on change
│
└── Framework::wait_for_shutdown() (blocks main thread)
    └── condition_variable::wait() until request_shutdown() fires
```

All shared state protected by `std::mutex` or `std::shared_mutex`.  
Atomic flags (`std::atomic<bool>`) used for stop signals to background threads.

---

## 5. Data Flow — UDS Firmware Flash

```
main.cpp
  └─ FirmwareFlasher::flash_via_uds(file, addr)
       ├─ CRCValidator::verify_file() → CRC-32 check
       ├─ UDSClient::send_session_control(PROGRAMMING)
       ├─ UDSClient::send_security_access() → seed/key
       ├─ UDSClient::start_routine(ERASE_MEMORY)
       ├─ UDSClient::request_download(addr, size)
       ├─ for each 256-byte block:
       │    UDSClient::transfer_data(block_seq, data)
       │    progress_callback(pct)
       ├─ UDSClient::transfer_exit()
       ├─ UDSClient::start_routine(CHECK_PROGRAMMING)
       └─ UDSClient::send_ecu_reset(HARD)
```

---

## 6. Data Flow — OTA Update

```
TelematicsSDKAdapter::check_for_updates()
  └─ returns OTAPackageInfo{url, version, size, checksum}

main.cpp / TestEngine
  ├─ acknowledge_ota(version)           → OEM SDK → server
  ├─ report_ota_progress(10, "DL")      → heartbeat thread
  ├─ [download firmware to file]
  ├─ FirmwareFlasher::flash(file)       → UDS path
  └─ report_ota_progress(100, "Done")
```

---

## 7. External Interface Summary

| Interface | Protocol | Config Key | Notes |
|-----------|----------|------------|-------|
| SocketCAN Rx/Tx | CAN 2.0A/B, CAN-FD | `can.interface` | Linux only |
| UDS | ISO 14229 / ISO-TP | `uds.tx_id`, `uds.rx_id` | Software ISO-TP |
| MQTT | MQTT 3.1.1 | `telematics.server_url` | mTLS in production |
| OEM SDK | Proprietary | `telematics.*` | Abstracted via adapter |
| RFP CLI | CLI subprocess | `firmware.rfp_tool_path` | `popen()` |
| Reports | File I/O | `reporting.output_dir` | HTML, JSON, CSV |
| Config | JSON file | `--config` flag | Hot reload supported |
