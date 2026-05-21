# 17 — MISRA C++ and AUTOSAR C++14 Guidelines

> **Standards:** MISRA C++:2008, MISRA C++:2023, AUTOSAR C++14 (2019)  
> **Tools:** Polyspace Bug Finder, Axivion Suite, Parasoft C++test, PC-lint Plus

---

## 17.1 Why MISRA C++?

```
Problem: C++ has many features that are safe on desktop but dangerous in embedded systems:
  - Exceptions: non-deterministic stack unwinding, extra ROM/RAM overhead
  - RTTI (typeid, dynamic_cast): runtime overhead, not available in -fno-rtti builds
  - Dynamic allocation: heap fragmentation, non-deterministic timing (→ 18-4-1)
  - Template metaprogramming: complex, hard to review, may cause code bloat
  - Undefined behaviour (UB): signed overflow, null deref, out-of-bounds → exploitable bugs

MISRA C++ provides rules to eliminate these hazards.
3 categories: Required (must follow), Advisory (should follow), Document (justify deviation)
```

---

## 17.2 Top 20 Critical MISRA C++ Rules

### Rule 0-3-1 — Minimise undefined behaviour
```cpp
// BAD: signed integer overflow is UB in C++
int a = INT_MAX;
int b = a + 1;  // UNDEFINED BEHAVIOUR — may or may not wrap

// GOOD: use uint32_t for counters, check before overflow
uint32_t counter = 0xFFFFFFFFU;
if (counter < UINT32_MAX) { ++counter; }
```

### Rule 2-10-2 — Identifiers should not shadow outer scope
```cpp
// BAD: inner 'speed' shadows outer 'speed' — confusing
float speed = readSpeed();
if (true) {
    float speed = 0.0F;  // shadows outer — MISRA violation
}

// GOOD: use distinct names
float vehicleSpeed = readSpeed();
float filteredSpeed = 0.0F;
```

### Rule 4-5-1 — Expressions with enum values and integer types
```cpp
// BAD: mixing enum with int arithmetic
enum class Gear { PARK=0, REVERSE, NEUTRAL, DRIVE };
Gear g = DRIVE;
int n = g + 1;  // implicit conversion: MISRA violation

// GOOD: explicit cast
int n = static_cast<int>(g) + 1;
```

### Rule 5-0-15 — Array indexing must use valid bounds
```cpp
static constexpr std::size_t MAX_N = 10U;
float data[MAX_N];

// BAD: index not bounds-checked
float val = data[idx];  // idx might be >= MAX_N

// GOOD: bounds check at access point
float val = (idx < MAX_N) ? data[idx] : 0.0F;
```

### Rule 6-2-1 — Assignment operators must not return references to *this for MISRA violation
(MISRA A6-5-1 AUTOSAR: No copy assignment returning reference to incomplete type)

### Rule 7-1-2 — A pointer or reference to const shall only be used where needed
```cpp
// GOOD: pass large structs by const reference
void processFrame(const CanFrame& frame);  // OK

// BAD: unnecessary mutable reference
void processFrame(CanFrame& frame);  // unless you modify frame
```

### Rule 8-4-1 — Functions shall not be defined using the ellipsis notation
```cpp
// BAD: variadic function — type unsafe
void log(const char* fmt, ...);  // MISRA violation

// GOOD: explicit parameters or template overloads
template <typename T>
void logValue(const char* name, T value);
```

### Rule 14-6-1 — In a class template, all member functions shall be defined in the template
(Ensures no implicit instantiation surprises)

### Rule 15-0-3 — Control shall not be transferred into a try or catch block using a goto
(Also: Rule 15-1-1: do not use setjmp/longjmp — non-local jumps are UB in C++ with objects)

### Rule 15-3-3 — Handlers of a function-try-block shall declare the same exceptions
(AUTOSAR: exceptions completely forbidden in safety-critical code — -fno-exceptions)

### Rule 16-0-1 — #include only allowed at global scope, include guards required
```cpp
// GOOD: every header has include guard or #pragma once
#ifndef LKA_CONTROLLER_HPP
#define LKA_CONTROLLER_HPP
// ... declarations ...
#endif
```

### Rule 17-0-5 — The name of a standard library macro or object shall not be reused
```cpp
// BAD: redefine assert
#define assert(x) do {} while(0)  // breaks standard assert → MISRA violation
```

### Rule 18-4-1 — Dynamic heap memory shall not be used (CRITICAL)
```cpp
// BAD: heap allocation forbidden in safety code
auto p = new LkaController();        // forbidden
auto v = std::make_unique<Sensor>(); // forbidden (allocates heap)
std::vector<int> v;                  // forbidden (heap-backed)

// GOOD: static allocation
static LkaController lka;            // OK
std::array<int, 16> arr{};           // OK — stack
```

### Rule 18-0-4 — The time-handling functions of <ctime> shall not be used
(Non-deterministic on embedded, OS-dependent — use hardware timers instead)

