# Advanced Modern C++ Interview Questions
## Automotive Embedded Engineer — Principal Level

---

## TOPIC OVERVIEW

Modern C++ (C++11/14/17) is increasingly used in automotive at the **application layer** (Adaptive AUTOSAR, ADAS, telematics, infotainment) and gradually in **deep-embedded** (constexpr, templates, no-exceptions, no-RTTI profiles). Companies like Continental, Harman, Qualcomm Automotive, and Mercedes-Benz R&D heavily test C++17 at senior level.

**Key areas probed in automotive C++ interviews:**
- RAII and resource management (sockets, CAN, file handles)
- Smart pointers vs raw pointers in embedded
- Move semantics and copy elision
- Rule of 3/5/0
- Virtual dispatch, vtables, and overhead
- Thread safety with mutexes, atomics, condition variables
- Template metaprogramming and type erasure
- Embedded-safe C++ (no exceptions, no RTTI, static memory)
- constexpr and compile-time computation

---

## BEGINNER QUESTIONS

---

### Q1. What is RAII and why is it the most important C++ idiom in automotive ECU development?

**Short Answer:** RAII (Resource Acquisition Is Initialisation) binds resource lifetime to object lifetime — the constructor acquires the resource, the destructor releases it. It eliminates resource leaks even when exceptions or early returns occur.

**Detailed Expert Answer:**
```cpp
// WITHOUT RAII — traditional C style (resource leak risk)
int process_firmware(const char *path) {
    FILE *f = fopen(path, "rb");
    if (!f) return -1;
    
    uint8_t *buf = (uint8_t*)malloc(BLOCK_SIZE);
    if (!buf) {
        fclose(f);  // Easy to forget
        return -1;
    }
    
    int result = do_flash(f, buf);
    
    free(buf);    // What if do_flash throws or returns early?
    fclose(f);    // Easy to miss in complex control flow
    return result;
}

// WITH RAII — exception-safe, leak-proof
class CRCFileReader {
    FILE* m_file;
public:
    explicit CRCFileReader(const char *path) : m_file(fopen(path, "rb")) {
        if (!m_file) throw std::runtime_error("Cannot open firmware file");
    }
    ~CRCFileReader() { if (m_file) fclose(m_file); }  // Always runs
    
    // Non-copyable (no duplicate close)
    CRCFileReader(const CRCFileReader&) = delete;
    CRCFileReader& operator=(const CRCFileReader&) = delete;
    
    FILE* get() const { return m_file; }
};

int process_firmware_safe(const char *path) {
    CRCFileReader reader(path);           // Opens file
    std::vector<uint8_t> buf(BLOCK_SIZE); // Allocates buffer
    return do_flash(reader.get(), buf.data());
    // Both file AND buffer auto-released here — even if exception is thrown
}
```

**Automotive RAII examples used daily:**

| Resource | RAII Wrapper | Destructor action |
|----------|-------------|------------------|
| CAN socket | `CANSocket` class | `close(socket_fd)` |
| Mutex lock | `std::lock_guard` | `mutex.unlock()` |
| UDS session | `UDSSession` class | Send `0x10 01` (default session) |
| DTC suppression | `DTCSuppressor` class | Re-enable DTC storage |
| Fault injection | `ActiveFault` class | Clear injected fault |
| POSIX file | `std::unique_ptr<FILE, decltype(&fclose)>` | `fclose(ptr)` |

