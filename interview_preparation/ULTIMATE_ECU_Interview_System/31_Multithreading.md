# Multithreading & Concurrency Interview Questions
## Senior Automotive Embedded Engineer — Principal Level

---

## TOPIC OVERVIEW

Multithreading knowledge is tested in **every senior automotive C/C++ interview**. Bosch, Continental, KPIT, Tata Elxsi, and Qualcomm Automotive routinely ask about race conditions, mutexes, atomic operations, and thread-safe design patterns. Automotive systems are highly concurrent: CAN Rx/Tx threads, OTA download threads, telemetry threads, diagnostic threads.

**Key areas probed:**
- Thread creation and lifecycle (pthreads, std::thread, RTOS tasks)
- Synchronisation primitives (mutex, semaphore, condition variable, spinlock)
- Lock-free programming (std::atomic, memory ordering, CAS operations)
- Race conditions and data races
- Deadlock, livelock, starvation
- Thread-safe design patterns (producer-consumer, reader-writer, thread pool)
- C++ memory model (std::atomic, memory_order)
- Automotive-specific: ISR-to-task communication, shared CAN buffers

---

## BEGINNER QUESTIONS

---

### Q1. What is a race condition? Give an automotive example and the fix.

**Short Answer:** A race condition occurs when two or more threads access shared data concurrently and the final result depends on the order of execution. In automotive, this can cause corrupted odometer readings, lost CAN messages, or incorrect sensor fusion state.

**Detailed Expert Answer:**

```c
/* RACE CONDITION EXAMPLE — TCU odometer update */
/* Two threads write to shared variable without synchronisation */

static uint32_t g_odometer_km = 0;  /* Shared — NO protection! */

/* Thread 1: GPS updates odometer from GPS distance */
void *gps_thread(void *arg) {
    while (1) {
        double dist = gps_get_distance_since_last();  /* e.g., 0.1 km */
        g_odometer_km += (uint32_t)(dist * 1000);    /* += 100m */
        /* Assembly expansion on Cortex-M (no atomic):
           LDR R0, [g_odometer_km]   ← Thread 1 reads: 1000
           ... context switch here!
           ADD R0, R0, #100
           STR R0, [g_odometer_km]   ← Writes 1100 (misses Thread 2's update)
        */
        usleep(100000);  /* 100ms */
    }
}

/* Thread 2: CAN wheel pulses also update odometer */
void *can_thread(void *arg) {
    while (1) {
        uint32_t pulses = can_get_wheel_pulses();
        g_odometer_km += pulses_to_km(pulses);  /* += 50m e.g. */
        usleep(10000);  /* 10ms */
    }
}

/* If both threads read 1000, add their values, then write:
   Thread 1 writes 1100, Thread 2 writes 1050 — one update lost!
   Odometer could under-read by up to 50km over a long trip */
```

**Fix with mutex:**
```c
#include <pthread.h>

static uint32_t        g_odometer_km = 0;
static pthread_mutex_t g_odometer_mutex = PTHREAD_MUTEX_INITIALIZER;

static inline void odometer_add(uint32_t delta_m) {
    pthread_mutex_lock(&g_odometer_mutex);
    g_odometer_km += delta_m;
    pthread_mutex_unlock(&g_odometer_mutex);
}

static inline uint32_t odometer_read(void) {
    pthread_mutex_lock(&g_odometer_mutex);
    uint32_t val = g_odometer_km;
    pthread_mutex_unlock(&g_odometer_mutex);
    return val;
}
```

**Fix with C++ atomic (lock-free, preferred for simple counters):**
```cpp
#include <atomic>

static std::atomic<uint32_t> g_odometer_m{0};  /* Atomic, in metres */

/* Thread-safe addition — no mutex needed */
void odometer_add(uint32_t delta_m) {
    g_odometer_m.fetch_add(delta_m, std::memory_order_relaxed);
    /* relaxed = no ordering constraints — only atomicity needed here */
}

uint32_t odometer_read_km(void) {
    return g_odometer_m.load(std::memory_order_relaxed) / 1000U;
}
```

---

### Q2. What is a mutex vs semaphore vs condition variable? When to use which?

**Short Answer:** Mutex = mutual exclusion (one owner, protects shared data). Semaphore = signalling mechanism (N slots, ISR→task sync). Condition variable = efficient waiting for a condition to become true (used with mutex).

**Detailed Expert Answer:**

