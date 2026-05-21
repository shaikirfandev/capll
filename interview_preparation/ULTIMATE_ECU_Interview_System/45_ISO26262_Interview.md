# ISO 26262 Functional Safety Interview Questions
## Senior Automotive Embedded Engineer — Principal Level

---

## TOPIC OVERVIEW

ISO 26262 (Functional Safety of Road Vehicles) is the foundational safety standard for automotive E/E systems. Senior engineers at **Bosch, Continental, ZF, Aptiv, Valeo, and any ADAS/powertrain/braking role** are expected to understand ASIL decomposition, safety lifecycle, safety mechanisms, and verification. Even if you're not a safety engineer, you must know the basics because your code will be reviewed against ASIL requirements.

**Key areas:**
- ISO 26262 structure (10 parts overview)
- ASIL levels (A–D) and risk assessment (S, E, C parameters)
- Safety lifecycle (concept, system, hardware, software, validation)
- ASIL decomposition (splitting into redundant components)
- Safety mechanisms: error detection, error handling, safe state
- Software requirements at each ASIL level (MC/DC coverage, MISRA C)
- Hardware safety mechanisms: ECC, watchdog, memory check
- Dependent failure analysis (DFA)
- Functional Safety Concept (FSC) and Technical Safety Concept (TSC)

---

## ISO 26262 BASICS

---

### Q1. What are ASIL levels? How are they determined?

**Short Answer:** ASIL (Automotive Safety Integrity Level) is a risk classification from A (lowest) to D (highest). It's derived from a risk assessment using three parameters: Severity (S0–S3), Exposure (E0–E4), and Controllability (C0–C3). The higher the ASIL, the more rigorous the safety requirements.

**Detailed Expert Answer:**

```
ASIL Determination — Risk Assessment:

SEVERITY (S) — How bad is the hazard?
  S0: No injury
  S1: Light to moderate injuries
  S2: Severe life-threatening injuries (survival probable)
  S3: Life-threatening injuries (survival uncertain) or fatal

EXPOSURE (E) — How often is the vehicle in this situation?
  E0: Incredible (never)
  E1: Very low probability (once in vehicle lifetime)
  E2: Low probability (occasionally)
  E3: Medium probability (fairly often)
  E4: High probability (every drive, normal operating)

CONTROLLABILITY (C) — Can driver avoid the hazard?
  C0: Controllable in general (driver easily avoids)
  C1: Simply controllable
  C2: Normally controllable (most drivers can handle)
  C3: Difficult to control or uncontrollable

ASIL Determination Table:
       C1    C2    C3
S1 E1: QM    QM    QM
S1 E2: QM    QM    QM-A
S1 E3: QM    QM-A  A
S1 E4: QM    A     B
S2 E1: QM    QM    QM-A
S2 E2: QM    A     B
S2 E3: A     B     C
S2 E4: B     C     D
S3 E1: QM    A     B
S3 E2: A     B     C
S3 E3: B     C     D
S3 E4: C     D     D

QM = Quality Management (no ASIL requirements, but still good engineering practice)
ASIL A = Lowest safety requirement
ASIL D = Highest safety requirement

Real Example: Autonomous Emergency Braking (AEB) System
  Hazard: Unintended sudden braking at highway speed
  S = S3 (life-threatening — rear-end collision likely)
  E = E4 (system active during every highway drive)
  C = C3 (difficult to control — sudden braking at 130km/h)
  → ASIL D (maximum safety requirement)

Real Example: Climate control incorrect temperature
  Hazard: Driver uncomfortable
  S = S0 (no injury)
  E = E4 (every drive)
  C = C0 (easily controlled — press button)
  → QM (no ASIL requirement)
```

---

### Q2. What is ASIL decomposition? Give a concrete example.

**Expert Answer:**

```c
/*
 * ASIL Decomposition Example:
 * Steering control = ASIL D requirement
 * Too expensive to implement entire path at ASIL D
 * Solution: split into two independent ASIL B channels
 * ASIL D = ASIL B (channel A) + ASIL B (channel B)
 * 
 * Rule: ASILx = ASILy + ASILz where x ≤ y + z (roughly)
 * Valid: ASIL D = ASIL B + ASIL B
 * Valid: ASIL D = ASIL C + ASIL A
 * Valid: ASIL B = ASIL A + ASIL A
 */

/* Channel A: Main steering ECU (ASIL B) */
typedef struct {
    float   steering_angle_deg;   /* Main angle calculation */
    uint8_t status;               /* Health status */
    uint32_t crc;                 /* E2E protection for this struct */
} SteeringOutput_A_t;

/* Channel B: Safety monitor ECU (ASIL B) — independent hardware! */
typedef struct {
    float   steering_angle_deg;   /* Independent angle calculation */
    uint8_t status;
    uint32_t crc;
} SteeringOutput_B_t;

/* Voter / comparator — compares both channels */
float steering_get_safe_output(const SteeringOutput_A_t *a,
                                const SteeringOutput_B_t *b) {
    /* Both channels must agree within tolerance */
    if (a->status != CHANNEL_OK || b->status != CHANNEL_OK) {
        return STEERING_SAFE_STATE;  /* Zero output */
    }
    
    float delta = fabsf(a->steering_angle_deg - b->steering_angle_deg);
    if (delta > STEERING_DIVERGENCE_LIMIT_DEG) {
        /* Channels disagree — safe state */
        log_safety_violation("Steering divergence: %.2f deg", delta);
        set_dtc(DTC_STEERING_CHANNEL_MISMATCH);
        return STEERING_SAFE_STATE;
    }
    
    /* Both agree — use channel A (primary) */
    return a->steering_angle_deg;
}

/*
 * Why this is valid:
 * Channel A: single hardware fault covered by ASIL B mechanisms
 * Channel B: independent hardware, independent SW, independent fault detection
 * Combined: if fault occurs in A, B detects divergence and safe state is selected
 * Two independent ASIL B failures required simultaneously to cause hazard
 * → Meets ASIL D requirement
 *
 * Independence requirement: ASIL decomposition requires:
 * - Different hardware (no shared MCU)
 * - Different software teams / tools / compilers
 * - Different power supplies
 * - Independent communication channels
 * - No shared single point of failure
 */
```

