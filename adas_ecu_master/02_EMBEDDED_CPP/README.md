# 02 — Embedded C++ for ECU Development

> **Context:** AUTOSAR Classic on ARM Cortex-M / PowerPC (MPC5xxx / TDA4VM / S32G)  
> **Constraints:** No heap, no exceptions, no RTTI, deterministic timing, < 1ms task cycles

---

## 2.1 Embedded Constraints vs Desktop C++

| Feature | Desktop / Server | ECU (AUTOSAR Classic) | ECU (AUTOSAR Adaptive) |
|---------|-----------------|----------------------|------------------------|
| Heap (new/malloc) | OK | **FORBIDDEN** | Allowed (limited) |
| std::vector | OK | **FORBIDDEN** (heap) | Allowed |
| Exceptions | OK | **FORBIDDEN** | Allowed |
| RTTI (dynamic_cast) | OK | **FORBIDDEN** | Allowed |
| std::thread | OK | No (use OSEK tasks) | Allowed |
| std::chrono | OK | Use HW timer | OK |
| Float operations | OK | Check FPU availability | OK |
| Recursion | OK | **AVOID** (stack overflow) | Avoid deep recursion |

---

## 2.2 volatile — The Most Misunderstood Keyword

```cpp
// volatile tells the compiler:
//   "Do NOT cache this in a register. Re-read from memory every access."
//   "Do NOT reorder or eliminate these reads/writes."
//
// WHEN to use volatile in ECU code:
//   1. Hardware register pointers
//   2. Variables written by ISR, read by main task (or vice versa)
//   3. Variables written by another core (multi-core ECU)
//
// WHEN NOT to use volatile:
//   volatile is NOT a substitute for memory barriers on multi-core!
//   Use atomic<> or OS primitives for multi-core shared data.

// ✅ CORRECT: Hardware register access
volatile uint32_t* const UART_DR = 
    reinterpret_cast<volatile uint32_t*>(0x40011004U);

// ✅ CORRECT: ISR to main task communication
static volatile bool g_canFrameReceived = false;
static CanFrame      g_receivedFrame    = {};  // ISR writes, task reads

// In ISR (Interrupt Service Routine):
void CAN0_RX_IRQHandler() {
    // Read CAN data register
    g_receivedFrame.data[0] = static_cast<uint8_t>(*UART_DR & 0xFFU);
    g_canFrameReceived = true;  // Signal to main task
}

// In main task (1ms cycle):
void canRxTask() {
    if (g_canFrameReceived) {
        g_canFrameReceived = false;  // Clear flag first (critical section!)
        processCanFrame(g_receivedFrame);
    }
}

// ⚠ PROBLEM with above: race condition!
// Fix with critical section (disable/enable interrupt):
void canRxTaskSafe() {
    __disable_irq();          // Disable interrupts (ARM Cortex-M intrinsic)
    bool received    = g_canFrameReceived;
    CanFrame localFrame = g_receivedFrame;
    g_canFrameReceived = false;
    __enable_irq();           // Re-enable interrupts

    if (received) {
        processCanFrame(localFrame);  // Process with interrupts enabled
    }
}
```

---

## 2.3 Interrupt Service Routines (ISR) — ECU Rules

