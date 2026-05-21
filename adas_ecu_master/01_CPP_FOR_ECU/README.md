# 01 — Modern C++ for ECU Development

> **Target:** Use C++ correctly in resource-constrained automotive ECUs  
> **Standards:** MISRA C++:2008, AUTOSAR C++14, ISO 26262  
> **No STL dynamic allocation. No exceptions. No RTTI.** These are disabled on most automotive ECUs.

---

## 1.1 Memory Layout — What Every ECU Engineer Must Know

```
ECU Memory Map (typical ARM Cortex-M microcontroller):

0x0000_0000 ──── FLASH (read-only, ~1–4MB)
                  - .text section   (compiled code)
                  - .rodata section (const strings, lookup tables)
                  - Interrupt vector table
                  
0x2000_0000 ──── SRAM (~256KB–512KB)
                  - .data section   (initialised global variables — copied from flash at startup)
                  - .bss  section   (zero-initialised globals)
                  - Stack           (grows downward, typically 4–16KB per task)
                  - Heap            (grows upward — AVOID on ECU, use static pools)

Key rule: In AUTOSAR/safety-critical ECU code, heap allocation (new/malloc) is FORBIDDEN.
         All memory must be determined at compile time.
```

---

## 1.2 Pointers vs References in ECU Code

```cpp
// === AUTOMOTIVE CONTEXT: Sensor data pipeline ===

// BAD: raw pointer with no ownership clarity
void processCameraFrame(uint8_t* frame) {
    // Who owns frame? Can it be null? Size unknown.
}

// GOOD: Reference — caller owns it, cannot be null
void processCameraFrame(const CameraFrame& frame) {
    // Cannot be null. Ownership clear. Read-only.
}

// GOOD: Raw pointer when null IS a valid state (e.g., optional sensor)
void processCameraFrame(const CameraFrame* frame) {
    if (frame == nullptr) { return; }  // sensor not present
    // process
}
```

### Pointer Arithmetic — ECU Register Access

```cpp
// Accessing ECU hardware registers via pointer arithmetic
// Common in MCAL (Microcontroller Abstraction Layer)

// CAN controller base address (from MCU datasheet)
static constexpr uintptr_t CAN0_BASE_ADDR = 0x40024000U;

// Register offsets (from datasheet)
static constexpr uint32_t CAN_MCR_OFFSET  = 0x000U;   // Master Control Register
static constexpr uint32_t CAN_MSR_OFFSET  = 0x004U;   // Master Status Register
static constexpr uint32_t CAN_TSR_OFFSET  = 0x008U;   // Transmit Status Register
static constexpr uint32_t CAN_TI0R_OFFSET = 0x180U;   // TX mailbox 0 identifier

// Volatile pointer — tells compiler: DO NOT optimise out this read/write
// Hardware register can change between reads without compiler knowing
volatile uint32_t* const CAN_MCR = 
    reinterpret_cast<volatile uint32_t*>(CAN0_BASE_ADDR + CAN_MCR_OFFSET);

void initCAN0() {
    // Request initialisation mode
    *CAN_MCR |= (1U << 0U);   // INRQ bit

    // Wait until hardware confirms init mode
    volatile uint32_t timeout = 1000U;
    while ((*(reinterpret_cast<volatile uint32_t*>(CAN0_BASE_ADDR + CAN_MSR_OFFSET))
            & (1U << 0U)) == 0U) {
        if (--timeout == 0U) { 
            // Handle timeout — safety reaction
            reportEcuError(EcuErrorCode::CAN_INIT_TIMEOUT);
            return;
        }
    }
}
```

---

## 1.3 RAII — The Most Important Pattern for ECU Code

```cpp
// RAII = Resource Acquisition Is Initialisation
// In ECU: critical sections, mutex locks, hardware resources
// When the object goes out of scope, the resource is ALWAYS released
// Even on early return. Even on exception (though exceptions are disabled on ECU).

// === AUTOMOTIVE CONTEXT: CAN TX mailbox management ===

class CanMailboxLock {
public:
    explicit CanMailboxLock(CanMailboxId id) : mailbox_id_(id) {
        acquireMailbox(mailbox_id_);  // Acquire in constructor
    }

    ~CanMailboxLock() {
        releaseMailbox(mailbox_id_);  // Release in destructor — GUARANTEED
    }

    // Non-copyable — a mailbox lock cannot be duplicated
    CanMailboxLock(const CanMailboxLock&)            = delete;
    CanMailboxLock& operator=(const CanMailboxLock&) = delete;

    // Movable — ownership can be transferred
    CanMailboxLock(CanMailboxLock&& other) noexcept : mailbox_id_(other.mailbox_id_) {
        other.mailbox_id_ = CanMailboxId::INVALID;
    }

private:
    CanMailboxId mailbox_id_;
};

// Usage: mailbox is ALWAYS released even on early return
bool sendCanFrame(const CanFrame& frame) {
    CanMailboxLock lock(CanMailboxId::TX0);   // Acquired here
    
    if (!isCanBusActive()) { 
        return false;   // lock destructor called here → mailbox released
    }
    
    loadFrameToMailbox(frame, CanMailboxId::TX0);
    triggerTransmit(CanMailboxId::TX0);
    return true;
    // lock destructor called here → mailbox released
}
```

