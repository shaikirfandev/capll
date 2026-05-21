# ECU Architecture Interview Questions
## Automotive Embedded Engineer — Principal Level

---

## TOPIC OVERVIEW

ECU architecture questions test your understanding of **how a complete Electronic Control Unit is designed, from silicon to software**, and how multiple ECUs cooperate in a vehicle network. This is a core topic at Bosch, Continental, Harman, KPIT, and Tata Elxsi senior rounds.

**Key areas probed:**
- ECU hardware architecture (MCU, RAM, FLASH, peripherals)
- Software layers (BSW, RTE, SWC — AUTOSAR Classic and Adaptive)
- Boot sequence and memory map
- Power modes and wake/sleep management
- CAN/LIN/Ethernet gateway ECU architecture
- ADAS domain controller architecture (heterogeneous compute)
- Functional safety hardware partitioning (ASIL decomposition)

---

## BEGINNER QUESTIONS

---

### Q1. Describe the hardware architecture of a typical automotive ECU. What components does it contain and why?

**Short Answer:** An automotive ECU contains a microcontroller (MCU), flash memory, RAM, power supply, communication peripherals, and I/O conditioning circuits — all designed for automotive temperature/voltage ranges (AEC-Q100).

**Detailed Expert Answer:**

```
┌─────────────────────────────────────────────────────────┐
│                   ECU Hardware Block Diagram             │
│                                                          │
│  ┌──────────────┐    ┌────────────────────────────────┐  │
│  │  Power       │    │          MCU                   │  │
│  │  Supply      │───▶│  CPU Core(s)  │  Flash 2-8 MB  │  │
│  │  (LDO/DCDC)  │    │  SRAM 256-512K│  EEPROM/DFLASH │  │
│  └──────────────┘    │  CAN/LIN/ETH  │  Timers/ADC    │  │
│                      │  SPI/I2C/UART │  Watchdog      │  │
│  ┌──────────────┐    └────────────────────────────────┘  │
│  │  External    │           │                             │
│  │  Flash/EEPROM│◀──────────┤                             │
│  │  (SPI/QSPI)  │           │                             │
│  └──────────────┘    ┌──────▼───────┐                     │
│                      │  CAN         │ ◀── CAN Bus          │
│  ┌──────────────┐    │  Transceiver │                     │
│  │  Wake-up     │    │  (TJA1044)   │                     │
│  │  Circuit     │    └──────────────┘                     │
│  │  (LIN/CAN)   │    ┌──────────────┐                     │
│  └──────────────┘    │  LIN         │ ◀── LIN Bus          │
│                      │  Transceiver │                     │
│  ┌──────────────┐    └──────────────┘                     │
│  │  Watchdog    │    ┌──────────────┐                     │
│  │  SBC         │    │  I/O         │ ◀── Sensors/Actuators│
│  │  (TLE9262)   │    │  Conditioning │                     │
│  └──────────────┘    └──────────────┘                     │
└─────────────────────────────────────────────────────────┘
```

**Component breakdown:**

| Component | Example parts | Purpose |
|-----------|--------------|---------|
| MCU | Infineon TC397, NXP S32K344, STM32H7A3 | Central processing unit, on-chip RAM/flash |
| CAN Transceiver | NXP TJA1044, Infineon TLE9251 | 5V CAN logic ↔ 12V differential bus |
| LIN Transceiver | NXP TJA1020, Infineon TLE7259 | Master/slave LIN bus interface |
| SBC (System Basis Chip) | Infineon TLE9262, NXP UJA1169 | Combines: LDO, CAN/LIN PHY, watchdog, wake-up |
| External Flash | Winbond W25Q256, Cypress S25FL512S | Firmware storage beyond MCU on-chip flash |
| EEPROM | AT24C256 (I2C) | Small non-volatile storage (counters, calibration) |
| Power Supply | TPS65381 (TI), OPTIREG (Infineon) | 12V → 5V/3.3V/1.8V for MCU core/IO |

