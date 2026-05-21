# Pointers & References Interview Questions
## Senior Automotive Embedded Engineer — Principal Level

---

## TOPIC OVERVIEW

Pointers are **the most common screening topic** in automotive embedded C/C++ interviews. Bosch, Tata Elxsi, KPIT, LG Electronics Automotive, and Continental will dedicate 15-20 minutes to pointer questions. The depth expected at senior level goes beyond basics into pointer arithmetic on hardware registers, function pointers for callbacks/dispatch tables, and C++ smart pointers.

**Key areas probed:**
- Pointer basics (declaration, dereferencing, address-of)
- Pointer arithmetic and arrays
- const correctness with pointers
- Function pointers and dispatch tables
- Pointer-to-pointer and double pointers
- Void pointers and type punning (with caveats)
- Common pointer bugs (dangling, wild, null dereference)
- C++ smart pointers (unique_ptr, shared_ptr, weak_ptr)
- Pointer in MCU register access (volatile + pointer)
- Pointers in linked lists, queues (embedded data structures)

---

## BEGINNER QUESTIONS

---

### Q1. What is the difference between `int *p`, `int * const p`, `const int *p`, and `const int * const p`?

**Short Answer:** The `const` placement determines whether the pointer itself or the data it points to is constant. In automotive code, `const int *` (read-only data) is used for hardware input registers, and `int * const` (fixed address pointer) for MMIO registers.

**Detailed Expert Answer:**

```c
int value = 42;
int other = 99;

/* 1. int *p — mutable pointer to mutable data */
int *p1 = &value;
*p1 = 10;    /* OK: can modify data */
p1 = &other; /* OK: can change what pointer points to */

/* 2. const int *p — mutable pointer to CONST data (read-only data) */
const int *p2 = &value;
/* *p2 = 10; */ /* ERROR: cannot modify data through this pointer */
p2 = &other;   /* OK: can change what pointer points to */
/* Use case: function parameters where you don't modify the input */

void process_can_frame(const uint8_t *data, uint8_t len) {
    /* data[0] is read-only here — can't accidentally modify input */
    uint16_t speed = (uint16_t)((data[1] << 8) | data[0]);
    (void)speed;
}

/* 3. int * const p — CONST pointer to mutable data (fixed address) */
int * const p3 = &value;
*p3 = 10;    /* OK: can modify data */
/* p3 = &other; */ /* ERROR: cannot change where pointer points */
/* Use case: hardware register pointer — address is fixed */

#define CAN1_BASE 0x40006400UL
volatile uint32_t * const CAN1_MCR = (volatile uint32_t *)(CAN1_BASE + 0x00);
/* CAN1_MCR always points to that register — can't reassign, can modify register */

/* 4. const int * const p — CONST pointer to CONST data */
const int * const p4 = &value;
/* *p4 = 10;   */ /* ERROR: cannot modify data */
/* p4 = &other;*/ /* ERROR: cannot change pointer */
/* Use case: ROM lookup tables accessed through pointer */

static const uint8_t CRC_TABLE[256] = { /* ... */ };
const uint8_t * const crc_table_ptr = CRC_TABLE;
/* crc_table_ptr[i] read-only, pointer fixed */
```

**Automotive hardware register access pattern:**
```c
/* CORRECT: volatile ensures compiler doesn't optimise away register reads/writes */
#define STM32_CAN1_BASE    0x40006400UL
#define STM32_CAN1_MCR     (*(volatile uint32_t *)(STM32_CAN1_BASE + 0x000))
#define STM32_CAN1_MSR     (*(volatile uint32_t *)(STM32_CAN1_BASE + 0x004))
#define STM32_CAN1_TSR     (*(volatile uint32_t *)(STM32_CAN1_BASE + 0x008))

/* Usage: */
STM32_CAN1_MCR |= (1U << 0);   /* Set INRQ bit — request init mode */
while (!(STM32_CAN1_MSR & (1U << 0)));  /* Wait for INAK bit */
/* Without volatile: compiler might read MSR once and loop forever on cached value */
```