```cpp
// Production TCU code — CAN socket RAII wrapper
class CANSocket {
    int m_fd{-1};
    std::string m_iface;
public:
    explicit CANSocket(std::string iface) : m_iface(std::move(iface)) {
        m_fd = socket(PF_CAN, SOCK_RAW, CAN_RAW);
        if (m_fd < 0) throw std::system_error(errno, std::system_category());
        
        struct ifreq ifr{};
        strncpy(ifr.ifr_name, m_iface.c_str(), IFNAMSIZ - 1);
        ioctl(m_fd, SIOCGIFINDEX, &ifr);
        
        struct sockaddr_can addr{ .can_family = AF_CAN,
                                  .can_ifindex = ifr.ifr_ifindex };
        if (bind(m_fd, (struct sockaddr*)&addr, sizeof(addr)) < 0) {
            close(m_fd);
            throw std::system_error(errno, std::system_category());
        }
    }
    
    ~CANSocket() { if (m_fd >= 0) close(m_fd); }
    
    // Move-only — sockets cannot be copied
    CANSocket(CANSocket&& o) noexcept : m_fd(o.m_fd) { o.m_fd = -1; }
    CANSocket& operator=(CANSocket&&) = delete;
    CANSocket(const CANSocket&) = delete;
    CANSocket& operator=(const CANSocket&) = delete;
    
    int fd() const noexcept { return m_fd; }
};
```

**Why critical for automotive:**
- No memory leaks in long-running ECU processes (uptime: years)
- No resource exhaustion (file descriptors, mutexes, CAN channels)
- Correct cleanup even in fault-injection scenarios (when early returns are forced)
- AUTOSAR Adaptive Platform (based on POSIX + C++14) mandates RAII in its coding guidelines

---

### Q2. Explain smart pointers: unique_ptr, shared_ptr, weak_ptr. Which one is safe for automotive embedded use?

**Short Answer:** `unique_ptr` is safe for automotive (zero overhead). `shared_ptr` has atomic reference counting overhead. `weak_ptr` is for breaking shared_ptr cycles. In deep-embedded (no-heap), avoid all heap-based smart pointers; use static allocation.

**Detailed Expert Answer:**
```cpp
// unique_ptr — sole ownership, zero overhead, no atomic ops
std::unique_ptr<CANManager> can_mgr = std::make_unique<CANManager>("can0");
// can_mgr owns the object exclusively
// No copy allowed; move transfers ownership
auto mgr2 = std::move(can_mgr);  // can_mgr is now null

// shared_ptr — shared ownership via atomic reference count
auto sdk1 = std::make_shared<TelematicsSDK>(config);
auto sdk2 = sdk1;  // ref count = 2 — atomic increment (expensive in RT!)
// Both sdk1 and sdk2 own the object — freed when count reaches 0

// weak_ptr — non-owning observer (breaks cycles)
std::weak_ptr<TelematicsSDK> weak_sdk = sdk1;
if (auto locked = weak_sdk.lock()) {
    locked->publish();  // Safe — sdk still alive
}
```

**Memory comparison:**
```
unique_ptr<T>:  sizeof(T*) = 8 bytes on 64-bit — same as raw pointer
shared_ptr<T>:  2 pointers (ptr + control block) = 16 bytes
                control block: ref count + weak count + deleter + allocator
                ~40-64 bytes total heap allocation
```

**Automotive embedded guidance:**

| Platform | Recommendation |
|----------|---------------|
| Classic AUTOSAR (bare metal MCU) | No smart pointers — MISRA C++ prohibits dynamic allocation |
| Adaptive AUTOSAR (Linux/QNX) | `unique_ptr` freely; `shared_ptr` only in non-RT paths |
| ADAS compute platform (NXP S32G) | `unique_ptr` in modules; avoid `shared_ptr` in ISR context |
| Infotainment (QNX/Android) | All smart pointers OK |

**Custom deleters for automotive:**
```cpp
// RAII for POSIX file descriptor (no heap, just a number)
auto deleter = [](int *fd) { if (fd && *fd >= 0) close(*fd); };
std::unique_ptr<int, decltype(deleter)> fd_guard(new int(open("/dev/can0", O_RDWR)), deleter);

// Cleaner — custom smart pointer for FD
struct FdDeleter { void operator()(FILE *f) const { if(f) fclose(f); } };
std::unique_ptr<FILE, FdDeleter> file(fopen("config.json", "r"));
```

