# Advanced C Interview Questions
## Automotive Embedded Engineer — Principal Level

---

## TOPIC OVERVIEW

C is the **lingua franca of automotive ECU development**. Every AUTOSAR BSW component, every bootloader, every microcontroller HAL is written in C. Expect 40–60% of a technical round to be pure C at Bosch, Continental, KPIT, and Tata Elxsi.

**Key areas interviewers probe:**
- Pointer arithmetic and undefined behaviour
- Volatile, const, restrict qualifiers
- Bit manipulation and hardware register access
- Memory layout (sections, alignment, padding)
- Embedded-safe coding (no dynamic allocation)
- Preprocessor and compile-time computation
- Interrupt-safe coding patterns

---

## BEGINNER QUESTIONS

---

### Q1. What is the difference between `const int *p`, `int * const p`, and `const int * const p`?

**Short Answer:** The `const` qualifier's position determines whether the pointer itself or the pointed-to value is immutable.

**Detailed Expert Answer:**
```c
const int *p;        // Pointer to const int:  can change p, cannot change *p
int * const p;       // Const pointer to int:  cannot change p, can change *p
const int * const p; // Const pointer to const int: cannot change either
```

In automotive ECU code, this is used to protect hardware register maps:
```c
// ROM-mapped calibration table — pointer fixed, data fixed
const uint16_t * const kCalibTable = (const uint16_t * const)0x08010000U;

// Peripheral register — pointer fixed, register value can change
volatile uint32_t * const kTimerCR = (volatile uint32_t * const)0x40000000U;
```

**Real-Time Industry Example:**
In a TCU CAN driver, the TX buffer address is fixed (`const` pointer) but its contents change per message (`non-const` data). The receive ISR handler takes a `const` pointer to ensure it never accidentally writes to the DMA buffer.

**How ECU uses this:**
- BSW memory drivers use `const *` for read-only NVM data
- AUTOSAR SWC ports use `const *` for input ports to enforce data direction at compile time
- Calibration RAM sections use pointer-to-const to prevent accidental overwrite

**Common Mistakes:**
- Confusing `const int *p` (east const) with `int const *p` — they are identical
- Forgetting that `const` on a local variable is not the same as ROM placement; the linker controls that
- Casting away `const` with `(int*)p` triggers undefined behaviour if the original object was truly const

**Best Practices:**
- Apply const correctness aggressively: MISRA C:2012 Rule 8.13 mandates this
- Use `const` for all function parameters that are not modified
- For hardware registers, always use `volatile` together with `const *`

**Follow-up Questions:**
1. Can you cast `const int *` to `int *`? → Technically yes (C allows it), but it is undefined behaviour if the object was declared `const`. MISRA prohibits this.
2. What is `volatile const`? → A register that changes without software action (read-only status register). The compiler must read it every time but must not write it.

**Whiteboard:**
```
Memory model:
┌──────────────────────────────────────────┐
│  const int *p → [ptr: mutable] → [data: immutable] │
│  int * const p → [ptr: immutable] → [data: mutable]│
│  const int * const p → both immutable               │
└──────────────────────────────────────────┘
```

---

### Q2. Explain `volatile` keyword — when and why you must use it in automotive embedded code.

**Short Answer:** `volatile` tells the compiler the variable can change outside normal program flow — preventing dangerous optimisations that would cache the value in a register.

**Detailed Expert Answer:**
Without `volatile`, the compiler may:
1. Eliminate repeated reads (keep value in a CPU register)
2. Reorder memory accesses (instruction scheduling)
3. Optimise away writes it "knows" are never read back

```c
// WRONG — compiler optimises the loop away
uint32_t *status_reg = (uint32_t*)0x40001000U;
while (*status_reg & 0x01U) { /* wait */ }  // compiled to: if (*status_reg & 1) { while(1); }

// CORRECT
volatile uint32_t *status_reg = (volatile uint32_t*)0x40001000U;
while (*status_reg & 0x01U) { /* wait for HW */ }
```

**Four categories where `volatile` is mandatory in automotive:**