---

### Q2. Explain function pointers with a dispatch table for a CAN signal router.

**Short Answer:** Function pointers allow calling functions through a pointer variable, enabling polymorphism in C, runtime dispatch, and lookup tables. In automotive ECUs, dispatch tables replace long switch statements for CAN message routing.

**Detailed Expert Answer:**

```c
/* CAN signal router using function pointer dispatch table */

typedef void (*CANHandler_t)(const uint8_t *data, uint8_t dlc);

/* Individual handlers */
void handle_vehicle_speed(const uint8_t *data, uint8_t dlc) {
    if (dlc < 4U) return;
    uint32_t raw  = ((uint32_t)data[1] << 8) | data[0];
    float speed   = raw * 0.01f;  /* 0.01 km/h per LSB */
    g_vehicle.speed_kmh = speed;
}

void handle_engine_rpm(const uint8_t *data, uint8_t dlc) {
    if (dlc < 4U) return;
    uint16_t raw = ((uint16_t)data[1] << 8) | data[0];
    g_engine.rpm = raw;  /* 1 RPM per LSB */
}

void handle_brake_pressure(const uint8_t *data, uint8_t dlc) {
    if (dlc < 2U) return;
    g_brakes.pressure_bar = data[0] * 2U;  /* 2 bar per LSB */
}

/* Dispatch table — sorted by CAN ID for O(1) or O(log N) lookup */
typedef struct {
    uint32_t      can_id;
    CANHandler_t  handler;
} CANDispatchEntry_t;

static const CANDispatchEntry_t CAN_DISPATCH_TABLE[] = {
    { 0x120, handle_vehicle_speed  },
    { 0x130, handle_engine_rpm     },
    { 0x1A0, handle_brake_pressure },
};
#define TABLE_SIZE (sizeof(CAN_DISPATCH_TABLE) / sizeof(CAN_DISPATCH_TABLE[0]))

/* Router using binary search (table must be sorted) */
void can_route_message(uint32_t id, const uint8_t *data, uint8_t dlc) {
    /* Binary search for O(log N) dispatch */
    uint32_t lo = 0U, hi = TABLE_SIZE;
    
    while (lo < hi) {
        uint32_t mid = lo + (hi - lo) / 2U;
        if (CAN_DISPATCH_TABLE[mid].can_id == id) {
            CAN_DISPATCH_TABLE[mid].handler(data, dlc);
            return;
        } else if (CAN_DISPATCH_TABLE[mid].can_id < id) {
            lo = mid + 1U;
        } else {
            hi = mid;
        }
    }
    /* Unknown CAN ID — log as unhandled */
}
```

**AUTOSAR-style function pointer callbacks:**
```c
/* AUTOSAR ComM notification callback — registered by application */
typedef void (*ComM_NotifT)(uint8_t channel, ComM_ModeType mode);

typedef struct {
    ComM_NotifT on_mode_change;
    ComM_NotifT on_bus_sleep;
} ComM_UserCallbacks_t;

static ComM_UserCallbacks_t s_user_cb = { NULL, NULL };

void ComM_RegisterCallbacks(const ComM_UserCallbacks_t *cb) {
    if (cb != NULL) {
        s_user_cb = *cb;
    }
}

/* Called internally when ComM state changes */
static void ComM_NotifyUser(uint8_t ch, ComM_ModeType mode) {
    if (s_user_cb.on_mode_change != NULL) {
        s_user_cb.on_mode_change(ch, mode);  /* Safe: NULL check first */
    }
}
```

---

## INTERMEDIATE QUESTIONS

---

### Q3. Explain pointer-to-pointer. When is `char **argv` used and where do you see it in embedded?

**Short Answer:** A pointer-to-pointer holds the address of another pointer. Used for: `main(argc, argv)`, modifying a pointer inside a function (output parameter), and linked list node manipulation.

**Detailed Expert Answer:**