**Follow-up grilling:**
- "What is `make_shared` vs `new` with shared_ptr?" → `make_shared` allocates object + control block in ONE allocation (cache-friendly, exception-safe). `shared_ptr<T>(new T())` makes TWO allocations.
- "Can you store a `unique_ptr` in a `std::vector`?" → Yes. But vector reallocation requires moveable elements, and unique_ptr IS moveable. `std::vector<std::unique_ptr<T>>` is valid.

---

### Q3. Explain move semantics and Rule of 5. Write a move-correct CAN frame buffer class.

**Short Answer:** Move semantics allow transferring resources instead of copying them. The Rule of 5 states: if you define any of {destructor, copy constructor, copy assignment, move constructor, move assignment}, you should define all 5.

**Detailed Expert Answer:**
```cpp
class CANFrameBuffer {
    uint8_t  *m_data;      // Raw heap buffer
    size_t    m_capacity;
    size_t    m_size;

public:
    // Constructor
    explicit CANFrameBuffer(size_t capacity)
        : m_data(new uint8_t[capacity * sizeof(can_frame)])
        , m_capacity(capacity)
        , m_size(0) {}

    // 1. Destructor
    ~CANFrameBuffer() {
        delete[] m_data;   // Safe even if m_data is nullptr (after move)
    }

    // 2. Copy constructor — deep copy
    CANFrameBuffer(const CANFrameBuffer& other)
        : m_data(new uint8_t[other.m_capacity * sizeof(can_frame)])
        , m_capacity(other.m_capacity)
        , m_size(other.m_size) {
        std::memcpy(m_data, other.m_data, m_size * sizeof(can_frame));
    }

    // 3. Copy assignment — copy-and-swap idiom
    CANFrameBuffer& operator=(CANFrameBuffer other) {   // pass by value
        swap(*this, other);
        return *this;
    }

    // 4. Move constructor — steal resources from rvalue
    CANFrameBuffer(CANFrameBuffer&& other) noexcept
        : m_data(other.m_data)
        , m_capacity(other.m_capacity)
        , m_size(other.m_size) {
        other.m_data     = nullptr;  // Prevent double-free
        other.m_capacity = 0;
        other.m_size     = 0;
    }

    // 5. Move assignment
    CANFrameBuffer& operator=(CANFrameBuffer&& other) noexcept {
        if (this != &other) {
            delete[] m_data;           // Release current resource
            m_data     = other.m_data;
            m_capacity = other.m_capacity;
            m_size     = other.m_size;
            other.m_data     = nullptr;
            other.m_capacity = 0;
            other.m_size     = 0;
        }
        return *this;
    }

    friend void swap(CANFrameBuffer& a, CANFrameBuffer& b) noexcept {
        using std::swap;
        swap(a.m_data,     b.m_data);
        swap(a.m_capacity, b.m_capacity);
        swap(a.m_size,     b.m_size);
    }
};
```

**Key points:**
- `noexcept` on move operations is critical — `std::vector` only uses move if it's `noexcept`, otherwise it copies
- Move constructor leaves the moved-from object in a **valid but unspecified state** — setting pointer to nullptr prevents the destructor from double-freeing
- The copy-and-swap idiom in copy assignment is exception-safe and self-assignment-safe

**Rule of 0 (modern C++ preference):**
```cpp
// If you use only standard library types, the compiler generates everything correctly
class CANManager {
    std::string        m_iface;        // handles itself
    std::vector<uint8_t> m_rx_buffer;  // handles itself
    std::unique_ptr<UDSClient> m_uds;  // handles itself
    // No destructor, no copy/move needed — Rule of 0
};
```

---

## INTERMEDIATE QUESTIONS

---

### Q4. Explain virtual functions, vtables, and their overhead. When should you avoid them in automotive ECU code?

**Short Answer:** Virtual functions add one indirection per call through a vtable pointer. Each polymorphic object stores a hidden `vptr` (8 bytes on 64-bit). Avoid in interrupt handlers, tight loops, and on bare-metal MCUs with MISRA C++ compliance.