| Category | Example |
|----------|---------|
| Memory-mapped I/O | CAN controller registers, ADC result registers |
| ISR-shared variables | `volatile uint8_t rx_flag;` set in ISR, read in task |
| DMA buffers | Data modified by DMA engine without CPU involvement |
| Setjmp/longjmp | Variables modified between setjmp and longjmp |

```c
// ISR-shared variable pattern — correct
static volatile uint8_t g_can_rx_flag = 0U;

void CAN_RxIRQHandler(void) {
    g_can_rx_flag = 1U;  // ISR writes
}

void Task_ProcessCAN(void) {
    if (g_can_rx_flag != 0U) {     // Task reads — must be volatile
        g_can_rx_flag = 0U;
        ProcessCANMessage();
    }
}
```

**Real-Time Industry Example:**
In a Bosch ECU watchdog driver, the watchdog answer register is `volatile uint32_t * const`. Without `volatile`, the compiler running at `-O2` will see the write to the watchdog trigger register happens in a loop and optimise multiple writes into one — causing the watchdog to expire and reset the ECU.

**Common Mistakes:**
- Using `volatile` for thread synchronisation — volatile does NOT provide atomic access or memory barriers on multicore systems. Use `stdatomic.h` or OS-provided primitives.
- Forgetting `volatile` on DMA destination buffers (silent data corruption — extremely hard to debug)
- Excessive use on normal variables (prevents compiler optimisations, reduces performance)

**MISRA Rule:** MISRA C:2012 Rule 8.3 — volatile objects shall only be accessed through volatile-qualified pointers.

**Follow-up Grilling:**
- Q: "Is `volatile` enough for multicore ECUs?" → No. You need memory barriers (`__DMB()` on ARM Cortex-M/R) + `volatile` together, or C11 atomics.
- Q: "Can you have a `volatile` struct member?" → Yes: `volatile struct { uint32_t status; } hw_regs;` — the volatile propagates to member accesses.

---

### Q3. What is undefined behaviour (UB) in C and give 5 automotive examples where it kills ECUs.

**Short Answer:** UB is any operation that the C standard does not define — the compiler is allowed to assume it never happens, leading to catastrophic code generation.

**Detailed Expert Answer:**

**5 UB categories that have caused real ECU field failures:**

**1. Signed integer overflow**
```c
// UB: signed overflow. Compiler assumes this NEVER happens (optimises out boundary check)
int16_t calc_torque(int16_t base, int16_t delta) {
    int16_t result = base + delta;  // UB if overflows
    if (result < 0) result = 0;     // Compiler MAY ELIMINATE this check!
    return result;
}

// SAFE — use unsigned or check before:
int16_t safe_calc(int16_t base, int16_t delta) {
    int32_t result = (int32_t)base + (int32_t)delta;
    if (result > INT16_MAX) return INT16_MAX;
    if (result < INT16_MIN) return INT16_MIN;
    return (int16_t)result;
}
```

**2. Null pointer dereference**
```c
// ECU crash on first cold boot when NVM not yet initialised
uint8_t ReadVIN(CANDatabase *db) {
    return db->vin[0];  // db is NULL on first boot → hard fault
}
```

**3. Accessing array out of bounds**
```c
uint8_t dtc_buffer[10];
dtc_buffer[dtc_count++] = new_dtc;  // UB when dtc_count reaches 10 — corrupts stack/heap
```

**4. Shift by negative or ≥ bit width**
```c
uint32_t mask = 1U << bit_pos;  // UB if bit_pos >= 32
// Seen in CAN ID masking code — caused random bus errors
```

**5. Type punning via pointer cast (strict aliasing violation)**
```c
// UB: violates strict aliasing — common in protocol parsers
float read_float_from_can(uint8_t *buf) {
    return *(float*)buf;  // UB — aliasing violation
}

// SAFE — use memcpy:
float safe_read_float(const uint8_t *buf) {
    float val;
    memcpy(&val, buf, sizeof(float));
    return val;
}
```

**Production Insight:** Toyota's unintended acceleration investigation (2009-2010) revealed task stack corruption caused by an array overrun — a classic UB scenario. Modern MISRA C:2012 and CERT-C rules are designed to eliminate these patterns.

**Tools to detect UB:**
- Compile-time: `-fsanitize=undefined` (UBSan), Polyspace, Klocwork
- Static analysis: LDRA, Parasoft C++test, PC-lint

