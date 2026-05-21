# Debugging Scenarios Interview Questions
## Senior Automotive Embedded Engineer — Principal Level

---

## TOPIC OVERVIEW

Debugging skill separates senior engineers from mid-level engineers. At Bosch, Continental, Harman, and KPIT, debugging questions are almost always scenario-based: "Here's an error — how do you find the root cause?" You are expected to demonstrate **systematic methodology** (hypothesis → evidence → isolation → fix → verification), knowledge of tools (GDB, OpenOCD, CANalyzer, oscilloscope, Lauterbach), and understanding of the full embedded stack.

**Key debugging areas:**
- Embedded C/C++ debugging (GDB, OpenOCD, Lauterbach T32)
- ARM Cortex-M HardFault analysis (stack frame, CFSR registers)
- CAN protocol debugging (candump, CANalyzer, oscilloscope)
- Memory corruption debugging (AddressSanitizer, valgrind, guard bytes)
- Timing/race condition debugging (ThreadSanitizer, logic analyser)
- Production field debugging (core dumps, logs, ETM tracing)
- AUTOSAR stack debugging (DEM/DTC analysis, ComM state)

---

## FUNDAMENTAL DEBUGGING METHODOLOGY

### Q1. Describe your systematic approach to debugging a complex automotive ECU failure.

**Expert Answer:**

```
Debugging Framework — 7 Steps:

1. REPRODUCE
   - Can you reproduce it? If not, instrument first, debug later
   - Document exact conditions: temperature, firmware version, load, sequence
   - Minimum reproducible case: isolate from other variables

2. OBSERVE
   - What observable symptoms? (ECU reset, CAN silence, DTC, crash, wrong value)
   - What changed recently? (new firmware, new hardware, new DBC)
   - When does it happen? (always, intermittently, after N hours)

3. HYPOTHESISE
   - Generate 3-5 hypotheses ordered by likelihood
   - Never start with the most obscure one
   - Think about: hardware, software, configuration, environment

4. TEST HYPOTHESIS
   - Design a test that DISPROVES the hypothesis (easier than proving)
   - If oscilloscope shows clean signal → not Option C
   - If same crash with simulated input → not real hardware issue

5. ISOLATE
   - Binary search: does it happen in first half of code? Second half?
   - Remove components one by one
   - Add minimal instrumentation

6. FIX
   - Fix root cause, not symptom
   - "Workaround" that masks the bug will resurface at worse time

7. VERIFY + PREVENT
   - Verify fix doesn't introduce regression
   - Add regression test for this exact scenario
   - Add monitoring so it's detected earlier next time
   - Document root cause in system for team knowledge
```

---

## HARD FAULT DEBUGGING

---

### Q2. Your ECU crashes with a HardFault. PC is at 0x08012A44. Walk through the diagnosis.

**Expert Answer:**

```c
/* ===== HardFault Handler — captures full register context ===== */

typedef struct {
    uint32_t r0;
    uint32_t r1;
    uint32_t r2;
    uint32_t r3;
    uint32_t r12;
    uint32_t lr;    /* Link Register at time of fault */
    uint32_t pc;    /* Program Counter = address of faulting instruction */
    uint32_t xpsr;
} ExceptionFrame_t;

void HardFault_Handler(void) {
    register uint32_t lr_reg asm("lr");
    ExceptionFrame_t *frame;
    
    /* Was processor using MSP or PSP? */
    if (lr_reg & 0x4U) {
        asm volatile("MRS %0, PSP" : "=r"(frame));  /* Task stack */
    } else {
        asm volatile("MRS %0, MSP" : "=r"(frame));  /* Handler/main stack */
    }
    
    /* Decode fault registers */
    uint32_t CFSR  = SCB->CFSR;   /* Configurable Fault Status Register */
    uint32_t HFSR  = SCB->HFSR;   /* HardFault Status Register */
    uint32_t MMFAR = SCB->MMFAR;  /* MemManage Fault Address */
    uint32_t BFAR  = SCB->BFAR;   /* BusFault Address */
    
    /* Decode CFSR */
    uint8_t  MMFSR = CFSR & 0xFF;           /* MemManage Fault Status */
    uint8_t  BFSR  = (CFSR >> 8) & 0xFF;   /* BusFault Status */
    uint16_t UFSR  = (CFSR >> 16) & 0xFFFF; /* UsageFault Status */
    
    /* Log everything */
    volatile uint32_t pc = frame->pc;
    volatile uint32_t lr = frame->lr;
    
    /* In production: save to NvM, then reset */
    struct {
        uint32_t pc, lr, r0, cfsr, hfsr, mmfar, bfar;
    } fault_info = { pc, lr, frame->r0, CFSR, HFSR, MMFAR, BFAR };
    
    /* Write to non-volatile region for post-mortem analysis */
    memcpy((void*)FAULT_LOG_NOINIT_ADDR, &fault_info, sizeof(fault_info));
    
    while (1);  /* Watchdog will reset */
}
```

