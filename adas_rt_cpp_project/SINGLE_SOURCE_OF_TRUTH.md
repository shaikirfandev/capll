# ADAS Real-Time C++ Project — Single Source of Truth

> **Repository**: `adas_rt_cpp_project`  
> **Language**: C++17  
> **Build System**: Bazel  
> **Target OS**: Embedded Linux (PREEMPT_RT) / Ubuntu 22.04 LTS  
> **Version**: 1.0  
> **Date**: May 2026

---

## Table of Contents

1. [Project Overview](#1-project-overview)  
2. [Repository Structure](#2-repository-structure)  
3. [C++ Development — Design Decisions & Patterns](#3-c-development)  
4. [ADAS Domain Architecture](#4-adas-domain)  
5. [HIL/SIL Environments](#5-hilsil-environments)  
6. [Bazel Build System](#6-bazel-build-system)  
7. [Embedded Linux](#7-embedded-linux)  
8. [Debugging & Integration](#8-debugging--integration)  
9. [Multi-threading & Real-Time Systems](#9-multi-threading--real-time-systems)  
10. [Quick-Start Commands](#10-quick-start-commands)

---

## 1. Project Overview

This project demonstrates a **production-quality ADAS (Advanced Driver Assistance Systems)** software stack running in real-time on embedded Linux. It covers the complete perception-planning-control pipeline, with full HIL/SIL test infrastructure and Bazel build automation.

```
Sensor Data (Camera/Radar/LiDAR)
        │
        ▼
┌──────────────────┐      ┌──────────────────┐
│  ObjectDetector  │─────►│  SensorFusion    │ EKF tracker
│  (50 Hz RT task) │      │  (EKF, 50 Hz)   │
└──────────────────┘      └────────┬─────────┘
                                    │ TrackedObject[]
                                    ▼
                          ┌──────────────────┐
                          │  PathPlanner     │ JMT trajectories
                          │  AEB / ACC / LKA │
                          └────────┬─────────┘
                                    │ Waypoints[]
                                    ▼
                          ┌──────────────────┐
                          │  VehicleController│ PID + Stanley
                          └────────┬─────────┘
                                    │ ControlCommand
                                    ▼
                          ┌──────────────────┐
                          │  CAN Bus (HAL)   │ 0x200 Tx
                          └──────────────────┘
```

---

## 2. Repository Structure

```
adas_rt_cpp_project/
├── WORKSPACE                        ← Bazel external dependencies
├── BUILD                            ← Root build targets
├── .bazelrc                         ← Build flags (rt / asan / tsan / release)
│
├── src/
│   ├── adas/
│   │   ├── perception/
│   │   │   ├── object_detection.{hpp,cpp}   ← Camera / Radar / LiDAR → ego-frame objects
│   │   │   ├── sensor_fusion.{hpp,cpp}      ← EKF multi-object tracker
│   │   │   └── BUILD
│   │   ├── planning/
│   │   │   ├── path_planner.{hpp,cpp}       ← JMT trajectory + AEB/ACC/cruise
│   │   │   └── BUILD (part of control/BUILD)
│   │   └── control/
│   │       ├── vehicle_controller.{hpp,cpp} ← PID longitudinal + Stanley lateral
│   │       └── BUILD
│   ├── realtime/
│   │   ├── lock_free_queue.hpp              ← SPSC ring buffer (wait-free)
│   │   ├── rt_scheduler.{hpp,cpp}           ← POSIX SCHED_FIFO periodic tasks
│   │   ├── thread_pool.{hpp,cpp}            ← Work-stealing background pool
│   │   └── BUILD
│   ├── hil_sil/
│   │   ├── hal.hpp                          ← Hardware Abstraction Layer interface
│   │   ├── can_bus_sim.{hpp,cpp}            ← SimHal (in-process) + SocketCAN backend
│   │   └── BUILD
│   ├── diagnostics/
│   │   ├── logger.{hpp,cpp}                 ← Lock-free SPSC logger
│   │   ├── fault_manager.{hpp,cpp}          ← DTC fault lifecycle management
│   │   └── BUILD
│   ├── main.cpp                             ← Entry point, RT task registration
│   └── BUILD
│
├── tests/
│   ├── unit/
│   │   ├── test_object_detection.cpp
│   │   ├── test_sensor_fusion.cpp
│   │   ├── test_can_signals.cpp
│   │   └── BUILD
│   └── sil/
│       ├── sil_test_harness.cpp             ← Closed-loop AEB scenario
│       └── BUILD
│
├── scripts/
│   ├── setup_rt_linux.sh                    ← One-time RT system configuration
│   ├── run_sil_test.sh                      ← Build + run all tests
│   └── gdb_adas.py                          ← GDB Python helper (adas-tracks, etc.)
│
└── config/
    ├── rt_config.json                       ← RT task priorities / periods
    └── adas_params.yaml                     ← Algorithm tuning parameters
```

---

## 3. C++ Development

### 3.1 Language Standard: C++17

All code targets **C++17** with specific features used:
- `std::optional<T>` — SPSC queue pop returns, avoiding sentinel values
- `if constexpr` — compile-time branching in template code
- `[[fallthrough]]` — explicit fall-through in switch statements
- `std::atomic<bool>` — wait/stop flags in RT/scheduler
- Structured bindings (`auto& [key, val]`) — iterating unordered_map
- `std::invoke_result_t<F,Args...>` — thread pool submit() return type deduction

### 3.2 Memory Management

| Principle | Implementation |
|-----------|----------------|
| **No heap in RT path** | `std::vector::reserve()` pre-allocates before the task loop. `SpscQueue` uses fixed-size array. |
| **Stack pre-faulting** | `prefaultStack()` in `rt_scheduler.cpp` touches every stack page before RT begins. |
| **mlockall** | `RtScheduler::lockMemory()` calls `mlockall(MCL_CURRENT \| MCL_FUTURE)` to pin all pages. |
| **RAII** | All resources: thread handles, file descriptors, socket FDs are managed by destructors. |

### 3.3 Key C++ Patterns Used

#### CRTP / Strategy via abstract base class
`IHal` is an abstract interface allowing compile-time swap of `SimHal` (SIL) vs `SocketCanHal` (HIL) without touching algorithm code.

#### Template lock-free queue (SPSC)
```cpp
SpscQueue<DetectedObject, 64>  detection_queue;
detection_queue.push(obj);   // Producer (sensor task)
auto item = detection_queue.pop();  // Consumer (fusion task)
```

#### Enum class for type safety
```cpp
enum class SensorType : uint8_t { CAMERA = 0, RADAR = 1, LIDAR = 2 };
// Cannot accidentally mix with int — compiler error
```

#### Atomic stop flags (no mutex for RT)
```cpp
std::atomic<bool> stop_flag{false};
while (!stop_flag.load(std::memory_order_relaxed)) { /* RT loop */ }
```

### 3.4 Numeric / Math Design

- **Single-precision float** throughout the algorithm (not double) — avoids 2× overhead on Cortex-A53 FPU and is sufficient for ±200 m ADAS range.
- **Fixed-size 4×4 matrices** in `sensor_fusion.hpp` — no Eigen dependency. All operations are loop-unrollable.
- **Closed-form 2×2 and 3×3 matrix inversion** — avoids general LU decomposition for small matrices.

---

## 4. ADAS Domain

### 4.1 Perception Pipeline

```
Raw CAN/Ethernet frames
        │
SensorFrame (type=CAMERA | RADAR | LIDAR)
        │
ObjectDetector::process()
        │
  Camera:  pin-hole unproject + extrinsic transform
  Radar:   polar (ρ, φ, ρ̇) → Cartesian + velocity
  LiDAR:   DBSCAN 2D clustering
        │
DetectedObject[] (ego frame, ISO 8855: X=forward, Y=left, Z=up)
```

### 4.2 Extended Kalman Filter (EKF)

**State vector**: `x = [px, py, vx, vy]ᵀ`

**Predict** (constant-velocity model):
```
F = | 1  0  dt  0 |     x_k = F * x_{k-1}
    | 0  1   0 dt |     P_k = F * P_{k-1} * Fᵀ + Q
    | 0  0   1  0 |
    | 0  0   0  1 |

Q = σ_a² * G * Gᵀ,  G = [dt²/2, dt²/2, dt, dt]ᵀ
```

**Camera update** (linear):
```
H = [1 0 0 0]     y = z - H*x
    [0 1 0 0]     K = P*Hᵀ*(H*P*Hᵀ + R)⁻¹
                  x = x + K*y
                  P = (I - K*H)*P
```

**Radar update** (EKF linearisation):
```
h(x) = [√(px²+py²), atan2(py,px), (px*vx+py*vy)/√(px²+py²)]ᵀ
H_j  = Jacobian dh/dx (3×4, computed analytically)
```

### 4.3 Path Planning — JMT (Jerk Minimising Trajectory)

Solves a 5th-order polynomial `s(t) = c₀ + c₁t + c₂t² + c₃t³ + c₄t⁴ + c₅t⁵` with boundary conditions:
- `s(0) = s₀, ṡ(0) = v₀, s̈(0) = a₀`  
- `s(T) = s₁, ṡ(T) = v₁, s̈(T) = a₁`

Linear system for `[c₃, c₄, c₅]` solved with Cramer's rule (Werling 2010).

### 4.4 Behavior FSM

```
             timeout/obstacle cleared
CRUISE ◄────────────────────────────── FOLLOW
  │                                       ▲
  │  obstacle detected                    │
  └────────────────────────────────────► FOLLOW
             TTC < 1.5 s
  all states ──────────────────────────► EMERGENCY_BRAKE
```

### 4.5 Vehicle Controller

| Axis | Method | Formula |
|------|--------|---------|
| Longitudinal | PID on speed error | `u = Kp*e + Ki*∫e dt + Kd*ė` → throttle/brake |
| Lateral | Stanley | `δ = ψ_e + atan(k * e_cte / v)` |

Anti-windup: integrator clamped to `[-5, +5]` m/s·s.

---

## 5. HIL/SIL Environments

### 5.1 Architecture Comparison

| Aspect | SIL | HIL |
|--------|-----|-----|
| Hardware | Host PC only | Real ECU + HIL rig (dSPACE SCALEXIO, NI PXI) |
| Timing | Simulated (replay) | Real-time (hard RT constraints) |
| Sensor data | From CSV/MDF4 files or in-process injection | From physical sensors / hardware-in-loop signals |
| CAN bus | `SimHal` (in-process) or `vcan0` | Real physical CAN (PEAK, Vector, Kvaser) |
| Coverage | All scenarios, regression, overnight | Critical safety paths, timing characterisation |
| Cost | Low (CI/CD friendly) | High (specialist equipment) |

### 5.2 SimHal (SIL)

The `SimHal` class implements `IHal` with an in-process virtual CAN bus:

```cpp
SimHal hal;
hal.open();
hal.registerCanRxCallback([](const CanFrame& f) { /* decode */ });

// Inject ego-speed frame from simulation model:
CanFrame spd{};
spd.id = 0x100;
encodeSignal(spd, signals::EGO_SPEED, 22.22f);
hal.injectFrame(spd);

// Check ADAS transmitted control command:
auto tx_log = hal.drainTxLog();
float steer = decodeSignal(tx_log[0], signals::STEER_ANGLE);
```

### 5.3 SocketCAN HIL (vcan0 or real CAN)

```bash
# Setup virtual CAN (SIL on Linux)
sudo modprobe vcan
sudo ip link add dev vcan0 type vcan
sudo ip link set up vcan0

# Monitor traffic
candump vcan0

# Build with SocketCAN backend
bazel build //src:adas_rt --config=rt --cxxopt='-DADAS_USE_SOCKETCAN'
```

### 5.4 CAN Signal Encoding

```
Physical = Raw * Scale + Offset
Raw = (Physical - Offset) / Scale

Example: EGO_SPEED signal
  Signal bits: start_bit=0, length=16, scale=0.01, offset=0
  Physical 100 km/h = 27.78 m/s → Raw = 2778 → 0x0ADA in frame bytes [0:1]
```

### 5.5 SIL Test Scenario: AEB from 80 km/h

File: `tests/sil/sil_test_harness.cpp`

```
t=0 s:   Ego at 80 km/h, no obstacles
t=1 s:   Static obstacle injected at 40 m ahead
t≈2.8 s: EKF confirms track (3 hits)
t≈3.2 s: TTC < 1.5 s → AEB triggered
t≈5.1 s: Ego stopped, separation > 0 m (PASS)
```

---

## 6. Bazel Build System

### 6.1 Why Bazel?

| Feature | Bazel | CMake |
|---------|-------|-------|
| Reproducibility | Hermetic sandbox, SHA256 deps | System-path dependent |
| Remote caching | Built-in | Plugin required |
| Cross-compilation | First-class toolchain concept | Platform-specific hacks |
| Parallel builds | All targets | Yes, but less elegant |
| Query tool | `bazel query` for dep analysis | No equivalent |

### 6.2 Build Configurations

```bash
# Standard debug build
bazel build //src:adas_rt

# Real-time build (adds -D_GNU_SOURCE, -lrt, -lpthread)
bazel build //src:adas_rt --config=rt

# Release (O2 + LTO + NDEBUG)
bazel build //src:adas_rt --config=release

# AddressSanitizer (find memory errors)
bazel build //src:adas_rt --config=asan

# ThreadSanitizer (find data races)
bazel build //src:adas_rt --config=tsan
```

### 6.3 Test Commands

```bash
# All unit tests
bazel test //tests/unit/...

# SIL integration scenario
bazel test //tests/sil:sil_aeb_scenario --test_output=all

# All tests with coverage
bazel coverage //... --combined_report=lcov
```

### 6.4 BUILD File Anatomy

```python
load("@rules_cc//cc:defs.bzl", "cc_library")

cc_library(
    name = "perception",          # Target label: //src/adas/perception:perception
    srcs = ["object_detection.cpp", "sensor_fusion.cpp"],
    hdrs = ["object_detection.hpp", "sensor_fusion.hpp"],
    copts = ["-std=c++17", "-O2"],
    visibility = ["//visibility:public"],  # Who can depend on this
)
```

### 6.5 Dependency Graph

```
//src:adas_rt
    ├── //src/adas/perception:perception
    ├── //src/adas/control:planning
    │       └── //src/adas/perception:perception
    ├── //src/adas/control:control
    │       └── //src/adas/control:planning
    ├── //src/realtime:realtime
    ├── //src/hil_sil:hil_sil
    └── //src/diagnostics:diagnostics
```

Query command: `bazel query 'deps(//src:adas_rt)' --output=graph | dot -Tsvg`

---

## 7. Embedded Linux

### 7.1 PREEMPT_RT Kernel

The standard Linux kernel is **not fully preemptible**. A high-priority RT thread can still be blocked by:
- Non-preemptible kernel sections holding spinlocks
- Interrupt handlers that cannot be preempted

The **PREEMPT_RT** patch (`CONFIG_PREEMPT_RT=y`) converts all spinlocks to mutexes and makes virtually all kernel code preemptible, reducing worst-case latency from ~hundreds of microseconds to **< 50 µs** on typical hardware.

```bash
# Check if running PREEMPT_RT
uname -v | grep -i preempt
# Output: #1 SMP PREEMPT_RT ... → confirmed
```

### 7.2 System Configuration Checklist

| Step | Command / Setting | Why |
|------|------------------|-----|
| **isolcpus** | `isolcpus=2,3 nohz_full=2,3` in GRUB | Remove CPUs from scheduler; OS tasks never run on these cores |
| **IRQ affinity** | `/proc/irq/*/smp_affinity = 0x3` | Move all interrupts to housekeeping CPUs |
| **CPU governor** | `echo performance > /sys/...` | Constant clock speed; no frequency transitions during RT |
| **RT throttling off** | `sched_rt_runtime_us = -1` | Prevents kernel from stealing 5% CPU from RT tasks |
| **mlockall** | `mlockall(MCL_CURRENT \| MCL_FUTURE)` | All pages in RAM; no page faults |
| **Stack pre-fault** | Touch 256 KB stack buffer before RT loop | Force stack pages into RAM before RT starts |
| **Swap off** | `vm.swappiness = 0` | No swap activity during RT |
| **Disable hyperthreading** | BIOS or `echo off > /sys/.../smt/control` | Avoid cache pollution from HT sibling |

### 7.3 Memory Layout in Embedded Linux

```
Virtual Address Space (process)
┌────────────────────┐ High
│   Kernel space     │
├────────────────────┤
│   Stack (RT thread)│ ← pre-faulted 256 KB
│   Stack (main)     │
├────────────────────┤
│   Heap             │ ← never used in RT path (no malloc)
├────────────────────┤
│   BSS / Data       │
│   (global objects) │ ← g_detector, g_fusion, etc. (pinned by mlockall)
├────────────────────┤
│   Text segment     │ ← code pages (pinned by mlockall)
└────────────────────┘ Low
```

### 7.4 Cross-Compilation Setup

```bash
# Install cross-toolchain for ARM Cortex-A53 (NXP S32G, Renesas R-Car)
sudo apt install gcc-arm-linux-gnueabihf g++-arm-linux-gnueabihf

# Build for target
bazel build //src:adas_rt --config=embedded
# .bazelrc: build:embedded --crosstool_top=//toolchains:arm_linux_toolchain
```

---

## 8. Debugging & Integration

### 8.1 GDB Commands (from `gdb_adas.py`)

```bash
# Attach to running process
gdb -x scripts/gdb_adas.py --pid $(pgrep adas_rt)

# Custom commands:
(gdb) adas-tracks            # Print EKF track table
(gdb) adas-faults            # Dump DTC table
(gdb) adas-rt-stats          # Jitter statistics
(gdb) adas-bt-all-threads    # All thread backtraces (condensed)
(gdb) adas-watch-latency 500 # Break on jitter > 500 µs
```

### 8.2 AddressSanitizer / ThreadSanitizer

```bash
# Find heap corruption / use-after-free
bazel build //src:adas_rt --config=asan
ASAN_OPTIONS=detect_leaks=1:halt_on_error=0 ./bazel-bin/src/adas_rt

# Find data races
bazel build //src:adas_rt --config=tsan
./bazel-bin/src/adas_rt
```

### 8.3 Performance Profiling

```bash
# perf record the RT application (needs kernel.perf_event_paranoid=0)
sudo perf record -g -p $(pgrep adas_rt) -- sleep 10
sudo perf report --stdio | head -50

# Real-time latency histogram (cyclictest from rt-tests package)
sudo cyclictest --mlockall --smp --priority=80 --interval=10000 --histogram=500

# Flame graph
perf script | stackcollapse-perf.pl | flamegraph.pl > flame.svg
```

### 8.4 Integration Fault Management

The `FaultManager` implements an automotive DTC lifecycle:

```
[reportFault()]
INACTIVE ──► PENDING ──► ACTIVE
                             │
                       [healFault()]
                             │
                             ▼
                          HEALED ──► [clearFaults()] ──► removed
```

Fatal DTCs (`WATCHDOG_TIMEOUT`, `MEMORY_CORRUPTION`, `CONTROL_ACTUATOR_FAULT`) immediately invoke the `SafeStateCallback` which should engage parking brake and disable actuators.

### 8.5 Common Integration Issues & Solutions

| Symptom | Likely Cause | Solution |
|---------|-------------|---------|
| `pthread_setschedparam: EPERM` | No CAP_SYS_NICE | Run as root or `sudo setcap cap_sys_nice+ep ./adas_rt` |
| `mlockall failed: ENOMEM` | ulimit too low | Add `@adas_rt - memlock unlimited` to `/etc/security/limits.conf` |
| Large jitter spikes | IRQ landing on RT CPU | Check `setup_rt_linux.sh` IRQ affinity step |
| EKF divergence DTC | Sensor timestamp skew | Verify all sensors share a common hardware time reference (PTP/PPS) |
| CAN Tx timeout | Socket buffer overflow | Increase `SO_SNDBUF`; reduce CAN message rate |

---

## 9. Multi-threading & Real-Time Systems

### 9.1 Threading Architecture

```
Process threads:
┌──────────────────────────────────────────────────────┐
│  SCHED_FIFO prio=70  sensor_fusion   CPU=2  20ms     │ ← RT
│  SCHED_FIFO prio=60  plan_control    CPU=2  50ms     │ ← RT
│  SCHED_FIFO prio=40  diagnostics     CPU=any 100ms   │ ← RT
│  SCHED_OTHER         logger flush    CPU=any  1ms    │ ← non-RT
│  SCHED_OTHER         CAN sim inject  CPU=any 100ms   │ ← non-RT
│  SCHED_OTHER         main thread     CPU=0           │ ← non-RT
└──────────────────────────────────────────────────────┘
```

### 9.2 POSIX Real-Time Scheduling

| Policy | Description | When to Use |
|--------|-------------|------------|
| `SCHED_OTHER` | Default time-sharing | Non-RT background tasks |
| `SCHED_FIFO` | Fixed-priority, FIFO within priority | RT periodic tasks (preferred) |
| `SCHED_RR` | Fixed-priority, round-robin | Multiple tasks at same priority |
| `SCHED_DEADLINE` | EDF with CBS | When exact deadlines are known |

Priority range: **1 (lowest RT) to 99 (highest RT)**.  
The kernel watchdog runs at priority **99** — never set application threads to 99.

### 9.3 Periodic Task Implementation

```cpp
// clock_nanosleep with TIMER_ABSTIME avoids drift accumulation
int64_t next_wake_us = monotonicNowUs();

while (!stop_flag) {
    next_wake_us += period_us;
    struct timespec deadline = usToTimespec(next_wake_us);
    clock_nanosleep(CLOCK_MONOTONIC, TIMER_ABSTIME, &deadline, nullptr);

    // Measure actual wake time vs expected (jitter)
    int64_t jitter = monotonicNowUs() - next_wake_us;

    task_callback();  // bounded execution time
}
```

**Critical**: use `CLOCK_MONOTONIC` (not `CLOCK_REALTIME`) to avoid NTP adjustments.

### 9.4 Lock-Free SPSC Queue

```
Producer thread (sensor_fusion, prio=70)
         push() ─────────────────────────────────►  [ring buffer]
                                                           │
                                                    pop()  ◄── Consumer thread
                                                           (plan_control, prio=60)

Memory ordering:
  push: write item → store tail (release)
  pop:  load tail (acquire) → read item → store head (release)
```

The `acquire/release` ordering ensures the consumer sees the complete item before it acts on the updated tail index.

### 9.5 Avoiding Priority Inversion

Priority inversion occurs when a high-priority thread waits for a lock held by a low-priority thread while a medium-priority thread runs.

**Solutions used in this project**:
1. **Lock-free SPSC queue** between RT threads — no mutex, no inversion possible.
2. **Priority inheritance mutex** (Linux default for `pthread_mutex`): `pthread_mutexattr_setprotocol(attr, PTHREAD_PRIO_INHERIT)`.
3. **Mutex usage only in non-RT paths** (fault manager, logger flush).

### 9.6 Jitter Budget Analysis

| Source | Typical Jitter | Mitigation |
|--------|----------------|-----------|
| Kernel scheduler | 1–10 µs (PREEMPT_RT) | `isolcpus`, `nohz_full` |
| Timer precision | 1 µs (`HZ=1000`) | High-res timers enabled |
| IRQ handling | 5–50 µs | IRQ affinity to housekeeping CPUs |
| Cache miss (cold) | 10–100 µs | `mlockall` + stack pre-fault |
| Memory allocation | Unbounded | No `malloc()` in RT path |

**Target**: worst-case jitter < 100 µs for all RT tasks on PREEMPT_RT kernel.

---

## 10. Quick-Start Commands

```bash
# ── Clone & enter project ────────────────────────────────────────────────────
cd adas_rt_cpp_project

# ── Build all targets ────────────────────────────────────────────────────────
bazel build //... --config=rt

# ── Run unit tests ───────────────────────────────────────────────────────────
bazel test //tests/unit/... --test_output=short

# ── Run SIL AEB scenario ─────────────────────────────────────────────────────
bazel test //tests/sil:sil_aeb_scenario --test_output=all

# ── Run application (SIL mode) ───────────────────────────────────────────────
./bazel-bin/src/adas_rt

# ── Run with AddressSanitizer ────────────────────────────────────────────────
bazel build //src:adas_rt --config=asan && ./bazel-bin/src/adas_rt

# ── Run with GDB ─────────────────────────────────────────────────────────────
bazel build //src:adas_rt -c dbg
gdb -x scripts/gdb_adas.py --args ./bazel-bin/src/adas_rt

# ── Setup RT Linux (run once, as root) ───────────────────────────────────────
sudo bash scripts/setup_rt_linux.sh

# ── Monitor CAN on vcan0 ─────────────────────────────────────────────────────
candump vcan0 -td

# ── Check RT latency (requires rt-tests package) ─────────────────────────────
sudo cyclictest -m -p 80 -i 10000 -d 0 -h 200 -D 60s

# ── Query Bazel dependency graph ─────────────────────────────────────────────
bazel query 'deps(//src:adas_rt)' --output=graph | dot -Tsvg > deps.svg
```

---

*This document is the authoritative reference for the `adas_rt_cpp_project`. All code decisions are traceable to the rationale documented in the relevant sections above.*