---

### Q4. Explain bit manipulation techniques used in automotive ECU register programming.

**Short Answer:** Bit manipulation with masks, shifts, and bitwise operators is the standard way to access hardware peripheral registers without affecting other bits.

**Detailed Expert Answer:**

**Fundamental operations:**
```c
#define REG_BASE    0x40021000UL
#define RCC_AHBENR  (*(volatile uint32_t*)(REG_BASE + 0x14U))

// Set bit (enable GPIOA clock — bit 17)
RCC_AHBENR |= (1UL << 17U);

// Clear bit (disable GPIOA clock)
RCC_AHBENR &= ~(1UL << 17U);

// Toggle bit
RCC_AHBENR ^= (1UL << 17U);

// Read bit
if (RCC_AHBENR & (1UL << 17U)) { /* GPIOA clock enabled */ }

// Set multiple bits — e.g., set CAN bitrate field [15:10]
#define CAN_BTR_BRP_MASK  (0x3FFU << 0U)
#define CAN_BTR_BRP_VALUE (9U)
CAN1->BTR = (CAN1->BTR & ~CAN_BTR_BRP_MASK) | (CAN_BTR_BRP_VALUE & CAN_BTR_BRP_MASK);
```

**Extract a bit field (CAN ID from register):**
```c
// CAN RIR register: bits[31:21] = STID (standard ID)
uint16_t can_id = (uint16_t)((CAN1->sFIFOMailBox[0].RIR >> 21U) & 0x7FFU);
```

**Count set bits (popcount) — used for parity in LIN frames:**
```c
uint8_t popcount(uint8_t val) {
    uint8_t count = 0U;
    while (val) {
        count += val & 1U;
        val >>= 1U;
    }
    return count;
}
// Or: __builtin_popcount(val) on GCC/Clang
```

**Reverse bits — used in CRC computation:**
```c
uint32_t reverse_bits(uint32_t val) {
    uint32_t result = 0U;
    for (uint8_t i = 0U; i < 32U; i++) {
        result = (result << 1U) | (val & 1U);
        val >>= 1U;
    }
    return result;
}
```

**Real-Time Industry Example:**
In a TCU LTE modem driver, the UART status register has bit 5 = RXNE (receive buffer not empty). The ISR checks this bit before reading the data register — avoiding reads from an empty FIFO which would return garbage into the telematics frame parser.

**MISRA compliance:**
- Use `uint8_t`, `uint16_t`, `uint32_t` — never `int` for bitwise operations (MISRA Rule 10.1)
- Always cast shift result back to the appropriate unsigned type
- Use `UL` or `U` suffixes on literals

---

### Q5. What is the difference between `#define` macros and `static inline` functions? Which should you use in automotive ECU code?

**Short Answer:** `static inline` functions are type-safe, respect scope, can be debugged, and are preferred in modern automotive C. Macros are needed only for compile-time constants and conditional compilation.

**Detailed Expert Answer:**

```c
// Macro — no type checking, expands everywhere, can't be stepped in debugger
#define MAX(a, b)  ((a) > (b) ? (a) : (b))

// Problem: MAX(x++, y++) evaluates x++ twice!
int result = MAX(x++, y++);  // x or y incremented TWICE — silent bug

// Static inline — type-safe, debuggable, optimised away by compiler
static inline int32_t max_i32(int32_t a, int32_t b) {
    return (a > b) ? a : b;
}
```

**Comparison table:**

| Feature | `#define` | `static inline` |
|---------|-----------|-----------------|
| Type safety | ❌ None | ✅ Enforced |
| Debuggable | ❌ Expanded away | ✅ Stepped in debugger |
| Scope | ❌ Global | ✅ File-scoped |
| Side-effect safe | ❌ Double evaluation | ✅ Safe |
| Compile-time constant | ✅ Yes | Depends |
| Conditional compilation | ✅ `#ifdef` | ❌ No |
| MISRA preferred | Avoid function-like | ✅ Preferred |