**Why these specific requirements:**
- **AEC-Q100 Grade 0/1**: Operating temperature -40°C to 125°C (engine bay ECUs go to 150°C)
- **EMC hardening**: Transient voltage suppression (TVS), ferrite beads, common mode chokes
- **Redundant supply monitoring**: SBC monitors VDD and resets MCU if voltage drops out of range
- **Watchdog**: Hardware watchdog in SBC (external to MCU) — can't be disabled by runaway software

---

### Q2. Explain the software layer architecture of an AUTOSAR Classic ECU.

**Short Answer:** AUTOSAR Classic has 4 layers: Application (SWC) → Runtime Environment (RTE) → Basic Software (BSW) → MCAL (microcontroller abstraction). The RTE is the generated glue layer that routes data between SWCs and BSW.

**Detailed Expert Answer:**

```
┌─────────────────────────────────────────────────────────┐
│              AUTOSAR Classic Software Stack              │
│                                                          │
│  ┌─────────────────────────────────────────────────┐    │
│  │         Application Layer (SWC)                 │    │
│  │  [Throttle Ctrl] [ABS Logic] [TCU State Machine] │    │
│  └─────────────────┬───────────────────────────────┘    │
│                    │ Ports (Sender/Receiver, C/S)        │
│  ┌─────────────────▼───────────────────────────────┐    │
│  │              RTE (Runtime Environment)           │    │
│  │   Auto-generated by AUTOSAR tools               │    │
│  │   Routes data between SWCs via virtual bus      │    │
│  └──┬────────────────────────────────────┬─────────┘    │
│     │ Standardised APIs                  │               │
│  ┌──▼───────────┐              ┌─────────▼──────────┐   │
│  │ Services Layer│              │  ECU Abstraction   │   │
│  │  Os, NvM,    │              │  Layer (ECUAL)      │   │
│  │  Dcm, Dem,   │              │  IoHwAb, CanIf      │   │
│  │  ComM, CanSM │              └──────────┬──────────┘   │
│  └──┬───────────┘                         │               │
│     └────────────────────┬────────────────┘               │
│                    ┌─────▼──────────────────┐             │
│                    │  MCAL                   │             │
│                    │  (Microcontroller       │             │
│                    │   Abstraction Layer)     │             │
│                    │  Can, Spi, Adc, Pwm,    │             │
│                    │  Gpt, Port, Mcu, Wdg    │             │
│                    └─────┬──────────────────┘             │
│                          │ Register-level                  │
│                    ┌─────▼──────────────────┐             │
│                    │   Hardware              │             │
│                    │   Infineon TC397        │             │
│                    └────────────────────────┘             │
└─────────────────────────────────────────────────────────┘
```

**Key layers explained:**

**MCAL (Microcontroller Abstraction Layer):**
- Vendor-delivered (Infineon EB-Tresos, NXP MCAL, Renesas Smart Configurator)
- Provides: `Can_Init()`, `Spi_WriteIB()`, `Adc_StartGroupConversion()`
- MCU-specific register access hidden here
- Must NOT be called directly from SWCs — always via abstraction above

**ECU Abstraction Layer:**
- `IoHwAb` (I/O Hardware Abstraction): Abstracts sensor/actuator signal conditioning
- `CanIf` (CAN Interface): Routes PDUs between `CanDrv` (MCAL) and `PduR`

**Services Layer:**
- `Os` (AUTOSAR OS): BSW scheduler, tasks, alarms, ISR management
- `NvM` (NV Manager): Reads/writes to NVRAM (EEPROM or data flash)
- `Dcm` (Diagnostic Communication Manager): UDS request handling
- `Dem` (Diagnostic Event Manager): DTC storage, freeze frame
- `ComM` (Communication Manager): Bus sleep/wake management

**RTE (Runtime Environment):**
- Auto-generated by AUTOSAR toolchain (Vector DaVinci, ETAS ISOLAR, Elektrobit Tresos)
- Implements `Rte_Write_<port>()`, `Rte_Read_<port>()`, `Rte_Call_<service>()` APIs
- Maps SWC ports to BSW COM signals and inter-SWC connections
- Critical insight: RTE is generated code — never hand-edited

