# 07 — Multi-threading & Real-Time Systems

## Overview

This module documents the **multi-threading architecture, POSIX real-time scheduling, lock-free data structures, work-stealing thread pool**, and jitter analysis used in `adas_rt_cpp_project`.

---

## 1. Thread Architecture Overview

```
Process: adas_rt
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  SCHED_FIFO Real-Time Threads                                   │   │
│  │                                                                 │   │
│  │  ┌───────────────────┐  ┌───────────────────┐  ┌───────────┐  │   │
│  │  │  sensor_fusion    │  │  plan_control     │  │ diagnos-  │  │   │
│  │  │  prio=70, 20ms    │  │  prio=60, 50ms    │  │ tics      │  │   │
│  │  │  CPU=2            │  │  CPU=2            │  │ prio=40   │  │   │
│  │  └────────┬──────────┘  └────────┬──────────┘  └─────┬─────┘  │   │
│  └───────────┼────────────────────── ┼──────────────────┼─────────┘   │
│              │                        │                   │             │
│    SpscQueue<DetectedObject>    SpscQueue<ControlCmd>                  │
│              │                        │                   │             │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  SCHED_OTHER Background Threads                                 │   │
│  │                                                                 │   │
│  │  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐  │   │
│  │  │  logger   │  │  CAN sim  │  │  pool[0]  │  │  pool[1]  │  │   │
│  │  │  flush    │  │  inject   │  │  steal    │  │  steal    │  │   │
│  │  └───────────┘  └───────────┘  └───────────┘  └───────────┘  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. POSIX Real-Time Scheduling

### 2.1 Scheduling Policies

| Policy | Description | Max Priority | Preemption |
|--------|-------------|-------------|-----------|
| `SCHED_OTHER` | Default Linux CFS | 0 | Yes (time-share) |
| `SCHED_BATCH` | Low-latency batch | 0 | Yes |
| `SCHED_IDLE` | Background only | 0 | Yes |
| `SCHED_FIFO` | RT fixed-priority | 1–99 | By higher-priority |
| `SCHED_RR` | RT round-robin | 1–99 | By higher-priority + time quantum |
| `SCHED_DEADLINE` | EDF + CBS | N/A | By earlier deadline |

For ADAS: **`SCHED_FIFO`** is preferred. Tasks at different priorities never need the round-robin quantum.

### 2.2 Priority Assignment Rationale

```
Priority 99  │  Kernel watchdog (never use application threads here)
Priority 90  │  (reserved — hardware interrupt threads on PREEMPT_RT)
Priority 80  │  (reserved — high-priority IRQ handlers)
─────────────┼──────────────────────────────────────────────────────
Priority 70  │  sensor_fusion task  ← highest ADAS priority
Priority 60  │  plan_control task   ← must wait for fusion output
Priority 50  │  (available — e.g., CAN Rx thread on real hardware)
Priority 40  │  diagnostics task    ← lowest RT, non-critical
─────────────┼──────────────────────────────────────────────────────
Priority 0   │  Logger flush, CAN sim, thread pool workers
```

**Rule**: Higher frequency = higher priority only if the task produces data needed by a lower-frequency task. Here, sensor_fusion at 50Hz feeds plan_control at 20Hz, so fusion must be higher priority.

### 2.3 Setting RT Priority in Code

**File**: `src/realtime/rt_scheduler.cpp`

```cpp
void RtScheduler::startTask(RtTask& task) {
    task.thread = std::thread([&]() {
        // 1. Set scheduling policy
        struct sched_param param;
        param.sched_priority = task.priority;
        if (pthread_setschedparam(pthread_self(), SCHED_FIFO, &param) != 0) {
            perror("pthread_setschedparam");
        }

        // 2. Pin to CPU
        cpu_set_t cpuset;
        CPU_ZERO(&cpuset);
        CPU_SET(task.cpu_affinity, &cpuset);
        pthread_setaffinity_np(pthread_self(), sizeof(cpuset), &cpuset);

        // 3. Pre-fault stack
        prefaultStack();

        // 4. Enter RT loop
        periodicLoop(task);
    });
}
```

---

## 3. Periodic Real-Time Loop

### 3.1 Absolute Timer (clock_nanosleep)

```cpp
void periodicLoop(RtTask& task) {
    struct timespec next_wake;
    clock_gettime(CLOCK_MONOTONIC, &next_wake);

    while (!stop_flag_.load(std::memory_order_relaxed)) {
        // Advance deadline by one period
        next_wake.tv_nsec += task.period_us * 1000LL;
        while (next_wake.tv_nsec >= 1'000'000'000LL) {
            next_wake.tv_nsec -= 1'000'000'000LL;
            next_wake.tv_sec  += 1;
        }

        // Sleep until absolute time (NOT relative sleep!)
        clock_nanosleep(CLOCK_MONOTONIC, TIMER_ABSTIME, &next_wake, nullptr);

        // Measure actual wake vs expected
        struct timespec actual;
        clock_gettime(CLOCK_MONOTONIC, &actual);
        int64_t jitter_us = timespecDiff(actual, next_wake) / 1000;

        // Update stats
        updateJitterStats(task, jitter_us);

        // Execute task
        task.callback();
    }
}
```

**Why `TIMER_ABSTIME`?**

```
Relative sleep (WRONG — drift accumulates):
  Period 10ms
  t=0:   sleep(10ms) → wake at t=10.008ms (8µs late)
  t=10:  sleep(10ms) → wake at t=20.017ms (17µs total drift)
  t=100: drift has accumulated to 800µs