**Interpreting CFSR (most important register):**
```
CFSR = 0x00020000 → UFSR bit 1 set = INVSTATE (invalid state, EPSR.T=0)
  Cause: Jumped to an address with LSB=0 (ARM Thumb requires LSB=1)
  Usually: function pointer to NULL or non-Thumb address
  
CFSR = 0x00000001 → MMFSR bit 0 set = IACCVIOL (instruction access violation)
  Cause: Tried to execute code in a region marked as no-execute (MPU)
  
CFSR = 0x00000082 → BFSR bit 7=1 (BFARVALID) + bit 1=1 (PRECISERR)
  Cause: Precise bus fault. BFAR contains the faulting address.
  Usually: access to invalid peripheral address or reserved memory
  
CFSR = 0x00008200 → UFSR bit 9=1 (DIVBYZERO) + bit 7=1 (STKERR)
  Cause: Integer division by zero
```

**addr2line for PC:**
```bash
# Convert PC address to source line
arm-none-eabi-addr2line -e tcu.elf -f -C 0x08012A44
# Output:
# decode_can_signal(unsigned char const*, unsigned int)
# /home/dev/tcu/src/can_decode.c:245

# Line 245:
# float factor = (signal->max - signal->min) / (float)signal->range;
# If signal->range == 0 → division by zero → DIVBYZERO UsageFault → HardFault
```

---

## MEMORY CORRUPTION DEBUGGING

---

### Q3. Your ECU has a memory corruption bug that appears hours after startup. How do you find it?

**Expert Answer:**

```c
/* Memory corruption detection strategies */

/* ===== Strategy 1: Guard bytes (canary values) ===== */
/* Add known pattern before/after suspected buffer */

#define CANARY_PATTERN  0xDEADBEEFU

typedef struct {
    uint32_t  canary_before;     /* Should always be CANARY_PATTERN */
    uint8_t   can_buffer[256];   /* The actual buffer */
    uint32_t  canary_after;      /* Should always be CANARY_PATTERN */
} GuardedBuffer_t;

static GuardedBuffer_t s_guarded;

void guarded_buffer_init(void) {
    s_guarded.canary_before = CANARY_PATTERN;
    s_guarded.canary_after  = CANARY_PATTERN;
    memset(s_guarded.can_buffer, 0, sizeof(s_guarded.can_buffer));
}

/* Check every 100ms in diagnostics task */
void guarded_buffer_check(void) {
    if (s_guarded.canary_before != CANARY_PATTERN ||
        s_guarded.canary_after  != CANARY_PATTERN) {
        uint32_t before = s_guarded.canary_before;
        uint32_t after  = s_guarded.canary_after;
        log_fatal("CORRUPTION: canary_before=0x%08X, canary_after=0x%08X",
                  before, after);
        /* Save backtrace, reset */
    }
}

/* ===== Strategy 2: AddressSanitizer (test/debug build) ===== */
/* Recompile with -fsanitize=address -fsanitize=undefined */
/* ASan adds red zones around all stack and heap allocations */
/* Any overflow writes to red zone → immediate fault at point of write */

/* Without ASan: overflow writes, detected hours later when canary checked */
/* With ASan:   overflow writes → IMMEDIATE abort with exact location */

/* Example ASan output:
==1234== ERROR: AddressSanitizer: stack-buffer-overflow on address 0x7fff
READ of size 1 at 0x7fff beyond end of 256-byte stack
in decode_can_frame can_decode.c:87
  87:  response[response_len + 1] = 0x00;  ← OFF BY ONE!
  
Shadow bytes around the buggy address:
  0x7fff...10: 00 00 00 00 [f2] f2 f2
  f2 = stack right redzone (written past end of buffer)
*/

/* ===== Strategy 3: Watchpoint (GDB hardware breakpoint on memory write) ===== */
/*  $ gdb tcu.elf                                          */
/*  (gdb) target remote localhost:3333  (OpenOCD/Lauterbach) */
/*  (gdb) watch g_global_variable       (break on write)    */
/*  (gdb) rwatch g_global_variable      (break on read)     */
/*  → GDB breaks exactly when the value is changed          */
/*  (gdb) bt                             (show call stack)  */
/*  → Source line of the corrupting write shown immediately */

/* Cortex-M has 4 hardware watchpoints — use for precise tracking */
```

