# Embedded SoC Firmware Platform - Architecture Guide

## Executive Summary

The Embedded SoC Firmware Simulation Platform is a production-grade firmware simulator designed to replicate AMD Embedded SoC behavior and validate firmware functionality at the post-silicon stage. This guide explains the architecture, subsystem interactions, and design decisions.

## System Architecture Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                   Firmware Application Layer                     │
│                 (firmware_application.cpp)                       │
└─────────────────────────────────────────────────────────────────┘
         │
         ├─────────────────────────────────────────────────────────┐
         │                                                           │
    ┌────▼────┐  ┌────────┐  ┌───────┐  ┌──────────┐  ┌────────┐ │
    │   Boot  │  │ Power  │  │Memory │  │Security  │  │ Health │ │
    │ Manager │  │Manager │  │Manager│  │ Manager  │  │Monitor │ │
    └────┬────┘  └────────┘  └───────┘  └──────────┘  └────────┘ │
         │
    ┌────▼────┐  ┌────────┐  ┌───────┐  ┌──────────┐  ┌────────┐ │
    │  PCIe   │  │  USB   │  │ BMC   │  │  LSIO    │  │ Logging│ │
    │ Manager │  │Manager │  │Manager│  │ Manager  │  │ System │ │
    └─────────┘  └────────┘  └───────┘  └──────────┘  └────────┘ │
         │
└────────┴─────────────────────────────────────────────────────────┘
         │
    ┌────▼────────────────────────────────────────────────────────┐
    │              Firmware Simulator Core (main)                   │
    │  - Orchestration                                              │
    │  - State Management                                           │
    │  - Event Handling                                             │
    └──────────────────────────────────────────────────────────────┘
```

## Core Design Principles

### 1. Modularity
Each subsystem operates independently with well-defined interfaces:
- **BootManager**: Handles power-on and boot sequences
- **PowerManager**: Manages power states and transitions
- **MemoryManager**: Simulates DDR operations
- **SecurityManager**: Implements security features
- **PCIeManager**: Manages PCIe devices
- **USBManager**: Manages USB devices
- **BMCManager**: Simulates remote management
- **LSIOManager**: Handles low-speed I/O
- **HealthMonitor**: Tracks system health

### 2. Abstraction
Clear separation between:
- **Interface (Public)**: What tests/clients see
- **Implementation**: Internal details hidden
- **State Management**: Encapsulated per subsystem

### 3. Extensibility
Easy to add new:
- Subsystems
- Failure injection points
- Test cases
- Metrics collection

### 4. Realism
Simulation accurately reflects:
- Timing and sequencing
- State dependencies
- Error conditions
- Hardware constraints

## Boot Manager Architecture

### Boot Sequence

```
Power-On Reset (POR)
    │
    ├─► SEC Phase (Security)
    │   └─ TPM initialization
    │   └─ Firmware verification
    │   └─ Security checks
    │
    ├─► PEI Phase (Pre-EFI Initialization)
    │   └─ Memory initialization
    │   └─ CPU cache enable
    │   └─ Graphics initialization
    │
    ├─► DXE Phase (Driver Execution Environment)
    │   └─ Driver loading
    │   └─ Device enumeration (PCIe, USB)
    │   └─ Service installation
    │
    ├─► BDS Phase (Boot Device Selection)
    │   └─ Boot option processing
    │   └─ Boot device selection
    │   └─ Pre-OS handoff preparation
    │
    └─► OS Loader
        └─ Transfer control to OS
        └─ Boot complete
```

### State Management

```
State Machine Transitions:
POWER_OFF → POWER_ON → SEC_PHASE → PEI_PHASE → DXE_PHASE → BDS_PHASE → OS_LOADER
              ↓                                                    ↓
           ERROR_STATE ◄────────────────────────────────────────┘
              ↓
        RECOVERY_MODE