```c
/* ===== Modifying caller's pointer via pointer-to-pointer ===== */

typedef struct CANNode {
    uint32_t        id;
    struct CANNode *next;
} CANNode_t;

/* Without **: function gets a COPY of head — caller's head unchanged */
void wrong_insert(CANNode_t *head, uint32_t id) {
    CANNode_t *new = pool_alloc();
    new->id = id;
    new->next = head;
    head = new;  /* Only changes LOCAL copy! Caller's head unchanged */
}

/* With **: function gets address of head — can modify caller's pointer */
void correct_insert(CANNode_t **head, uint32_t id) {
    CANNode_t *new_node = pool_alloc();
    if (new_node == NULL) return;
    new_node->id   = id;
    new_node->next = *head;  /* New node points to old head */
    *head = new_node;        /* Caller's head now points to new node */
}

/* Usage */
CANNode_t *list = NULL;
correct_insert(&list, 0x120);
correct_insert(&list, 0x130);
/* list now: 0x130 → 0x120 → NULL */

/* ===== Automotive use: error output parameter ===== */
bool can_read_signal(uint32_t can_id, float *out_value, const char **out_error) {
    CANFrame frame;
    if (!can_recv(&frame)) {
        if (out_error) *out_error = "CAN timeout";
        return false;
    }
    *out_value = decode_speed_signal(&frame);
    return true;
}

/* Caller */
float speed;
const char *err = NULL;
if (!can_read_signal(0x120, &speed, &err)) {
    log_error("Signal read failed: %s", err ? err : "unknown");
}
```

---

### Q4. What is a dangling pointer and how do you prevent it in automotive code?

**Expert Answer:**
```c
/* ===== Dangling pointer types ===== */

/* Type 1: Pointer to stack variable that went out of scope */
const char *get_ecu_state_name(void) {
    char name[32];  /* Stack variable */
    snprintf(name, sizeof(name), "STATE_%d", g_ecu_state);
    return name;    /* DANGLING! name is destroyed when function returns */
}
/* Fix: use static or pass buffer from caller */
const char *get_ecu_state_name_safe(char *buf, size_t len) {
    snprintf(buf, len, "STATE_%d", g_ecu_state);
    return buf;  /* Caller owns buffer — valid */
}

/* Type 2: Pointer to freed memory */
void process_dtc(void) {
    DTCRecord *dtc = pool_alloc_dtc();
    dtc->code = 0xC0200;
    pool_free_dtc(dtc);
    log_dtc(dtc);  /* DANGLING: dtc freed, pool may have reused block */
}
/* Fix: NULL pointer after free */
pool_free_dtc(dtc);
dtc = NULL;  /* Subsequent use of NULL pointer → crash immediately (detectable) */
             /* vs dangling use → silent corruption (undetectable) */

/* Type 3: Iterator invalidation (C++) */
std::vector<CANFilter> filters = get_filters();
for (auto it = filters.begin(); it != filters.end(); ++it) {
    if (it->matches(frame)) {
        filters.erase(it);  /* UNDEFINED BEHAVIOUR: it is now dangling! */
    }
}
/* Fix: */
filters.erase(
    std::remove_if(filters.begin(), filters.end(),
                   [&](const auto &f) { return f.matches(frame); }),
    filters.end()
);

/* ===== Wild pointer (uninitialised) ===== */
CANMessage_t *msg;     /* Wild pointer — random value */
msg->id = 0x120;       /* UNDEFINED BEHAVIOUR: writes to random address */

/* Fix: always initialise */
CANMessage_t *msg = NULL;
/* Or immediately assign: */
CANMessage_t *msg = pool_alloc_msg();
if (msg == NULL) { /* handle failure */ return; }
```

---

## ADVANCED QUESTIONS

---

### Q5. Explain C++ smart pointers in automotive context. When should you use unique_ptr vs shared_ptr?

