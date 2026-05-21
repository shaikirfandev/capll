# 06 — Debugging & Integration

## Overview

This module documents the **debugging, fault management, and system integration** practices in `adas_rt_cpp_project`: GDB Python scripts, sanitizers, logging, DTC fault lifecycle, and common integration failure patterns.

---

## 1. GDB Python Extension

**File**: `scripts/gdb_adas.py`

The GDB Python script adds custom commands for inspecting ADAS-specific runtime state without manually navigating C++ data structures.

### 1.1 Loading the Script

```bash
# Option 1: On command line
gdb -x scripts/gdb_adas.py --pid $(pgrep adas_rt)
# or
gdb -x scripts/gdb_adas.py --args ./bazel-bin/src/adas_rt

# Option 2: From inside GDB
(gdb) source scripts/gdb_adas.py

# Option 3: Auto-load (save in project .gdbinit)
echo "source $(pwd)/scripts/gdb_adas.py" >> .gdbinit
```

---

### 1.2 Command Reference

#### `adas-tracks` — Print EKF Track Table

```
(gdb) adas-tracks

ADAS Track Table
  ID   State      PX       PY       VX       VY     Hits  Misses
  1    CONFIRMED  32.45    1.23     -0.12    0.05    8     0
  2    TENTATIVE  18.72   -0.85      4.50   -0.20    2     0
  3    CONFIRMED  61.10    2.44      0.00    0.10   15     1
```

**Implementation**: Traverses the `SensorFusion::tracks_` unordered_map, prints `KalmanTrack::state_x_`, `hit_count_`, `miss_count_`, `track_state_`.

---

#### `adas-faults` — Dump DTC Fault Table

```
(gdb) adas-faults

ADAS Fault Table
  DTC     Description                  Status    Count  LastSeen
  0x0101  SENSOR_TIMEOUT              ACTIVE    3      t+12.4s
  0x0201  OBJECT_DETECTION_FAIL       HEALED    1      t+5.1s
  0x0601  CONTROL_ACTUATOR_FAULT      INACTIVE  0      -
```

**Implementation**: Reads `FaultManager::faults_` map, prints fault code, status enum name, occurrence count, timestamp.

---

#### `adas-rt-stats` — RT Task Jitter Statistics

```
(gdb) adas-rt-stats

RT Task Statistics
  Task              Period  MinJitter  MaxJitter  AvgJitter  Overruns
  sensor_fusion     20ms    2µs        45µs       8µs        0
  plan_control      50ms    3µs        62µs       11µs       0
  diagnostics       100ms   1µs        28µs       5µs        0
```

**Implementation**: Reads `RtScheduler::task_stats_` vector, prints `TaskStats::min_jitter_us`, `max_jitter_us`, `avg_jitter_us`, `deadline_misses`.

---

#### `adas-bt-all-threads` — Condensed All-Thread Backtrace

```
(gdb) adas-bt-all-threads

Thread 1 (main): main() → RtScheduler::run() → waiting
Thread 2 (sensor_fusion): clock_nanosleep → sensorFusionTask()
Thread 3 (plan_control): ObjectDetector::process() → [in callback]
Thread 4 (logger_flush): Logger::flushThread() → write()
Thread 5 (pool_0): WorkStealingPool::workerLoop() → idle
```

**Implementation**: Iterates `inferior_threads()`, calls `thread.switch()`, `gdb.execute("bt 5")` for top 5 frames, then prints thread name from `g_scheduler.tasks_[i].name`.

---

#### `adas-watch-latency THRESHOLD_US` — Break on Jitter Spike

```
(gdb) adas-watch-latency 500

Watching for RT jitter > 500µs ...
Breakpoint 1 at rt_scheduler.cpp:142 (jitter check)
→ If triggered: jitter = 823µs in task sensor_fusion
```

**Implementation**: Sets a GDB watchpoint on `RtScheduler::last_jitter_us_` with condition `> threshold_us`.

---

## 2. AddressSanitizer (ASan)

Detects memory corruption bugs: buffer overflows, use-after-free, heap-use-after-return.

### 2.1 Build and Run

