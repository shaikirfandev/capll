# 13 — Memory Management in Automotive ECU

> **Constraint:** No heap allocation in safety-critical code (ISO 26262, MISRA C++)  
> **Pattern:** Static allocation, memory pools, stack budgeting

---

## 13.1 ECU Memory Map

```
Flash (Read-Only):
  .text  — executable code
  .rodata — const variables, lookup tables, DBC descriptors
  Size: 512KB – 16MB (AURIX TC3xx: up to 16MB)

RAM (Read-Write):
  .data  — initialised global/static variables (copied from flash at startup)
  .bss   — zero-initialised global/static variables
  .stack — task stacks (statically allocated per task in OSEK)
  .heap  — EMPTY in safety-critical ECUs (or < 4KB for startup only)
  Size: 64KB – 1MB internal SRAM + external SDRAM (domain controllers)

Tightly Coupled Memory (AURIX DSPR/PSPR):
  DSPR: Data Scratch-Pad RAM — fast, non-cached, used for critical real-time data
  PSPR: Program Scratch-Pad RAM — place ISR handlers here for single-cycle fetch
```

---

## 13.2 Why No Dynamic Allocation?

```
Forbidden in automotive safety code:
  1. Fragmentation: heap fragments over time → malloc() can fail non-deterministically
  2. Non-deterministic timing: malloc() has variable execution time (violates WCET)
  3. No standard heap in OSEK/AUTOSAR OS
  4. MISRA C++ Rule 18-4-1: "Dynamic heap memory allocation shall not be used"
  5. ISO 26262: heap faults are hard to detect without MPU (dangling pointers, overflow)

Allowed alternatives:
  - Static global / local static arrays
  - Stack allocation (predictable, auto-freed)
  - Memory pool (fixed-block allocator): deterministic, O(1) alloc/free
  - std::array, std::span instead of std::vector
  - Custom StaticVector<T,N> template (pre-allocated storage, dynamic-like API)
```

---

## 13.3 Fixed-Block Memory Pool

```cpp
/**
 * MemoryPool<T, N>:
 *   - N fixed-size blocks of type T
 *   - Allocate/free in O(1)
 *   - No fragmentation (all blocks same size)
 *   - Thread-safe with spinlock (or ISR-disabled allocate/free)
 */
template <typename T, std::size_t N>
class MemoryPool {
public:
    T* allocate() noexcept {
        for (std::size_t i = 0U; i < N; ++i) {
            if (!used_[i]) {
                used_[i] = true;
                return reinterpret_cast<T*>(&blocks_[i]);
            }
        }
        return nullptr;  // Pool exhausted — log diagnostic
    }

    void free(T* ptr) noexcept {
        for (std::size_t i = 0U; i < N; ++i) {
            if (reinterpret_cast<T*>(&blocks_[i]) == ptr) {
                used_[i] = false;
                return;
            }
        }
        // Invalid pointer — assert / DEM log in production
    }

    std::size_t available() const noexcept {
        std::size_t count = 0U;
        for (std::size_t i = 0U; i < N; ++i) {
            if (!used_[i]) { ++count; }
        }
        return count;
    }

private:
    alignas(T) unsigned char blocks_[N][sizeof(T)] = {};
    bool used_[N] = {};
};
```

---

## 13.4 Stack Analysis

```
Each OSEK task has a statically configured stack size (OIL file):
  TASK LKA_10ms {
      STACK_SIZE = 1024;   /* 1 KB */
  };

Stack sizing methodology:
  1. Worst-case call depth: trace deepest function call chain in task
  2. Each stack frame = local variables + return address + saved registers
  3. Interrupt nesting: ISR can preempt any task → add ISR stack overhead
  4. Tool: TASKING/HIGHTECH compiler generates stack usage report per function
  5. Safety margin: 20% overhead

Stack overflow detection methods:
  A. Paint pattern: fill stack with 0xDEADBEEF at startup
     Background task checks watermark: how much of pattern was overwritten
     → actual max stack depth measurement
  
  B. MPU guard page: configure MPU region below stack as read-only
     Stack overflow → immediate MPU fault → hard reset (no silent corruption)
  
  C. AUTOSAR OS stack monitoring:
     TerminateTask() checks if stack pattern is intact
     Calls ErrorHook(E_OS_STACKFAULT) on violation

Typical ADAS ECU stack sizes:
  LKA task:        1-2KB (simple PID, minimal local data)
  Sensor fusion:   4-8KB (large arrays for Kalman matrices)
  Diagnostics:     8KB  (UDS buffer, diagnostic data)
  CAN handler:     512B  (ISR-like, minimal work)
```

