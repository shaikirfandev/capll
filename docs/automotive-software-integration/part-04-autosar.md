# Part 4 — AUTOSAR Integration

AUTOSAR (AUTomotive Open System ARchitecture) is the dominant software architecture standard for automotive ECUs. There are two variants: **Classic AUTOSAR** for microcontroller-based ECUs and **Adaptive AUTOSAR** for microprocessor/SoC-based ECUs.

---

## 4.1 Classic AUTOSAR Architecture

### Layer Overview

```
+=====================================================+
|           Application Layer (SWCs)                 |
|  SpeedControl_SWC  |  EngineControl_SWC  | ...     |
+=====================================================+
|           RTE (Run-Time Environment)               |
|  Generated code connecting SWCs to BSW             |
+=====================================================+
|           BSW (Basic Software)                     |
|  Services Layer:  Dcm | Dem | NvM | FiM | Com      |
|  ECU Abstraction:  CanIf | EthIf | SpiIf | AdcIf  |
|  Microcontroller Abstraction (MCAL):               |
|    CanDrv | SpiDrv | AdcDrv | WdgDrv | GptDrv     |
+=====================================================+
|           AUTOSAR OS                               |
+=====================================================+
|           Hardware (MCU, Peripherals)               |
+=====================================================+
```

### Key BSW Modules

| Module | Full Name | Purpose |
|---|---|---|
| COM | Communication | Signal-based I/O, PDU routing |
| PduR | PDU Router | Routes PDUs between modules |
| CanIf | CAN Interface | Abstracts CAN driver |
| CanTp | CAN Transport Protocol | ISO 15765-2, segmentation for UDS |
| Dcm | Diagnostic Communication Manager | UDS service handling |
| Dem | Diagnostic Event Manager | DTC storage and management |
| NvM | NV Memory Manager | Persistent data storage |
| FiM | Function Inhibition Manager | Inhibit functions when DTCs active |
| EcuM | ECU Manager | ECU startup and shutdown |
| BswM | BSW Mode Manager | Mode-based BSW configuration |
| Wdg | Watchdog Driver | Hardware watchdog management |
| WdgM | Watchdog Manager | Supervises tasks via watchdog |
| ComM | Communication Manager | Network state management |
| CanSM | CAN State Machine | CAN bus state (offline/online/bus-off) |
| EthIf | Ethernet Interface | Abstracts Ethernet driver |
| EthSM | Ethernet State Machine | Ethernet network state management |
| Os | AUTOSAR OS | OSEK-based task scheduler |

---

### SWC → RTE → BSW → MCAL → Hardware Flow

```
Application SWC calls:
  Rte_Write_SpeedControlSWC_VehicleSpeedPort(speed_value)

RTE routes this to:
  COM module (signal packing into PDU)

COM → PduR:
  PduR routes PDU to appropriate transport

PduR → CanIf:
  CanIf selects correct CAN driver/controller

CanIf → CAN Driver (MCAL):
  CAN driver writes to MCU CAN controller registers

MCU CAN controller → CAN transceiver → CAN bus
```

### ARXML (AUTOSAR XML)

ARXML is the configuration file format for AUTOSAR. It describes:
- SWC definitions (ports, interfaces, runnables)
- BSW module configuration
- ECU composition (how SWCs are mapped to ECUs)
- Communication matrix (signals, PDUs, messages)

```xml
<!-- Example: SWC port definition in ARXML -->
<SW-COMPONENT-PROTOTYPE>
  <SHORT-NAME>SpeedControlSWC</SHORT-NAME>
  <PORTS>
    <P-PORT-PROTOTYPE>
      <SHORT-NAME>VehicleSpeedPort</SHORT-NAME>
      <PROVIDED-INTERFACE-TREF>
        /Interfaces/VehicleSpeedInterface
      </PROVIDED-INTERFACE-TREF>
    </P-PORT-PROTOTYPE>
  </PORTS>
</SW-COMPONENT-PROTOTYPE>
```

### ECUC (ECU Configuration)

ECUC is the parameter container format for BSW module configuration. Example: configuring CanIf to use a specific CAN controller.

### BSW Configuration Workflow