---

## 1.4 OOP, Polymorphism and Virtual Functions — ECU Constraints

```cpp
// Virtual dispatch has a cost: vtable lookup (~3-5 ns)
// On ECU with 1ms task cycle and 100 objects: measurable overhead
// Rule: use virtual only at architecture boundaries (abstract interfaces)
// Never in tight inner loops (e.g., sensor data filtering running at 1kHz)

// === Pattern: Abstract Sensor Interface ===
// Used in AUTOSAR SWC layer

class ISensor {
public:
    virtual ~ISensor() = default;

    // Pure virtual — must be implemented by each sensor type
    virtual bool init()                          = 0;
    virtual SensorStatus getStatus() const       = 0;
    virtual void update()                        = 0;  // Called every task cycle
    virtual float getLatestReading() const       = 0;

    // Non-virtual base behaviour (concrete method in abstract class)
    bool isHealthy() const { 
        return getStatus() == SensorStatus::OK; 
    }
};

class RadarSensor : public ISensor {
public:
    bool init() override;
    SensorStatus getStatus() const override { return status_; }
    void update() override;
    float getLatestReading() const override { return distance_m_; }

private:
    SensorStatus status_   = SensorStatus::UNINITIALIZED;
    float        distance_m_ = 0.0F;
    uint32_t     failCount_  = 0U;
};

class CameraSensor : public ISensor {
public:
    bool init() override;
    SensorStatus getStatus() const override { return status_; }
    void update() override;
    float getLatestReading() const override { return laneOffsetM_; }

private:
    SensorStatus status_    = SensorStatus::UNINITIALIZED;
    float        laneOffsetM_ = 0.0F;
};

// ECU sensor manager: polymorphic but statically allocated
class SensorManager {
public:
    static constexpr std::size_t MAX_SENSORS = 8U;

    void registerSensor(ISensor& sensor) {
        if (sensorCount_ < MAX_SENSORS) {
            sensors_[sensorCount_++] = &sensor;  // Store pointer (no heap)
        }
    }

    void updateAll() {
        for (std::size_t i = 0U; i < sensorCount_; ++i) {
            if (sensors_[i] != nullptr) {
                sensors_[i]->update();
            }
        }
    }

private:
    ISensor*    sensors_[MAX_SENSORS] = {};
    std::size_t sensorCount_          = 0U;
};
```

---

## 1.5 Templates in ECU Code

```cpp
// Templates generate code at compile time: zero runtime overhead
// Ideal for: type-safe containers, compile-time constants, policy-based design

// === ECU Static Ring Buffer (no heap, fixed capacity) ===
template<typename T, std::size_t Capacity>
class StaticRingBuffer {
    static_assert(Capacity > 0U, "Capacity must be > 0");
    static_assert((Capacity & (Capacity - 1U)) == 0U, 
                  "Capacity must be power of 2 for efficient modulo");

public:
    bool push(const T& item) noexcept {
        if (isFull()) { return false; }
        buffer_[writeIdx_ & MASK] = item;
        ++writeIdx_;
        return true;
    }

    bool pop(T& item) noexcept {
        if (isEmpty()) { return false; }
        item = buffer_[readIdx_ & MASK];
        ++readIdx_;
        return true;
    }

    bool isEmpty() const noexcept { return writeIdx_ == readIdx_; }
    bool isFull()  const noexcept { return (writeIdx_ - readIdx_) == Capacity; }
    std::size_t size() const noexcept { return writeIdx_ - readIdx_; }

private:
    static constexpr std::size_t MASK = Capacity - 1U;
    T           buffer_[Capacity]     = {};
    std::size_t writeIdx_             = 0U;
    std::size_t readIdx_              = 0U;
};

// Usage in ECU:
StaticRingBuffer<CanFrame, 64U>    canRxBuffer;   // CAN receive queue
StaticRingBuffer<SensorSample, 16U> radarSamples; // Radar sample history

// === Compile-time lookup table using constexpr ===
// Faster than runtime calculation; all in flash (read-only)
constexpr std::array<float, 256U> generateSinTable() {
    std::array<float, 256U> table{};
    for (std::size_t i = 0U; i < 256U; ++i) {
        table[i] = static_cast<float>(
            std::sin(static_cast<double>(i) * 3.14159265358979323846 / 128.0)
        );
    }
    return table;
}
constexpr auto SIN_TABLE = generateSinTable();
// Entire table in .rodata section — zero runtime cost
```

