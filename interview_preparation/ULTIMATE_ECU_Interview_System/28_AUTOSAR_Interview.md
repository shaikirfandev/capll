# AUTOSAR Interview Questions
## Senior Automotive Embedded Engineer — Principal Level

---

## TOPIC OVERVIEW

AUTOSAR (AUTomotive Open System ARchitecture) is the **industry standard architecture** for automotive ECU software. Knowledge of AUTOSAR Classic (for microcontrollers) and AUTOSAR Adaptive (for high-compute platforms) is required at Bosch, Continental, KPIT, Tata Elxsi, LG Electronics Automotive, and all tier-1 suppliers.

**Key areas probed:**
- AUTOSAR Classic layered architecture
- SWC (Software Component) types and ports
- COM stack (CanIf/PduR/Com/ComM)
- NvM (Non-Volatile Memory Manager)
- DCM (Diagnostic Communication Manager)
- OS (AUTOSAR OS / OSEK)
- Adaptive AUTOSAR vs Classic differences
- AUTOSAR toolchains (Vector DaVinci, ETAS ISOLAR)
- ARXML files and configuration methodology

---

## BEGINNER QUESTIONS

---

### Q1. What is AUTOSAR and why was it created? Compare Classic and Adaptive.

**Short Answer:** AUTOSAR is a worldwide partnership of automotive companies that created a standardised software architecture to allow ECU software reuse across platforms, reduce integration costs, and enable multiple suppliers to contribute to the same ECU.

**Detailed Expert Answer:**

**Why AUTOSAR was created:**
```
Before AUTOSAR (pre-2003):
  - Each OEM had proprietary ECU architecture
  - Software written for Bosch ECU couldn't run on Delphi ECU
  - Each supplier locked OEM into proprietary solution
  - No reuse — engine calibration rewritten for every platform

AUTOSAR goals:
  1. Standardise BSW (Basic Software) — suppliers implement same APIs
  2. Enable SWC portability — app code runs on any AUTOSAR ECU
  3. Separate methodology from hardware — abstract MCU differences
  4. Enable parallel development — OEM defines interface, suppliers implement
```

**AUTOSAR Classic vs Adaptive:**

| Feature | AUTOSAR Classic | AUTOSAR Adaptive |
|---------|----------------|-----------------|
| Target | MCUs (TC397, S32K, STM32H7) | Processors (Cortex-A, Orin, S32G) |
| OS | AUTOSAR OS (OSEK-based) | POSIX (Linux, QNX, Integrity) |
| Memory | Static allocation, no heap | Dynamic allocation allowed |
| Config | All static at compile time | Dynamic at runtime |
| Language | C (MISRA C:2012) | C++14/17 |
| Comm | Signal-based (COM/PDU) | Service-based (SOME/IP) |
| Use case | Body, chassis, powertrain ECUs | ADAS, infotainment, zone controllers |
| Exception | No exceptions | C++ exceptions allowed |
| Standards | ISO 26262 ASIL-D | ISO 26262 ASIL-D (newer profile) |
| Release | R2.0 (2006) – R22-11 | R19-03 (2019) – current |

**Example: SWC in Classic vs Adaptive:**
```c
/* Classic AUTOSAR SWC — C, generated stubs, Rte_ API */
FUNC(void, TorqueCtrl_CODE) TorqueCtrl_Run(void) {
    Rte_Read_PedPos_Value(&pedal_position);   /* Read input port */
    torque = calc_torque(pedal_position);
    Rte_Write_Torque_Value(torque);           /* Write output port */
}
```

```cpp
/* Adaptive AUTOSAR SWC — C++, ara:: API, SOME/IP */
class TorqueController {
    ara::com::ServiceHandle<SpeedSensor> m_speed_svc;
public:
    void Run() {
        auto speed = m_speed_svc->GetCurrentSpeed().GetResult().Value();
        auto torque = CalcTorque(speed);
        m_torque_port.Send(torque);  // SOME/IP event publication
    }
};
```

---

### Q2. Explain the AUTOSAR Classic COM stack. How does a signal travel from SWC to CAN bus?

**Short Answer:** Signal flow: SWC → RTE → COM → PduR → CanIf → CAN driver → CAN bus. Each layer has a specific role: COM packs/unpacks signals, PduR routes PDUs, CanIf abstracts the CAN controller.

**Detailed Expert Answer:**