**When macros are still needed in automotive:**
```c
// 1. Compile-time constants (use enum or constexpr in C++ though)
#define CAN_MAX_DLC    8U
#define ECU_SW_VERSION "2.1.0"

// 2. Conditional compilation for target hardware
#ifdef TARGET_STM32H7
  #define CPU_FREQ_HZ 480000000UL
#elif defined TARGET_TC397
  #define CPU_FREQ_HZ 300000000UL
#endif

// 3. Stringification and concatenation
#define ASSERT(cond) do { if(!(cond)) { fault_handler(__FILE__, __LINE__); } } while(0)
```

**Production Insight (Bosch ECU style):**
AUTOSAR MCAL layer uses `static inline` extensively in HAL abstraction. All MCAL register access functions are `static inline` — they compile down to single-instruction register writes with zero call overhead, yet remain type-safe and debuggable.

**Follow-up:** "What does `do { ... } while(0)` buy you in macro definitions?" → It allows the macro to be used as a single statement safely in all contexts, including `if-else` without braces:
```c
// Without do-while: if(err) ASSERT(0); else foo(); → broken
// With do-while:   if(err) { ASSERT(0); } else foo(); → correct
```

---

## INTERMEDIATE QUESTIONS

---

### Q6. Explain `restrict` keyword and its role in automotive DSP and sensor fusion code.

**Short Answer:** `restrict` is a C99 qualifier that tells the compiler two pointers do not alias — enabling aggressive optimisations like auto-vectorisation and loop transformation.

**Detailed Expert Answer:**
```c
// Without restrict — compiler cannot assume src and dst don't overlap
void copy(uint8_t *dst, const uint8_t *src, size_t n) {
    for (size_t i = 0; i < n; i++) dst[i] = src[i];
}

// With restrict — compiler knows they don't overlap → can vectorise with SIMD
void copy_fast(uint8_t * restrict dst, const uint8_t * restrict src, size_t n) {
    for (size_t i = 0; i < n; i++) dst[i] = src[i];
}
```

**Where used in automotive:**

1. **Camera/Radar signal processing** — image convolution kernels on ADAS ECUs (NXP S32G, Renesas R-Car)
2. **Sensor fusion** — Kalman filter matrix multiply in autonomous driving ECUs
3. **CAN message encoding** — `encode_can_payload(uint8_t * restrict buf, const Signal_t * restrict sig)` — the signal and buffer never overlap

```c
// AUTOSAR ComStack style — restrict in signal encoding
void Com_PackSignal(uint8_t * restrict pdu_buf,
                   const Signal_t * restrict signal,
                   uint32_t value) {
    // Compiler can vectorise this knowing buf and signal don't alias
    uint8_t byte_pos = signal->byte_pos;
    uint8_t bit_mask = signal->bit_mask;
    pdu_buf[byte_pos] = (pdu_buf[byte_pos] & ~bit_mask) |
                        ((uint8_t)(value << signal->bit_shift) & bit_mask);
}
```

**Common Mistake:** Passing overlapping buffers to a `restrict`-qualified function is undefined behaviour (even if the function "works"). The compiler is free to reorder or eliminate reads/writes based on the non-alias guarantee.

---

### Q7. What is memory alignment and why does it matter in CAN frame parsing?

**Short Answer:** Alignment refers to data objects being placed at memory addresses that are multiples of their size. Misaligned accesses on ARM Cortex-M and most embedded MCUs cause a HardFault or silent data corruption.

**Detailed Expert Answer:**
```c
// Danger: casting raw byte buffer to struct (misalignment)
typedef struct {
    uint16_t speed;     // expects 2-byte aligned address
    uint32_t timestamp; // expects 4-byte aligned address
    uint8_t  flags;
} CANPayload_t;

uint8_t can_data[8] = {0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08};

// WRONG: can_data+1 is NOT 4-byte aligned — HardFault on Cortex-M3/M4
CANPayload_t *p = (CANPayload_t*)(can_data + 1);
uint32_t ts = p->timestamp;  // Misaligned read → fault!

// CORRECT: use memcpy
CANPayload_t payload;
memcpy(&payload, can_data, sizeof(payload));
```