**Detailed Expert Answer:**
```cpp
// Memory layout with vtable:
class Module {                    // sizeof = 8 (vptr only)
    virtual bool start() = 0;
    virtual void stop() = 0;
};

class CANManager : public Module { // sizeof = 8 (vptr) + member data
    int m_fd;                      // sizeof = 4 → total = 16 (with padding)
    
public:
    bool start() override { /* ... */ return true; }
    void stop()  override { /* ... */ }
};

// What the compiler generates:
// CANManager vtable (in .rodata):
//   [0] → &CANManager::start
//   [1] → &CANManager::stop
//
// CANManager object in memory:
//   [0..7]  vptr → points to CANManager vtable
//   [8..11] m_fd
```

**Virtual call cost:**
```
Virtual call: obj->start()  →  load vptr → load function pointer → indirect call
              3 memory ops + 1 indirect branch

Direct call:  cobj.start()  →  direct call
              1 instruction
```

**When to avoid in automotive:**

| Context | Recommendation |
|---------|---------------|
| ISR handlers | Never — indirect call in ISR adds cycles, may miss timing |
| CAN Rx hot path | Avoid — use function pointer or template CRTP instead |
| AUTOSAR MCAL | Not used — pure C |
| RTOS task bodies | OK, but prefer CRTP for compile-time dispatch |
| ADAS application layer | OK — non-real-time paths |

**CRTP pattern — virtual without overhead:**
```cpp
// Curiously Recurring Template Pattern — static polymorphism
template<typename Derived>
class ModuleBase {
public:
    bool start() { return static_cast<Derived*>(this)->start_impl(); }
    void stop()  { static_cast<Derived*>(this)->stop_impl(); }
};

class CANManager : public ModuleBase<CANManager> {
    friend class ModuleBase<CANManager>;
    bool start_impl() { /* ... */ return true; }
    void stop_impl()  { /* ... */ }
};

// No vtable, no vptr, no virtual dispatch overhead
// Resolved at compile time — same cost as direct call
```

**Production Insight (Continental):**
Continental's PREEvision-generated AUTOSAR SWC code uses virtual functions only at the application/composition layer. All BSW, COM, and OS layers use function pointers (C-style) to avoid the overhead and to remain MISRA-C compliant. The RTE generated code uses direct function calls (no virtual dispatch).

---

### Q5. Explain `std::atomic` and memory ordering. Write thread-safe ECU telemetry counter.

**Short Answer:** `std::atomic<T>` provides hardware-level atomic operations without locks. Memory ordering controls how atomic operations are sequenced relative to other memory operations across threads.

**Detailed Expert Answer:**
```cpp
#include <atomic>
#include <cstdint>

// Six memory orders (from weakest to strongest):
// relaxed → acquire → consume → release → acq_rel → seq_cst

// Telemetry counters — relaxed is sufficient (just counting, no synchronisation needed)
class TelemetryCounters {
    std::atomic<uint64_t> m_can_rx_count{0};
    std::atomic<uint64_t> m_can_tx_count{0};
    std::atomic<uint64_t> m_ota_bytes{0};
    std::atomic<uint32_t> m_error_count{0};

public:
    void on_can_rx() noexcept {
        m_can_rx_count.fetch_add(1, std::memory_order_relaxed);
    }
    
    void on_can_tx() noexcept {
        m_can_tx_count.fetch_add(1, std::memory_order_relaxed);
    }
    
    uint64_t get_rx_count() const noexcept {
        return m_can_rx_count.load(std::memory_order_relaxed);
    }
};

// Flag shared between ISR thread and task — needs acquire/release
class CANRxFlag {
    std::atomic<bool> m_flag{false};
    can_frame          m_frame{};  // Protected by flag protocol

public:
    // Called from Rx thread — RELEASE ensures m_frame writes are visible
    void set(const can_frame& frame) noexcept {
        m_frame = frame;                            // Write data first
        m_flag.store(true, std::memory_order_release); // Release: makes m_frame visible
    }

    // Called from processing thread — ACQUIRE sees all writes before set's release
    bool try_get(can_frame& out) noexcept {
        if (!m_flag.load(std::memory_order_acquire)) return false;
        out = m_frame;                              // Read data after acquire
        m_flag.store(false, std::memory_order_release);
        return true;
    }
};
```