```
Signal transmission path (top to bottom):

SWC (Application):
  Rte_Write_Speed_Value(58.88)  ← writes physical value

  ↓ RTE converts to raw signal value (physical → raw)

COM (Communication Service):
  Com_SendSignal(COM_SIGNAL_SPEED, &raw_value)
  → Packs raw bits into PDU buffer (signal bit packing)
  → Applies transfer property (triggered, pending, etc.)
  → If cyclic: schedules PDU for next transmission cycle (10ms)
  
  ↓ Com_TriggerIPDUSend(PDU_TX_SPEED_STATUS)

PduR (PDU Router):
  Routes PDU from COM to appropriate CanIf
  → Lookup table: PDU_TX_SPEED_STATUS → CanIf, channel CAN0

  ↓ CanIf_Transmit(CANIF_PDU_TX_SPEED, &pdu)

CanIf (CAN Interface):
  → Converts PDU to CAN frame (adds CAN ID, DLC)
  → Calls MCAL CAN driver: Can_Write(controller, mb, &pdu)

CAN Driver (MCAL):
  → Loads data into transmit mailbox registers
  → Sets TX request bit in CAN controller
  → Hardware arbitrates and transmits frame

CAN Bus: Frame visible with ID 0x120, 8 bytes
```

**COM signal properties (configured in AUTOSAR tool):**
```
ComSignal:
  ComSignalId:          SIGNAL_VEHICLE_SPEED
  ComBitPosition:       16         (Intel byte order, start bit)
  ComBitSize:           16
  ComSignalByteOrder:   LITTLE_ENDIAN
  ComFactor:            0.01       (physical = raw × 0.01)
  ComOffset:            0.0
  ComTransferProperty:  TRIGGERED   (send immediately when written)
  
  OR: ComTransferProperty: PENDING  (send on next scheduled ComMainFunction cycle)
```

**Receive path (CAN bus → SWC):**
```
CAN hardware ISR → CAN driver → CanIf_RxIndication() → PduR_CanIfRxIndication()
→ Com_RxIndication() (signal extraction from PDU)
→ Signal stored in COM Rx buffer
→ SWC calls: Rte_Read_Speed_Value(&speed)
→ RTE reads from COM Rx buffer → returns value to SWC
```

---

### Q3. What is the AUTOSAR OS? Explain tasks, ISRs, and scheduling.

**Short Answer:** AUTOSAR OS is an OSEK-based real-time operating system providing fixed-priority preemptive scheduling, basic/extended tasks, and two ISR categories. It is statically configured — no dynamic task creation.

**Detailed Expert Answer:**

```
AUTOSAR OS Task Types:

BASIC TASK:
  - Runs to completion (no waiting allowed)
  - Does not call WaitEvent() — use only SetEvent/ClearEvent patterns
  - Lower overhead than extended tasks
  - Used for most ECU periodic functions

EXTENDED TASK:
  - Can call WaitEvent() and suspend itself
  - OS context switch occurs
  - Used when task needs to wait for asynchronous operation (NvM, I/O)
  - Higher stack usage (save/restore full CPU context)

Example OS configuration (OIL format or ARXML):
  TASK Task_10ms {
    PRIORITY = 3;
    SCHEDULE = FULL;        // Can be preempted by higher priority tasks
    ACTIVATION = 1;         // Can only have 1 activation at a time
    AUTOSTART = TRUE;
    APPMODE = AppMode_Normal;
    STACKSIZE = 2048;       // 2KB stack
  }
  
  TASK Task_1ms {
    PRIORITY = 10;          // Higher priority than Task_10ms
    SCHEDULE = FULL;
    ACTIVATION = 1;
    STACKSIZE = 512;
  }
```

**ISR categories:**
```c
/* Category 1 ISR — fastest, no OS API calls, just hardware service */
ISR(CAN_Rx_ISR_Category1) {
    /* Only direct register access — no OS calls, no queues */
    g_can_frame = can_read_mailbox();
    can_clear_interrupt_flag();
}

/* Category 2 ISR — can call OS APIs (SetEvent, GetResource) */
ISR(CAN_Rx_ISR_Category2) {
    can_read_mailbox(&g_can_frame);
    SetEvent(Task_ProcessCAN, EVENT_CAN_RX);  /* Wakes up waiting task */
    can_clear_interrupt_flag();
}
```