**Struct padding rules:**
```c
struct Example1 {
    uint8_t  a;     // offset 0
    // 1 byte padding
    uint16_t b;     // offset 2
    uint32_t c;     // offset 4
    uint8_t  d;     // offset 8
    // 3 bytes padding
};  // sizeof = 12

struct Example2 {
    uint32_t c;     // offset 0
    uint16_t b;     // offset 4
    uint8_t  a;     // offset 6
    uint8_t  d;     // offset 7
};  // sizeof = 8 — reordering saves 4 bytes
```

**In automotive CAN parsing:**
```c
// MISRA/AUTOSAR safe approach for CAN signal extraction
uint16_t extract_speed(const uint8_t *can_buf) {
    uint16_t raw;
    memcpy(&raw, &can_buf[0], sizeof(uint16_t));  // safe regardless of alignment
    return __builtin_bswap16(raw);                // swap if big-endian signal
}
```

**Production Insight:** A Continental ADAS ECU field bug was traced to packed struct casting. The struct was declared with `__attribute__((packed))` to match the CAN payload layout. On Cortex-A9 (used in infotainment), aligned access traps were enabled, causing a fault every time the parser ran. Fix: replaced struct casting with explicit byte extraction macros.

---

### Q8. Explain static, extern, and linkage in embedded C — common source of ODR violations in ECU projects.

**Short Answer:**
- `static` at file scope = internal linkage (symbol not visible outside translation unit)
- `static` at function scope = persistent storage across calls
- `extern` = declaration only, definition elsewhere

**Detailed Expert Answer:**
```c
// File: can_driver.c
static uint32_t s_tx_count = 0U;    // internal — not accessible from other files

void CAN_Transmit(CANFrame_t *frame) {
    static uint8_t seq_num = 0U;    // persists across calls — local static
    frame->seq = seq_num++;
    s_tx_count++;
}
```

**Common ECU project ODR (One Definition Rule) violations:**
```c
// header.h — placed in multiple .c files
uint32_t global_timeout = 1000U;  // WRONG: defines symbol in every TU → linker error

// CORRECT: declare in header, define in ONE .c file
// header.h
extern uint32_t g_timeout;  // declaration only

// config.c
uint32_t g_timeout = 1000U;  // single definition
```

**AUTOSAR pattern — STATIC_INLINE for BSW:**
```c
// In AUTOSAR BSW, static + inline together ensure:
// 1. No external linkage (won't collide across modules)
// 2. Inlined at call site (zero overhead)
static inline uint8_t Dio_ReadChannel(Dio_ChannelType id) { ... }
```

**Automotive build system issue:** In large ECU projects (Bosch BOSCH-ETAS, KPIT AUTOSAR stack), multiple teams contributing .c files to the same project. Without `static` on internal helpers, name collisions between teams' private functions cause linker errors that take hours to diagnose.

---

### Q9. How does a C `struct` layout differ from a packed struct in a CAN payload context?

**Short Answer:** Standard structs have compiler-inserted padding for alignment; packed structs eliminate padding, making them match exact byte layouts in CAN frames but introducing misalignment risk.

**Detailed Expert Answer:**
```c
// Standard struct (has padding)
typedef struct {
    uint8_t  dlc;        // offset 0
    // 3 bytes padding
    uint32_t can_id;     // offset 4
    uint8_t  data[8];    // offset 8
} CANFrame_Padded;      // sizeof = 16

// Packed struct (matches over-the-wire layout)
typedef struct __attribute__((packed)) {
    uint8_t  dlc;        // offset 0
    uint32_t can_id;     // offset 1  ← misaligned on 32-bit MCU!
    uint8_t  data[8];    // offset 5
} CANFrame_Packed;      // sizeof = 13
```

**Safe pattern used in AUTOSAR COM:**
```c
// Never cast raw buffer to struct directly
// Instead, use explicit field-by-field copy:
void CAN_ParseFrame(const uint8_t *raw, CANFrame_t *out) {
    out->dlc    = raw[0];
    out->can_id = ((uint32_t)raw[1] << 24U) |
                  ((uint32_t)raw[2] << 16U) |
                  ((uint32_t)raw[3] <<  8U) |
                  ((uint32_t)raw[4]);
    memcpy(out->data, &raw[5], 8U);
}
```

---

## ADVANCED QUESTIONS

---

