# RTOS Interview Questions
## Senior Automotive Embedded Engineer — Principal Level

---

## TOPIC OVERVIEW

Real-Time Operating Systems (RTOS) are **mandatory knowledge** for automotive ECU developers. FreeRTOS, AUTOSAR OS (OSEK), and QNX are the dominant RTOSes in automotive. RTOS concepts are heavily probed at Continental, Bosch, STMicroelectronics, NXP, and any role involving MCU-based ECU development (safety, powertrain, chassis, body domains).

**Key areas probed:**
- RTOS fundamentals (task scheduling, preemption, context switch)
- FreeRTOS internals (task creation, queues, semaphores, mutexes, timers)
- AUTOSAR OS vs OSEK OS
- Priority inversion and priority inheritance
- Interrupt handling in RTOS
- Memory management in RTOS (static allocation, heap alternatives)
- Deadlock prevention
- Timing analysis (WCET, utilisation, CPU load)
- Watchdog integration

---

## BEGINNER QUESTIONS

---

### Q1. What is a Real-Time Operating System and when is it needed in automotive ECUs?

**Short Answer:** An RTOS provides deterministic task scheduling with guaranteed worst-case response times. In automotive ECUs, it's needed when hard real-time deadlines must be met — braking, engine control, airbag deployment.

**Detailed Expert Answer:**

```
Types of real-time requirements:

HARD REAL-TIME:
  Deadline miss = system failure
  Example: ABS braking ECU — brake force calculation must complete in <1ms
           Airbag ECU — detonation command within 30ms of crash detection
  RTOS: AUTOSAR OS (OSEK), FreeRTOS with static priorities, QNX

SOFT REAL-TIME:
  Deadline miss = degraded performance, not failure
  Example: Infotainment audio buffer — miss causes glitch, not crash
           ADAS camera processing — miss causes late lane warning
  RTOS: Linux PREEMPT_RT, QNX

FIRM REAL-TIME:
  Deadline miss invalidates result but system continues
  Example: GPS coordinate update — stale reading discarded
```

**Automotive RTOS landscape:**

| RTOS | Use Case | Companies |
|------|----------|-----------|
| AUTOSAR OS (OSEK) | Powertrain, chassis, body ECUs | Bosch, Continental, Denso |
| FreeRTOS | Low-cost MCU-based ECUs, IoT-connected | NXP S32K, STM32, TI F2837 |
| QNX | ADAS, infotainment, gateway ECUs | BlackBerry QNX, Renesas R-Car |
| VxWorks | Aerospace/mil crossover, radar | Valeo, TRW |
| Integrity (Green Hills) | Safety-critical, ASIL-D certified | Medical crossover, radar |
| Linux PREEMPT_RT | Telematics, infotainment, Adaptive AUTOSAR | Harman, Panasonic, Continental |

**Decision matrix:**
```
Is it safety-critical (ASIL-B or higher)?
    YES → AUTOSAR OS or certified RTOS (QNX, Integrity)
    NO  → FreeRTOS or Linux
    
Does it need dynamic loading / complex filesystems?
    YES → Linux or QNX
    NO  → FreeRTOS or AUTOSAR OS

Are there <1ms hard deadlines?
    YES → RTOS with preemption (AUTOSAR OS, FreeRTOS SCHED_FIFO)
    NO  → Soft-RT Linux is sufficient
    
Is the MCU < 256KB flash?
    YES → FreeRTOS (minimal footprint: ~5KB)
    NO  → AUTOSAR OS, QNX
```

---

### Q2. Explain FreeRTOS tasks — how do you create them and what happens internally?

**Short Answer:** A FreeRTOS task is a function that runs in an infinite loop. Tasks have a stack, TCB (Task Control Block), and a priority. The scheduler maintains a ready list per priority and runs the highest-priority ready task.

**Detailed Expert Answer:**