**Alarm (timer-based task activation):**
```c
/* OS alarm activates Task_10ms every 10ms */
/* Configured statically in OS configuration */
/* No code needed — OS scheduler handles this */

/* Task body — activated every 10ms */
TASK(Task_10ms) {
    Can_MainFunction_Write();     /* Confirm TX frames */
    Can_MainFunction_Read();      /* Process Rx frames */
    Com_MainFunction_Tx();        /* Trigger periodic transmissions */
    Com_MainFunction_Rx();        /* Signal timeout monitoring */
    
    TerminateTask();  /* MUST call at end of basic task */
}
```

---

## INTERMEDIATE QUESTIONS

---

### Q4. Explain AUTOSAR NvM (Non-Volatile Memory Manager) — blocks, mirrors, and redundancy.

**Short Answer:** NvM manages read/write operations to non-volatile storage (EEPROM, data flash) through a block abstraction. Each NvM block has a CRC and optionally a RAM mirror. Reads/writes are asynchronous.

**Detailed Expert Answer:**

```c
/* NvM block definition (configured in AUTOSAR tool) */
NvMBlockDescriptor OdometerBlock = {
    .BlockId          = NVM_BLOCK_ODOMETER,
    .BlockType        = NVM_BLOCK_REDUNDANT,  /* Two copies for reliability */
    .NvBlockLength    = sizeof(OdometerData_t),
    .RamBlockAddress  = &g_odometer_ram,      /* RAM mirror */
    .CrcType          = NVM_CRC_16,
    .WriteBlockOnce   = FALSE,
    .ResistantToChangedSw = TRUE,             /* Retain data after reflash */
};
```

**Read operation (asynchronous):**
```c
/* Application requests read — returns immediately */
void App_ReadOdometer(void) {
    Std_ReturnType ret = NvM_ReadBlock(NVM_BLOCK_ODOMETER, NULL);
    /* NULL = use block's configured RAM mirror address */
    
    if (ret == E_OK) {
        /* Request queued — data NOT available yet! */
        g_nvm_read_pending = TRUE;
    }
}

/* Called after NvM completes (NvM SingleBlockCallback) */
void NvM_OdometerReadCallback(uint8 ServiceId, NvM_RequestResultType JobResult) {
    if (JobResult == NVM_REQ_OK) {
        /* Data is now available in g_odometer_ram */
        App_ProcessOdometerData(&g_odometer_ram);
    } else if (JobResult == NVM_REQ_INTEGRITY_FAILED) {
        /* CRC failed — block corrupted, NvM loaded default value */
        App_SetOdometerToDefault();
    }
}
```

**NvM write with immediate flag:**
```c
/* Write odometer — must be done frequently (every journey end) */
void App_WriteOdometer(const OdometerData_t *data) {
    memcpy(&g_odometer_ram, data, sizeof(OdometerData_t));
    
    /* Queue write — executed during NvM_MainFunction() call */
    NvM_WriteBlock(NVM_BLOCK_ODOMETER, NULL);
    
    /* IMPORTANT: writing is slow (EEPROM: 5ms per byte, Data Flash: sector erase) */
    /* AUTOSAR ensures write queue processed during normal operation */
    /* On shutdown: NvM_WriteAll() blocks until all pending writes complete */
}
```

**NVM_REQ status codes:**
```
NVM_REQ_OK                 = Success
NVM_REQ_NOT_OK             = Write/read error
NVM_REQ_INTEGRITY_FAILED   = CRC check failed (corruption)
NVM_REQ_BLOCK_SKIPPED      = Block type disabled or not needed
NVM_REQ_RESTORED_FROM_ROM  = Used ROM default (first use or corruption)
```

---

### Q5. Explain AUTOSAR CommunicationManager (ComM) and how ECUs enter/exit sleep on a CAN bus.

**Detailed Expert Answer:**

```
ComM State Machine (per channel/bus):

FULL_COMMUNICATION ──────────────────────────────────────▶ SILENT_COMMUNICATION
        │                         (nm_timeout)                     │
        │ nm_no_communication                                       │
        │ (all SWCs released bus)                                   │
        ▼                                                           │
NO_COMMUNICATION ◀─────────────────────────────────────────────────┘
(Bus Sleep)

State descriptions:
  FULL_COM:   ECU actively communicating, NM active, sending periodic frames
  SILENT_COM: ECU can receive but not transmit (bus release in progress)
  NO_COM:     ECU sleeping, bus powered down (transceiver in sleep/standby)
```