**Memory ordering explained with automotive analogy:**
```
Thread A (CAN Rx ISR):                Thread B (CAN Task):
  m_frame = received_data             [...]
  m_flag.store(true, release)  -->    if(m_flag.load(acquire))
                                          // GUARANTEED to see m_frame written by A
                                          process(m_frame)

Without acquire/release:
  CPU/compiler may reorder so that flag is set BEFORE data is written
  → Thread B sees flag=true but reads stale/garbage frame data
```

**Lock-free OTA progress tracker:**
```cpp
class OTAProgress {
    std::atomic<int>         m_percent{0};
    std::atomic<bool>        m_complete{false};
    std::atomic<bool>        m_error{false};
    std::atomic<uint64_t>    m_bytes_written{0};

public:
    void update(int pct, uint64_t bytes) noexcept {
        m_bytes_written.store(bytes, std::memory_order_relaxed);
        m_percent.store(pct, std::memory_order_release);
    }
    
    void set_complete() noexcept {
        m_complete.store(true, std::memory_order_seq_cst);
    }
    
    int progress() const noexcept {
        return m_percent.load(std::memory_order_acquire);
    }
};
```

---

### Q6. What is `constexpr` and how does it replace magic numbers in automotive ECU code?

**Short Answer:** `constexpr` forces compile-time evaluation — values are computed by the compiler and placed in `.rodata` or even eliminated entirely, resulting in zero runtime overhead.

**Detailed Expert Answer:**
```cpp
// BAD — magic numbers, no type safety, no documentation
uint32_t calc_timeout(uint32_t baud) {
    return (1000000U / baud) * 10U;  // What is 10? What is the unit?
}

// GOOD — constexpr constants with self-documenting names
constexpr uint32_t BITS_PER_CAN_FRAME    = 111U;   // SOF+ID+ctrl+data+CRC+ACK+EOF
constexpr uint32_t CAN_GUARD_FACTOR_PCT  = 20U;    // 20% margin

constexpr uint32_t can_frame_timeout_us(uint32_t bitrate_bps) {
    // bit_time_us = 1_000_000 / bitrate
    // frame_time_us = BITS_PER_CAN_FRAME * bit_time_us
    // timeout_us = frame_time_us * (1 + GUARD_FACTOR_PCT / 100)
    return (BITS_PER_CAN_FRAME * 1'000'000U / bitrate_bps) *
           (100U + CAN_GUARD_FACTOR_PCT) / 100U;
}

// Evaluated entirely at compile time — zero runtime cost:
constexpr uint32_t CAN_500K_TIMEOUT_US = can_frame_timeout_us(500'000U); // = 266 μs
constexpr uint32_t CAN_1M_TIMEOUT_US   = can_frame_timeout_us(1'000'000U); // = 133 μs

// Compile-time lookup table for ISO-TP block size values
constexpr std::array<uint8_t, 8> ISOTP_BLOCK_SIZES = {0, 8, 16, 32, 64, 128, 255, 0};
```

**`constexpr` in AUTOSAR RTE stub generation:**
```cpp
// Generated by AUTOSAR tool — routing table computed at compile time
constexpr uint8_t route_table[256] = []() {
    std::array<uint8_t, 256> t{};
    for (int i = 0; i < 256; i++) {
        t[i] = (i < 128) ? 0 : 1;  // Route low IDs to bus 0, high to bus 1
    }
    return t;
}();  // Immediately invoked lambda — fully constexpr
```

---

## ADVANCED QUESTIONS

---

### Q7. Write a type-safe compile-time state machine for an ECU bootloader using C++ templates.