**Expert Answer:**
```cpp
/* ===== unique_ptr: single ownership, zero overhead ===== */
/* Use for: most objects where one owner manages lifetime */

#include <memory>

/* Good: ECU manager owns CAN controller */
class ECUManager {
    std::unique_ptr<CANController> m_can;  /* ECUManager exclusively owns CAN */
    
public:
    ECUManager() 
        : m_can(std::make_unique<CANController>("can0")) {}
    
    /* move-only: cannot copy ECUManager (CAN controller shouldn't be shared) */
    ECUManager(const ECUManager&) = delete;
    ECUManager &operator=(const ECUManager&) = delete;
    ECUManager(ECUManager&&) = default;
    ECUManager &operator=(ECUManager&&) = default;
    
    /* Destructor: m_can.~unique_ptr() automatically closes CAN socket */
};

/* Transfer ownership to another function */
std::unique_ptr<OTAPacket> create_ota_packet(const uint8_t *data, size_t len) {
    auto pkt = std::make_unique<OTAPacket>();
    pkt->parse(data, len);
    return pkt;  /* Moved out — caller owns it */
}

void ota_process(std::unique_ptr<OTAPacket> pkt) {
    /* pkt destructs at end of function — automatic cleanup */
    pkt->verify_signature();
    pkt->flash_write();
}

/* ===== shared_ptr: shared ownership with reference counting ===== */
/* Use when: multiple owners genuinely exist simultaneously */
/* Cost: atomic ref count increment/decrement — avoid in tight RT loops */

class VehicleState {
public:
    float speed_kmh;
    float engine_rpm;
};

/* Multiple subsystems reference same state object */
std::shared_ptr<VehicleState> g_state = std::make_shared<VehicleState>();

void analytics_thread(std::shared_ptr<VehicleState> state) {
    /* state ref count = 2: g_state + this local copy */
    /* state stays alive even if analytics takes a long time */
    while (running) {
        auto snap = *state;  /* Snapshot of state */
        upload_telemetry(snap);
    }
    /* state goes out of scope here: ref count drops to 1 */
}

/* ===== weak_ptr: non-owning observation ===== */
/* Use when: you want to observe shared object but not extend its lifetime */
/* Also: break shared_ptr cycles */

class CANListener {
    std::weak_ptr<VehicleState> m_state_obs;  /* Doesn't keep state alive */
    
public:
    void set_state(std::shared_ptr<VehicleState> state) {
        m_state_obs = state;  /* Weak reference */
    }
    
    void on_can_rx(void) {
        auto state = m_state_obs.lock();  /* Try to get strong reference */
        if (state) {
            state->speed_kmh = decode_speed();
        }
        /* If state was destroyed (ECU shutdown), lock() returns nullptr — safe */
    }
};

/* Automotive embedded rules:
   - unique_ptr: preferred everywhere — zero overhead, clear ownership
   - shared_ptr: only when ownership genuinely shared — has atomic ref count cost
   - weak_ptr: observer pattern, break cycles
   - No raw owning pointers (CppCoreGuidelines R.3)
   - prefer make_unique/make_shared over new — exception-safe
*/
```

---

## PRODUCTION SCENARIO QUESTIONS

---

### Q6. A crash report shows PC (program counter) at 0x00000004 on an ARM Cortex-M. How do you diagnose?

**Expert Answer:**

"An address of `0x00000004` on Cortex-M is a null pointer dereference. The CPU loaded a function pointer from address 0 and jumped to `0x00000004` (ARM Thumb adds 1 for odd — null function pointer decoded as `NULL+4`).

**Step 1 — Understand ARM Cortex-M null function pointer:**
```
Function pointer call: BLX Rn
If Rn = 0 (NULL pointer), CPU jumps to address 0
Address 0 in Cortex-M = Vector Table (reset vector, etc.)
The CPU reads the reset handler address and calls it = executes reset handler code
But usually address 0 is flash-mapped → executing some valid instruction at 0x00000004
Or: HardFault at 0x00000000 → PC = 0x00000004 (instruction after fault)
```