### Q10. Explain linker scripts for embedded systems — how do you place code in FLASH vs RAM, and why does it matter for automotive bootloaders?

**Short Answer:** A linker script (`.ld` file) defines memory regions and tells the linker where to place each section (`.text`, `.data`, `.bss`, `.rodata`) — critical for bootloaders that need code in specific flash banks and variables in specific RAM regions.

**Detailed Expert Answer:**
```ld
/* Simplified STM32H7 linker script */
MEMORY {
    FLASH   (rx)  : ORIGIN = 0x08000000, LENGTH = 2M
    DTCMRAM (rwx) : ORIGIN = 0x20000000, LENGTH = 128K
    SRAM    (rw)  : ORIGIN = 0x24000000, LENGTH = 512K
}

SECTIONS {
    /* Vector table MUST be at flash start */
    .isr_vector : {
        . = ALIGN(512);    /* Cortex-M vector table alignment */
        KEEP(*(.isr_vector))
        . = ALIGN(4);
    } > FLASH

    /* Code in flash */
    .text : {
        *(.text)
        *(.text.*)
    } > FLASH

    /* Read-only data in flash */
    .rodata : {
        *(.rodata)
        calibration_start = .;
        KEEP(*(.calibration_data))
        calibration_end = .;
    } > FLASH

    /* Initialized data — load address in FLASH, run address in RAM */
    .data : {
        _sdata = .;
        *(.data)
        _edata = .;
    } > SRAM AT > FLASH    /* LMA in FLASH, VMA in SRAM */

    /* Zero-initialized data in RAM */
    .bss : {
        _sbss = .;
        *(.bss)
        *(COMMON)
        _ebss = .;
    } > SRAM

    /* Stack at end of SRAM */
    .stack (NOLOAD) : {
        . = ALIGN(8);
        _stack_start = .;
        . = . + 0x4000;    /* 16KB stack */
        _stack_end = .;
    } > SRAM
}
```

**Startup code that uses these symbols:**
```c
// startup.c — copies .data from FLASH to SRAM, zeros .bss
extern uint32_t _sdata, _edata, _sidata;  // defined by linker script
extern uint32_t _sbss, _ebss;

void Reset_Handler(void) {
    // Copy .data section from FLASH to RAM
    uint32_t *src = &_sidata;
    uint32_t *dst = &_sdata;
    while (dst < &_edata) *dst++ = *src++;

    // Zero .bss section
    uint32_t *bss = &_sbss;
    while (bss < &_ebss) *bss++ = 0U;

    // Call main
    main();
    while(1);  // Should never reach here
}
```

**Automotive bootloader use case:**
Dual-bank flash for safe OTA:
```ld
/* Bootloader linker script */
MEMORY {
    BOOTLOADER (rx) : ORIGIN = 0x08000000, LENGTH = 64K   /* Bank 0 — bootloader */
    APP_BANK_A (rx) : ORIGIN = 0x08010000, LENGTH = 960K  /* Bank 1 — app */
    APP_BANK_B (rx) : ORIGIN = 0x08100000, LENGTH = 960K  /* Bank 2 — OTA target */
    SHARED_RAM (rw) : ORIGIN = 0x20000000, LENGTH = 4K    /* Shared boot flags */
}

SECTIONS {
    .boot_flags (NOLOAD) : {
        *(.boot_flags)
    } > SHARED_RAM
}
```

**Follow-up Grilling:**
- "What is `.text.unlikely`?" → GCC puts cold code (error handlers, infrequently called paths) in `.text.unlikely` so the hot path stays in cache.
- "How do you place a function in a specific flash bank?" → `__attribute__((section(".app_bank_b")))` on the function.

---

### Q11. Write a CRC-32 (ISO-HDLC) implementation in C from scratch, and explain where automotive ECUs use it.

**Short Answer:** CRC-32/ISO-HDLC uses polynomial 0xEDB88320 (reflected 0x04C11DB7), init 0xFFFFFFFF, final XOR 0xFFFFFFFF.