```cpp
/* ===== MUTEX — protects shared data, one owner at a time ===== */
#include <mutex>

class CANBuffer {
    mutable std::mutex m_mutex;
    std::array<CANFrame, 128> m_buffer{};
    size_t m_count = 0;

public:
    bool push(const CANFrame &frame) {
        std::lock_guard<std::mutex> lock(m_mutex);  /* RAII — auto unlock */
        if (m_count >= m_buffer.size()) return false;
        m_buffer[m_count++] = frame;
        return true;
    }
};

/* ===== SEMAPHORE — counting/binary signalling ===== */
#include <semaphore.h>  /* POSIX */

sem_t g_can_rx_sem;
sem_init(&g_can_rx_sem, 0, 0);  /* Initial count = 0 */

/* In ISR or producer: signal consumer */
void CAN_Rx_Callback(void) {
    copy_frame_to_queue();
    sem_post(&g_can_rx_sem);  /* Increment count, wake waiter */
}

/* In consumer task: wait for signal */
void can_processor_thread(void) {
    while (1) {
        sem_wait(&g_can_rx_sem);  /* Block until count > 0 */
        process_can_frame();
    }
}

/* ===== CONDITION VARIABLE — wait for condition ===== */
#include <condition_variable>

class OTAController {
    std::mutex              m_mutex;
    std::condition_variable m_cv;
    bool                    m_ready = false;
    OTAPacket               m_packet{};

public:
    /* Producer: OTA download thread delivers packet */
    void deliver_packet(const OTAPacket &p) {
        {
            std::lock_guard<std::mutex> lock(m_mutex);
            m_packet = p;
            m_ready = true;
        }
        m_cv.notify_one();  /* Wake up exactly one waiting thread */
    }

    /* Consumer: flash writer thread waits for packet */
    OTAPacket wait_for_packet(void) {
        std::unique_lock<std::mutex> lock(m_mutex);
        m_cv.wait(lock, [this] { return m_ready; });
        /* Spurious wakeup safe — lambda predicate rechecked */
        m_ready = false;
        return m_packet;
    }
};
```

**Decision table:**
```
Need to protect shared data (one thread at a time)?
  → mutex (std::mutex or pthread_mutex)

Need to signal "event occurred" from ISR to task?
  → binary semaphore or task notification (FreeRTOS)

Need to limit concurrent access (e.g., max 4 threads in pool)?
  → counting semaphore (std::counting_semaphore C++20)

Need to wait for a complex condition (not just "data available")?
  → condition variable (with mutex)

Simple integer counter/flag, no complex condition?
  → std::atomic<T> (lock-free, fastest)
```

---

## INTERMEDIATE QUESTIONS

---

### Q3. Explain C++ memory ordering. When do you need acquire/release vs relaxed?

**Short Answer:** Memory ordering controls how CPU and compiler reorder memory operations around atomic loads/stores. `relaxed` = only atomicity. `acquire/release` = synchronisation point. `seq_cst` = total ordering (slowest, safest).

**Detailed Expert Answer:**

```cpp
/* ===== RELAXED — only atomicity, no ordering ===== */
/* Use for: independent counters, statistics, no happens-before relationship needed */

std::atomic<uint32_t> tx_count{0};
std::atomic<uint32_t> rx_count{0};

void on_can_tx(void) { tx_count.fetch_add(1, std::memory_order_relaxed); }
void on_can_rx(void) { rx_count.fetch_add(1, std::memory_order_relaxed); }

/* Both threads can read stale values of the other counter — that's fine for stats */

/* ===== ACQUIRE/RELEASE — synchronisation between producer and consumer ===== */
/* Use for: flagging that data is ready, lock-free buffer hand-off */

struct DataPacket {
    uint32_t vehicle_speed;
    uint32_t engine_rpm;
    uint64_t timestamp_us;
};

static DataPacket          g_packet{};
static std::atomic<bool>   g_packet_ready{false};

/* Producer thread (CAN Rx thread): */
void produce_packet(uint32_t speed, uint32_t rpm) {
    g_packet.vehicle_speed = speed;   /* Write data BEFORE setting flag */
    g_packet.engine_rpm    = rpm;
    g_packet.timestamp_us  = get_time_us();
    
    /* RELEASE: all writes above CANNOT be reordered past this store */
    g_packet_ready.store(true, std::memory_order_release);
}

/* Consumer thread (telemetry thread): */
void consume_packet(void) {
    /* ACQUIRE: all reads below CANNOT be reordered before this load */
    while (!g_packet_ready.load(std::memory_order_acquire)) {
        /* Spin or yield */
    }
    
    /* Guaranteed to see all writes from producer after release store */
    uint32_t speed = g_packet.vehicle_speed;  /* Safe: happened-before established */
    uint32_t rpm   = g_packet.engine_rpm;
    g_packet_ready.store(false, std::memory_order_relaxed);
}

/* ===== SEQ_CST — total global ordering ===== */
/* Use for: when you need global consistency across 3+ threads */
/* Default for std::atomic — safe but adds memory barrier on ARM/x86 */

std::atomic<int> x{0}, y{0};

/* Thread 1: */ x.store(1);         /* seq_cst by default */
/* Thread 2: */ y.store(1);
/* Thread 3: */ int r1 = x.load(); int r2 = y.load();
/* Thread 4: */ int r3 = y.load(); int r4 = x.load();
/* seq_cst guarantees: r1==1 implies r3==1 (total order) */
/* acquire/release does NOT guarantee this cross-thread property */
```