---

## SOFTWARE REQUIREMENTS

---

### Q3. What software requirements does ISO 26262 impose for each ASIL level?

**Expert Answer:**

```
Software requirements per ASIL level:

CODING STANDARDS:
  ASIL A: Recommended MISRA C
  ASIL B: Mandatory MISRA C (with documented deviations)
  ASIL C: Mandatory MISRA C, SW design methods (modularity, encapsulation)
  ASIL D: Mandatory MISRA C, strongly recommended MISRA C++, formal methods

TESTING REQUIREMENTS:
  ASIL A: Statement coverage 100%
  ASIL B: Branch coverage 100%
  ASIL C: MC/DC (Modified Condition/Decision Coverage) — 100%
  ASIL D: MC/DC 100% + data flow test coverage

What is MC/DC (ASIL C/D requirement):
  Ensures every condition in every decision independently affects the outcome
  
  Example: if (A && B && C) — MC/DC requires tests showing:
  Test 1: A=T, B=T, C=T → result=T
  Test 2: A=F, B=T, C=T → result=F  (A independently changes result)
  Test 3: A=T, B=F, C=T → result=F  (B independently changes result)
  Test 4: A=T, B=T, C=F → result=F  (C independently changes result)
  4 tests minimum vs 2^3=8 for full boundary (more efficient)

DEFENSIVE CODING REQUIREMENTS:
  ASIL B+:
    - Range checks on all safety-critical inputs
    - Division protection (check denominator before dividing)
    - Array bounds protection (never index beyond bounds)
    - Pointer null checks before dereference
    - Watchdog timeout monitoring
    - Periodic memory check (stack overflow detection)
  
  ASIL C+:
    - E2E data protection on all safety-critical interfaces (CRC + counter)
    - Error detection AND error handling with safe state
    - Alive counter in CAN messages
  
  ASIL D:
    - Formal proof of absence of runtime errors (Polyspace/ASTREE)
    - Hardware fault detection coverage measurable
    - All software requirements formally verified

CODE EXAMPLE — E2E Protection for ASIL C communication:
```
```c
/* AUTOSAR E2E Profile 1 for safety signal protection */
typedef struct {
    uint8_t  counter;         /* Increments each cycle 0x00–0x0E, wraps */
    uint8_t  crc;             /* CRC-8 of {data_id[0], data_id[1], counter, payload} */
    uint16_t payload;         /* Actual safety data (e.g., steering angle) */
} E2E_Profile1_Frame_t;

/* Protect (sender side) */
void E2E_P1_Protect(E2E_Profile1_Frame_t *frame, uint16_t data_id, uint16_t payload) {
    static uint8_t s_counter = 0U;
    
    frame->counter = s_counter & 0x0FU;  /* 4-bit counter, wraps 0-14 */
    frame->payload = payload;
    
    /* CRC covers: data_id bytes + counter nibble + payload */
    uint8_t crc_input[5] = {
        (uint8_t)(data_id >> 8), (uint8_t)(data_id),
        frame->counter,
        (uint8_t)(payload >> 8), (uint8_t)(payload)
    };
    frame->crc = crc8_autosar(crc_input, sizeof(crc_input));
    
    s_counter = (s_counter >= 14U) ? 0U : (s_counter + 1U);
}

typedef enum {
    E2E_P_OK = 0,
    E2E_P_WRONG_CRC,
    E2E_P_COUNTER_LOST,  /* Missed frames */
    E2E_P_REPEATED       /* Duplicate frame */
} E2E_Result_t;

/* Check (receiver side) */
E2E_Result_t E2E_P1_Check(const E2E_Profile1_Frame_t *frame, uint16_t data_id) {
    static uint8_t s_last_counter = 0xFFU;  /* 0xFF = not yet received */
    
    /* Verify CRC */
    uint8_t crc_input[5] = {
        (uint8_t)(data_id >> 8), (uint8_t)(data_id),
        frame->counter,
        (uint8_t)(frame->payload >> 8), (uint8_t)(frame->payload)
    };
    uint8_t expected_crc = crc8_autosar(crc_input, sizeof(crc_input));
    
    if (frame->crc != expected_crc) {
        return E2E_P_WRONG_CRC;
    }
    
    /* Check counter */
    if (s_last_counter != 0xFFU) {
        uint8_t expected_counter = (s_last_counter >= 14U) ? 0U : (s_last_counter + 1U);
        if (frame->counter == s_last_counter) return E2E_P_REPEATED;
        if (frame->counter != expected_counter) return E2E_P_COUNTER_LOST;
    }
    
    s_last_counter = frame->counter;
    return E2E_P_OK;
}
```

