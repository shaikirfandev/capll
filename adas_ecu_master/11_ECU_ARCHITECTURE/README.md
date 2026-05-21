# 11 — ECU Architecture

> **Standard:** AUTOSAR Classic R4.x, AUTOSAR Adaptive R21-11  
> **Hardware:** AURIX TC3xx, S32G, TDA4VM domain controller

---

## 11.1 AUTOSAR Classic Layered Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                    APPLICATION LAYER                           │
│  SWC: LKA  │  SWC: ACC  │  SWC: LDA  │  SWC: Diagnostics     │
│  (Runnable: LKA_MainFunction, period 10ms)                     │
└────────────────────────┬───────────────────────────────────────┘
                         │  Rte_Read / Rte_Write / Rte_Call
┌────────────────────────▼───────────────────────────────────────┐
│                  RUNTIME ENVIRONMENT (RTE)                     │
│  Auto-generated from ARXML. Bridges SWCs to BSW.              │
│  Inter-SWC communication: sender/receiver + client/server ports│
└────────────────────────┬───────────────────────────────────────┘
                         │
┌────────────────────────▼───────────────────────────────────────┐
│              BASIC SOFTWARE (BSW) LAYER                        │
│                                                                │
│  Services Layer:                                               │
│    OS (OSEK/AUTOSAR OS) | DEM | NvM | ComM | BswM | WdgM      │
│                                                                │
│  ECU Abstraction Layer:                                        │
│    CanIf | LinIf | EthIf | SpiIf | IoHwAb                     │
│                                                                │
│  MCAL (Microcontroller Abstraction Layer):                     │
│    CanDrv | LinDrv | SpiDrv | GptiDrv | AdcDrv | PwmDrv       │
│                                                                │
└────────────────────────┬───────────────────────────────────────┘
                         │
┌────────────────────────▼───────────────────────────────────────┐
│                   HARDWARE                                     │
│  CAN controllers | SPI | GPIO | ADC | Watchdog | Flash        │
└────────────────────────────────────────────────────────────────┘
```

---

## 11.2 SWC Types

| SWC Type          | Description                                        | Example |
|-------------------|----------------------------------------------------|---------|
| Application SWC   | Feature logic, no BSW access                       | LKA, ACC |
| Sensor/Actuator SWC | Direct hardware via IoHwAb                       | Camera SWC, EPS SWC |
| Service SWC       | Provides services to other SWCs                    | NvM service |
| Composition SWC   | Groups multiple SWCs into one deployable unit      | ADAS feature SWC |
| Parameter SWC     | Provides calibration data (AUTOSAR parameters)     | LKA calibration |

---

## 11.3 AUTOSAR OS Task Scheduling (OSEK)

```
Task types:
  Basic task:   runs to completion, no blocking. Used for periodic ADAS functions.
  Extended task: can wait on events, suspend. Used for initialization sequences.

Scheduling: Preemptive, fixed-priority (BCC1 or ECC1/ECC2)

Typical ADAS ECU task configuration:
  Priority | Task Name         | Period  | Function
  ---------|-------------------|---------|---------------------------
  10       | 1ms_ISR_Task      | 1ms     | Watchdog service, CAN ISR post-process
  8        | 5ms_Task          | 5ms     | ADC sampling, PwmDrv
  6        | 10ms_Task         | 10ms    | LKA_MainFunction, LDA_MainFunction  
  5        | 20ms_Task         | 20ms    | ACC_MainFunction, SensorFusion
  4        | 50ms_Task         | 50ms    | Diagnostics, DEM, NvM
  3        | 100ms_Task        | 100ms   | BswM mode management, ComM
  2        | Background_Task   | IDLE    | Stack health check, CRC verification

OS AlarmCallback: triggers task activation at configured period.
  SetRelAlarm(AlarmID, initialOffset_ms, cycleTime_ms)
  
Resource management:
  OS Resource (mutex equivalent): GetResource / ReleaseResource
  Priority Ceiling Protocol prevents priority inversion.
```

---

## 11.4 COM Stack Signal Flow

```
SWC writes:        Rte_Write_LkaTorqueRequest(2.5F)
                         │
RTE:               Routes to COM layer via AUTOSAR signal mapping
                         │
COM:               Packs signal into I-PDU (Interaction Protocol Data Unit)
                   Packs multiple signals into one CAN frame data bytes
                   Applies timeout, repetition, update bit rules
                         │