**Automotive use cases:**
```
relaxed:   CAN statistics counters, ODO meter pulse counting (single writer)
acquire/release: OTA state flag (download complete → flash state machine reads)
seq_cst:   Multi-producer ring buffer index management
```

---

### Q4. Implement a thread-safe lock-free ring buffer for CAN messages (ISR-safe).

**Expert Answer:**
```cpp
/* Single Producer Single Consumer (SPSC) lock-free ring buffer */
/* Safe for ISR → task communication without disabling interrupts */
/* Power-of-2 size allows cheap modulo via bitwise AND */

template<typename T, size_t N>
class SPSCRingBuffer {
    static_assert((N & (N - 1)) == 0, "N must be power of 2");
    
    alignas(64) std::atomic<uint32_t> m_head{0};  /* Written by producer */
    alignas(64) std::atomic<uint32_t> m_tail{0};  /* Written by consumer */
    alignas(64) std::array<T, N>      m_buf{};
    
    static constexpr uint32_t MASK = N - 1U;

public:
    /* Push — called by ISR or single producer thread */
    bool push(const T &item) noexcept {
        uint32_t head = m_head.load(std::memory_order_relaxed);
        uint32_t next = (head + 1U) & MASK;
        
        /* Full check: next == tail means buffer full */
        if (next == m_tail.load(std::memory_order_acquire)) {
            return false;  /* Buffer full — caller handles (DTC, counter) */
        }
        
        m_buf[head] = item;
        m_head.store(next, std::memory_order_release);
        return true;
    }
    
    /* Pop — called by single consumer thread */
    bool pop(T &item) noexcept {
        uint32_t tail = m_tail.load(std::memory_order_relaxed);
        
        /* Empty check */
        if (tail == m_head.load(std::memory_order_acquire)) {
            return false;  /* Buffer empty */
        }
        
        item = m_buf[tail];
        m_tail.store((tail + 1U) & MASK, std::memory_order_release);
        return true;
    }
    
    bool empty(void) const noexcept {
        return m_tail.load(std::memory_order_acquire) ==
               m_head.load(std::memory_order_acquire);
    }
    
    size_t size(void) const noexcept {
        uint32_t h = m_head.load(std::memory_order_acquire);
        uint32_t t = m_tail.load(std::memory_order_acquire);
        return (h - t) & MASK;
    }
};

/* Usage: */
struct CANFrame { uint32_t id; uint8_t dlc; uint8_t data[8]; };
static SPSCRingBuffer<CANFrame, 64> g_can_rx_buf;  /* 64 frames */

/* In CAN ISR: */
void CAN_Rx_ISR(void) {
    CANFrame f = read_hw_mailbox();
    if (!g_can_rx_buf.push(f)) {
        g_can_rx_overflow++;  /* Track drops */
    }
}

/* In processing task: */
void can_task(void) {
    CANFrame f;
    while (g_can_rx_buf.pop(f)) {
        process_frame(&f);
    }
}
```

---

## PRODUCTION SCENARIO QUESTIONS

---

### Q5. In production, a Continental telematics ECU shows intermittent data corruption in telemetry packets. The issue occurs only under high CAN bus load. How do you diagnose?

**Expert Answer:**

"This is a textbook example of a benign-looking race condition surfacing only under load.

**Hypothesis generation:**
```
Corruption under high load suggests:
1. Thread-unsafe buffer — writer modifies while reader serialises
2. DMA buffer reuse — CAN DMA overwrites buffer before telemetry copies it
3. Missing barrier — compiler/CPU reorders stores past flag check
4. Semaphore miss — packet processed before all bytes DMA-transferred
```