```c
#include "FreeRTOS.h"
#include "task.h"
#include "queue.h"

/* Task stack and TCB — static allocation (MISRA-safe, no heap) */
static StaticTask_t   s_can_task_tcb;
static StackType_t    s_can_task_stack[512];  /* 512 × 4 = 2KB stack */

static StaticTask_t   s_ign_task_tcb;
static StackType_t    s_ign_task_stack[256];

/* Task function — must run forever (or delete itself) */
void vCAN_Task(void *pvParameters) {
    (void)pvParameters;
    
    TickType_t xLastWakeTime = xTaskGetTickCount();
    const TickType_t xPeriod = pdMS_TO_TICKS(10);  /* 10ms period */
    
    while (1) {
        /* Process CAN messages */
        CAN_ProcessMessages();
        
        /* Precise periodic execution — accounts for execution time */
        vTaskDelayUntil(&xLastWakeTime, xPeriod);
        /* vTaskDelayUntil is preferred over vTaskDelay for periodic tasks */
        /* vTaskDelay: delay AFTER execution (jitter accumulates) */
        /* vTaskDelayUntil: next wake at fixed interval from last wake (no jitter) */
    }
}

void vIgnition_Task(void *pvParameters) {
    (void)pvParameters;
    
    while (1) {
        /* Wait for ignition event (event group, queue, or semaphore) */
        uint32_t notif;
        xTaskNotifyWait(0, 0xFFFFFFFF, &notif, portMAX_DELAY);
        
        if (notif & EVENT_IGN_ON) {
            System_HandleIgnitionOn();
        }
    }
}

/* Startup: create tasks before starting scheduler */
void main(void) {
    /* Static creation — no heap allocation */
    TaskHandle_t h_can = xTaskCreateStatic(
        vCAN_Task,           /* Task function */
        "CAN_Task",          /* Task name (debug) */
        512,                 /* Stack depth in words */
        NULL,                /* Parameter */
        5,                   /* Priority: 5 (higher = more urgent) */
        s_can_task_stack,    /* Pre-allocated stack */
        &s_can_task_tcb      /* Pre-allocated TCB */
    );
    
    xTaskCreateStatic(vIgnition_Task, "IGN_Task", 256, NULL, 3,
                      s_ign_task_stack, &s_ign_task_tcb);
    
    vTaskStartScheduler();  /* Never returns in normal operation */
    
    /* If we get here: heap exhausted (shouldn't happen with static tasks) */
    for (;;);
}
```

**What happens internally at vTaskStartScheduler():**
```
1. Idle task created (priority 0, runs when no other task is ready)
2. Timer task created (if configUSE_TIMERS=1)
3. SysTick timer configured for tick interrupt (e.g., 1ms)
4. Interrupts enabled
5. First task from ready list dispatched (highest priority)
6. Never returns

On every tick interrupt (SysTick ISR):
  → xTaskIncrementTick() called
  → Any tasks waiting for vTaskDelay become ready if timer expires
  → If higher-priority task became ready: context switch triggered
  → PendSV interrupt pends
  
On PendSV (context switch):
  → Save current task's CPU registers onto its stack
  → scheduler selects next task (highest priority ready)
  → Restore next task's CPU registers from its stack
  → Return to new task's last execution point
```

---

## INTERMEDIATE QUESTIONS

---

### Q3. What is priority inversion? Explain with a real automotive example and the fix.

**Short Answer:** Priority inversion occurs when a high-priority task is blocked waiting for a resource held by a low-priority task, while a medium-priority task preempts the low-priority task — causing the high-priority task to effectively run at low priority.

**Detailed Expert Answer:**

```
Classic priority inversion scenario (ABS ECU):

Tasks:
  H (P=10): ABS braking calculation  — needs CAN mutex for wheel speed
  M (P=5):  Infotainment CAN logger  — CPU intensive, no mutex needed  
  L (P=1):  Odometer update          — holds CAN mutex for EEPROM write

Timeline without priority inheritance:

t=0:  L acquires CAN mutex
t=1:  H preempts L (higher priority), tries to acquire CAN mutex → BLOCKED
t=1:  M becomes ready (higher than L)
t=1:  M preempts L and runs (L still holds mutex, H is blocked waiting for L!)
t=6:  M completes, L resumes
t=7:  L releases CAN mutex
t=7:  H finally runs
  
Result: H (P=10) was blocked for 6 time units while M (P=5) ran!
        ABS calculation delayed → safety hazard
```

**Priority Inheritance (fix):**
```
With priority inheritance (MUTEX_INHERIT):

t=0:  L acquires CAN mutex
t=1:  H tries to acquire CAN mutex → BLOCKED
      Kernel RAISES L's priority to H's priority (10)
t=1:  M tries to preempt L but L now has P=10 > M's P=5 → M waits
t=2:  L finishes work quickly (now at P=10, not preempted by M)
t=2:  L releases mutex → L's priority restored to P=1
t=2:  H acquires mutex, runs
t=3:  H completes, M runs
  
Result: H is only delayed by L's critical section, not by M
```