```bash
# Build with ASan
bazel build //src:adas_rt --config=asan

# Run — ASan injects itself automatically
ASAN_OPTIONS=detect_leaks=1:halt_on_error=0 ./bazel-bin/src/adas_rt

# Run tests with ASan
bazel test //tests/unit/... --config=asan
```

### 2.2 Example ASan Output

```
=================================================================
==12345==ERROR: AddressSanitizer: heap-buffer-overflow on address 0x...
READ of size 4 at 0x... thread T2 (sensor_fusion)
    #0 0x... in SensorFusion::predict src/adas/perception/sensor_fusion.cpp:87
    #1 0x... in sensorFusionTask src/main.cpp:112
    ...
SUMMARY: AddressSanitizer: heap-buffer-overflow sensor_fusion.cpp:87
```

### 2.3 ASan Environment Options

| Option | Effect |
|--------|--------|
| `detect_leaks=1` | Run LeakSanitizer after process exit |
| `halt_on_error=0` | Continue after first error (find all issues) |
| `print_stats=1` | Print heap stats on exit |
| `malloc_fill_byte=0xAA` | Fill freed memory with 0xAA (detect UAF early) |

---

## 3. ThreadSanitizer (TSan)

Detects **data races**: two threads accessing shared data where at least one access is a write, with no synchronisation.

### 3.1 Build and Run

```bash
bazel build //src:adas_rt --config=tsan
./bazel-bin/src/adas_rt
```

### 3.2 Example TSan Output

```
==================
WARNING: ThreadSanitizer: data race (pid=12345)
  Write of size 4 at 0x... by thread T3 (plan_control):
    #0 PathPlanner::setTarget() path_planner.cpp:201
    
  Previous read of size 4 at 0x... by thread T2 (sensor_fusion):
    #0 SensorFusion::getTracks() sensor_fusion.cpp:145
    
SUMMARY: ThreadSanitizer: data race path_planner.cpp:201
```

### 3.3 Interpreting TSan Results

TSan reports are always real issues (no false positives for `std::atomic`). Action:
1. If on a shared variable: add mutex or convert to `std::atomic`
2. If in a lock-free queue: verify memory ordering is correct
3. If in a callback: ensure the callback is only called from one thread

---

## 4. Logging System

**File**: `src/diagnostics/logger.hpp/.cpp`

### 4.1 Architecture

```
RT thread writes:
  ADAS_LOG_ERROR("EKF diverged: track %d", id)
         │
         ▼ (wait-free push into SpscQueue<LogEntry, 1024>)
  Ring buffer (1024 × 256-byte fixed entries)
         │
         ▼ (flush thread, wakes every 1ms)
  stdout / syslog / file
```

**Key property**: The RT thread never blocks. If the ring buffer is full, the log entry is silently dropped (this is the correct RT trade-off — dropping a log line is better than causing jitter).

### 4.2 Log Macros

```cpp
ADAS_LOG_DEBUG("Predict: track %d  dt=%.3f", id, dt);
ADAS_LOG_INFO ("Track confirmed: id=%d  px=%.2f", id, px);
ADAS_LOG_WARN ("Gating miss: d=%.2f > %.2f (gate)", d, gate_thresh);
ADAS_LOG_ERROR("EKF inversion failed: det=%.6f", det);
ADAS_LOG_FATAL("Watchdog timeout — entering safe state");
```

`ADAS_LOG_FATAL` also calls `FaultManager::reportFault(FaultCode::WATCHDOG_TIMEOUT)`, which triggers the safe-state callback.

### 4.3 Log Level Configuration

```yaml
# config/adas_params.yaml
diagnostics:
  log_level: "INFO"    # DEBUG / INFO / WARN / ERROR / FATAL
  log_to_file: false
  log_file: "/var/log/adas_rt.log"
```

---

## 5. Fault Manager (DTC Lifecycle)

**File**: `src/diagnostics/fault_manager.hpp/.cpp`

### 5.1 DTC Code Table