```c
/* SWC requests communication (e.g., ignition ON) */
void App_IgnitionOn(void) {
    ComM_RequestComMode(COMM_USER_IGNITION, COMM_FULL_COMMUNICATION);
}

/* SWC releases communication (ignition OFF, function not needed) */
void App_IgnitionOff(void) {
    ComM_RequestComMode(COMM_USER_IGNITION, COMM_NO_COMMUNICATION);
}
/* ComM waits until ALL users release before entering bus sleep */
/* Even if ignition user releases, if another user (TCU, OTA) holds it, stay active */
```

**Network Management (NM) integration:**
```
AUTOSAR NM (OSEK/AUTOSAR NM):
  Each ECU sends NM frames (CAN ID 0x400-0x47F typically)
  NM frame = ECU node ID + control bits
  
  If an ECU stops seeing NM frames from network participants
  → assumes all others are ready to sleep
  → releases its own NM frame transmission
  → ComM triggers bus sleep sequence
  
  Bus sleep entry:
  1. Application releases ComM channel
  2. ComM waits for all ComM users to release
  3. ComM calls NM to coordinate bus sleep
  4. NM waits for NM timeout (no more NM frames seen)
  5. CanSM instructs CanIf to power down transceiver
  6. Transceiver enters standby mode (low power, wake-up detection active)
```

---

## ADVANCED QUESTIONS

---

### Q6. Explain AUTOSAR E2E protection and why it's needed for safety-critical signals.

**Short Answer:** E2E (End-to-End) protection adds a CRC + sequence counter to safety-critical COM signals to detect data corruption in the communication stack (memory errors, buffer overwrites) that CAN's hardware CRC doesn't catch.

**Detailed Expert Answer:**

```
Why E2E is needed:
  CAN hardware CRC: checks physical transmission errors (bit flips on wire)
  
  BUT: once data is received correctly in CAN buffer, software can corrupt it:
    - MCU RAM bit flip (SEU — Single Event Upset)
    - Stack overflow corrupting signal buffer
    - Race condition overwriting signal value
    - COM layer misconfiguration causing signal mismatch
  
  ISO 26262 ASIL-B/D requirement: end-to-end protection for safety signals
```

**E2E Profile 1 (most common in CAN-based automotive):**
```c
/* E2E Profile 1 protection — adds to each signal group: */
/* CRC (1 byte) + Counter (4 bits) */

typedef struct {
    uint8_t  counter;     /* Increments each transmission */
    uint8_t  crc;         /* CRC-8 over data + counter */
} E2E_P1_Header_t;

/* Before transmission (E2E protect): */
void E2E_P1_Protect(uint8_t *data, uint8_t len, uint8_t *counter) {
    data[0] = (*counter) & 0x0FU;    /* Lower nibble = counter */
    data[0] |= calc_crc8(data, len) & 0xF0U; /* Upper nibble = CRC */
    (*counter) = ((*counter) + 1U) % 15U;    /* Counter 0-14, wraps */
}

/* After reception (E2E check): */
E2E_P1_CheckStatusType E2E_P1_Check(const uint8_t *data, uint8_t len,
                                     uint8_t *last_counter) {
    uint8_t received_crc     = (data[0] >> 4) & 0x0FU;
    uint8_t received_counter = data[0] & 0x0FU;
    uint8_t expected_crc     = calc_crc8(data, len) & 0x0FU;
    
    if (received_crc != expected_crc) return E2E_P1_STATUS_ERROR;  /* Data corruption */
    
    int8_t delta = (int8_t)(received_counter - *last_counter);
    if (delta == 1) {
        *last_counter = received_counter;
        return E2E_P1_STATUS_OK;
    } else if (delta > 1) {
        return E2E_P1_STATUS_LOST;     /* Messages lost */
    } else if (delta == 0) {
        return E2E_P1_STATUS_REPEATED; /* Duplicate */
    }
    return E2E_P1_STATUS_WRONGSEQUENCE;
}
```

**Which signals need E2E in a TCU:**
```
ASIL-D: Steering torque setpoint → E2E Profile 4 (highest protection)
ASIL-B: Vehicle speed, engine torque → E2E Profile 1/2
QM:     Infotainment, comfort → no E2E required
```

---

## PRODUCTION SCENARIO QUESTIONS

---

### Q7. During AUTOSAR integration, a diagnostic test shows NvM block integrity failures after ECU reflash. How do you diagnose?

**Expert Answer:**

"This is a classic issue when updating ECU firmware without coordinating NvM block layout changes.