```

### Failure Injection Points

1. **Memory Training Failure**: Injected at BDS phase → boot fails
2. **PCIe Failure**: Injected at DXE phase → device enumeration fails
3. **USB Failure**: Injected at DXE phase → USB subsystem unavailable
4. **Firmware Corruption**: Injected at SEC phase → immediate boot failure
5. **Boot Timeout**: Injected at OS Loader → boot timeout error

## Power Manager Architecture

### Power States

```
S0 (Working)
  ├─ Full power consumption
  ├─ All subsystems active
  └─ Normal operation

S1 (Light Sleep)
  ├─ Reduced power consumption
  ├─ CPU in low-power state
  └─ Devices ready to wake

S3 (Deep Sleep)
  ├─ Minimal power consumption
  ├─ Memory retained
  └─ Wake from LAN possible

S4 (Hibernation)
  ├─ Lowest power consumption
  ├─ Memory to disk
  └─ Long wake-up time

S5 (Soft Off)
  ├─ Power savings mode
  ├─ Can wake from power button
  └─ Some devices powered

S6 (Hard Off)
  ├─ Complete power shutdown
  ├─ No wake capability
  └─ Manual restart required
```

### Transition Valid Paths

```
S0 ←→ S1
S0 ↔ S3
S0 → S4
S0, S1, S3, S4 → S5
Any → S6

Wake Paths:
S1, S3, S4 → S0
S5 → S0 (power button)
```

## Memory Manager Architecture

### DDR Initialization Flow

```
Power-On
  │
  ├─ SPD Reading
  │   └─ Detect DDR type, speed, capacity
  │
  ├─ DDR Initialization
  │   └─ Apply reference clock
  │   └─ Configure memory controller
  │
  └─ DDR Training
      ├─ Read leveling
      ├─ Write leveling
      └─ Timing calibration
```

### ECC (Error Correcting Code) Simulation

```
Memory Write:  Data → ECC Calculation → Memory + ECC

Memory Read:   Memory + ECC → ECC Check → Data (or Error)

Error Types:
  ├─ Single-Bit Error (SBE)
  │   └─ Correctable, reported
  │
  └─ Double-Bit Error (DBE)
      └─ Uncorrectable, critical
```

## Security Manager Architecture

### Secure Boot Flow

```
Power-On
  │
  ├─ Load SEC Phase
  │
  ├─ Load PEI Phase
  │
  ├─ Verify PEI Signature
  │   ├─ Validate certificate chain
  │   ├─ Check firmware signature
  │   └─ Verify no rollback
  │
  ├─ Load DXE Phase
  │
  ├─ Verify DXE Signature
  │   └─ Same as PEI verification
  │
  └─ Boot Proceed or Fail
```

### TPM and PCR (Platform Configuration Register)

```
PCR[0] - SEC Phase
PCR[1] - PEI Phase
PCR[2] - DXE Phase
PCR[3] - Configuration
PCR[7] - Secure Boot Status

Extension: Hash(PCR_old || NewData) → PCR_new
```

## PCIe Manager Architecture

### Device Enumeration

```
Enumeration Start
  │
  ├─ Bus 0 Scan
  │   ├─ Slot 0-31 Check
  │   │   ├─ Check Device ID/Vendor ID
  │   │   ├─ Allocate resources
  │   │   └─ Function 0-7
  │   │
  │   └─ Secondary Bus Setup
  │
  ├─ Link Training (per device)
  │   ├─ Gen1 (2.5 GT/s)
  │   ├─ Gen2 (5.0 GT/s)
  │   ├─ Gen3 (8.0 GT/s)
  │   └─ Gen4 (16.0 GT/s)
  │
  └─ Enumeration Complete
```

### Bandwidth Calculation

```
Bandwidth = (Speed in GT/s × Lane Width × 125 MHz) / 10

Gen1 × 1 lane: 250 MB/s
Gen1 × 16 lanes: 4 GB/s
Gen4 × 16 lanes: 64 GB/s
```

## USB Manager Architecture

### USB Device Classes

```
Mass Storage (Class 08h)
  └─ Bulk-only transfer protocol
  └─ Typical: External drives, USB sticks

Human Interface Device (Class 03h)
  ├─ Keyboard
  ├─ Mouse
  └─ Other input devices

Communications (Class 02h)
  └─ Modems, network adapters