---

## PRODUCTION SCENARIO QUESTIONS

---

### Q4. An ASIL-B function writes to the wrong memory address. How do you prevent/detect this?

**Expert Answer:**

"Memory write violations in safety-critical functions are prevented and detected through multiple layers (defence in depth):

**Prevention (at design time):**
```c
/* 1. MPU (Memory Protection Unit) — hardware enforcement */
/* Partition memory regions by ASIL level */

/* ASIL-B safety data: separate MPU region, write-protected except by specific tasks */
#pragma section ".safety_data" /* Linker places this in dedicated region */
static volatile uint16_t s_steering_angle_asil = 0U;  /* ASIL-B */

/* MPU configured: Task_Safety can write; Task_Normal is read-only for this region */
/* If Task_Normal attempts write → MemManage fault → OS catches → DTC + safe state */

/* 2. Compile-time protection: MISRA C Rule 8.4 */
/* All safety variables declared in single header with clear ASIL tagging */
/* #define SAFETY_CRITICAL __attribute__((section(".safety_section"))) */

/* 3. AUTOSAR OS: no direct memory sharing between ASIL partitions */
/* Use OS_IOC (Inter-OS-Application Communication) for cross-partition data */
```

**Detection (at runtime):**
```c
/* 4. Periodic memory integrity check */
/* Calculate CRC-32 of entire safety section at init */
/* Re-check every 10ms in safety supervisor task */

void safety_memory_integrity_check(void) {
    static uint32_t s_baseline_crc = 0U;
    
    if (s_baseline_crc == 0U) {
        /* First call: establish baseline */
        s_baseline_crc = crc32((uint8_t *)SAFETY_SECTION_ADDR, SAFETY_SECTION_SIZE);
        return;
    }
    
    uint32_t current_crc = crc32((uint8_t *)SAFETY_SECTION_ADDR, SAFETY_SECTION_SIZE);
    if (current_crc != s_baseline_crc) {
        /* Safety memory corrupted — safe state */
        log_safety_critical("MEMORY INTEGRITY FAIL: expected=0x%08X actual=0x%08X",
                             s_baseline_crc, current_crc);
        set_dtc(DTC_SAFETY_MEMORY_CORRUPTION);
        safety_enter_safe_state();
    }
}

/* 5. Stack overflow detection: MPU guard page at stack bottom */
/* OS places no-access MPU region at stack bottom */
/* Stack overflow → MemManage fault → caught → reset */
```

**Production Insight (Valeo parking sensor ECU, ASIL B):** Corrupted steering angle in safety section was traced to stack overflow in a non-ASIL task. The overflow walked into the safety memory region. MPU was configured for the safety section but stack guard was missing. Fix: added MPU guard page at bottom of every task stack. ASan in debug caught it first; MPU caught it in production firmware."

---

## CHEAT SHEET — ISO 26262

```
ASIL levels:
  QM = Quality Management (no safety requirements)
  A = Lowest (ABS chime, courtesy light)
  B = Medium-low (ACC sensor)
  C = Medium-high (electric power steering, ABS)
  D = Highest (airbag, by-wire braking/steering)

Risk parameters:
  S = Severity (S0=none → S3=fatal)
  E = Exposure (E0=never → E4=every drive)
  C = Controllability (C0=easy → C3=uncontrollable)

ASIL decomposition:
  ASIL D = ASIL B + ASIL B
  ASIL C = ASIL A + ASIL B
  ASIL B = ASIL A + ASIL A
  Requires: independent hardware, SW, power supply, communication

Software requirements by ASIL:
  A: Statement coverage 100%
  B: Branch coverage 100%, mandatory MISRA C
  C: MC/DC 100%, E2E protection, formal SW design
  D: MC/DC 100%, formal proof (Polyspace), MISRA C++

Safety mechanisms:
  Hardware: ECC memory, dual-core lock-step, hardware WDG
  Software: CRC/E2E on safety signals, range checks, MPU
  Communication: E2E Profile 1/2 (counter + CRC on CAN signals)
  System: ASIL decomposition, safe state, DTC logging

E2E protection elements:
  Counter: detects lost or repeated messages (alive counter)
  CRC: detects data corruption
  Data ID: prevents routing errors (signal from wrong source)

Safe state principle:
  For every hazardous event: define a safe state
  Safe state = no hazard, even if function is impaired
  Examples:
    Steering: zero assist (driver maintains control)
    Braking: maintain current braking force (stable)
    Engine: cut torque (vehicle decelerates safely)
    Infotainment: display off (no hazard)
```