**Diagnosis steps:**
```bash
# Step 1: Enable thread sanitizer (TSan) in test build
CXXFLAGS="-fsanitize=thread -g -O1" cmake -DCMAKE_BUILD_TYPE=Debug

# TSan output example:
# WARNING: ThreadSanitizer: data race
#   Write of size 8 at 0x... by thread T2 (telemetry_thread):
#     #0 copy_can_to_telemetry()  tcu_manager.cpp:234
#   Read of size 8 at 0x... by thread T1 (can_rx_thread):
#     #0 fill_can_packet()  can_handler.cpp:178
# This directly identifies the racy lines!
```

**Root cause found (classic case):**
```cpp
/* Buggy code — g_telemetry_buf written by CAN thread, read by telemetry thread */
struct TelemetryPacket {
    uint32_t speed;
    uint32_t rpm;
    uint64_t timestamp;
    uint8_t  payload[48];
};

static TelemetryPacket g_telemetry_buf;  /* SHARED — no lock! */

/* CAN thread: fills struct field by field */
void on_can_speed(uint32_t speed) {
    g_telemetry_buf.speed     = speed;  /* Write #1 */
    g_telemetry_buf.timestamp = get_us(); /* Write #2 */
}

/* Telemetry thread: reads entire struct */
void send_telemetry(void) {
    mqtt_publish(&g_telemetry_buf, sizeof(g_telemetry_buf));
    /* If CAN thread writes between speed and timestamp writes: torn packet */
}
```

**Fix — double-buffering pattern:**
```cpp
/* Double buffer: one for writing, one for reading */
/* Swap with atomic pointer when write is complete */

class DoubleBuffer {
    TelemetryPacket m_buf[2];
    std::atomic<int> m_write_idx{0};  /* Which buffer writer is using */
    std::atomic<int> m_read_idx{1};   /* Which buffer reader can use */
    std::mutex m_swap_mutex;

public:
    TelemetryPacket *get_write_buf(void) {
        return &m_buf[m_write_idx.load(std::memory_order_relaxed)];
    }
    
    void commit_write(void) {
        std::lock_guard<std::mutex> lock(m_swap_mutex);
        int old_write = m_write_idx.load();
        m_write_idx.store(m_read_idx.load());
        m_read_idx.store(old_write, std::memory_order_release);
    }
    
    const TelemetryPacket *get_read_buf(void) const {
        return &m_buf[m_read_idx.load(std::memory_order_acquire)];
    }
};
```

**Production Insight (Continental project):** The bug was that three different CAN IDs all wrote into the same struct, and telemetry thread read it between the second and third write. Only surfaced at >200 CAN msg/s (8% CPU utilisation). ThreadSanitizer found it in 30 seconds on a stress test that replayed a captured high-load CAN trace. Fix was a copy-on-update pattern + commit flag."

---

## CHEAT SHEET — Multithreading

```
C++ Synchronisation Quick Reference:

std::mutex:               Lock/unlock, one owner, blocking
std::recursive_mutex:     Same thread can re-lock (careful with invariants)
std::timed_mutex:         try_lock_for(), try_lock_until()
std::shared_mutex:        Multiple readers OR one writer (reader-writer lock)

std::lock_guard:          RAII lock, no manual unlock
std::unique_lock:         RAII + unlock/relock for condition_variable
std::scoped_lock:         Multi-mutex deadlock-safe lock (C++17)

std::atomic<T>:           Lock-free for scalar types
  fetch_add, fetch_sub, exchange, compare_exchange_weak/strong
  
Memory orders:
  relaxed:       Only atomicity (no ordering)
  acquire:       Load — no reads/writes reordered after this
  release:       Store — no reads/writes reordered before this
  acq_rel:       Both (used in exchange, CAS)
  seq_cst:       Total order (default, safest, slowest)

std::condition_variable:  Wait for predicate
  wait(lock, pred)        Spurious-wakeup-safe
  notify_one()            Wake one waiter
  notify_all()            Wake all waiters

Common pitfalls:
  Spurious wakeup: always use predicate form of wait()
  Priority inversion: use priority-inheritance mutex
  Deadlock: always lock in the same order, use std::scoped_lock
  Data race: use ThreadSanitizer (-fsanitize=thread) to detect
  
Automotive rules:
  - ISR → task: use lock-free SPSC ring buffer or semaphore
  - Shared config: std::shared_mutex (many readers, rare writes)
  - Statistics counters: std::atomic<uint32_t> with relaxed
  - State transitions: std::atomic<enum> with acquire/release
  - No blocking in ISR context (no mutex lock in ISR!)
```