PduR (PDU Router): Routes PDU to correct transport layer (CanTp / CAN / Ethernet)
                         │
CanIf:             Adds CAN ID, DLC, calls CanDrv
                         │
CanDrv (MCAL):     Writes to CAN controller hardware register
                         │
CAN Hardware:      Arbitration, transmission
```

---

## 11.5 AUTOSAR Adaptive (R21-11) Differences

```
Adaptive = Dynamic service-based architecture for L3+ systems:

  1. ara::com (Communication): SOME/IP service discovery + events/methods/fields
     vs Classic: static ARXML signal mapping

  2. ara::exec (Execution): Functional clusters, dynamic process management
     vs Classic: static OS tasks

  3. ara::diag: UDS diagnostics over DoIP (Ethernet)
     vs Classic: UDS over CAN (CanTp)

  4. ara::log: structured logging to central server
     vs Classic: DEM fault memory only

  5. Middleware: AUTOSAR Adaptive Platform (AP) runs on Linux or QNX
     vs Classic: runs on bare-metal OSEK/AUTOSAR OS

  6. C++14/17 allowed, dynamic memory with ara::core::Vector
     vs Classic: MISRA C++, no dynamic allocation

When used:
  Classic: powertrain ECU, body ECU, simple ADAS (LKA, ACC)
  Adaptive: domain controller (NXP S32G), L3+ highway assist, OTA update server
```

---

## 11.6 Interview Questions

```
L1:
  Q: What is the RTE in AUTOSAR?
  A: Runtime Environment — auto-generated middleware layer between Application SWCs
     and BSW. Provides:
     - Rte_Read / Rte_Write: inter-SWC signal exchange (replaces global variables)
     - Rte_Call: synchronous client/server communication
     - Rte_Switch: mode management
     Generated from ARXML descriptions using tools like Vector DaVinci Developer.
     Key benefit: SWC code is hardware-independent — same SWC code runs on AURIX, 
     S32K, Renesas RH850 just by regenerating RTE and MCAL.

  Q: What is DEM in AUTOSAR?
  A: Diagnostic Event Manager. Manages fault (DTC) storage.
     Application calls: Dem_ReportErrorStatus(DEM_EVENT_STATUS_FAILED)
     DEM stores DTC + snapshot data (freeze frame) in NvM.
     Reads via UDS service 0x19. Key attributes per DTC:
     - EventId, DTC format (SAE J2012)
     - Storage conditions (e.g., only store when speed > 10 km/h)
     - Aged counter: fault clears after N ignition cycles without re-occurrence

L2:
  Q: How do you add a new signal from a new sensor to AUTOSAR Classic?
  A: 1. Add signal to DBC file (or ARXML ComSignal)
     2. Configure COM signal: startBit, bitLength, factor, offset, timeout in ARXML
     3. RTE auto-generates: Rte_Read_<Port>_<Signal>()
     4. SWC reads signal via generated API — no direct CAN access
     5. Configure RTE port connection: sensor SWC output → your SWC input
     6. Regenerate RTE with DaVinci/EB tresos tool
     7. Rebuild and test

L3:
  Q: What is the difference between AUTOSAR Classic and Adaptive from a software 
     architecture perspective?
  A: Classic (static, safety-critical):
     - All SWCs and their connections configured at design time (ARXML)
     - No runtime service discovery
     - Fixed-priority preemptive OS (OSEK), no dynamic tasking
     - C++14 subset (MISRA), no exceptions, no dynamic allocation
     - ASIL-D certified MCAL, BSW stack (e.g., Vector MICROSAR)
     - Use case: brakes, airbag, powertrain, LKA ECU
     
     Adaptive (dynamic, high-compute):
     - Services discovered at runtime via SOME/IP discovery
     - Processes managed by ara::exec Execution Manager
     - Runs on Linux + POSIX threads, or QNX
     - C++17, ara::core::Vector, ara::log, no strict allocation rules
     - ASIL-B max for AP itself (ASIL decomposition for D)
     - Use case: domain controller, ML inference, OTA management, L3 highway system
     
     Hybrid systems (e.g., NVIDIA Drive AGX):
     - Safety island: AURIX TC3xx running AUTOSAR Classic (ASIL-D monitors)
     - Application processor: NXP S32G or ARM Cortex-A running Adaptive (high compute)
     - They communicate via internal Ethernet (100BASE-T1)
```