**Root cause analysis:**
```
Scenario: NvM block layout changed between SW versions

Old SW v1.0:
  Block 0x0001: OdometerData_v1 (4 bytes: uint32_t km)
  Block 0x0002: CalibrationData_v1 (20 bytes)

New SW v2.0:
  Block 0x0001: OdometerData_v2 (8 bytes: uint64_t km + uint32_t trip_m)
  Block 0x0002: CalibrationData_v2 (24 bytes — added 4 bytes of new cal)

After reflash:
  Flash contains new SW (v2.0)
  EEPROM still contains old data layout (v1.0)
  
  On boot: NvM_ReadAll reads block 0x0001
           Reads 8 bytes from EEPROM but EEPROM only has 4 bytes of valid data
           CRC computed over 8 bytes includes 4 bytes of garbage
           CRC mismatch → NVM_REQ_INTEGRITY_FAILED
           ECU loads default values → odometer resets to 0!
```

**Fix strategies:**

**Option 1 — Compatible layout change (extend at end):**
```c
/* GOOD: Add new fields at end — old CRC covers old bytes */
typedef struct {
    uint32_t km;           /* v1.0 — existing */
    uint32_t trip_m;       /* v2.0 — new field at end */
} OdometerData_v2;        /* Same first 4 bytes as v1.0 */
/* But: total size changed → block length config must match → still breaks CRC */
```

**Option 2 — Version field in block:**
```c
typedef struct {
    uint8_t  version;      /* 0x01 for v1.0, 0x02 for v2.0 */
    uint32_t km;
    uint32_t trip_m;       /* Only valid if version >= 0x02 */
} OdometerData_t;

void NvM_OdometerReadCallback(...) {
    if (g_odometer_ram.version == 0x01) {
        /* Migrate v1 → v2 */
        g_odometer_ram.trip_m = 0;
        g_odometer_ram.version = 0x02;
        NvM_WriteBlock(NVM_BLOCK_ODOMETER, NULL);  /* Save migrated data */
    }
}
```

**Option 3 — Programming sequence specifying NvM erase:**
```
In production flash process:
  1. Start programming session (0x10 0x02)
  2. Run 'Erase NvM' routine (0x31 0x01 0xXXXX) before firmware flash
  3. Flash new firmware
  4. Reset ECU
  5. On boot: NvM blocks are empty → loaded from ROM defaults (safe)
```

**Production Insight:** KPIT AUTOSAR guideline: every NvM block MUST have a version byte and a migration callback. Before any NvM block structure change, the change must be registered in the AUTOSAR NvM migration matrix. EOL programming sequences are updated to include NvM erase when structure changes are made."

---

## CHEAT SHEET — AUTOSAR

```
Classic AUTOSAR Stack:
  Application SWC → RTE → BSW (Services/ECU Abstraction/MCAL) → Hardware

Key BSW modules:
  MCAL:    MCU, Port, Can, Spi, Adc, Pwm, Gpt, Wdg (MCU-specific, vendor-supplied)
  CanIf:   CAN Interface — abstracts CAN controller from upper layers
  PduR:    PDU Router — routes PDUs between CanIf, Com, Dcm
  Com:     Signal packing/unpacking, cyclic/event transmission
  ComM:    Bus sleep/wake management, coordinates multiple users
  NvM:     Async NVRAM management, CRC validation, block mirrors
  Dem:     DTC storage, freeze frames, aging/healing counters
  Dcm:     UDS request handling, calls application callbacks
  OS:      OSEK-based RTOS, fixed-priority, static configuration

Adaptive AUTOSAR (AP):
  Based on POSIX (Linux/QNX)
  Dynamic config, C++17, exceptions allowed
  ara::com (SOME/IP), ara::diag (UDS), ara::log (logging)

COM signal path: SWC → Rte_Write → Com_SendSignal → PduR → CanIf → CAN driver
Receive path:    CAN ISR → CanIf_RxIndication → PduR → Com_RxIndication → Rte_Read

NvM key points:
  - Reads/writes are ASYNCHRONOUS — use callbacks
  - Block corruption → NVM_REQ_INTEGRITY_FAILED → ROM default loaded
  - Always add version byte to NvM blocks for migration

E2E Protection:
  Profile 1: CRC-8 + 4-bit counter (CAN signals, 1-12 bytes)
  Profile 4: CRC-16 + 8-bit counter (large safety data)
  Required for ASIL-B and ASIL-D signals

AUTOSAR OS tasks:
  Basic: runs to completion, no WaitEvent()
  Extended: can WaitEvent() and suspend
  ISR Cat1: no OS API, fastest
  ISR Cat2: can call SetEvent, GetResource
```