Absolute sleep (CORRECT — no drift):
  next_wake = 10ms
  t=0:   sleep_until(10ms) → wake at t=10.008ms
  next_wake = 20ms
  t=10:  sleep_until(20ms) → wake at t=20.009ms (drift reset each cycle!)
```

### 3.2 Jitter Measurement

```cpp
struct TaskStats {
    int64_t min_jitter_us{INT64_MAX};
    int64_t max_jitter_us{0};
    int64_t sum_jitter_us{0};
    uint64_t count{0};
    uint64_t deadline_misses{0};
};

void updateJitterStats(RtTask& task, int64_t jitter_us) {
    auto& s = task.stats;
    s.min_jitter_us = std::min(s.min_jitter_us, jitter_us);
    s.max_jitter_us = std::max(s.max_jitter_us, jitter_us);
    s.sum_jitter_us += jitter_us;
    ++s.count;

    // Alert if jitter exceeds 80% of period
    const int64_t threshold = task.period_us * 8 / 10;
    if (jitter_us > threshold) {
        ++s.deadline_misses;
        ADAS_LOG_WARN("Deadline miss: %s jitter=%ldus", task.name.c_str(), jitter_us);
    }
}
```

---

## 4. Lock-Free SPSC Queue

**File**: `src/realtime/lock_free_queue.hpp`

### 4.1 Design Constraints

1. **Single producer, single consumer** (SPSC) — enables lock-free implementation
2. **Wait-free** — bounded number of operations (no retries possible in RT)
3. **Trivially copyable types only** — no constructor/destructor called in hot path
4. **Power-of-2 capacity** — bitmask replaces modulo (no division)
5. **Cache-line separated atomics** — prevents false sharing between producer and consumer

### 4.2 Implementation

```cpp
template <typename T, size_t CAPACITY>
class SpscQueue {
    static_assert((CAPACITY & (CAPACITY - 1)) == 0, "Power of 2 required");
    static_assert(std::is_trivially_copyable_v<T>, "No constructors in hot path");

    // Separated onto different cache lines (64 bytes)
    alignas(64) std::atomic<size_t> head_{0};   // Consumer: reads head, writes head
    alignas(64) std::atomic<size_t> tail_{0};   // Producer: reads tail, writes tail
    T buf_[CAPACITY]{};
    static constexpr size_t MASK = CAPACITY - 1;

public:
    bool push(const T& item) noexcept {
        const size_t tail = tail_.load(std::memory_order_relaxed);
        const size_t next_tail = (tail + 1) & MASK;

        // Queue full — cannot push
        if (next_tail == head_.load(std::memory_order_acquire)) {
            return false;
        }

        buf_[tail] = item;
        // Release: ensures buf_[tail] write is visible before tail update
        tail_.store(next_tail, std::memory_order_release);
        return true;
    }

    std::optional<T> pop() noexcept {
        const size_t head = head_.load(std::memory_order_relaxed);

        // Queue empty — nothing to pop
        if (head == tail_.load(std::memory_order_acquire)) {
            return std::nullopt;
        }

        T item = buf_[head];
        // Release: ensures buf_[head] read before head update
        head_.store((head + 1) & MASK, std::memory_order_release);
        return item;
    }
};
```

### 4.3 Memory Ordering Proof

```
Producer (sensor_fusion thread):           Consumer (plan_control thread):
─────────────────────────────────         ─────────────────────────────────
buf_[tail] = item;     ① write            load(tail_) ③  [acquire]
store(tail_, [release]) ②                 // ③ is ordered AFTER ②
                                          // ① is visible before ③
                                          T item = buf_[head];  ④ read
                                          // ④ sees the data written in ①
```

The `release` on ② synchronizes with the `acquire` on ③, creating a happens-before edge: ① → ④.

### 4.4 False Sharing Prevention

Without `alignas(64)`:
```
Cache line 1: [head (8 bytes) | tail (8 bytes) | .... padding ....]
              ↑ Producer writes tail     ↑ Consumer writes head
              Both in SAME cache line → false sharing → cache thrash
```

With `alignas(64)`:
```
Cache line 1: [head (8 bytes) | 56 bytes padding]   ← Consumer only
Cache line 2: [tail (8 bytes) | 56 bytes padding]   ← Producer only
              No sharing → no cache invalidation between cores