**Detailed Expert Answer:**
```c
#include <stdint.h>
#include <stddef.h>

/* CRC-32/ISO-HDLC — polynomial 0xEDB88320 (bit-reflected 0x04C11DB7) */
/* Same algorithm used by Ethernet FCS, ZIP, PNG */

static uint32_t s_crc32_table[256];
static uint8_t  s_table_initialized = 0U;

static void crc32_init_table(void) {
    for (uint32_t i = 0U; i < 256U; i++) {
        uint32_t crc = i;
        for (uint8_t j = 0U; j < 8U; j++) {
            if (crc & 1U) {
                crc = (crc >> 1U) ^ 0xEDB88320UL;
            } else {
                crc >>= 1U;
            }
        }
        s_crc32_table[i] = crc;
    }
    s_table_initialized = 1U;
}

uint32_t crc32_compute(const uint8_t *data, size_t length) {
    if (!s_table_initialized) crc32_init_table();
    uint32_t crc = 0xFFFFFFFFUL;
    for (size_t i = 0U; i < length; i++) {
        uint8_t idx = (uint8_t)((crc ^ data[i]) & 0xFFU);
        crc = (crc >> 8U) ^ s_crc32_table[idx];
    }
    return crc ^ 0xFFFFFFFFUL;  /* Final XOR */
}

/* File verification — automotive use case for OTA integrity check */
#include <stdio.h>
int verify_firmware_file(const char *path, uint32_t expected_crc) {
    FILE *f = fopen(path, "rb");
    if (!f) return -1;
    uint8_t buf[4096];
    uint32_t crc = 0xFFFFFFFFUL;
    if (!s_table_initialized) crc32_init_table();
    size_t n;
    while ((n = fread(buf, 1U, sizeof(buf), f)) > 0U) {
        for (size_t i = 0U; i < n; i++) {
            crc = (crc >> 8U) ^ s_crc32_table[(uint8_t)((crc ^ buf[i]) & 0xFFU)];
        }
    }
    fclose(f);
    crc ^= 0xFFFFFFFFUL;
    return (crc == expected_crc) ? 0 : -1;
}
```

**Known test vector:** `crc32("123456789") == 0xCBF43926`

**Automotive uses:**
| Use case | Notes |
|----------|-------|
| UDS 0x37 TransferExit | ECU verifies firmware CRC before committing to flash |
| NVM integrity | Each NVM block has a stored CRC — checked on every read |
| AUTOSAR E2E Profile 1/2 | E2E protection for critical signals (steering angle, brake) |
| OTA package integrity | Cloud sends CRC with firmware package |
| Bootloader verification | Bootloader checks application CRC before jump |

---

## PRODUCTION SCENARIO QUESTIONS

---

### Q12. During CAN log analysis, you see random NRC 0x31 errors from the ECU during firmware download. Walk through your complete debugging approach.

**Expert Answer (how to answer like a principal engineer):**

"I'd approach this systematically across five layers:

**Layer 1 — Reproduce and capture**
First, I'd set up Vector CANoe with the diagnostic database and enable the full UDS trace, including ISO-TP frames, not just the service-level view. The 0x31 NRC is `requestOutOfRange` — it means the ECU rejected the request parameters, not a communication error.

**Layer 2 — Analyse the failing request**
I'd look at the specific UDS request that triggers 0x31:
- Service 0x34 (RequestDownload): Check `memoryAddress` and `memorySize` parameters. 0x31 is returned if the address is outside the programmable region or if the size exceeds the bank
- Service 0x36 (TransferData): 0x31 is returned if block sequence counter is wrong or block size exceeds what was negotiated in 0x34

**Layer 3 — Check programming conditions**
```
0x31 can also mean:
- ECU not in Programming Session (0x10 02) — check if session timed out
- Security access (0x27) not completed before download
- ECU internal flash erase not finished (erase routine returned 0x31)
```

**Layer 4 — Cross-reference with ECU calibration**
I'd check the ECU's flash driver spec document:
- Flash segment boundaries (Infineon TC397 has 4 KB pflash pages — addresses must be page-aligned)
- Maximum transfer block size (negotiated in 0x74 MaxNumberOfBlockLength)
- Erase routine ID correctness (0x31 01 FF00 vs 0x31 01 0202)