**FreeRTOS mutex with priority inheritance:**
```c
/* Use SemaphoreCreateMutex (has priority inheritance) */
/* NOT SemaphoreCreateBinary (no inheritance) */

static StaticSemaphore_t s_can_mutex_buf;
SemaphoreHandle_t s_can_mutex;

void init(void) {
    /* xSemaphoreCreateMutexStatic — static allocation, no heap */
    s_can_mutex = xSemaphoreCreateMutexStatic(&s_can_mutex_buf);
}

void L_OdometerTask(void *p) {
    while (1) {
        if (xSemaphoreTake(s_can_mutex, pdMS_TO_TICKS(10)) == pdTRUE) {
            /* CRITICAL SECTION: keep as short as possible! */
            CAN_WriteOdometer(&g_odometer);
            xSemaphoreGive(s_can_mutex);
        }
        vTaskDelay(pdMS_TO_TICKS(1000));
    }
}

void H_ABSTask(void *p) {
    while (1) {
        if (xSemaphoreTake(s_can_mutex, pdMS_TO_TICKS(5)) == pdTRUE) {
            /* Read wheel speeds — time critical */
            CAN_ReadWheelSpeed(&g_wheel_data);
            xSemaphoreGive(s_can_mutex);
            ABS_Calculate();
        }
        vTaskDelay(pdMS_TO_TICKS(10));
    }
}
```

**Deadlock prevention rules:**
```
1. Always acquire mutexes in the same order across all tasks
2. Use timeout with xSemaphoreTake — detect deadlock
3. Minimize critical section length
4. Consider lock-free alternatives (ring buffers, atomic operations)

Deadlock example:
  Task A: takes Mutex1, then tries Mutex2
  Task B: takes Mutex2, then tries Mutex1
  → Both blocked forever = DEADLOCK
  
  Fix: Both acquire in order Mutex1 → Mutex2
```

---

### Q4. How do you use FreeRTOS queues for CAN message processing between an ISR and a task?

**Expert Answer:**
```c
/* CAN ISR → Queue → Processing Task pattern */
/* Decouples ISR from processing work (keep ISR fast) */

#define CAN_QUEUE_DEPTH  32

typedef struct {
    uint32_t  id;
    uint8_t   dlc;
    uint8_t   data[8];
    uint32_t  timestamp_ms;
} CANMessage_t;

static StaticQueue_t   s_can_queue_struct;
static uint8_t         s_can_queue_storage[CAN_QUEUE_DEPTH * sizeof(CANMessage_t)];
static QueueHandle_t   s_can_queue;

void can_init_queue(void) {
    s_can_queue = xQueueCreateStatic(
        CAN_QUEUE_DEPTH,
        sizeof(CANMessage_t),
        s_can_queue_storage,
        &s_can_queue_struct
    );
}

/* CAN Rx ISR — called from hardware interrupt */
/* MUST be fast: just enqueue, never block */
void CAN1_RX_IRQHandler(void) {
    CANMessage_t msg;
    
    /* Read from CAN hardware register */
    msg.id         = CAN1->sFIFOMailBox[0].RIR >> 21;  /* STM32 CAN */
    msg.dlc        = CAN1->sFIFOMailBox[0].RDTR & 0x0FU;
    msg.timestamp_ms = xTaskGetTickCountFromISR();
    
    uint32_t rdlr  = CAN1->sFIFOMailBox[0].RDLR;
    uint32_t rdhr  = CAN1->sFIFOMailBox[0].RDHR;
    msg.data[0] = (uint8_t)(rdlr);
    msg.data[1] = (uint8_t)(rdlr >> 8);
    msg.data[2] = (uint8_t)(rdlr >> 16);
    msg.data[3] = (uint8_t)(rdlr >> 24);
    msg.data[4] = (uint8_t)(rdhr);
    msg.data[5] = (uint8_t)(rdhr >> 8);
    msg.data[6] = (uint8_t)(rdhr >> 16);
    msg.data[7] = (uint8_t)(rdhr >> 24);
    
    CAN1->RF0R |= CAN_RF0R_RFOM0;  /* Release FIFO slot */
    
    /* xQueueSendFromISR — never blocks (ISR context) */
    BaseType_t higher_prio_woken = pdFALSE;
    xQueueSendFromISR(s_can_queue, &msg, &higher_prio_woken);
    
    /* If queue send woke a higher-priority task, yield to it immediately */
    portYIELD_FROM_ISR(higher_prio_woken);
}

/* CAN processing task — runs in task context */
void vCAN_ProcessTask(void *p) {
    CANMessage_t msg;
    
    while (1) {
        /* Block indefinitely until a message arrives */
        if (xQueueReceive(s_can_queue, &msg, portMAX_DELAY) == pdTRUE) {
            /* Process message — can be slow, complex, etc. */
            switch (msg.id) {
            case 0x120: process_vehicle_speed(&msg); break;
            case 0x130: process_engine_rpm(&msg);    break;
            case 0x360: process_gear_status(&msg);   break;
            }
        }
    }
}

/* Queue health monitoring (run in low-priority diagnostics task) */
void check_can_queue_watermark(void) {
    UBaseType_t watermark = uxQueueMessagesWaiting(s_can_queue);
    UBaseType_t spaces    = uxQueueSpacesAvailable(s_can_queue);
    
    if (spaces == 0) {
        /* Queue full — messages being dropped by ISR */
        fault_handler_report(FAULT_CAN_QUEUE_OVERFLOW);
    }
}
```