---

## 1.6 Smart Pointers — ECU Restrictions

```cpp
// On standard Linux/PC: use std::unique_ptr, std::shared_ptr freely
// On AUTOSAR/safety ECU:
//   - std::shared_ptr:  FORBIDDEN (uses heap + atomic ref count)
//   - std::unique_ptr:  Allowed IF no custom deleter + no dynamic allocation
//   - Raw pointers:     Used when pointing to statically allocated objects

// === AUTOSAR-safe ownership pattern ===
// Simulate unique ownership without heap

// Static allocation pool
class RadarSensorPool {
public:
    static RadarSensor* acquire() {
        for (auto& slot : pool_) {
            if (!slot.inUse) {
                slot.inUse = true;
                return &slot.sensor;
            }
        }
        return nullptr;  // Pool exhausted — handle as safety reaction
    }

    static void release(RadarSensor* p) {
        for (auto& slot : pool_) {
            if (&slot.sensor == p) {
                slot = {};  // Zero-init = release slot
                return;
            }
        }
    }

private:
    struct Slot {
        RadarSensor sensor;
        bool        inUse = false;
    };
    static constexpr std::size_t POOL_SIZE = 4U;
    static Slot pool_[POOL_SIZE];
};

// If you ARE on Linux-based ADAS ECU (AUTOSAR Adaptive):
// unique_ptr is fully acceptable
auto radarSensor = std::make_unique<RadarSensor>();  // OK on Adaptive AUTOSAR
```

---

## 1.7 enum class — Replace #define in Automotive Code

```cpp
// BAD (C-style, no type safety):
#define SENSOR_OK    0
#define SENSOR_ERROR 1
#define SENSOR_TIMEOUT 2
// Problem: SENSOR_OK == 0 silently compares to any integer

// GOOD (C++11 enum class, strongly typed):
enum class SensorStatus : uint8_t {
    UNINITIALIZED = 0U,
    OK            = 1U,
    ERROR         = 2U,
    TIMEOUT       = 3U,
    NOT_PRESENT   = 4U,
};

// GOOD: ADAS system states
enum class AdasSystemState : uint8_t {
    INACTIVE      = 0U,   // System off
    STANDBY       = 1U,   // Initialised, waiting for conditions
    ACTIVE        = 2U,   // Feature active (e.g., LKA controlling steering)
    DEGRADED      = 3U,   // Partial functionality (sensor degraded)
    FAULT         = 4U,   // Safety reaction: feature disabled, DTC logged
    OVERRIDE      = 5U,   // Driver override active
};

// Usage: type-safe, readable
void onStateChange(AdasSystemState newState) {
    switch (newState) {
    case AdasSystemState::ACTIVE:
        enableSteeringTorque();
        break;
    case AdasSystemState::FAULT:
        disableSteeringTorque();
        logDiagnosticTroubleCode(DtcId::LKA_SYSTEM_FAULT);
        break;
    default:
        break;
    }
}
```

---

## 1.8 Move Semantics in ECU (AUTOSAR Adaptive)

```cpp
// On AUTOSAR Adaptive (Linux-based), move semantics reduce copies
// Critical for: large sensor data buffers, image frames, point clouds

class LidarPointCloud {
public:
    explicit LidarPointCloud(std::size_t numPoints)
        : points_(numPoints) {}  // vector OK on Adaptive AUTOSAR

    // Copy: expensive (copies all points)
    LidarPointCloud(const LidarPointCloud&) = default;

    // Move: transfers ownership, O(1)
    LidarPointCloud(LidarPointCloud&&) noexcept = default;
    LidarPointCloud& operator=(LidarPointCloud&&) noexcept = default;

    std::vector<Point3D>& getPoints() { return points_; }

private:
    std::vector<Point3D> points_;
};

// Function returns large object — move semantics (NRVO / explicit move)
LidarPointCloud parseLidarFrame(const RawLidarData& raw) {
    LidarPointCloud cloud(raw.numPoints);
    for (std::size_t i = 0U; i < raw.numPoints; ++i) {
        cloud.getPoints()[i] = decodePoint(raw.data[i]);
    }
    return cloud;  // NRVO: no copy, no move — compiler eliminates temporary
}

// Caller: no copies
LidarPointCloud cloud = parseLidarFrame(rawData);  // Zero-copy thanks to NRVO
```