**Application SWC:**
- Written by application engineers
- Only uses Rte_* APIs — hardware independent
- Portable across different ECU variants (only RTE changes per variant)

---

### Q3. What is the ECU boot sequence? Walk through from power-on to application start.

**Short Answer:** Power-on → voltage stabilisation → startup code → BSW init → AUTOSAR OS start → application tasks.

**Detailed Expert Answer:**
```
POWER-ON RESET SEQUENCE (Infineon TC397 example):

T=0ms:    12V applied to battery line
T=0.5ms:  SBC powers up, generates VDD_CPU (3.3V), releases MCU reset
T=1ms:    MCU comes out of reset
          → CPU executes startup code from address 0x80000000 (PFLASH)
          → Startup code: init TCM, copy .data, zero .bss, init FPU/MPU

T=2ms:    EcuM_Init() called (ECU State Manager)
          → Hardware pin read (wake-up reason: ignition, CAN wake, timer)
          → NvM read for ECU configuration
          → MCU clock switch (internal oscillator → external 20 MHz crystal → PLL 300 MHz)

T=5ms:    BSW initialization (AUTOSAR sequence):
          → Mcu_Init()      — PLL, clocks, power modes
          → Port_Init()     — GPIO configuration (input/output/alt function)
          → Can_Init()      — CAN controller register configuration
          → Spi_Init()      — SPI for external flash/sensors
          → Wdg_Init()      — Hardware watchdog (window watchdog, trigger window)
          → Com_Init()      — Signal routing table
          → NvM_ReadAll()   — Asynchronous NVRAM read (all NvM blocks)

T=15ms:   Os_StartOS() called
          → AUTOSAR OS starts
          → Tasks created and released to scheduler
          → First 1ms task tick

T=20ms:   NvM_ReadAll() complete callback
          → Application data available
          → CommunicationManager allows CAN bus activity

T=25ms:   Full operation
          → First application task cycle
          → CAN frames transmitted
          → ECU visible on network
```

**Security critical step — secure boot:**
```
Modern ECUs (ISO 21434 compliant) add:
T=0.8ms:  Hardware Security Module (HSM) validates bootloader signature
          → Uses stored OEM public key
          → Signature check with CMAC/RSA-PKCS1v15
          → If fails: ECU enters secure lockdown, no application start
```

**Watchdog management during boot:**
```c
/* Bootloader must service the watchdog during long NvM reads */
void nvm_read_with_watchdog(void) {
    for (uint32_t block = 0; block < NVM_BLOCK_COUNT; block++) {
        NvM_ReadBlock(block);
        Wdg_Trigger();  /* Service watchdog every ~5ms */
        Os_WaitEvent(NVM_READ_DONE_EVENT);
    }
}
```

---

## INTERMEDIATE QUESTIONS

---

### Q4. What is an ADAS Domain Controller? How does it differ architecturally from a classic ECU?

**Short Answer:** An ADAS domain controller (like Mobileye EyeQ5, NXP S32G, Nvidia Orin) is a **heterogeneous compute platform** combining CPU clusters, GPU/NPU for AI inference, DSPs for signal processing, and safety MCUs — all running different OS environments simultaneously.

**Detailed Expert Answer:**