**Detailed Expert Answer:**
```cpp
#include <type_traits>
#include <variant>
#include <optional>
#include <functional>

// States
struct BootState_Init   {};
struct BootState_Check  { bool app_valid; };
struct BootState_Flash  { uint32_t address; size_t size; };
struct BootState_Verify {};
struct BootState_Run    {};
struct BootState_Error  { std::string reason; };

using BootState = std::variant<
    BootState_Init,
    BootState_Check,
    BootState_Flash,
    BootState_Verify,
    BootState_Run,
    BootState_Error
>;

// Events
struct Evt_PowerOn  {};
struct Evt_AppValid { bool valid; };
struct Evt_FlashReq { uint32_t addr; size_t size; };
struct Evt_FlashOK  {};
struct Evt_VerifyOK {};
struct Evt_Error    { std::string msg; };

class BootLoader {
    BootState m_state{BootState_Init{}};

public:
    // Type-safe transition: only valid state/event combos compile
    void process(Evt_PowerOn) {
        std::visit([this](auto&& s) {
            using T = std::decay_t<decltype(s)>;
            if constexpr (std::is_same_v<T, BootState_Init>) {
                m_state = BootState_Check{.app_valid = false};
                log("Init → Check");
            }
        }, m_state);
    }

    void process(Evt_AppValid evt) {
        std::visit([&](auto&& s) {
            using T = std::decay_t<decltype(s)>;
            if constexpr (std::is_same_v<T, BootState_Check>) {
                if (evt.valid) {
                    m_state = BootState_Run{};
                    log("Check → Run (app valid)");
                } else {
                    m_state = BootState_Flash{.address = APP_START, .size = 0};
                    log("Check → Flash (app invalid)");
                }
            }
        }, m_state);
    }

    void process(Evt_FlashOK) {
        std::visit([this](auto&& s) {
            using T = std::decay_t<decltype(s)>;
            if constexpr (std::is_same_v<T, BootState_Flash>) {
                m_state = BootState_Verify{};
            }
        }, m_state);
    }

    template<typename Evt>
    void process(Evt evt) {
        // Invalid state/event combo — caught at compile time
        static_assert(sizeof(Evt) == 0, "Invalid event for current state");
    }

    bool is_running() const {
        return std::holds_alternative<BootState_Run>(m_state);
    }

private:
    static constexpr uint32_t APP_START = 0x08010000U;
    void log(const char *msg) { /* spdlog */ }
};
```

---

### Q8. Explain the volatile + atomic relationship for multicore ARM Cortex-R5 ECU (Aurix TC397).

**Expert Answer:**

"On the Infineon Aurix TC397, which has a triple-core Cortex-R5 lockstep + 2 additional cores, this is one of the most important topics:

**`volatile` alone is insufficient for inter-core communication:**
```cpp
// Core 0 writes, Core 1 reads
volatile bool g_flag = false;
volatile int  g_data = 0;

// Core 0:
g_data = compute();   // 1
g_flag = true;        // 2

// Core 1:
while (!g_flag) {}    // 3
use(g_data);          // 4

// PROBLEM: On a weakly-ordered multicore system, Core 1 may see:
// g_flag = true BEFORE it sees g_data = compute()
// This is a CPU reordering issue — volatile doesn't prevent it!
```

**Correct approach — C++11 atomics with release/acquire:**
```cpp
std::atomic<int>  g_data{0};
std::atomic<bool> g_flag{false};

// Core 0:
g_data.store(compute(), std::memory_order_relaxed);    // 1
g_flag.store(true,      std::memory_order_release);    // 2 — publishes data

// Core 1:
while (!g_flag.load(std::memory_order_acquire)) {}     // 3 — synchronises
use(g_data.load(std::memory_order_relaxed));           // 4 — guaranteed to see Core 0's write
```

**For the Aurix TC397 specifically:**
- Each core has private L1 cache + shared L2
- `dsync` (TRICORE data sync instruction) acts as memory barrier
- In C, you'd use `__asm volatile("dsync" ::: "memory")`
- In C++, `atomic<bool>` with release/acquire generates the correct `dsync` instructions

**When is `volatile` still needed?**
For memory-mapped I/O registers that are NOT shared between cores — the peripheral register changes without software intervention. Volatile prevents the compiler from caching the register value, but you still need barriers if the register write must be ordered relative to writes visible to other cores."