---

## 13.5 MPU Configuration

```
ARM Cortex-M MPU: 8-16 configurable regions
Typical automotive configuration:

  Region 0: Flash — Read + Execute, no Write
  Region 1: Global RAM (.data/.bss) — Read + Write, no Execute
  Region 2: Task A stack — Read + Write, no Execute (size = stack_size)
  Region 3: Task B stack — Read + Write, no Execute
  Region 4: Shared memory ring buffer — Read + Write (explicit shared)
  Region 5: Peripheral registers — Read + Write, Device memory (non-cacheable)
  Region 6: Guard below stack A — No access (trap stack overflow)
  Region 7: Default: No access (trap null pointer dereference)

AUTOSAR OS SC3/SC4 uses MPU for application isolation:
  Each OS-Application has its own memory partition.
  Task context switch = MPU reconfiguration.
  Task A cannot read/write Task B's stack → freedom from interference (ISO 26262).
```

---

## 13.6 Interview Questions

```
L1:
  Q: Why is heap allocation forbidden in AUTOSAR safety code?
  A: Three main reasons:
     1. Non-determinism: malloc() timing varies by heap state — violates WCET 
        analysis required by ISO 26262.
     2. Fragmentation: long-running ECU may exhaust heap non-deterministically.
     3. MISRA Rule 18-4-1: explicitly forbids dynamic heap memory.
     Alternative: static arrays, memory pools (fixed-size blocks), stack allocation.

  Q: What is the difference between .data and .bss sections?
  A: .data: statically-initialised variables (initial value != 0).
       float pidKp = 0.8F;  → stored in .data (initial value 0.8 is in flash)
       At startup: C runtime copies .data initial values from flash → RAM.
     .bss: zero-initialised variables (initial value == 0 or not specified).
       static int counter;  → in .bss (no flash storage needed, just zero-fill RAM)
       At startup: C runtime memsets .bss region to 0.
     Optimisation: .bss in flash uses zero bytes (just size metadata). .data
     requires flash storage for initial values → prefer .bss where possible.

L2:
  Q: How do you size a task's stack in an OSEK system?
  A: Step 1: Use compiler stack usage report (GCC: -fstack-usage, TASKING: reports .su file)
     Step 2: Sum all function stack frames in worst-case call chain
     Step 3: Add interrupt nesting overhead (ISR stack used on same core in OSEK)
     Step 4: Add 20% safety margin
     Step 5: Measure at runtime: paint with 0xDEADBEEF, run test cases, measure watermark
     Step 6: Verify no stack overflow in Hardware test (MPU guard page will catch violations)
     
     Rule of thumb: 1KB for simple feature task, 4-8KB for sensor fusion with matrix ops.

L3:
  Q: How does AUTOSAR OS SC4 enforce memory protection between applications?
  A: OS Scalability Class 4 (SC4) = SC3 (memory protection) + SC1 (timing protection):
     Memory protection: MPU configured per OS-Application at task switch.
     Each OsApplication has an OsApplicationTrusted attribute.
     Non-trusted applications can only access own RAM + explicitly shared data.
     Trusted applications can call OS services directly.
     
     Practical example: LKA SWC (safety: ASIL C) and Radio SWC (QM) on same ECU.
     SC4 prevents Radio SWC from corrupting LKA RAM:
     - Radio runs in OsApplication "QM_App" — MPU blocks it from touching LKA stack
     - LKA runs in OsApplication "Safety_App" — MPU blocks it from touching Radio peripherals
     
     Timing protection: OS can terminate a task if it exceeds its configured execution budget.
     Prevents runaway QM task from starving safety-critical LKA task.
```