```
1. Import DBC/ARXML into configurator tool
2. Configure CanIf: add HW object definitions for each CAN ID
3. Configure COM: define signals and PDUs
4. Configure PduR: define routing paths
5. Configure Dcm: add supported UDS services and DIDs
6. Configure Dem: add DTC entries with conditions
7. Configure NvM: define non-volatile data blocks
8. Configure OS: define tasks, alarms, resources
9. Generate code: tool generates C source files for each BSW module
10. Integrate generated code with application SWCs
11. Build and verify
```

### RTE Generation

The RTE is generated from ARXML. The generated RTE code includes:
- `Rte_Write_*` / `Rte_Read_*` for data communication
- `Rte_Call_*` for client/server operations
- `Rte_Switch_*` / `Rte_Mode_*` for mode management
- Task activation for runnable entities

### Classic AUTOSAR Integration Errors

| Error | Cause | Fix |
|---|---|---|
| SWC port not connected | Missing RTE port connection in ARXML | Check port composition in ARXML |
| Wrong signal value on CAN | Byte order (endianness) mismatch | Verify Intel/Motorola byte order in DBC vs COM config |
| DTC not set | Dem event not reported | Check `Dem_ReportErrorStatus()` call in application |
| ECU bus-off after startup | Wrong CAN bit timing | Reconfigure CanIf/CanDrv timing parameters |
| Task overrun | Runnable exceeds slot time | Profiling, optimize runnable, adjust task period |
| NvM write not persisting | Block descriptor misconfigured | Verify NvM block definition and storage type |

---

## 4.2 Adaptive AUTOSAR Architecture

### Why Adaptive AUTOSAR?
Classic AUTOSAR was designed for resource-constrained MCUs with static configuration. Modern vehicles require:
- Dynamic service discovery
- High-performance SoCs (64-bit, multi-core)
- OTA software updates
- Complex ML/AI applications (object detection)
- POSIX-based development (Linux, QNX)

### Adaptive AUTOSAR Architecture

```
+=====================================================+
|         Adaptive Applications (AA)                 |
|  Camera_AA | ObjectDetection_AA | Planning_AA      |
+=====================================================+
|         ara:: API (C++ Functional Clusters)        |
+=====================================================+
|         ARA Functional Clusters                    |
|  ara::com  | ara::diag | ara::exec | ara::per      |
|  ara::log  | ara::tsync| ara::nm   | ara::crypto   |
+=====================================================+
|         POSIX OS (Linux / QNX)                     |
+=====================================================+
|         Hardware (SoC, GPU, accelerators)          |
+=====================================================+
```

### Key Adaptive AUTOSAR Functional Clusters

| Cluster | Purpose |
|---|---|
| ara::com | Service-oriented communication (SOME/IP, IPC) |
| ara::exec | Execution Management — start/stop processes |
| ara::diag | Diagnostics (UDS) |
| ara::per | Persistency — key-value storage, file storage |
| ara::log | Logging framework |
| ara::tsync | Time synchronization |
| ara::nm | Network Management |
| ara::crypto | Cryptographic operations |
| ara::iam | Identity & Access Management |

### ara::com — Service Communication

```cpp
// Service Provider (Server Application)
#include "ara/com/sample_speed_service_skeleton.h"

class SpeedServiceImpl : public SpeedServiceSkeleton {
public:
    ara::core::Future<Fields::Speed::FieldType> GetSpeed() override {
        return ara::core::MakeReadyFuture<Fields::Speed::FieldType>(current_speed_);
    }
    void SetSpeed(Fields::Speed::FieldType speed) {
        current_speed_ = speed;
        SpeedField.Update(current_speed_);  // notify subscribers
    }
private:
    Fields::Speed::FieldType current_speed_ = 0;
};

// Service Consumer (Client Application)
#include "ara/com/sample_speed_service_proxy.h"

SpeedServiceProxy proxy(handle);
proxy.SpeedField.Subscribe(1);  // subscribe to field updates
auto value = proxy.SpeedField.GetCachedSamples();
```

### Execution Management (ara::exec)

Each Adaptive Application is a separate POSIX process. The Execution Manager (EM) starts, stops, and monitors processes based on **Machine State** and **Function Group State**.