```cpp
// ISR rules in ECU development:
// Rule 1: Keep ISR SHORT. Move work to task (deferred processing pattern).
// Rule 2: No blocking operations in ISR (no mutex, no sleep, no printf).
// Rule 3: No dynamic allocation in ISR.
// Rule 4: ISR-shared variables must be volatile (or atomic on multi-core).
// Rule 5: ISR must have predictable worst-case execution time (WCET).

// === Deferred Processing Pattern ===
// ISR: receive data → put in buffer → set flag
// Task: check flag → process data from buffer

// ISR-safe ring buffer (single producer: ISR, single consumer: task)
template<typename T, std::size_t Capacity>
class IsrSafeRingBuffer {
public:
    // Called from ISR — must be lock-free, no blocking
    bool pushFromIsr(const T& item) noexcept {
        const std::size_t nextWrite = (writeIdx_ + 1U) & MASK;
        if (nextWrite == readIdx_) { 
            overflowCount_++;
            return false;  // Buffer full — drop data, log overflow
        }
        buffer_[writeIdx_] = item;
        writeIdx_ = nextWrite;
        return true;
    }

    // Called from task (not ISR)
    bool popFromTask(T& outItem) noexcept {
        if (readIdx_ == writeIdx_) { return false; }
        outItem  = buffer_[readIdx_];
        readIdx_ = (readIdx_ + 1U) & MASK;
        return true;
    }

    uint32_t getOverflowCount() const noexcept { return overflowCount_; }

private:
    static constexpr std::size_t MASK     = Capacity - 1U;
    volatile T           buffer_[Capacity] = {};
    volatile std::size_t writeIdx_         = 0U;
    volatile std::size_t readIdx_          = 0U;
    uint32_t             overflowCount_    = 0U;
};

// Global ISR buffer (statically allocated, no heap)
static IsrSafeRingBuffer<CanFrame, 32U> g_canIsrBuffer;

// ISR handler
extern "C" void CAN1_RX0_IRQHandler() {
    CanFrame frame{};
    // Read from CAN peripheral registers (hardware-specific)
    frame.id       = CAN1_RIR0 & 0x1FFFFFFFU;
    frame.dlc      = (CAN1_RDTR0 >> 0U) & 0x0FU;
    frame.data[0U] = (CAN1_RDLR0 >> 0U)  & 0xFFU;
    frame.data[1U] = (CAN1_RDLR0 >> 8U)  & 0xFFU;
    frame.data[2U] = (CAN1_RDLR0 >> 16U) & 0xFFU;
    frame.data[3U] = (CAN1_RDLR0 >> 24U) & 0xFFU;

    g_canIsrBuffer.pushFromIsr(frame);  // Non-blocking, short

    // Release CAN FIFO
    CAN1_RF0R |= (1U << 5U);  // RFOM0 bit
}

// 1ms task: process all frames in buffer
void canProcessTask() {
    CanFrame frame{};
    while (g_canIsrBuffer.popFromTask(frame)) {
        routeCanFrame(frame);
    }
}
```

---

## 2.4 Hardware Timers — ECU Tick Generation

```cpp
// AUTOSAR OS uses hardware timer to generate periodic ticks
// Each "task" runs at a fixed rate (1ms, 5ms, 10ms, 20ms, 100ms)
// This matches the real-time requirements of each function:
//
//  1ms:  CAN RX processing, safety watchdog feed
//  5ms:  Sensor data acquisition, state machine updates
// 10ms:  Control algorithm (ACC, LKA PID)
// 20ms:  Driver assistance decisions
// 100ms: Diagnostic checks, NvM operations

// Simulated RTOS task scheduler (simplified OSEK-style)
struct Task {
    void (*function)(void);    // Task function pointer
    uint32_t periodMs;         // Period in milliseconds
    uint32_t lastRunMs;        // Last execution time
    const char* name;
};

class TaskScheduler {
public:
    static constexpr std::size_t MAX_TASKS = 16U;

    bool registerTask(void (*fn)(void), uint32_t periodMs, const char* name) {
        if (taskCount_ >= MAX_TASKS) { return false; }
        tasks_[taskCount_++] = Task{fn, periodMs, 0U, name};
        return true;
    }

    // Called every 1ms from SysTick ISR
    void tick(uint32_t currentTimeMs) {
        for (std::size_t i = 0U; i < taskCount_; ++i) {
            if ((currentTimeMs - tasks_[i].lastRunMs) >= tasks_[i].periodMs) {
                tasks_[i].function();
                tasks_[i].lastRunMs = currentTimeMs;
            }
        }
    }

private:
    Task        tasks_[MAX_TASKS] = {};
    std::size_t taskCount_        = 0U;
};
```

---

## 2.5 Circular Buffer with DMA — Real ECU UART Logging

```cpp
// Real production pattern: DMA fills circular buffer
// Software reads without knowing DMA write position

class DmaCircularBuffer {
public:
    // Called when DMA triggers "half-transfer" or "full-transfer" interrupt
    // Process new bytes since last read
    void processNewData(uint32_t dmaWritePos) {
        while (readPos_ != dmaWritePos) {
            processLogByte(buffer_[readPos_]);
            readPos_ = (readPos_ + 1U) % BUFFER_SIZE;
        }
    }

    // DMA is configured to write here directly (bypasses CPU)
    uint8_t* getDmaBaseAddr() { return buffer_; }
    uint32_t getDmaBufferSize() const { return BUFFER_SIZE; }

private:
    static constexpr uint32_t BUFFER_SIZE = 256U;
    uint8_t  buffer_[BUFFER_SIZE] = {};
    uint32_t readPos_             = 0U;

    void processLogByte(uint8_t byte) {
        // Parse log protocol (could be AUTOSAR Det or custom)
        // In production: send to UART output or CAN diag message
        (void)byte;
    }
};
```