| DTC Code | Name | Category |
|----------|------|---------|
| 0x0101 | SENSOR_TIMEOUT | Warning |
| 0x0201 | OBJECT_DETECTION_FAIL | Warning |
| 0x0301 | EKF_DIVERGENCE | Warning |
| 0x0401 | PATH_PLANNING_FAIL | Warning |
| 0x0501 | MEMORY_CORRUPTION | **Fatal** |
| 0x0601 | WATCHDOG_TIMEOUT | **Fatal** |
| 0x0701 | CONTROL_ACTUATOR_FAULT | **Fatal** |

### 5.2 Fault Lifecycle

```
FaultManager::reportFault(code)
        │
        ▼
[INACTIVE] ──────────────────────────────────────────────► [PENDING]
                                                                │
                                                     reportFault() again
                                                           (2nd time)
                                                                │
                                                                ▼
                                                           [ACTIVE]
                                                                │
                                              FaultManager::healFault(code)
                                                                │
                                                                ▼
                                                           [HEALED]
                                                                │
                                              FaultManager::clearFaults()
                                                                │
                                                                ▼
                                                          [removed from map]

Fatal DTCs (0x0501, 0x0601, 0x0701):
  ACTIVE state → immediately invoke SafeStateCallback
```

### 5.3 Safe State Callback

```cpp
FaultManager::instance().setSafeStateCallback([]() {
    // Disengage actuators
    hal->txCan(buildBrakeFrame(1.0f));      // Full brake
    hal->txCan(buildThrottleFrame(0.0f));   // Zero throttle
    g_scheduler.requestStop();              // Halt RT tasks
    ADAS_LOG_FATAL("Safe state entered");
});
```

---

## 6. Integration Debugging Checklist

### 6.1 Startup Issues

| Problem | Check |
|---------|-------|
| `pthread_setschedparam: EPERM` | Need `CAP_SYS_NICE` → run as root or `setcap cap_sys_nice+ep ./adas_rt` |
| `mlockall: ENOMEM` | ulimit: `ulimit -l unlimited`; or `/etc/security/limits.conf` |
| CAN socket open fail | `ip link show vcan0` → interface must be UP |
| `clock_nanosleep: EINVAL` | Check that `CLOCK_MONOTONIC` is used, not a negative `timespec` |

### 6.2 Runtime Issues

| Symptom | Likely Cause | Debug Step |
|---------|-------------|-----------|
| Large jitter spikes (> 500µs) | IRQ landing on RT CPU | Check `/proc/irq/*/smp_affinity` |
| EKF divergence DTC every ~10s | Sensor timestamp out-of-sync | Verify all sensors use same clock source |
| AEB always triggering at startup | Object at (0,0) from uninitialised detection | Check `ObjectDetector::reset()` called before first frame |
| CAN Tx lost frames | Socket buffer overflow | Increase buffer: `setsockopt(SO_SNDBUF)` |
| Thread pool starvation | Work-steal from same thread | Verify pool workers ≥ 2 |

### 6.3 Test Failure Analysis

```bash
# Run tests with verbose output and valgrind (for memory issues on non-RT host)
valgrind --leak-check=full --error-exitcode=1 \
  ./bazel-bin/tests/unit/test_sensor_fusion

# Run tests under GDB (stop on first failure)
gdb -ex run --args ./bazel-bin/tests/unit/test_sensor_fusion \
  --gtest_break_on_failure
```

---

## 7. CI Integration for Quality Gates

```bash
# Gate 1: Compilation (no warnings-as-errors violations)
bazel build //... --config=rt

# Gate 2: Unit tests
bazel test //tests/unit/...

# Gate 3: SIL scenario
bazel test //tests/sil/...

# Gate 4: ASan clean
bazel test //tests/unit/... --config=asan

# Gate 5: TSan clean
bazel test //tests/unit/... --config=tsan

# Gate 6: Static analysis (optional, if clang-tidy configured)
bazel build //... --config=clang_tidy
```

All gates must pass before merging to `main`.

---

*See also*: [07_Multithreading_Realtime.md](07_Multithreading_Realtime.md) for RT jitter analysis.  
*See also*: [03_HIL_SIL_Environments.md](03_HIL_SIL_Environments.md) for the SIL scenario test setup.