### Rule 27-0-1 — The stream input/output library <iostream> shall not be used
(std::cout has heap allocation, exceptions, OS dependency — forbidden in production ECU)

---

## 17.3 AUTOSAR C++14 Specific Rules

```
AUTOSAR C++14 guidelines (A-numbered) extend MISRA for modern C++:

A0-1-1: No dead code (unreachable code). CI must verify with coverage.
A2-11-1: Volatile only for hardware registers or ISR-shared variables.
A5-10-1: Pointer to member virtual function shall not be used.
A5-16-1: Ternary operator shall not be used as sub-expression.
A6-2-2: Expression statements shall not be explicitly void-cast (MISRA 0-1-6 extension)
A8-4-1: Functions shall not be defined using the ellipsis notation.
A12-8-3: Moved-from object shall only be destroyed or assigned.
A18-1-1: C-style arrays shall not be used (use std::array instead).
A18-5-10: The std::move shall only be used to move non-const lvalue references.
A23-0-1: An instance of std::initializer_list shall not be moved.

Example compliant code:
  std::array<float, 8U> sensorData{};  // A18-1-1 compliant (not float[8])
  auto& ref = sensorData[0U];          // OK: bounds checked in debug builds
```

---

## 17.4 Static Analysis Tool Workflow

```
1. Developer writes code with MISRA/AUTOSAR flags
2. CI pipeline runs static analysis:
   
   Polyspace Bug Finder:
     polyspace-bug-finder \
       -sources lka_controller.cpp \
       -misra-cpp 2008 \
       -autosar-cpp14 \
       -checkers all
   
   Results: GREEN (proven no defect) / ORANGE (unproven — review) / RED (defect)
   
   Axivion Suite: architectural analysis + MISRA + complexity metrics (cyclomatic)
   Parasoft C++test: MISRA + unit test generation + code review integration

3. Deviations: if MISRA rule must be violated, document via:
   // MISRA C++ Rule 18-4-1 Deviation: heap used only during startup (once, not freed)
   // Safety analysis: startup-only, deterministic timing — acceptable
   // Approved by: [safety engineer], [date]
   
4. Review: qualified MISRA checker result is part of software release evidence
   (ASPICE SWE.4 unit test, SWE.5 integration)
```

---

## 17.5 Interview Questions

```
L1:
  Q: Name 3 C++ features forbidden in MISRA for automotive ECU.
  A: 1. Dynamic heap allocation (new/delete, malloc/free): non-deterministic, fragmentation
     2. Exceptions (try/catch/throw): stack unwinding overhead, non-deterministic latency
     3. RTTI (dynamic_cast, typeid): runtime type table overhead, -fno-rtti breaks RTTI
     Also commonly forbidden: goto (control flow confusion), recursion (stack depth unknown),
     global mutable state (concurrency hazard).

  Q: What is the purpose of a MISRA deviation?
  A: When a MISRA rule cannot be followed due to a legitimate reason, a deviation documents:
     1. Which rule is violated (rule number, short description)
     2. Why the deviation is necessary (technical justification)
     3. Risk analysis (why it is still safe)
     4. Who approved it (safety engineer sign-off)
     
     Example: using printf() in a test build (Rule 27-0-1 deviation for host testing only).
     Deviations are NOT exceptions from safety — they require explicit justification.

L2:
  Q: Why is volatile important in embedded C++ (MISRA A2-11-1)?
  A: volatile tells the compiler: this variable may change outside the program's control.
     → Compiler must NOT cache it in a register, must NOT reorder reads/writes to it.
     
     When to use:
     1. Memory-mapped hardware register: volatile uint32_t* CAN_REG = (uint32_t*)0x40000000;
        Without volatile: compiler may optimise away repeated reads.
     2. ISR-shared variable: volatile bool canRxFlag; (set in ISR, read in task)
        Without volatile: compiler may keep old cached value in task loop.
     
     MISRA A2-11-1: only use volatile for these two cases.
     COMMON MISTAKE: using volatile for thread synchronisation (does NOT make it atomic!).
     For multi-threaded: use std::atomic<T> instead.

L3:
  Q: How does a static analysis tool like Polyspace prove code is defect-free?
  A: Polyspace uses abstract interpretation — a mathematical framework that:
     1. Computes ALL possible values for every variable at every program point
        (without running the code)
     2. For each operation, checks: can this possibly overflow/null-deref/etc.?
     
     Results:
     GREEN: proven safe — all possible inputs lead to defined behaviour here.
     ORANGE: unknown — may or may not be safe. Developer must review.
     RED: proven unsafe — at least one input causes defect here.
     
     For ASIL-D: require 0 RED results + all ORANGE reviewed/documented.
     Full formal verification (model checker) used for most critical safety goals:
       SCADE (Esterel Technologies): formal specification + code generation for ASIL-D
       Verified that: no runtime error exists in the generated code
```