---

## GDB DEBUGGING

---

### Q4. Walk through a GDB session debugging a TCU crash on an NXP i.MX8 (Linux, production firmware).

**Expert Answer:**

```bash
# ==== GDB Remote Debugging Session ====

# On target (NXP i.MX8, Linux):
# gdbserver :1234 tcu-manager         # Start gdbserver on port 1234
# OR: attach to running process:
# gdbserver :1234 --attach $(pidof tcu-manager)

# On host:
arm-linux-gnueabihf-gdb tcu-manager   # Must have debug symbols

(gdb) set sysroot /path/to/sysroot    # For shared library symbol resolution
(gdb) target remote 192.168.1.50:1234 # Connect to target gdbserver
(gdb) continue                         # Let it run

# ===== When crash occurs =====
# GDB stops with:
# Program received signal SIGSEGV, Segmentation fault.
# 0x0000aaab1234 in CANSignalBus::publish(unsigned int, float)
#    (this=0x0, signal_id=288, value=58.88)

(gdb) bt           # Backtrace — full call stack
# #0  CANSignalBus::publish (this=0x0, ...)  ← this is NULL!
# #1  can_rx_thread (arg=0x...) can_rx.cpp:178
# #2  pthread_start_thread (...)

(gdb) frame 1      # Jump to frame #1 (can_rx.cpp:178)
(gdb) list         # Show source around line 178
# 175: void can_rx_thread(void *arg) {
# 176:     while (running) {
# 177:         auto frame = can_recv(s_fd);
# 178:         g_bus_ptr->publish(frame.id, decode(frame));  ← g_bus_ptr is NULL!

(gdb) p g_bus_ptr  # Check the value
# $1 = (CANSignalBus *) 0x0   ← NULL pointer confirmed

# Find where g_bus_ptr should have been set
(gdb) rwatch g_bus_ptr  # Watchpoint on write to g_bus_ptr
(gdb) run           # Re-run
# Hardware watchpoint 1: g_bus_ptr
# Old value = (CANSignalBus *) 0xaaab5678
# New value = (CANSignalBus *) 0x0
# main() ecu_init.cpp:234
# 234:  g_bus_ptr = nullptr;  ← Deliberately nulled during shutdown, but thread still running!

# Root cause: can_rx_thread not stopped before g_bus_ptr set to nullptr during shutdown
# Fix: signal thread to stop, join thread, then null the pointer
```

---

## PRODUCTION FIELD DEBUGGING

---

### Q5. A customer complains their car's speed doesn't show on the infotainment for 30 seconds after ignition ON. How do you debug remotely?

**Expert Answer:**

"This is a field symptom that I can't reproduce easily. I'd approach it remotely first.