```
┌──────────────────────────────────────────────────────────────┐
│              ADAS Domain Controller (Nvidia Orin example)     │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Safety Island (Cortex-R52 lockstep)                │   │
│  │  Running: AUTOSAR Classic + SafetyOS                │   │
│  │  Handles: Fault detection, safe state, watchdog     │   │
│  └────────────────────┬────────────────────────────────┘   │
│                        │ HSM/SHE                            │
│  ┌────────────┐  ┌─────▼──────────────────────────────┐   │
│  │  GPU/NPU   │  │  Application Processor              │   │
│  │  (AI/ML)   │  │  Cortex-A78 Cluster (8 cores)       │   │
│  │  TOPS = 254│  │  Running: Linux / QNX               │   │
│  └────────────┘  │  Adaptive AUTOSAR, ROS2             │   │
│                  └─────────────────────────────────────┘   │
│  ┌────────────┐  ┌─────────────────────────────────────┐   │
│  │  DSP Array │  │  Communication Hub                  │   │
│  │  (Sensor   │  │  100BaseT1 Automotive Ethernet       │   │
│  │  fusion)   │  │  Multi-channel CAN-FD (6 ports)      │   │
│  └────────────┘  │  PCIe (NVMe, external GPU)          │   │
│                  └─────────────────────────────────────┘   │
│                                                              │
│  External: Radar, LiDAR, Camera CSI-2, USS, GPS, IMU        │
└──────────────────────────────────────────────────────────────┘
```

**Key architectural differences:**

| Feature | Classic ECU (TCU/BCM/EPS) | ADAS Domain Controller |
|---------|--------------------------|----------------------|
| CPU | Single core, 200-400 MHz | 8+ cores, 2+ GHz |
| RAM | 256 KB - 2 MB | 8-32 GB LPDDR5 |
| OS | AUTOSAR Classic OSEK | Linux + AUTOSAR Adaptive + RTOS |
| Power | 1-5W | 10-100W (Orin = 65W) |
| Connectivity | 2-4 CAN ports | Ethernet + CAN + PCIe |
| AI/ML | None | 200+ TOPS NPU |
| Functional Safety | ASIL-D (lockstep MCU) | ASIL-D safety island + ASIL-B main CPU |
| OTA | Simple flash write | Container-based OTA (Docker-like) |

**Adaptive AUTOSAR on ADAS:**
```
Adaptive AUTOSAR (AP) differs from Classic:
- Based on POSIX operating system (Linux/QNX)
- Dynamic configuration (no code generation for every variant)
- Service-oriented communication (SOME/IP over Ethernet)
- Allows dynamic memory allocation (unlike Classic AUTOSAR)
- C++14 required, C++17 common
- ara::com (Communication API), ara::diag (Diagnostics), ara::log (Logging)
```

---

### Q5. How does ECU memory map work? Explain flash sectors, RAM regions, and NVM usage.

**Detailed Expert Answer:**
```
Infineon TC397 Memory Map (simplified):

┌──────────────────────────────────────────────┐
│  0xA0800000  │  Program Flash (PFLASH 8MB)    │
│              │  .text, .rodata (read-only)    │
│              │  Bootloader: 0xA0800000-0xA0BFFFFF │
│              │  Application: 0xA0C00000-0xA0FFFFFF │
│  0xA0FFFFFF  │                                │
├──────────────────────────────────────────────┤
│  0xAF000000  │  Data Flash (DFLASH 512KB)     │
│              │  AUTOSAR NvM blocks            │
│              │  Calibration data              │
│              │  DTC freeze frames             │
├──────────────────────────────────────────────┤
│  0xC0000000  │  DSRAM (1MB data SRAM)         │
│              │  .data, .bss, heap, stack      │
│              │  OS task stacks                │
├──────────────────────────────────────────────┤
│  0xD0000000  │  PSRAM (1MB program SRAM)      │
│              │  Code that needs fast execution│
│              │  (copied from flash at boot)   │
├──────────────────────────────────────────────┤
│  0xF0000000  │  Peripheral Registers (SFR)    │
│              │  CAN, SPI, ADC, Timer, GPIO    │
├──────────────────────────────────────────────┤
│  0xFE000000  │  Safety RAM (SRAM with ECC)    │
│              │  Safety-critical globals       │
└──────────────────────────────────────────────┘
```