```

---

## 5. Work-Stealing Thread Pool

**File**: `src/realtime/thread_pool.hpp/.cpp`

### 5.1 Architecture

```
Pool workers (SCHED_OTHER, non-RT)

  Worker 0                Worker 1                Worker 2
  ┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
  │  local deque     │   │  local deque     │   │  local deque     │
  │  front→ push/pop │   │  front→ push/pop │   │  front→ push/pop │
  │  ← steal back    │   │  ← steal back    │   │  ← steal back    │
  └────────┬─────────┘   └────────┬─────────┘   └────────┬─────────┘
           │  idle?                │  idle?                │
           └──────────────────────►│  steal from W0 back   │
                                   └──────────────────────►│
```

### 5.2 Submitting Work

```cpp
ThreadPool pool(4);  // 4 worker threads

// Fire-and-forget heavy computation
pool.submit([&]() {
    recomputeOfflineMap(waypoints);
});

// Synchronise on result
auto future = pool.submit([&]() -> float {
    return computeObstacleRisk(tracks);
});
float risk = future.get();  // Blocks until done
```

### 5.3 Why Work-Stealing?

| Pool Type | Idle Worker Behaviour | Overhead |
|-----------|----------------------|---------|
| Fixed mutex queue | Wait on mutex for any task | Contention at high submission rate |
| Work-stealing | Steal from another worker's back | Low — only contend when stealing |

Work-stealing is ideal when task granularity varies: long tasks leave tasks on the back of the deque, short tasks get consumed locally at the front.

---

## 6. Priority Inversion Analysis

### 6.1 Classic Scenario

```
High-priority thread H (sensor_fusion, prio=70)
       waiting for mutex M
              ↑ blocked
Medium-priority thread M (non-RT, prio=0) running
       (M can run because H is blocked)
Low-priority thread L (logger, prio=0) holds mutex M
       (L cannot run because M is running)
→ H is blocked indefinitely by M — PRIORITY INVERSION
```

### 6.2 Mitigations Used in This Project

| Mechanism | How Used |
|-----------|---------|
| **Lock-free SPSC queue** | No mutex at all between RT threads — no inversion possible |
| **Priority inheritance mutex** | `pthread_mutexattr_setprotocol(PTHREAD_PRIO_INHERIT)` for fault manager mutex |
| **Mutex only in non-RT code** | RT threads never acquire mutexes; only non-RT flush/diagnostics threads use them |

### 6.3 Lock Hierarchy

```
RT thread:    SpscQueue::push/pop (lock-free, no mutex)
                      │
                      ▼
Non-RT thread:  FaultManager::reportFault (mutex protected)
Non-RT thread:  Logger::flush (mutex protected)

Cross-thread access: ONLY via lock-free SpscQueue
```

---

## 7. Jitter Budget Summary

| Layer | Source of Jitter | Typical Value | Mitigation |
|-------|-----------------|--------------|-----------|
| Kernel | Non-preemptible section | 200µs (no RT) → 10µs (PREEMPT_RT) | PREEMPT_RT kernel |
| Scheduler | Tick-based wakeup | 0–1ms (HZ=1000) → 0–10µs (nohz) | `nohz_full`, high-res timers |
| Interrupt | IRQ handler on RT CPU | 5–50µs | `isolcpus` + IRQ affinity |
| Memory | Page fault | 50–500µs | `mlockall` + stack pre-fault |
| Cache | Cold cache miss | 10–100µs | `mlockall` keeps code/data hot |
| Application | Variable task duration | Implementation-dependent | Profile with perf |

**Target (well-tuned PREEMPT_RT)**: max jitter < 100µs for all ADAS RT tasks.

---

## 8. Concurrency Patterns Quick Reference

| Pattern | Use Case | Tool |
|---------|---------|------|
| SCHED_FIFO task | Periodic RT control loop | `RtScheduler::addTask()` |
| SPSC lock-free queue | RT inter-thread data | `SpscQueue<T,N>` |
| Work-stealing pool | Background non-RT computation | `ThreadPool::submit()` |
| Atomic stop flag | Clean thread shutdown | `std::atomic<bool>` |
| Priority inheritance mutex | Non-RT shared state | `pthread_mutex` with PRIO_INHERIT |
| `clock_nanosleep ABSTIME` | Drift-free periodic wakeup | `RtScheduler::periodicLoop()` |
| `pthread_setaffinity_np` | Pin task to isolated CPU | `RtScheduler::startTask()` |

---

*See also*: [05_Embedded_Linux.md](05_Embedded_Linux.md) for `isolcpus`, `mlockall`, and kernel-level setup.  
*See also*: [06_Debugging_Integration.md](06_Debugging_Integration.md) for jitter measurement and `adas-rt-stats` GDB command.
