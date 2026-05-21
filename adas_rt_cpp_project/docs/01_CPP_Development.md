# 01 — C++ Development

## Overview

This module documents all **C++17 patterns, memory management strategies, design decisions**, and code quality practices used in `adas_rt_cpp_project`. Every choice is explained with the automotive/real-time rationale behind it.

---

## 1. C++17 Features Used

### 1.1 `std::optional<T>`

**File**: `src/realtime/lock_free_queue.hpp`

```cpp
std::optional<T> pop() noexcept {
    const size_t head = head_.load(std::memory_order_relaxed);
    if (head == tail_.load(std::memory_order_acquire)) {
        return std::nullopt;  // Queue is empty
    }
    T item = buf_[head & MASK];
    head_.store(head + 1, std::memory_order_release);
    return item;
}
```

**Why**: Avoids sentinel values (like `-1` or `nullptr`) that could be misinterpreted. The caller knows explicitly whether data was available.

---

### 1.2 `if constexpr`

Used in template code where branches must be eliminated at compile time:

```cpp
template <typename Derived>
struct SensorTraits {
    static constexpr bool hasVelocity = false;
};

template <>
struct SensorTraits<RadarDetection> {
    static constexpr bool hasVelocity = true;
};

// Zero-overhead — the false branch is never compiled
if constexpr (SensorTraits<S>::hasVelocity) {
    obj.vx = det.vr * cos(det.azimuth);
}
```

---

### 1.3 Structured Bindings

**File**: `src/diagnostics/fault_manager.cpp`

```cpp
for (const auto& [code, fault] : faults_) {
    if (fault.status == FaultStatus::ACTIVE) {
        log_active(fault);
    }
}
```

Cleaner than `it->first` / `it->second` when iterating maps.

---

### 1.4 `[[fallthrough]]`

Prevents accidental compiler warnings while explicitly documenting intentional fall-through:

```cpp
switch (behavior) {
    case BehaviorDecision::EMERGENCY_BRAKE:
        activateAEB();
        [[fallthrough]];  // AEB also does braking, which FOLLOW does too
    case BehaviorDecision::FOLLOW:
        applyBraking();
        break;
}
```

---

### 1.5 `std::invoke_result_t`

**File**: `src/realtime/thread_pool.hpp`

```cpp
template <typename F, typename... Args>
auto submit(F&& f, Args&&... args)
    -> std::future<std::invoke_result_t<F, Args...>>
{
    using R = std::invoke_result_t<F, Args...>;
    auto task = std::make_shared<std::packaged_task<R()>>(
        std::bind(std::forward<F>(f), std::forward<Args>(args)...));
    auto future = task->get_future();
    // ... enqueue
    return future;
}
```

`std::invoke_result_t` replaces the old `std::result_of_t` and works correctly with `noexcept` functions and perfect forwarding.

---

## 2. Template Design

### 2.1 Fixed-Size Matrix Template

**File**: `src/adas/perception/sensor_fusion.hpp`

```cpp
template <size_t ROWS, size_t COLS>
struct Matrix {
    float data[ROWS][COLS]{};

    // Operator overloads: +, *, transpose()
    // All inline → fully unrolled by compiler with -O2
};

using Mat4x4 = Matrix<4, 4>;
using Mat2x4 = Matrix<2, 4>;
```

**Why not Eigen?**
- Eigen requires an additional Bazel/CMake dependency
- For 4×4 matrices, hand-rolled loops are fully unrolled by GCC/Clang with `-O2`
- No dynamic allocation — Eigen's `MatrixXd` would heap-allocate
- Simpler type names in debugging sessions

---

### 2.2 Lock-Free Queue Template

```cpp
template <typename T, size_t CAPACITY>
class SpscQueue {
    static_assert(std::is_trivially_copyable_v<T>,
        "SpscQueue only works with trivially copyable types");
    static_assert((CAPACITY & (CAPACITY - 1)) == 0,
        "CAPACITY must be a power of two");

    alignas(64) std::atomic<size_t> head_{0};
    alignas(64) std::atomic<size_t> tail_{0};
    T buf_[CAPACITY]{};
    static constexpr size_t MASK = CAPACITY - 1;
};
```

The static_asserts act as **contracts** checked at compile time, not at runtime.

---

## 3. Memory Management

### 3.1 Allocation Strategy

```
RT hot path (periodic tasks):
  ─────────────────────────────────────────────────────
  ✅  Stack-allocated temporaries (plain arrays, structs)
  ✅  Pre-reserved std::vector (capacity fixed before loop)
  ✅  Fixed-size ring buffers (SpscQueue, LogEntry ring)
  ❌  std::vector::push_back (may reallocate)
  ❌  std::make_shared / new (heap)
  ❌  std::string construction (SSO may heap-allocate)
  ─────────────────────────────────────────────────────

Initialisation path (before RT loop starts):
  ✅  std::vector::reserve()
  ✅  std::make_unique / std::make_shared
  ✅  JSON config parsing (nlohmann/json)
  ✅  Logger and fault manager construction
```

### 3.2 Pre-reservation Pattern