---

## 1.9 Thread Safety — Multi-Core ECU

```cpp
// Modern ADAS ECUs: multi-core (e.g., Renesas R-Car, NXP S32G, TDA4VM)
// Tasks on different cores: camera processing core vs CAN communication core
// Shared data requires protection

#include <mutex>   // AUTOSAR Adaptive (Linux)
#include <atomic>

// Pattern 1: atomic for simple shared values (lock-free, fast)
std::atomic<float> g_vehicleSpeed_mps{0.0F};    // Written by speed sensor task
                                                  // Read by LKA, ACC task

// Task A (CAN Rx, 10ms cycle):
void canRxTask() {
    float speed = parseSpeedSignal(canFrame);
    g_vehicleSpeed_mps.store(speed, std::memory_order_release);
}

// Task B (LKA, 20ms cycle):
void lkaTask() {
    float speed = g_vehicleSpeed_mps.load(std::memory_order_acquire);
    // Use speed safely
}

// Pattern 2: mutex for complex shared data structures
std::mutex          g_sensorDataMutex;
SensorFusionOutput  g_fusedData;

void sensorFusionTask() {
    SensorFusionOutput newData = computeFusion();
    {
        std::lock_guard<std::mutex> lock(g_sensorDataMutex);
        g_fusedData = newData;
    }  // lock released here (RAII)
}
```

---

## 1.10 Interview Questions — C++ for ECU

```
L1 (Junior):
  Q: Why is heap allocation (new/malloc) forbidden in AUTOSAR Classic?
  A: Heap allocation is non-deterministic in timing (can block for unknown duration),
     can lead to fragmentation over time (ECU runs for years), and is difficult to
     analyse statically for worst-case execution time (WCET). AUTOSAR Classic mandates
     static memory allocation so all memory usage is determined at compile time.

  Q: What is volatile in C++? When do you use it in ECU code?
  A: volatile tells the compiler that a variable can change without the program 
     modifying it (e.g., a hardware register changed by peripheral, or a variable
     written by an ISR). Without volatile, the compiler may optimise reads away
     (cache in register). In ECU: all hardware register pointers must be volatile.
     Variables shared between ISR and main task must be volatile + atomic.

  Q: What is RAII and why is it critical in ECU code?
  A: RAII binds resource lifetime to object lifetime. Constructor acquires, destructor
     releases. In ECU: critical sections, mutex locks, hardware resources. Guarantees
     release even on early return — prevents resource leaks in long-running ECU code.

L2 (Senior):
  Q: How do you implement a type-safe CAN signal without dynamic allocation?
  A: Use a static ring buffer templated on message type and fixed capacity.
     Template parameters determine size at compile time → .bss/.data section.
     No heap. The type parameter (e.g., CanFrame, SpeedSignal) enforces type safety.
     Add static_assert to enforce size constraints at compile time.

  Q: When would you choose virtual dispatch vs CRTP in ECU code?
  A: Virtual dispatch: use at module boundaries (ISensor interface) where runtime
     polymorphism is needed. Cost: vtable lookup (~3-5ns).
     CRTP (Curiously Recurring Template Pattern): compile-time polymorphism, zero
     runtime overhead. Use in tight loops (sensor filtering at 1kHz, signal encoding).
     CRTP is MISRA-compliant; virtual is allowed but document the overhead.

L3 (Principal):
  Q: How do you ensure memory safety on an ECU without smart pointers?
  A: 1) Static object pools (fixed-size allocation pools in .bss section)
     2) RAII wrappers around pool acquire/release
     3) Lifetime analysis at design time (object lifetimes known at architecture phase)
     4) Static analysis tools (Polyspace, Axivion, LDRA) to detect use-after-free, 
        buffer overflows at compile/analysis time
     5) MPU (Memory Protection Unit) configuration to trap out-of-bounds writes at runtime
     6) MISRA Rule 18.x compliance: no pointer arithmetic beyond array bounds
```