---

## 2.6 Watchdog — Safety-Critical ECU Requirement

```cpp
// ISO 26262 requirement: hardware watchdog must be fed within timeout
// If CPU hangs (infinite loop, fault), watchdog resets ECU
// MISRA Rule: watchdog feed must be in a monitored path

class WatchdogManager {
public:
    static constexpr uint32_t WDG_TIMEOUT_MS = 100U;
    static constexpr uint32_t WDG_WINDOW_MS  = 50U;   // Windowed WDG: must feed in window

    void init() noexcept {
        // Configure hardware watchdog (MCU-specific)
        // IWDG prescaler + reload value for 100ms timeout
        // In real code: write to IWDG_PR and IWDG_RLR registers
        lastFeedTime_ = 0U;
    }

    // Called from monitored task (e.g., 10ms safety task)
    void feed(uint32_t currentTimeMs) noexcept {
        uint32_t elapsed = currentTimeMs - lastFeedTime_;
        
        // Windowed watchdog: do NOT feed too early (indicates scheduling error)
        if (elapsed >= WDG_WINDOW_MS && elapsed < WDG_TIMEOUT_MS) {
            // Write magic value to hardware IWDG register
            // IWDG_KR = 0xAAAAU;  (reload)
            lastFeedTime_ = currentTimeMs;
        } else if (elapsed >= WDG_TIMEOUT_MS) {
            // We're late — LOG but still feed to avoid reset in production
            // In development: let it reset (catches bugs)
            reportWatchdogLateFeeding();
            lastFeedTime_ = currentTimeMs;
        }
    }

private:
    uint32_t lastFeedTime_ = 0U;
    void reportWatchdogLateFeeding() { /* Log DTC */ }
};
```

---

## 2.7 Interview Questions

```
L1:
  Q: What is the difference between volatile and const in ECU code?
  A: const: value cannot be changed by software. Stored in flash (.rodata).
     volatile: value may change outside software control (hardware or ISR).
     A register can be BOTH: const volatile uint32_t* reg — you cannot write it,
     but must re-read it every access (status register that clears on read).

  Q: Why is recursion dangerous on an ECU?
  A: Recursion uses stack space that grows at runtime. On ECU, stack is fixed (e.g., 4KB).
     Deep recursion → stack overflow → undefined behaviour → potential safety incident.
     MISRA C++ Rule 7-5-4: "Functions shall not call themselves."
     Alternative: iterative algorithm with explicit stack (statically allocated).

  Q: What is a deferred processing pattern?
  A: ISR receives data quickly and stores it in a lock-free buffer.
     Main task processes the buffer data outside ISR context.
     Keeps ISR short (WCET bounded), prevents priority inversion.

L2:
  Q: What is the difference between ISR and OSEK task in AUTOSAR?
  A: ISR (Category 1): directly triggered by hardware interrupt. No OS involvement.
                        Fastest response. Cannot use OS services.
     ISR (Category 2): triggered by hardware, but OS manages it. Can use limited OS services.
     OSEK Task:         Scheduled by OS. Can be periodic or event-triggered.
                        More overhead than ISR but full OS services available.
     Rule: only time-critical handling (< 10μs response) should be in ISR.
           Everything else → OSEK task triggered by event from ISR.

  Q: How do you prevent stack overflow on a multi-tasking ECU?
  A: 1. Static stack size analysis: WCET + worst-case call depth → calculate max stack usage
     2. Stack watermark: fill stack with 0xDEADBEEF at init; measure usage at runtime
     3. MPU stack guard: place a memory protection region at stack limit → fault on overflow
     4. Avoid VLAs (variable length arrays) — stack usage unknown at compile time
     5. MISRA Rule 8-5-2: "Braces shall be used to indicate and match the structure"
        (related: all stack allocations visible at function entry)
```