```cpp
void ObjectDetector::init() {
    // Reserve worst-case capacity before the RT loop runs
    detected_.reserve(MAX_OBJECTS);   // 64 objects
    cluster_ids_.reserve(2048);       // LiDAR point count
}

void ObjectDetector::process(const SensorFrame& frame) {
    // This runs in the RT task — NO allocations possible here
    detected_.clear();  // Does NOT free memory

    for (auto& pt : frame.lidar_pts) {
        // Process using only pre-reserved space
    }
}
```

### 3.3 RAII Resource Ownership

Every resource follows strict RAII:

| Resource | Owner | Destructor Action |
|----------|-------|------------------|
| `pthread_t` (RT tasks) | `RtScheduler` | `stop_flag=true` + `join()` |
| `SocketCAN` fd | `SocketCanHal` | `close(fd_)` |
| `std::thread` (pool) | `ThreadPool` | `done_=true` + `join()` |
| `Logger` singleton | `Logger` | flush remaining entries to stdout |

---

## 4. Concurrency Patterns

### 4.1 Atomic Stop Flags

Preferred over `volatile bool` (which has no memory-ordering guarantees):

```cpp
// Declaration (in class)
std::atomic<bool> stop_flag_{false};

// Signalling shutdown (SIGINT handler or destructor)
stop_flag_.store(true, std::memory_order_seq_cst);

// RT thread check (relaxed — ordering not required)
while (!stop_flag_.load(std::memory_order_relaxed)) {
    // periodic work
}
```

### 4.2 Memory Ordering Reference

| Order | Guarantees | Use Case |
|-------|-----------|---------|
| `relaxed` | No ordering | Counter increments, stop flags |
| `acquire` | See all writes before paired release | Queue consumer reading tail |
| `release` | All prior writes visible to paired acquire | Queue producer writing tail |
| `seq_cst` | Global total order | Signals, one-shot events |

### 4.3 Work-Stealing Thread Pool

```cpp
// Submit returns a future — caller can synchronise or fire-and-forget
auto future = pool.submit([&]() {
    return computeHeavyTrajectory(waypoints);
});

// Later, when result is needed:
auto trajectory = future.get();
```

The pool steals from the **back** of other workers' deques:
- Owner pushes/pops from the **front** (stack discipline — cache locality)
- Stealer takes from the **back** (reduces contention with owner)

---

## 5. Type Safety Practices

### 5.1 Enum Class Instead of Bare Enum

```cpp
// Bad — accidents possible: if (type == 1)
enum SensorType { CAMERA, RADAR, LIDAR };

// Good — compiler enforces type
enum class SensorType : uint8_t { CAMERA = 0, RADAR = 1, LIDAR = 2 };
if (type == SensorType::RADAR) { ... }
```

### 5.2 Strong Typedefs

Physical quantities should not mix:

```cpp
struct Metres { float value; };
struct Radians { float value; };

void setSteerAngle(Radians angle);
// setSteerAngle(Metres{1.5f}) ← compile error! Good.
```

> Note: This project uses `float` directly for performance but wraps safety-critical unit conversions in explicit helper functions (e.g. `degToRad()`, `mpsToKph()`).

### 5.3 noexcept Contracts

RT functions are marked `noexcept` to:
1. Document that they will not throw (which would disrupt timing)
2. Allow compiler to skip exception stack unwinding code generation

```cpp
bool SpscQueue<T,N>::push(const T& item) noexcept;
std::optional<T> SpscQueue<T,N>::pop() noexcept;
```

---

## 6. Code Quality Standards

### 6.1 MISRA C++ Alignment

This codebase follows MISRA C++:2023 spirit (not formally verified):

| MISRA Rule | Practice |
|-----------|---------|
| Avoid global mutable state | Globals in `main.cpp` only, `g_` prefix |
| No dynamic allocation after init | RT path is heap-free |
| No `reinterpret_cast` on data | CAN bytes accessed as `uint8_t[]` |
| Explicit base class destructors | `IHal::~IHal() = default;` |
| `override` on virtual functions | All derived HAL methods use `override` |

### 6.2 Unit Test Naming Convention

```
TEST(ModuleName_Feature, ExpectedBehaviour_WhenCondition) {
    // Arrange / Act / Assert
}

// Example:
TEST(SensorFusion_Tracking, TrackDeletedAfterMaxMisses) {
    SensorFusion fusion(cfg);
    // ... inject 3 hits then 5 misses ...
    EXPECT_TRUE(fusion.getTracks().empty());
}
```

### 6.3 Compiler Warning Flags

From `.bazelrc`:
```
build --cxxopt='-Wall'
build --cxxopt='-Wextra'
build --cxxopt='-Wpedantic'
build --cxxopt='-Werror'           # Warnings are errors in CI
build --cxxopt='-Wno-unused-parameter'  # Common in virtual functions
```

---

## 7. Build Flags and Their Effect

| Flag | Effect |
|------|--------|
| `-O2` | Unrolls matrix loops, inlines small functions |
| `-O3 -flto` | Release: link-time optimisation across TUs |
| `-fsanitize=address` | AddressSanitizer — detects out-of-bounds, UAF |
| `-fsanitize=thread` | ThreadSanitizer — detects data races |
| `-fstack-protector-strong` | Stack canary for buffer overflow detection |
| `-D_FORTIFY_SOURCE=2` | Glibc bounds-checking for memcpy/sprintf |
| `-DNDEBUG` | Disables `assert()` in release |

---

*See also*: [04_Bazel_Build_System.md](04_Bazel_Build_System.md) for full build configuration.