---

## ADVANCED QUESTIONS

---

### Q5. Explain watchdog integration with FreeRTOS — how to prevent false resets and detect hung tasks.

**Expert Answer:**
```c
/* Watchdog integration pattern — automotive production code */
/* Strategy: each critical task "kicks" its own watchdog token */
/* Main WDG task collects all tokens — only kicks HW watchdog if all received */

#define WDG_TASK_COUNT       4U
#define WDG_HW_TIMEOUT_MS  100U  /* Hardware watchdog timeout */
#define WDG_TASK_PERIOD_MS  20U  /* Token refresh period */

typedef struct {
    const char *name;
    TaskHandle_t handle;
    bool        alive;
} WdgToken_t;

static WdgToken_t s_wdg_tokens[WDG_TASK_COUNT] = {
    { "CAN",       NULL, false },
    { "IGN",       NULL, false },
    { "Diag",      NULL, false },
    { "Telemetry", NULL, false },
};

/* Each monitored task calls this once per cycle */
void wdg_task_kick(uint8_t task_id) {
    if (task_id < WDG_TASK_COUNT) {
        taskENTER_CRITICAL();
        s_wdg_tokens[task_id].alive = true;
        taskEXIT_CRITICAL();
    }
}

/* Watchdog supervisor task — highest priority */
void vWatchdogTask(void *p) {
    TickType_t last_wake = xTaskGetTickCount();
    
    while (1) {
        vTaskDelayUntil(&last_wake, pdMS_TO_TICKS(WDG_TASK_PERIOD_MS));
        
        bool all_alive = true;
        for (uint8_t i = 0; i < WDG_TASK_COUNT; i++) {
            taskENTER_CRITICAL();
            bool alive = s_wdg_tokens[i].alive;
            s_wdg_tokens[i].alive = false;  /* Reset token */
            taskEXIT_CRITICAL();
            
            if (!alive) {
                all_alive = false;
                log_error("WDG: task '%s' not responsive!", s_wdg_tokens[i].name);
                /* Option: trigger controlled shutdown vs hard reset */
            }
        }
        
        if (all_alive) {
            HAL_IWDG_Refresh(&hiwdg);  /* Kick hardware watchdog */
        }
        /* If not all alive: hardware WDG times out → ECU reset */
    }
}
```

---

## PRODUCTION SCENARIO QUESTIONS

---

### Q6. Your FreeRTOS ECU sometimes hangs after 2-3 hours of operation. How do you diagnose?

**Expert Answer:**

"This is one of the most difficult embedded bugs to reproduce and diagnose. I'd approach it systematically:

**Step 1 — Enable FreeRTOS stack overflow detection:**
```c
/* In FreeRTOSConfig.h */
#define configCHECK_FOR_STACK_OVERFLOW  2  /* Method 2: fill + check pattern */

/* Application must implement this hook */
void vApplicationStackOverflowHook(TaskHandle_t xTask, char *pcTaskName) {
    /* Log before reset */
    (void)xTask;
    log_fatal("STACK OVERFLOW in task: %s", pcTaskName);
    system_safe_shutdown();
    while (1);  /* Watchdog will reset */
}
```