**NvM block organisation (AUTOSAR Classic):**
```c
/* AUTOSAR NvM block — each has header + CRC */
typedef struct {
    uint16_t block_id;      /* NVM block ID (configured in NvM_Cfg.h) */
    uint8_t  crc[4];        /* CRC32 of block data */
    uint8_t  status;        /* Valid/Invalid/Default */
} NvM_BlockHeader_t;

/* Example NvM blocks used in a TCU */
#define NVM_BLOCK_ODOMETER      0x0001U   /* Total distance */
#define NVM_BLOCK_VIN           0x0002U   /* Vehicle Identification Number */
#define NVM_BLOCK_CALIBRATION   0x0003U   /* TCU-specific calibration */
#define NVM_BLOCK_DTC_MEM       0x0100U   /* DTC storage (Primary Memory) */
#define NVM_BLOCK_DTC_FREEZE    0x0200U   /* Freeze frame data */
```

**Flash erase sectors matter for OTA:**
```
Infineon TC397 PFLASH erase unit = 16 KB sector
OTA constraint: cannot erase part of a sector — must erase whole 16 KB
OTA firmware download strategy:
  1. Download new firmware to inactive bank (Bank B)
  2. Verify CRC of Bank B
  3. Update boot vector to Bank B
  4. Watchdog reset
  5. Bootloader boots from Bank B
  6. Mark Bank A as update target for next OTA
```

---

## ADVANCED QUESTIONS

---

### Q6. Explain ASIL decomposition for a dual-core lockstep ECU. How is the software partitioned for ISO 26262?

**Short Answer:** ASIL-D safety requirements can be met either by a single ASIL-D lockstep MCU or by decomposing into two independent ASIL-B channels (ASIL-D = ASIL-B + ASIL-B decomposition).

**Detailed Expert Answer:**

**Single-core lockstep (Infineon TC397 lockstep core pair):**
```
TC397 Core 0 + Core 1 run IDENTICAL instructions in lockstep
Compare unit checks outputs every cycle
If mismatch → safe state immediately

Software sees: ONE CPU (transparency)
Safety achieves: ASIL-D (hardware redundancy handles HW faults)
```

**ASIL decomposition for software:**
```
ASIL-D requirement → decompose into:
  Channel A: ASIL-B software (main application)
  Channel B: ASIL-B software (safety monitor)

Both channels must be:
- Independent (no shared state)
- Developed by different teams (independence requirement)
- Using different algorithms where possible (avoiding common cause failure)
```

```c
/* Channel A — Main application (ASIL-B) */
void MainApp_CalcBrakeForce(void) {
    float brake_force = pedal_pos * BRAKE_GAIN;
    // Send to actuator AND to Channel B monitor
    Brake_SetForce(brake_force);
    SafetyMonitor_Report(BRAKE_FORCE, brake_force);  // Cross-monitoring
}

/* Channel B — Safety monitor (ASIL-B) */
void SafetyMonitor_CheckBrakeForce(void) {
    float reported = SafetyMonitor_GetLastReport(BRAKE_FORCE);
    float expected_max = pedal_pos_raw * BRAKE_GAIN_MAX;
    
    if (reported > expected_max * 1.1f) {  // >10% over expected
        FaultManager_Raise(FAULT_BRAKE_OVERRUN, ASIL_CRITICAL);
    }
}
```

**Memory protection for software partitioning:**
```c
/* MPU configuration separating ASIL-B and QM regions */
MPU_Region_t regions[] = {
    { .base = ASIL_CODE_START, .size = ASIL_CODE_SIZE,
      .attr = MPU_RO_PRIVILEGED_ONLY },   /* ASIL code — read-only */
    
    { .base = ASIL_DATA_START, .size = ASIL_DATA_SIZE,
      .attr = MPU_RW_PRIVILEGED_ONLY },   /* ASIL data — privileged only */
    
    { .base = QM_DATA_START,   .size = QM_DATA_SIZE,
      .attr = MPU_RW_UNPRIVILEGED },      /* QM data — accessible to all */
};
/* QM tasks cannot corrupt ASIL data — MPU fault if attempted */
```

---

## PRODUCTION SCENARIO QUESTIONS