**Step 1 — Instrument the timing path:**
```c
/* Add timestamps to the entire signal flow */
void can_rx_callback(const CANFrame *frame) {
    if (frame->id == 0x120) {  /* Vehicle speed signal */
        uint64_t rx_ts = get_timestamp_us();
        log_debug("SPEED_RX: t=%llu raw=0x%04X", rx_ts, 
                  (uint16_t)((frame->data[1] << 8) | frame->data[0]));
    }
}

void infotainment_update_speed(float speed_kmh) {
    uint64_t ts = get_timestamp_us();
    log_debug("SPEED_DISP: t=%llu speed=%.1f", ts, speed_kmh);
}
```

**Step 2 — Analyse the logs (from field via OTA log upload):**
```
Log analysis shows:
  T+0.0s:  CAN speed signal RX: raw=0x0000 (0 km/h, car stationary)
  T+0.0s:  CAN speed signal RX: raw=0x0000 ... (many times)
  T+30.2s: SPEED_DISP: speed=0.0
  T+31.0s: CAN speed signal RX: raw=0x0B9C (29.08 km/h)
  T+31.0s: SPEED_DISP: speed=29.1

Observation: CAN speed IS received from T=0, but display updates only at T=30.2s
This is NOT a CAN receive issue — it's a display logic issue
```

**Step 3 — Find the 30-second delay:**
```c
/* Investigation shows display has a timeout filter */
void infotainment_speed_filter(float speed_raw) {
    static uint32_t speed_stable_count = 0;
    
    if (fabsf(speed_raw - s_last_speed) < 1.0f) {
        speed_stable_count++;
    } else {
        speed_stable_count = 0;  /* Reset on change */
        s_last_speed = speed_raw;
    }
    
    /* Only display after 300 consistent readings at 10Hz = 30 seconds! */
    if (speed_stable_count >= 300) {
        display_update_speed(speed_raw);
    }
}
/* This filter was meant to prevent jitter but the threshold was wrong: */
/* 300 readings × 100ms interval = 30 seconds — far too conservative */
/* Should be: 5 readings × 100ms = 500ms for stable display */
```

**Fix:**
```c
/* Reduce stable threshold from 300 to 5 */
#define SPEED_STABLE_THRESHOLD  5U  /* Was 300 → 30s, now 5 → 500ms */
```

**Production Insight (Continental infotainment, VW Golf):** Exact scenario from a customer complaint after a firmware update. The developer changed the 10Hz CAN cycle to 100ms (same) but updated the debounce count from 30 to 300 thinking they were changing the debounce window from 3s to 30s, but the cycle was 100ms not 10ms. Result: 30-second delay. Fixed in OTA within 48 hours of root cause identification."

---

## CHEAT SHEET — Debugging

```
HardFault diagnosis (Cortex-M):
  CFSR register:
    Bits [7:0]   = MMFSR (MemManage) — MMFAR has address if MMARVALID set
    Bits [15:8]  = BFSR (Bus Fault) — BFAR has address if BFARVALID set
    Bits [31:16] = UFSR (Usage Fault) — DIVBYZERO(bit9), INVSTATE(bit1)
  
  frame->pc = address of instruction that caused fault
  arm-none-eabi-addr2line -e firmware.elf -f -C 0xXXXXXXXX

GDB remote debugging:
  Target: gdbserver :1234 ./app (or --attach PID)
  Host:   gdb app → target remote host:1234
  
  Useful commands:
    bt            — backtrace (call stack)
    frame N       — switch to stack frame N
    p var         — print variable
    watch var     — break on write to var
    rwatch var    — break on read
    x/16wx addr   — dump 16 words at address
    info registers — all CPU registers
    disassemble   — show assembly around current PC

Memory corruption tools:
  ASan (-fsanitize=address):  catches buffer overflows immediately at crash site
  TSan (-fsanitize=thread):   detects data races
  Valgrind:                   comprehensive but slow (10x), good for Linux
  Guard bytes:                production-safe, check periodically
  GDB watchpoints:            hardware-assisted, Cortex-M has 4

Systematic debugging questions:
  1. Can I reproduce it?
  2. When did it start? What changed?
  3. Is it hardware, software, or configuration?
  4. What do the logs say just before the failure?
  5. Can I narrow it to a subsystem?
  6. What does the hypothesis predict? How do I falsify it?
```