**Step 2 — Find the call site (HardFault handler):**
```c
/* Hard fault handler — captures register state at crash */
void HardFault_Handler(void) {
    /* Get faulting PC from exception stack frame */
    register uint32_t lr asm("lr");
    uint32_t *frame;
    
    /* Determine which stack was in use (MSP or PSP) */
    if (lr & 0x4U) {
        asm volatile("MRS %0, PSP" : "=r" (frame));
    } else {
        asm volatile("MRS %0, MSP" : "=r" (frame));
    }
    
    /* Stack frame layout: r0, r1, r2, r3, r12, lr, pc, xpsr */
    uint32_t pc = frame[6];  /* Faulting instruction address */
    uint32_t faulting_lr = frame[5];  /* Return address of faulting caller */
    
    log_fatal("HardFault: PC=0x%08X, LR=0x%08X", pc, faulting_lr);
    /* Use addr2line to find the source line:
       arm-none-eabi-addr2line -e tcu.elf 0xXXXXXXXX */
}
```

**Step 3 — Using addr2line:**
```bash
arm-none-eabi-addr2line -e tcu.elf -f -C 0x08003A7C  # From LR in crash log
# Output:
# can_route_message(unsigned int, unsigned char const*, unsigned char)
# /src/can_handler.c:178

# Line 178:
#   CAN_DISPATCH_TABLE[idx].handler(data, dlc);
#   ^ handler is NULL because table entry for this CAN ID was not initialised
```

**Step 4 — Root cause and fix:**
```c
/* Bug: handler not initialised for ID 0x1B0 (new CAN ID added after release) */
static const CANDispatchEntry_t CAN_DISPATCH_TABLE[] = {
    { 0x120, handle_vehicle_speed  },
    { 0x130, handle_engine_rpm     },
    { 0x1B0, NULL                  },  /* Handler not implemented yet! */
};

/* Fix: NULL check before calling */
void can_route_message(uint32_t id, const uint8_t *data, uint8_t dlc) {
    /* ... binary search ... */
    if (entry->handler != NULL) {
        entry->handler(data, dlc);
    } else {
        log_warn("No handler for CAN ID 0x%03X", id);
        DEM_SetDTC(DTC_CAN_UNHANDLED_MSG);
    }
}
```

**Production Insight (Valeo parking ECU):** Crash was in production for 6 weeks before surfacing because ID 0x1B0 was only sent by a new parking sensor introduced in a PFC (Production Facility Change), not in the test environment. The PC=0x00000004 symptom is diagnostic — it means null function pointer call on ARM."

---

## CHEAT SHEET — Pointers

```
const with pointers (read right to left):
  int *p         → pointer to int (both mutable)
  const int *p   → pointer to const int (data read-only, pointer movable)
  int * const p  → const pointer to int (pointer fixed, data mutable)
  const int * const p → const pointer to const int (both read-only)

Pointer arithmetic:
  int arr[10]; int *p = arr;
  p + 1 → &arr[1] (advances by sizeof(int))
  p[i]  → *(p + i) (exactly equivalent)

Function pointer:
  void (*fp)(int, int)   → pointer to function taking 2 ints
  typedef void (*HandlerT)(int);  → cleaner typedef
  fp = some_function;    → assign (no & needed for functions)
  fp(1, 2);              → call via pointer

Common bugs:
  Dangling: pointer to freed/scoped memory  → NULL after free
  Wild:     uninitialised pointer           → initialise to NULL
  Null deref: dereference NULL              → always NULL-check before use

Smart pointers (C++):
  unique_ptr<T>: single owner, move-only, zero overhead
  shared_ptr<T>: shared owners, ref-counted (atomic), use sparingly
  weak_ptr<T>:   non-owning observer, must lock() before use
  
  make_unique<T>(args) → preferred over new (exception-safe)
  make_shared<T>(args) → preferred over new (one allocation for obj+counter)

Hardware register access:
  volatile uint32_t * const REG = (volatile uint32_t *)0x40006400UL;
  volatile: don't optimise away reads/writes
  const ptr: register address is fixed
```