```
Machine State transitions:
  Off → Init → Running → Shutdown

Function Group (e.g., "ADAS"):
  Off → StartingUp → Running → ShuttingDown
```

Process lifecycle:
```
1. EM reads manifest (JSON/ARXML) listing all AAs
2. EM starts process when its function group enters "Running"
3. AA calls ReportApplicationState(kRunning) to signal readiness
4. EM monitors process; restarts on crash (configurable restart policy)
```

### Service Discovery (SOME/IP-SD)

In Adaptive AUTOSAR, service discovery is done via ara::com which uses SOME/IP-SD under the hood.

```
Server AA starts → OfferService via ara::com
Client AA calls FindService → ara::com sends SOME/IP-SD FindService
Server responds → Client gets service handle → communicate
```

### Persistency (ara::per)

Two storage types:
- **Key-Value Storage** — small configuration/calibration data
- **File-based Storage** — larger files (logs, map data)

```cpp
// Key-Value Storage example
auto kvsResult = ara::per::OpenKeyValueStorage("VehicleConfig");
auto& kvs = kvsResult.Value();
kvs.SetValue<uint32_t>("OdometerValue", 12345);
kvs.SyncToStorage();
```

### Diagnostics in Adaptive AUTOSAR (ara::diag)

Adaptive AUTOSAR supports UDS diagnostics via ara::diag:
- Request handling (ReadDataByIdentifier, RoutineControl)
- DTC management
- Session management

### Adaptive vs Classic AUTOSAR — Practical Comparison

| Scenario | Classic AUTOSAR | Adaptive AUTOSAR |
|---|---|---|
| Engine RPM control | Classic (RH850 MCU) | — |
| Camera perception | — | Adaptive (Qualcomm SoC) |
| Cluster telltales | Classic or Adaptive | Both used in different layers |
| OTA update | Bootloader-based | ara::exec + UCM |
| Service discovery | Static (COM config) | Dynamic (SOME/IP-SD) |
| CAN signal | COM/PduR/CanIf | ara::com (CAN binding) |
| Code language | C (mostly) | C++14/17 |

---

## 4.3 AUTOSAR Integration Workflow (Practical)

### Step-by-Step Integration

```
1. SYSTEM DESIGN
   - Define SWCs in DaVinci Developer
   - Create port interfaces, data element types
   - Map SWCs to ECU in composition

2. BSW CONFIGURATION
   - Import DBC into DaVinci Configurator
   - Configure CanIf (HW objects, buffer sizes)
   - Configure COM (signals, PDUs, timeouts)
   - Configure PduR (routing paths)
   - Configure Dcm (services, DIDs, security)
   - Configure Dem (DTCs, events, conditions)
   - Configure NvM (blocks, EEPROM/flash mapping)
   - Configure OS (tasks, ISRs, priorities)

3. CODE GENERATION
   - Generate RTE code from ARXML
   - Generate BSW module code from ECUC
   - Review generated code for correctness

4. BUILD
   - Compile application SWCs + generated RTE + generated BSW
   - Link with vendor BSW libraries (CanDrv, etc.)
   - Output: HEX/SREC binary

5. FLASH & VERIFY
   - Flash to ECU hardware
   - Monitor DTC startup, CAN signals in CANoe
   - Run integration test cases

6. CONFIGURATION DEBUGGING
   Common issues:
   - "DTC 0x100501 set at startup" → check Dem condition/event
   - "CAN signal not received" → check CanIf HW object / COM PDU config
   - "Task watchdog reset" → task taking too long → profile and optimize
```

---

## Summary

| Aspect | Classic AUTOSAR | Adaptive AUTOSAR |
|---|---|---|
| HW target | MCU (RH850, S32K) | SoC (S32G, Orin) |
| OS | AUTOSAR OS | POSIX |
| Configuration | Static ARXML/ECUC | Manifest (JSON/ARXML) |
| Communication | COM/PduR/CanIf static | ara::com dynamic |
| Deployment | Flash/UDS | OTA/ara::exec |
| Key tools | DaVinci, EB tresos | ETAS, Vector MICROSAR |

---

*Next: [Part 5 — ADAS Integration](part-05-adas.md)*