**Layer 5 — Reproduce with known-good parameters**
I'd use CANoe Diagnostic Feature Set with a known-good ODX/CDD file and compare byte-by-byte with the failing tool's request. 99% of the time, `random 0x31` is a tool configuration issue — wrong memory address format (3-byte vs 4-byte) or wrong block size calculation."

---

### Q13. How would you implement a non-blocking ring buffer in C for a CAN Rx ISR — explain all design decisions.

**Detailed Expert Answer:**
```c
/* Lock-free single-producer single-consumer ring buffer */
/* Producer: CAN Rx ISR  |  Consumer: CAN Processing Task */

#define CAN_RX_BUFFER_SIZE  32U  /* Power of 2 for fast modulo */
#define CAN_RX_BUFFER_MASK  (CAN_RX_BUFFER_SIZE - 1U)

typedef struct {
    uint32_t id;
    uint8_t  dlc;
    uint8_t  data[8];
} CANMsg_t;

typedef struct {
    CANMsg_t buf[CAN_RX_BUFFER_SIZE];
    volatile uint32_t head;  /* Written by ISR */
    volatile uint32_t tail;  /* Written by task */
} CANRxBuffer_t;

static CANRxBuffer_t s_rx_buf;

/* Called from ISR — must be fast, no blocking */
int8_t CAN_ISR_Push(const CANMsg_t *msg) {
    uint32_t next_head = (s_rx_buf.head + 1U) & CAN_RX_BUFFER_MASK;
    if (next_head == s_rx_buf.tail) {
        return -1;  /* Buffer full — drop frame (count loss) */
    }
    s_rx_buf.buf[s_rx_buf.head] = *msg;
    /* Memory barrier before updating head */
    __DMB();  /* ARM Data Memory Barrier */
    s_rx_buf.head = next_head;
    return 0;
}

/* Called from task — non-blocking */
int8_t CAN_Task_Pop(CANMsg_t *msg) {
    if (s_rx_buf.tail == s_rx_buf.head) {
        return -1;  /* Empty */
    }
    *msg = s_rx_buf.buf[s_rx_buf.tail];
    /* Memory barrier before updating tail */
    __DMB();
    s_rx_buf.tail = (s_rx_buf.tail + 1U) & CAN_RX_BUFFER_MASK;
    return 0;
}

uint32_t CAN_GetFillLevel(void) {
    return (s_rx_buf.head - s_rx_buf.tail) & CAN_RX_BUFFER_MASK;
}
```

**Design decisions explained:**

1. **Power-of-2 size + bitmask** → avoids division for modulo (`% N` is slow, `& (N-1)` is one instruction)
2. **Separate head/tail on separate cache lines** → prevents false sharing on dual-core ECUs (Cortex-A/R)
3. **`volatile` on head/tail** → prevents compiler from caching them in registers across the barrier
4. **`__DMB()`** → ARM memory barrier ensures write to buffer completes before head is updated (prevents reader seeing a new head value with stale buffer contents)
5. **Power-of-2 overflow** → head/tail use natural uint32 overflow, bitmask extracts position correctly even across wrap

**What makes this safe (SPSC proof):**
- Only the ISR writes `head`, only the task writes `tail` → no write-write conflict
- Each side reads the other's index once per operation → consistent view guaranteed by DMB

---

## CHEAT SHEET — Advanced C

```
volatile → prevent compiler optimisation on HW registers, ISR-shared vars
const *  → pointer to read-only data (protect HW maps, calibration)
* const  → read-only pointer address (fixed peripheral base)
restrict → no-alias hint → enables SIMD vectorisation
static   → file-local linkage OR persistent local storage
extern   → declaration only — define once in ONE .c file

Alignment:
  alignof(T) → minimum alignment of type T
  __attribute__((aligned(N))) → force alignment to N bytes
  memcpy() → always safe for unaligned access

UB landmines:
  signed overflow, out-of-bounds, uninitialized read,
  strict aliasing violation, null dereference, shift by ≥ width

Bit manipulation:
  Set:    reg |= (1U << n)
  Clear:  reg &= ~(1U << n)
  Toggle: reg ^= (1U << n)
  Read:   (reg >> n) & 1U
  Field:  (reg & MASK) >> SHIFT

CRC-32 test vector: crc32("123456789") = 0xCBF43926
```