**Step 2 — Add runtime stack watermark monitoring:**
```c
void vDiagnosticsTask(void *p) {
    while (1) {
        vTaskDelay(pdMS_TO_TICKS(5000));  /* Every 5 seconds */
        
        TaskStatus_t tasks[16];
        UBaseType_t n = uxTaskGetSystemState(tasks, 16, NULL);
        
        for (UBaseType_t i = 0; i < n; i++) {
            uint32_t min_free = tasks[i].usStackHighWaterMark * 4;  /* bytes */
            if (min_free < 128) {  /* Less than 128 bytes remaining */
                log_warn("LOW STACK: %s, min_free=%u bytes",
                          tasks[i].pcTaskName, min_free);
            }
        }
    }
}
```

**Step 3 — Check for heap exhaustion:**
```c
/* In configASSERT handler and periodically: */
size_t free_heap = xPortGetFreeHeapSize();
size_t min_heap  = xPortGetMinimumEverFreeHeapSize();

if (min_heap < 1024) {
    log_warn("HEAP LOW: min_ever=%u bytes", (uint)min_heap);
}
/* If using pvPortMalloc in tasks (should be avoided): check for NULL returns */
```

**Step 4 — Detect deadlock with timeout-based mutex acquisition:**
```c
/* Change all xSemaphoreTake(mutex, portMAX_DELAY) to: */
if (xSemaphoreTake(s_mutex, pdMS_TO_TICKS(500)) != pdTRUE) {
    log_error("DEADLOCK suspected: %s couldn't acquire mutex in 500ms", 
               pcTaskGetName(NULL));
    /* Dump task states */
    vTaskList(debug_buffer);
    log_debug(debug_buffer);
}
```

**Common root causes for 2-3 hour hangs:**
```
1. Memory fragmentation: pvPortMalloc fragments heap over time
   Fix: use static allocation everywhere (configSUPPORT_STATIC_ALLOCATION=1)

2. Event group / notification miss: task waiting for event never wakes
   Fix: add timeout to all xEventGroupWaitBits() calls

3. Stack overflow in rarely-taken code path:
   Fix: check stack watermarks — a task with 4 bytes free will corrupt on next deep call

4. CAN bus-off causing ISR storm: 1000+ interrupts/sec fills queue, starves other tasks
   Fix: detect bus-off (CAN error counter), disable ISR temporarily, exponential backoff
```

**Production Insight (Continental body ECU, STM32H7):** The 2-3 hour hang was traced to a CAN filter misconfiguration that caused the ECU to receive its own transmitted frames (echo). At high message rate (200 msg/s), the Rx queue filled in 160ms, ISR started blocking, task starvation occurred within 3 hours. Fix: disable CAN loopback via `CAN_FilterActivation_DISABLE` on the self-transmission IDs."

---

## CHEAT SHEET — RTOS

```
FreeRTOS essentials:
  xTaskCreateStatic()      ← Preferred (no heap, MISRA-safe)
  vTaskDelayUntil()        ← Periodic tasks (no jitter drift)
  xQueueSendFromISR()      ← Queue from interrupt (non-blocking)
  portYIELD_FROM_ISR()     ← Yield after ISR queue send
  xSemaphoreCreateMutexStatic() ← Mutex with priority inheritance

Key config (FreeRTOSConfig.h):
  configUSE_PREEMPTION = 1             ← Enable preemption
  configCHECK_FOR_STACK_OVERFLOW = 2  ← Stack overflow detection
  configSUPPORT_STATIC_ALLOCATION = 1 ← No dynamic heap
  configTICK_RATE_HZ = 1000           ← 1ms tick
  configMAX_PRIORITIES = 16           ← Priority levels

Priority inversion:
  Problem: Medium task runs while high waits for low (mutex held by low)
  Fix: Priority inheritance mutex (xSemaphoreCreateMutex)
  Rule: keep critical sections SHORT

ISR rules in FreeRTOS:
  - Only call *FromISR() variants in ISR context
  - Never call blocking functions (xQueueReceive, vTaskDelay)
  - Always use portYIELD_FROM_ISR() if send/give returned high-priority task wake

Watchdog:
  - Hardware WDG: Kicked only if all tasks alive
  - Each task refreshes its token
  - WDG supervisor at HIGHEST priority
  - Never kick WDG unconditionally in main loop (defeats the purpose)

AUTOSAR OS vs FreeRTOS:
  AUTOSAR OS: static configuration, no dynamic create, OSEK-based
  FreeRTOS: dynamic or static, smaller footprint, widely ported
  Both: fixed-priority preemptive scheduling
```
