# 12 — RTOS for Automotive ECU

> **Standards:** OSEK/VDX, AUTOSAR OS (ISO 17356), FreeRTOS (non-safety), QNX (POSIX)  
> **Hardware:** AURIX TriCore (OSEK), ARM Cortex-M (FreeRTOS), ARM Cortex-A (Linux/QNX)

---

## 12.1 OSEK/VDX vs FreeRTOS vs AUTOSAR OS

| Feature | OSEK/VDX | AUTOSAR OS | FreeRTOS | Linux/QNX |
|---------|----------|------------|----------|-----------|
| Standard | OSEK/VDX 2.2 | ISO 17356 (extends OSEK) | MIT open source | POSIX |
| Scheduling | Fixed-priority preemptive | Fixed-priority + mixed | Priority preemptive | Fair share + RT patches |
| Dynamic tasks | No | No | Yes | Yes |
| Conformance class | BCC1/BCC2/ECC1/ECC2 | Same + SC1-SC4 | N/A | N/A |
| Memory protection | Optional | SC3/SC4 | MPU optional | Full MMU |
| Functional safety | QM baseline | ASIL-D certified | QM only | Up to ASIL-B (QNX) |
| Typical use | Body ECU, powertrain | ADAS, brakes, gateway | Prototyping, low-cost MCU | Domain controller |

---

## 12.2 OSEK Task Configuration (OIL file)

```oil
/* OSEK Implementation Language (OIL) — task configuration */

TASK LKA_10ms {
    PRIORITY    = 10;
    SCHEDULE    = FULL;         /* Preemptible */
    ACTIVATION  = 1;            /* Max 1 pending activation */
    AUTOSTART   = FALSE;
    RESOURCE    = RES_SENSOR_BUS;
};

ALARM LKA_Alarm {
    COUNTER = SystemTimer;      /* 1ms base tick */
    ACTION  = ACTIVATETASK {
        TASK = LKA_10ms;
    };
    AUTOSTART = TRUE {
        APPMODE = OSDEFAULTAPPMODE;
        ALARMTIME = 5;          /* Start after 5ms */
        CYCLETIME = 10;         /* 10ms period */
    };
};

RESOURCE RES_SENSOR_BUS {
    RESOURCEPROPERTY = STANDARD;
    /* Priority ceiling = max priority of all tasks using this resource */
};
```

---

## 12.3 FreeRTOS Core Concepts (ARM Cortex-M)

```cpp
// Task creation
static StackType_t  lkaStack[256];
static StaticTask_t lkaTCB;

void lkaTask(void* params) {
    TickType_t lastWake = xTaskGetTickCount();
    for (;;) {
        // Execute LKA function
        LKA_MainFunction();
        // Precise 10ms period
        vTaskDelayUntil(&lastWake, pdMS_TO_TICKS(10U));
    }
}

// Create task (static allocation — MISRA compliant)
xTaskCreateStatic(lkaTask, "LKA", 256U, nullptr, 5U, lkaStack, &lkaTCB);

// Binary semaphore for ISR-to-task synchronisation
static SemaphoreHandle_t canRxSem;
static StaticSemaphore_t canRxSemBuf;

void CAN_RX_IRQHandler(void) {
    // ISR: signal task
    BaseType_t woken = pdFALSE;
    xSemaphoreGiveFromISR(canRxSem, &woken);
    portYIELD_FROM_ISR(woken);
}

void canProcessTask(void* p) {
    for (;;) {
        xSemaphoreTake(canRxSem, portMAX_DELAY);  // Block until ISR signals
        processCanFrame();
    }
}
```

---

## 12.4 Watchdog Management

```
Hardware Watchdog (WDG) requirement (ISO 26262):
  Watchdog must be serviced regularly. If ECU hangs → WDG triggers reset.
  Windowed watchdog: must be serviced WITHIN a time window (not too early, not too late).
  
  Window: Open at 50ms, Close at 100ms.
  Correct servicing: call WdgIf_SetMode(WDGIF_SLOW_MODE) between 50-100ms.
  Too early: treated as error.
  Too late (no service): hard reset.

AUTOSAR WdgM (Watchdog Manager):
  Each supervised entity (task or SW function) has a "checkpoint".
  WdgM monitors checkpoint sequence.
  
  WdgM_CheckpointReached(entityId, checkpointId);
  
  Example:
    LKA_Init() calls WdgM_CheckpointReached(LKA_ENTITY, INIT_CHECKPOINT)
    LKA_MainFunction() calls WdgM_CheckpointReached(LKA_ENTITY, MAIN_CHECKPOINT)
    
    If LKA task stops calling checkpoints → WdgM detects missing → triggers reset or
    transitions to safe state.

Stack overflow detection:
  AUTOSAR OS: stack fill pattern (0xCD) at stack bottom, checked in each task entry.
  FreeRTOS: configCHECK_FOR_STACK_OVERFLOW = 2 → vApplicationStackOverflowHook().
```