```

## LSIO Manager Architecture

### Sub-Interfaces

```
GPIO (General Purpose I/O)
  ├─ 32-64 pins
  ├─ Input/Output modes
  └─ Interrupt capable

I2C (Inter-Integrated Circuit)
  ├─ 400 kHz standard speed
  ├─ 3.4 MHz fast-mode
  └─ Master-slave protocol

SPI (Serial Peripheral Interface)
  ├─ 4-wire: MOSI, MISO, CLK, CS
  ├─ Configurable speed
  └─ Full-duplex

UART (Asynchronous Serial)
  ├─ Configurable baud rate
  ├─ 8 bit data typical
  └─ Flow control support
```

## Logging System Architecture

### Log Format Options

#### JSON Format
```json
{
  "timestamp": "2026-06-01 12:34:56.789",
  "level": "INFO",
  "component": "BootManager",
  "message": "Running SEC Phase",
  "type": "BOOT_EVENT"
}
```

#### Text Format
```
[2026-06-01 12:34:56.789] [INFO] [BootManager] Running SEC Phase
```

#### CSV Format
```
timestamp,level,component,message,type
2026-06-01 12:34:56.789,INFO,BootManager,Running SEC Phase,BOOT_EVENT
```

### Thread-Safe Logging

- Mutex protection for concurrent access
- Buffering before file write
- Automatic log rotation (optional)
- Multiple output handlers

## Data Flow Example: Boot Sequence

```
main() 
  │
  ├─ FirmwareApplication::initialize()
  │   ├─ Logger::initialize()
  │   ├─ MemoryManager::initialize_ddr()
  │   ├─ SecurityManager::initialize_tpm()
  │   └─ HealthMonitor setup
  │
  └─ FirmwareApplication::start_boot_sequence()
      │
      ├─ BootManager::power_on_reset()
      │
      ├─ BootManager::run_sec_phase()
      │   └─ LOG_INFO() → Logger writes to file/console
      │
      ├─ BootManager::run_pei_phase()
      │   └─ Update BootMetrics
      │
      ├─ BootManager::run_dxe_phase()
      │   ├─ PCIeManager::enumerate_devices()
      │   └─ USBManager::enumerate_devices()
      │
      ├─ BootManager::run_bds_phase()
      │   └─ MemoryManager check
      │
      ├─ BootManager::run_os_loader()
      │   ├─ Final boot metrics calculation
      │   └─ Logger::log_boot_metrics()
      │
      └─ FirmwareApplication::shutdown()
          └─ Logger::flush_to_file()
```

## Concurrency Model

- **Main Thread**: Firmware execution
- **Logger Thread**: Async log writing (optional)
- **Timer Thread**: Periodic health monitoring (optional)

Thread-safe operations:
- Logger uses mutex
- Manager state variables protected
- No shared mutable state between managers

## Error Handling Strategy

```
Level 1: Validation
  └─ Parameter checking
  └─ State validation

Level 2: Recovery
  └─ Retry mechanism
  └─ Fallback paths

Level 3: Escalation
  └─ Boot to recovery mode
  └─ Error logging and reporting

Level 4: Shutdown
  └─ Graceful termination
  └─ State preservation
```

## Performance Characteristics

### Timing Simulation

- SEC Phase: ~50 ms
- PEI Phase: ~75 ms
- DXE Phase: ~100 ms
- BDS Phase: ~60 ms
- OS Load: ~50 ms
- **Total Boot Time**: ~335 ms

### Memory Usage

- Firmware binary: ~5 MB
- Runtime memory: ~50 MB
- Logging buffer: ~10 MB
- Total system: ~100 MB

## Summary

This architecture provides:
1. **Clear separation of concerns** through modularity
2. **Realistic firmware behavior** simulation
3. **Comprehensive failure injection** capability
4. **Professional-grade logging** for analysis
5. **Scalable test framework** for validation
6. **Production-quality code** following best practices

The design allows AMD firmware validation engineers to:
- Validate firmware in post-silicon phase
- Inject faults and verify recovery
- Measure performance and timing
- Analyze logs and identify root causes
- Generate comprehensive test reports