---

### Q7. Describe a real-world ECU intermittent reset issue and how you would diagnose it.

**Expert Answer (principal-level walkthrough):**

"I've debugged this specific pattern at a telematics ECU project. The ECU was resetting intermittently — about once per 8 hours of operation.

**Step 1 — Determine reset source:**
Every automotive MCU has a reset status register. On boot, before clearing it:
```c
void analyze_reset_cause(void) {
    uint32_t rstat = MCU_RST_STATUS_REG;
    
    if (rstat & RST_WATCHDOG_MASK) {
        log_error("WATCHDOG reset — task starved");
    } else if (rstat & RST_VOLTAGE_MONITOR_MASK) {
        log_error("Voltage monitor reset — power supply issue");
    } else if (rstat & RST_TRAP_MASK) {
        log_error("CPU trap — illegal instruction or MPU fault");
    } else if (rstat & RST_SW_MASK) {
        log_error("Software reset — intended or panic");
    }
    
    MCU_RST_STATUS_REG = 0; /* Clear for next boot */
    /* Store to NvM for field diagnosis */
    NvM_WriteBlock(NVM_BLOCK_RESET_LOG, &rstat);
}
```

**Step 2 — In this case: watchdog reset**
Watchdog reset means a task wasn't serviced in time. On the TC397 with TLE9262 SBC watchdog:
- Window watchdog: must be serviced between t_open and t_close
- If serviced too early OR too late → reset

**Step 3 — Find the blocking task**
Using AUTOSAR OS trace (ETAS RTAOS trace or Lauterbach TRACE32 OS-aware):
- Identified: `Task_Telemetry` holding mutex for 120ms (window = 50ms)
- Root cause: MQTT TCP socket had 100ms blocking send timeout

**Step 4 — Fix:**
```c
/* Before — blocking send in OS task */
int send_result = mqtt_client_publish(topic, payload, timeout_ms=100);

/* After — non-blocking with timeout check at OS level */
int send_result = mqtt_client_publish(topic, payload, timeout_ms=10);
if (send_result == MQTT_TIMEOUT) {
    DEM_ReportErrorStatus(DEM_EVENT_MQTT_TIMEOUT, DEM_EVENT_STATUS_FAILED);
    /* Don't block — report DTC and continue */
}
```

**Production Insight:** Always log the reset cause to NvM on every boot. Field ECUs often can't be connected to JTAG, so having a reset history in NvM (readable via UDS 0x22 ReadDataByIdentifier) is the only way to diagnose intermittent resets after a customer complaint."

---

## CHEAT SHEET — ECU Architecture

```
ECU Hardware:
  MCU = CPU + on-chip RAM/Flash + peripherals (CAN/SPI/ADC)
  SBC = LDO + CAN/LIN PHY + watchdog (external to MCU)
  AEC-Q100 = automotive qualification standard (-40 to 150°C)

AUTOSAR Classic Stack (bottom to top):
  MCAL → ECU Abstraction → Services → RTE → Application SWC
  RTE = auto-generated routing layer (never hand-edit)

Boot sequence:
  Reset → startup code → EcuM_Init → BSW init → Os_StartOS → NvM_ReadAll → App run

Memory map:
  PFLASH = code (.text, .rodata)
  DFLASH = NvM (calibration, DTC)
  SRAM   = runtime data (.data, .bss, stack)
  SFR    = peripheral registers (volatile, memory-mapped)

ADAS Domain Controller vs Classic ECU:
  Classic: single-core MCU, AUTOSAR Classic, CAN-based
  ADAS: heterogeneous (CPU + GPU + DSP + safety MCU), Linux + AUTOSAR Adaptive, Ethernet

ASIL decomposition:
  ASIL-D = ASIL-B channel A + ASIL-B channel B (independent)
  Lockstep = two cores running identical instructions, compare outputs

Reset cause register: always save to NvM before clearing!
  Sources: watchdog / voltage / SW trap / power-on
```