---

## 12.5 Multi-Core Scheduling (AURIX TriCore)

```
AURIX TC3xx: 3 TriCore CPUs (core0, core1, core2) + lockstep core (safety)

Typical ADAS partitioning:
  Core0 (1MHz, safety island):
    - Watchdog management
    - Voltage/temperature monitoring  
    - ASIL-D safety monitors
    - Lockstep comparison

  Core1 (300MHz, feature core):
    - LKA 10ms task
    - ACC 20ms task
    - Sensor fusion 20ms task
    - CAN driver tasks

  Core2 (300MHz, communication core):
    - Ethernet (SOME/IP) handler
    - Diagnostics (UDS) handler
    - NvM read/write

Inter-core communication:
  Spinlock (hardware semaphore): AURIX provides dedicated spinlock registers
  Shared memory: place shared data in DSPR (Data Scratch-Pad RAM) accessible to all cores
  Core-to-core interrupt: trigger ISR on another core via IPI (Inter-Processor Interrupt)

Cache coherency: AURIX uses no cache (DSPR/PSPR are tightly coupled) → no flush needed.
For ARM Cortex-A (domain controller): explicit cache invalidate/flush required!
```

---

## 12.6 Interview Questions

```
L1:
  Q: What is the difference between a task and an ISR in automotive RTOS?
  A: ISR (Interrupt Service Routine):
     - Triggered by hardware event (CAN frame received, timer overflow)
     - Executes in privileged interrupt context, preempts tasks
     - Must be SHORT (< 10µs ideally) — only read registers, post to queue/semaphore
     - No blocking operations allowed
     
     Task (OSEK/FreeRTOS):
     - Scheduled by OS, runs at configured priority
     - Can call blocking operations (wait for semaphore, vTaskDelay)
     - Performs actual work: run algorithms, call SWC functions
     
     Pattern: ISR reads CAN register → posts frame to ring buffer → signals semaphore
              Task wakes → reads from ring buffer → processes frame

  Q: What is priority inversion and how does OSEK prevent it?
  A: Priority inversion: Low-priority task L holds resource R. High-priority task H
     needs R → H blocks. Medium-priority task M preempts L → M runs while H waits.
     Effective priority of H is inverted to below M.
     
     OSEK solution: Priority Ceiling Protocol (via OS Resource).
     When task acquires resource: OS elevates its priority to ceiling_priority.
     Ceiling = max priority of all tasks that use this resource.
     → No medium-priority task can preempt while resource is held.

L2:
  Q: How do you avoid race conditions between tasks sharing a CAN signal buffer?
  A: Multiple approaches:
     1. Single producer / single consumer ring buffer: no lock needed for ISR→task
        Producer (ISR): writes head. Consumer (task): reads tail. Both are atomic.
     2. OS Resource (OSEK) / Mutex (FreeRTOS): wrap access in GetResource/ReleaseResource
     3. Double buffering: ISR writes to buffer A. Task reads from buffer B. Swap pointers
        atomically (single instruction on 32-bit aligned pointer).
     4. AUTOSAR: use COM signal access which has internal lock mechanism.
     
     MISRA: Global shared data must have explicit documentation of concurrency protection.

L3:
  Q: How do you partition a multi-core ECU for ISO 26262 ASIL D?
  A: ASIL decomposition allows ASIL D = ASIL B(D) + ASIL B(D):
     Core 0: ASIL B element — LKA main function
     Core 1: ASIL B element — LKA safety monitor (independent implementation)
     
     Requirements:
     - Freedom from interference: Core 0 code cannot corrupt Core 1 memory
       → MPU partitioning (AUTOSAR OS SC3/SC4 with memory protection)
     - Independent development: different developers, different tools
     - Diverse implementation: different algorithm to detect common-cause failures
     - Cross-core comparison: Core 1 safety monitor validates Core 0 output
       If deviation > threshold → safe state transition (zero torque)
     
     Hardware support: AURIX TC3xx lockstep (Core 0 + shadow core run same code,
     results compared in hardware — single-point fault detection, ASIL D capable)
```