---

## PRODUCTION SCENARIO QUESTIONS

---

### Q9. A shared_ptr in your telematics module is causing a performance regression in the CAN Rx callback path. How do you diagnose and fix it?

**Expert walkthrough:**

"This is a classic embedded C++ performance problem I've seen at Continental and Harman.

**Step 1 — Profile to confirm:**
```bash
perf stat -e cache-misses,atomic-stalls ./tcu_validator --suite can
# If 'atomic-stalls' is high → shared_ptr atomic ref-counting is the bottleneck
```

**Step 2 — Identify the hot path:**
```cpp
// PROBLEM: shared_ptr copy in hot Rx callback (called every CAN frame)
void CANManager::rx_callback(const can_frame& f) {
    auto sdk = m_sdk;           // ← atomic ref-count increment + decrement!
    sdk->publish_telemetry(f);  // Every CAN frame copies the shared_ptr
}
```

**Step 3 — Fix options (in order of preference):**

Option A — Store raw pointer (if lifetime is guaranteed):
```cpp
TelematicsSDK* m_sdk_raw;  // Guaranteed valid for Manager's lifetime

void rx_callback(const can_frame& f) {
    m_sdk_raw->publish_telemetry(f);  // Zero atomic ops
}
```

Option B — Cache the raw pointer (observer pattern):
```cpp
// Only copy shared_ptr at construction, keep raw pointer for hot path
class CANManager {
    std::shared_ptr<TelematicsSDK> m_sdk_owner;  // Keeps alive
    TelematicsSDK* m_sdk_raw;                     // Hot-path access

    explicit CANManager(std::shared_ptr<TelematicsSDK> sdk)
        : m_sdk_owner(std::move(sdk))
        , m_sdk_raw(m_sdk_owner.get()) {}
};
```

Option C — Use `std::weak_ptr::lock()` only periodically, not per frame:
```cpp
// Check liveness every 100 frames, not every frame
uint32_t frame_count = 0;
TelematicsSDK* m_sdk_raw = nullptr;

void rx_callback(const can_frame& f) {
    if (++frame_count % 100 == 0) {
        if (auto locked = m_sdk_weak.lock()) m_sdk_raw = locked.get();
    }
    if (m_sdk_raw) m_sdk_raw->publish_telemetry(f);
}
```

**Production Insight:** At a KPIT project, a similar issue caused 15% latency regression in the SOME/IP CAN bridge. The fix was Option B — the architectural fix took 20 minutes, the performance returned to baseline immediately."

---

## CHEAT SHEET — Modern C++

```
RAII:     Constructor acquires, destructor releases — no leaks even with early returns
unique_ptr: Zero overhead, sole ownership, move-only
shared_ptr: Atomic ref-count, 16 bytes, avoid in RT hot paths
Rule of 5: dtor + copy ctor + copy assign + move ctor + move assign
Rule of 0: Use only STL members → let compiler generate all 5

Move:     Steal resource from rvalue, leave source in valid-but-unspecified state
noexcept: Mark move operations noexcept → vector uses move instead of copy

virtual:  One indirect branch per call, vptr = 8 bytes per object
CRTP:     Static polymorphism — zero overhead, compile-time dispatch

atomic:   Hardware atomic ops, no mutex needed for simple flags/counters
memory_order:
  relaxed  = no ordering constraint (counters only)
  acquire  = no reorder after this load
  release  = no reorder before this store
  seq_cst  = total order across all threads (default, slowest)

constexpr: Compile-time evaluation — zero runtime cost
           CAN timeouts, lookup tables, routing tables

Embedded rules:
  - No exceptions (-fno-exceptions) in safety-critical code
  - No RTTI (-fno-rtti) — no dynamic_cast, no typeid
  - No dynamic allocation in RT tasks — use static/stack allocation
  - Prefer unique_ptr over shared_ptr in all embedded contexts
  - Use std::array instead of std::vector on stack
  - Mark all move operations noexcept
```
