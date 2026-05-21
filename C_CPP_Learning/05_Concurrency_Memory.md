# 05 — Concurrency & Memory Model
## Threads, Synchronisation, Atomics, Memory Model, Lock-Free Patterns

---

## Table of Contents

1. [Threading Fundamentals](#1-threading-fundamentals)
2. [std::thread & std::jthread](#2-stdthread--stdjthread)
3. [Mutex & Locking](#3-mutex--locking)
4. [Condition Variables](#4-condition-variables)
5. [std::async, future, promise](#5-stdasync-future-promise)
6. [Atomic Operations](#6-atomic-operations)
7. [C++ Memory Model](#7-c-memory-model)
8. [Lock-Free Programming](#8-lock-free-programming)
9. [C++20: latch, barrier, semaphore](#9-c20-latch-barrier-semaphore)
10. [Thread Pool Pattern](#10-thread-pool-pattern)
11. [Parallel STL Algorithms](#11-parallel-stl-algorithms)
12. [POSIX Threads (pthreads)](#12-posix-threads-pthreads)
13. [Thread-Local Storage](#13-thread-local-storage)
14. [Deadlock Avoidance](#14-deadlock-avoidance)
15. [Common Concurrency Bugs](#15-common-concurrency-bugs)

---

## 1. Threading Fundamentals

### 1.1 Why Concurrency Is Hard

Concurrency introduces three classes of problems:

| Problem | Description | Solution |
|---------|-------------|----------|
| **Data race** | Two threads access same memory, at least one writes, without synchronisation | mutex, atomic |
| **Deadlock** | Two threads each hold a lock the other needs | lock ordering, `std::lock` |
| **Race condition** | Correctness depends on thread scheduling order | correct synchronisation protocol |
| **Spurious wakeup** | Condition variable wakes without notification | always re-check condition in while loop |

### 1.2 When to Use Each Primitive

| Need | Primitive |
|------|-----------|
| Run code in parallel | `std::thread` / `std::jthread` |
| Return result from async work | `std::future` / `std::async` |
| Protect shared data | `std::mutex` + `std::lock_guard` |
| Wait for condition to become true | `std::condition_variable` |
| Simple counter / flag | `std::atomic` |
| Signal one event (one-shot) | `std::latch` (C++20) |
| Repeated synchronisation point | `std::barrier` (C++20) |
| Limit concurrent access (N slots) | `std::counting_semaphore` (C++20) |

---

## 2. std::thread & std::jthread

### 2.1 std::thread Basics

```cpp
#include <thread>
#include <iostream>

void worker(int id, std::string name) {
    std::cout << "Thread " << id << ": " << name << '\n';
}

std::thread t1(worker, 1, "Alice");    // Launch thread
std::thread t2(worker, 2, "Bob");

t1.join();   // MUST join or detach before t1 goes out of scope
t2.join();   // (or destructor calls std::terminate)

// Detach: let thread run independently (fire-and-forget)
std::thread t3(worker, 3, "Carol");
t3.detach(); // t3 object can be destroyed; thread runs until completion

// Lambda thread
std::thread t4([](int n) {
    std::cout << "Lambda: " << n << '\n';
}, 42);
t4.join();

// Thread ID
t1.get_id();
std::this_thread::get_id();

// Hardware concurrency
unsigned hw = std::thread::hardware_concurrency();  // # of CPU cores
```

### 2.2 std::jthread (C++20 — Joining Thread)

```cpp
#include <thread>

// jthread automatically joins on destruction (RAII)
// Also supports cooperative cancellation via std::stop_token
{
    std::jthread jt([](std::stop_token stoken) {
        while (!stoken.stop_requested()) {
            // Do work...
            std::this_thread::yield();
        }
        std::cout << "Thread stopping gracefully\n";
    });

    // ... do other work ...
    jt.request_stop();   // Request the thread to stop
    // jt.join() called automatically in destructor
}
```

---

## 3. Mutex & Locking

### 3.1 Mutex Variants

```cpp
#include <mutex>

std::mutex              mtx;    // Basic mutual exclusion; non-recursive
std::recursive_mutex    rmtx;   // Same thread can lock multiple times
std::timed_mutex        tmtx;   // try_lock_for / try_lock_until
std::recursive_timed_mutex rtmtx;
std::shared_mutex       smtx;   // Reader-writer lock (C++17) — multiple readers OR one writer
```

### 3.2 Lock Guards (RAII)

```cpp
// std::lock_guard — simplest RAII wrapper; cannot unlock early
{
    std::lock_guard<std::mutex> guard(mtx);   // Locks on construction
    // ... critical section ...
}   // Destructor unlocks — even if exception thrown

// C++17: deduction guide
std::lock_guard guard(mtx);   // No need to specify std::mutex

// std::unique_lock — flexible; can unlock/relock, used with condition_variable
{
    std::unique_lock<std::mutex> lock(mtx);   // Locks immediately
    lock.unlock();             // Unlock before scope end
    // ... non-critical work ...
    lock.lock();               // Relock
    // ... critical section ...
}   // Destructor unlocks

// std::scoped_lock (C++17) — locks multiple mutexes atomically (deadlock-free)
std::scoped_lock lock(mtx1, mtx2);   // Both locked; no deadlock
```

### 3.3 std::shared_mutex (Reader-Writer Lock)

```cpp
#include <shared_mutex>

std::shared_mutex rw_mtx;

// Writer: exclusive lock
void writeData(int val) {
    std::unique_lock<std::shared_mutex> write_lock(rw_mtx);
    data_ = val;   // Only one writer at a time; no readers
}

// Reader: shared lock (multiple readers allowed simultaneously)
int readData() {
    std::shared_lock<std::shared_mutex> read_lock(rw_mtx);
    return data_;  // Many readers can hold simultaneously
}
```

### 3.4 std::once_flag & std::call_once

```cpp
// Initialise shared resource exactly once (thread-safe)
std::once_flag init_flag;

void ensureInit() {
    std::call_once(init_flag, []() {
        // Runs exactly once, even if called from multiple threads
        initDatabase();
    });
}
```

---

## 4. Condition Variables

Condition variables allow threads to **wait for a condition** to become true.

### 4.1 Producer-Consumer Pattern

```cpp
#include <condition_variable>
#include <queue>
#include <mutex>

std::queue<int>          q;
std::mutex               q_mtx;
std::condition_variable  q_cv;
bool                     done = false;

// Consumer thread
void consumer() {
    std::unique_lock<std::mutex> lock(q_mtx);
    while (true) {
        // Always check condition in while loop (guards against spurious wakeups)
        q_cv.wait(lock, []{ return !q.empty() || done; });
        //       └──────── Predicate: re-check after wakeup
        // wait() releases lock and blocks; reacquires lock when notified + predicate true

        if (done && q.empty()) break;

        int item = q.front(); q.pop();
        lock.unlock();         // Allow producer to push while we process
        process(item);
        lock.lock();
    }
}

// Producer thread
void producer() {
    for (int i = 0; i < 100; i++) {
        {
            std::lock_guard<std::mutex> lock(q_mtx);
            q.push(i);
        }
        q_cv.notify_one();   // Wake one waiting consumer
    }
    {
        std::lock_guard<std::mutex> lock(q_mtx);
        done = true;
    }
    q_cv.notify_all();   // Wake all consumers to check done flag
}
```

### 4.2 condition_variable_any

Works with **any** lockable type (not just `std::mutex`). Use with `std::shared_mutex` or custom locks.

---

## 5. std::async, future, promise

### 5.1 std::async

```cpp
#include <future>

// Launch function asynchronously; returns a future
auto fut = std::async(std::launch::async, [](int n) {
    return n * n;
}, 10);

// Do other work here...

int result = fut.get();   // Blocks until result is ready; 100
// get() can only be called ONCE — future is then invalid
```

### 5.2 std::promise / std::future

```cpp
// Promise is the write-end; future is the read-end of a channel
std::promise<int> promise;
std::future<int>  future = promise.get_future();

std::thread worker([&promise]() {
    int result = compute();
    promise.set_value(result);            // Wake any thread waiting on future
    // or on error:
    // promise.set_exception(std::make_exception_ptr(MyException{}));
});

int val = future.get();   // Block until worker calls set_value
worker.join();
```

### 5.3 std::shared_future

```cpp
// Multiple threads can all call get() on a shared_future
std::shared_future<int> sfut = promise.get_future().share();

// Now many threads can:
sfut.get();   // All receive the same result
```

---

## 6. Atomic Operations

### 6.1 std::atomic Basics

```cpp
#include <atomic>

std::atomic<int>  counter{0};
std::atomic<bool> flag{false};

// Basic operations — all guaranteed atomic (no mutex needed)
counter++;                        // Atomic increment
counter.fetch_add(1);             // Same
int old = counter.fetch_add(5);   // Returns old value before add

counter.load();                   // Read
counter.store(42);                // Write
counter.exchange(100);            // Write, return old value

// Compare-and-swap (CAS) — foundation of lock-free algorithms
int expected = 5;
bool success = counter.compare_exchange_strong(expected, 10);
// If counter == expected (5): sets counter=10, returns true
// If counter != expected: sets expected=counter, returns false

// Weak version: may fail spuriously but faster on some architectures
counter.compare_exchange_weak(expected, 10);  // Loop-safe version
```

### 6.2 std::atomic_flag (Spinlock)

```cpp
// Lock-free spinlock using atomic_flag
class SpinLock {
    std::atomic_flag flag_ = ATOMIC_FLAG_INIT;
public:
    void lock() {
        while (flag_.test_and_set(std::memory_order_acquire)) {
            // Spin until we set the flag (previous holder cleared it)
            std::this_thread::yield();  // Hint to scheduler
        }
    }
    void unlock() {
        flag_.clear(std::memory_order_release);
    }
};
```

---

## 7. C++ Memory Model

### 7.1 Why We Need a Memory Model

Without explicit ordering, compilers and CPUs **reorder instructions** for performance. The memory model defines which reorderings are allowed and how threads observe each other's writes.

### 7.2 Happens-Before

A **happens-before** relationship guarantees that if operation A happens-before operation B, then B will see the effects of A.

```
Thread 1:          Thread 2:
x = 1              // What does Thread 2 see?
y.store(1)         while (y.load() != 1) {}
                   read(x);  // Is x guaranteed to be 1?
```

**Without ordering**: NO guarantee — CPU/compiler may reorder the stores.
**With acquire-release**: YES — the store to `y` synchronises with the load of `y`.

### 7.3 Memory Order Values

```cpp
std::memory_order_relaxed    // No ordering constraints; only atomicity
std::memory_order_consume    // (Deprecated-ish) data dependency ordering
std::memory_order_acquire    // No later reads/writes can move before this load
std::memory_order_release    // No earlier reads/writes can move after this store
std::memory_order_acq_rel    // Both acquire and release (for RMW operations)
std::memory_order_seq_cst    // Default; total sequential ordering across all threads
```

### 7.4 Acquire-Release Pattern

```cpp
// Thread 1 (writer):
data.store(42, std::memory_order_relaxed);    // Write data first
ready.store(true, std::memory_order_release); // RELEASE: all prior writes visible

// Thread 2 (reader):
while (!ready.load(std::memory_order_acquire)) {}  // ACQUIRE: spin until ready
int val = data.load(std::memory_order_relaxed);     // Guaranteed to see 42
// The ACQUIRE of ready "synchronises-with" the RELEASE of ready
// → happens-before: all Thread 1 writes before release VISIBLE to Thread 2 after acquire
```

### 7.5 Sequential Consistency (seq_cst)

```cpp
// Default for all atomics; easiest to reason about; most expensive
// All seq_cst operations form a single total order visible to all threads

std::atomic<int> x{0}, y{0};

// Thread 1:
x.store(1);    // seq_cst (default)
int ry = y.load();

// Thread 2:
y.store(1);
int rx = x.load();

// With seq_cst: IMPOSSIBLE for both rx==0 and ry==0
// Without seq_cst (relaxed): both could be 0
```

### 7.6 Memory Ordering Choice Guide

| Use Case | Memory Order |
|---------|-------------|
| Simple counter (no ordering needed) | `relaxed` |
| Publish-subscribe (one writer, one reader) | `release` on write, `acquire` on read |
| Lock implementation | `acquire` on lock, `release` on unlock |
| Everything else / correctness first | `seq_cst` (default) |

---

## 8. Lock-Free Programming

### 8.1 Lock-Free Stack

```cpp
template <typename T>
class LockFreeStack {
    struct Node {
        T         value;
        Node*     next;
    };
    std::atomic<Node*> head_{nullptr};

public:
    void push(T val) {
        Node* new_node = new Node{std::move(val), nullptr};
        new_node->next = head_.load(std::memory_order_relaxed);
        // CAS loop: try to set head to new_node
        while (!head_.compare_exchange_weak(
            new_node->next,   // expected (updated on failure)
            new_node,         // desired
            std::memory_order_release,
            std::memory_order_relaxed)) {
            // retry on failure
        }
    }

    std::optional<T> pop() {
        Node* old_head = head_.load(std::memory_order_acquire);
        while (old_head &&
               !head_.compare_exchange_weak(
                   old_head,
                   old_head->next,
                   std::memory_order_acquire,
                   std::memory_order_relaxed)) {
            // retry
        }
        if (!old_head) return std::nullopt;
        T val = std::move(old_head->value);
        delete old_head;   // NOTE: ABA problem not handled here — use hazard pointers
        return val;
    }
};
```

### 8.2 ABA Problem

```cpp
// Thread 1 reads head = A
// Thread 2: pops A, pops B, pushes A again — head is A again
// Thread 1's CAS(A → C) succeeds — but node B was lost!

// Solutions:
// 1. Tagged pointer: pack a version counter into the pointer bits
// 2. Hazard pointers: mark pointers in-use before using them
// 3. RCU (Read-Copy-Update): epoch-based reclamation
```

---

## 9. C++20: latch, barrier, semaphore

### 9.1 std::latch (One-Shot Countdown)

```cpp
#include <latch>

std::latch latch{4};   // Count = 4

// Each worker calls count_down() when ready
auto worker = [&latch](int id) {
    doWork(id);
    latch.count_down();   // Decrement count; wake waiters when 0
};

for (int i = 0; i < 4; i++) threads.emplace_back(worker, i);

latch.wait();   // Block until count reaches 0
// All 4 workers have finished initialisation
// Latch CANNOT be reset — single use only
```

### 9.2 std::barrier (Reusable)

```cpp
#include <barrier>

// Synchronisation point all threads must reach before any can continue
std::barrier bar{4, []() noexcept {
    // Completion function: called once when all threads arrive
    // Runs before any thread is released
    swapBuffers();
}};

auto worker = [&bar](int id) {
    while (hasWork()) {
        processChunk(id);
        bar.arrive_and_wait();   // Wait for all threads to finish chunk
        // All threads resume here together for next iteration
    }
};
```

### 9.3 std::semaphore

```cpp
#include <semaphore>

// Binary semaphore (mutex-like but can be signalled from different thread)
std::binary_semaphore ready{0};   // Initial count = 0

// Thread 1: signal when ready
ready.release();   // count → 1

// Thread 2: wait for signal
ready.acquire();   // blocks if count == 0; decrements to 0 when unblocked

// Counting semaphore: limit N concurrent accesses
std::counting_semaphore<4> pool{4};  // Max 4 concurrent users

pool.acquire();   // Take one slot (blocks if 0)
// ... use shared resource ...
pool.release();   // Return slot
```

---

## 10. Thread Pool Pattern

```cpp
#include <thread>
#include <mutex>
#include <condition_variable>
#include <queue>
#include <functional>
#include <vector>

class ThreadPool {
    std::vector<std::thread>          workers_;
    std::queue<std::function<void()>> tasks_;
    std::mutex                        mtx_;
    std::condition_variable           cv_;
    bool                              stop_ = false;

public:
    explicit ThreadPool(size_t num_threads) {
        for (size_t i = 0; i < num_threads; ++i) {
            workers_.emplace_back([this]() {
                while (true) {
                    std::function<void()> task;
                    {
                        std::unique_lock<std::mutex> lock(mtx_);
                        cv_.wait(lock, [this] {
                            return stop_ || !tasks_.empty();
                        });
                        if (stop_ && tasks_.empty()) return;
                        task = std::move(tasks_.front());
                        tasks_.pop();
                    }
                    task();   // Execute task outside the lock
                }
            });
        }
    }

    template <typename F>
    auto submit(F&& f) -> std::future<std::invoke_result_t<F>> {
        using ReturnType = std::invoke_result_t<F>;
        auto pkg  = std::make_shared<std::packaged_task<ReturnType()>>(std::forward<F>(f));
        auto fut  = pkg->get_future();
        {
            std::lock_guard<std::mutex> lock(mtx_);
            if (stop_) throw std::runtime_error("Pool is stopped");
            tasks_.emplace([pkg]{ (*pkg)(); });
        }
        cv_.notify_one();
        return fut;
    }

    ~ThreadPool() {
        { std::lock_guard<std::mutex> lock(mtx_); stop_ = true; }
        cv_.notify_all();
        for (auto& t : workers_) t.join();
    }
};

// Usage
ThreadPool pool(4);
auto f1 = pool.submit([]{ return compute_something(); });
auto f2 = pool.submit([]{ return compute_other(); });
int r1 = f1.get(), r2 = f2.get();
```

---

## 11. Parallel STL Algorithms

C++17 adds execution policies to standard algorithms.

```cpp
#include <execution>
#include <algorithm>
#include <numeric>

std::vector<int> v = { ... };  // Large vector

// Sequential (default behaviour)
std::sort(std::execution::seq, v.begin(), v.end());

// Parallel (uses thread pool internally)
std::sort(std::execution::par, v.begin(), v.end());

// Parallel + SIMD vectorised
std::sort(std::execution::par_unseq, v.begin(), v.end());
// NOTE: lambdas used with par_unseq must not synchronise (no mutexes)

// Parallel reduce (parallel accumulate)
auto sum = std::reduce(std::execution::par, v.begin(), v.end(), 0);
// reduce (unlike accumulate) doesn't guarantee left-to-right order

// Parallel transform-reduce (common pattern)
auto dot = std::transform_reduce(
    std::execution::par,
    a.begin(), a.end(),
    b.begin(),
    0,                          // Identity
    std::plus{},                // Reduce op
    std::multiplies{}           // Transform op
);
```

---

## 12. POSIX Threads (pthreads)

Lower-level threading; used in C code and available on all POSIX systems.

```cpp
#include <pthread.h>

// Thread function signature must be: void* fn(void*)
void* worker(void* arg) {
    int id = *(int*)arg;
    printf("Thread %d running\n", id);
    return nullptr;
}

pthread_t tid;
int id = 5;
pthread_create(&tid, nullptr, worker, &id);
pthread_join(tid, nullptr);   // Wait for completion

// Mutex
pthread_mutex_t mtx = PTHREAD_MUTEX_INITIALIZER;
pthread_mutex_lock(&mtx);
// ... critical section ...
pthread_mutex_unlock(&mtx);
pthread_mutex_destroy(&mtx);

// Condition variable
pthread_cond_t cond = PTHREAD_COND_INITIALIZER;
pthread_cond_wait(&cond, &mtx);   // Release mtx and wait; reacquires on wakeup
pthread_cond_signal(&cond);        // Wake one waiter
pthread_cond_broadcast(&cond);     // Wake all waiters
pthread_cond_destroy(&cond);
```

---

## 13. Thread-Local Storage

Each thread gets its own independent copy of a thread-local variable.

```cpp
// C++11 thread_local keyword
thread_local int error_code = 0;       // Each thread has its own error_code
thread_local std::string buffer;        // Each thread has its own buffer

void setError(int code) { error_code = code; }
int  getError()         { return error_code; }

// No mutex needed! Different threads never share thread_local variables

// Thread-local with class
struct PerThreadCache {
    std::vector<int> items;
};
thread_local PerThreadCache cache;
```

---

## 14. Deadlock Avoidance

### 14.1 Lock Ordering

```cpp
// RULE: Always acquire locks in the same order across all threads
// Thread A: lock(mtx1) then lock(mtx2)
// Thread B: lock(mtx1) then lock(mtx2)  ← same order = no deadlock

// DEADLOCK if:
// Thread A: lock(mtx1) then lock(mtx2)
// Thread B: lock(mtx2) then lock(mtx1)  ← different order!
```

### 14.2 std::lock — Atomic Multi-Lock Acquisition

```cpp
// Acquires BOTH locks atomically without risk of deadlock
// Uses deadlock avoidance algorithm (no arbitrary ordering required)
std::mutex mtx1, mtx2;
std::lock(mtx1, mtx2);   // Acquires both; on failure: releases all and retries
std::lock_guard<std::mutex> g1(mtx1, std::adopt_lock);  // take ownership
std::lock_guard<std::mutex> g2(mtx2, std::adopt_lock);

// C++17: scoped_lock does this in one step
std::scoped_lock lock(mtx1, mtx2);   // Deadlock-free acquisition of both
```

### 14.3 Lock Hierarchy (Practical)

```cpp
// Assign a numeric level to each mutex; only allow locking lower levels
// when a higher level is already held
class HierarchicalMutex {
    std::mutex        inner_;
    unsigned          level_;
    unsigned          prev_level_{0};

    inline thread_local static unsigned this_thread_level = UINT_MAX;

public:
    explicit HierarchicalMutex(unsigned level) : level_(level) {}

    void lock() {
        if (level_ >= this_thread_level)
            throw std::logic_error("Mutex hierarchy violated");
        inner_.lock();
        prev_level_ = this_thread_level;
        this_thread_level = level_;
    }

    void unlock() {
        this_thread_level = prev_level_;
        inner_.unlock();
    }
};
```

---

## 15. Common Concurrency Bugs

### 15.1 Data Race

```cpp
// BUG: Two threads write to same non-atomic variable
int shared_counter = 0;
void bad_increment() { shared_counter++; }  // Read-modify-write: NOT atomic!

// FIX 1: mutex
std::mutex mtx;
void good_increment() {
    std::lock_guard lock(mtx);
    shared_counter++;
}

// FIX 2: atomic
std::atomic<int> atomic_counter{0};
void best_increment() { atomic_counter++; }
```

### 15.2 Spurious Wakeup

```cpp
// BUG: Only checks condition once
std::condition_variable cv;
bool ready = false;
void consumer() {
    std::unique_lock<std::mutex> lock(mtx);
    cv.wait(lock);           // BUG: may wake spuriously!
    process();
}

// FIX: Always wrap cv.wait in a while loop checking condition
void consumer_fixed() {
    std::unique_lock<std::mutex> lock(mtx);
    cv.wait(lock, []{ return ready; });  // Equivalent to while(!ready) cv.wait(lock)
    process();
}
```

### 15.3 Calling std::thread::join() Twice

```cpp
std::thread t(worker);
t.join();
t.join();   // BUG: undefined behaviour! Check joinable() first

if (t.joinable()) t.join();   // Safe
```

### 15.4 Accessing Destroyed mutex

```cpp
// BUG: Lambda captures mutex by reference; mutex destroyed before thread finishes
std::thread spawnThread() {
    std::mutex mtx;                          // LOCAL mutex
    return std::thread([&mtx]{ mtx.lock(); }); // DANGLES after spawnThread returns
}
// FIX: Use shared_ptr or ensure lifetime exceeds thread lifetime
```

---

*Continue to*: [06_Systems_Debugging.md](06_Systems_Debugging.md) — memory layout, undefined behaviour, sanitisers, GDB, CMake, profiling, and compiler internals.
