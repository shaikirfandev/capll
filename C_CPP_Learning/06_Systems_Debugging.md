# 06 — Systems & Debugging
## Memory Layout, UB, Sanitisers, GDB, CMake, Profiling, Compiler Internals

---

## Table of Contents

1. [Process Memory Layout](#1-process-memory-layout)
2. [Struct Padding & Alignment](#2-struct-padding--alignment)
3. [Undefined Behaviour (UB) Catalogue](#3-undefined-behaviour-ub-catalogue)
4. [AddressSanitizer (ASan)](#4-addresssanitizer-asan)
5. [ThreadSanitizer (TSan)](#5-threadsanitizer-tsan)
6. [UndefinedBehaviourSanitizer (UBSan)](#6-undefinedbehavioursanitizer-ubsan)
7. [Valgrind](#7-valgrind)
8. [GDB Reference](#8-gdb-reference)
9. [CMake](#9-cmake)
10. [Linking & Symbols](#10-linking--symbols)
11. [Performance Profiling](#11-performance-profiling)
12. [Compiler Optimisation Flags](#12-compiler-optimisation-flags)
13. [GCC/Clang Extensions](#13-gccclang-extensions)
14. [Cross-Compilation](#14-cross-compilation)
15. [SIMD Intrinsics Overview](#15-simd-intrinsics-overview)

---

## 1. Process Memory Layout

```
High addresses
┌──────────────────────────────┐
│           Stack              │ ← grows down (toward lower addresses)
│   local variables, frames    │   default: 8 MB on Linux
│        ↓ grows ↓             │
├──────────────────────────────┤
│         (gap)                │
├──────────────────────────────┤
│        ↑ grows ↑             │
│  Heap (dynamic allocation)   │ ← malloc/new allocates here
│                              │
├──────────────────────────────┤
│  BSS segment                 │ ← uninitialised static/global variables (zero-init)
│  (zero-initialised)          │   stored as just a size in ELF; OS zero-pages on demand
├──────────────────────────────┤
│  Data segment                │ ← initialised static/global variables
│  (initialised data)          │   e.g., int x = 5; (global)
├──────────────────────────────┤
│  Text segment (code)         │ ← compiled instructions (read-only, executable)
├──────────────────────────────┤
│  Read-only data (rodata)     │ ← string literals, const globals
└──────────────────────────────┘
Low addresses
```

### 1.1 Where Variables Live

```cpp
int global_init   = 5;       // Data segment
int global_uninit;           // BSS segment (zero)
const char* msg   = "hi";    // "hi" → rodata; msg (pointer) → data

void foo() {
    int local = 5;           // Stack frame of foo()
    static int s = 10;       // Data segment (persists across calls)
    int* p = new int(42);    // *p → heap; p (pointer) → stack
}
```

### 1.2 Stack Frame Structure

```
┌────────────────────────┐  ← previous frame
│  return address        │  ← set by call instruction
│  saved rbp             │  ← callee saves caller's base pointer
│  local variables       │  ← [rbp - offset]
│  saved registers       │  ← callee-saved registers
└────────────────────────┘  ← rsp (stack pointer)
```

---

## 2. Struct Padding & Alignment

### 2.1 Why Padding Exists

CPUs typically access memory most efficiently when data is **aligned** to its own size boundary (int at multiple of 4, double at multiple of 8). Compilers insert padding to ensure alignment.

```cpp
struct S1 {
    char  a;    // 1 byte; at offset 0
    // 3 bytes padding (to align 'b' to 4-byte boundary)
    int   b;    // 4 bytes; at offset 4
    char  c;    // 1 byte; at offset 8
    // 3 bytes padding (to make struct size multiple of 4 = its max alignment)
};
sizeof(S1);   // 12 bytes (not 6!)

// Reordering fields by size (largest first) minimises padding:
struct S2 {
    int   b;    // 4 bytes; offset 0
    char  a;    // 1 byte;  offset 4
    char  c;    // 1 byte;  offset 5
    // 2 bytes padding
};
sizeof(S2);   // 8 bytes
```

### 2.2 Checking Layout

```cpp
#include <cstddef>

static_assert(offsetof(S1, a) == 0);
static_assert(offsetof(S1, b) == 4);
static_assert(sizeof(S1) == 12);
```

### 2.3 Packed Struct (No Padding)

```cpp
struct __attribute__((packed)) Packed {
    char a;   // offset 0
    int  b;   // offset 1 (unaligned!)
    char c;   // offset 5
};
sizeof(Packed);   // 6 bytes — but UNALIGNED access may be slow or crash on some CPUs
// Use only for network protocols, file formats — not general data
```

### 2.4 alignas / alignof (C++11)

```cpp
alignof(int);      // 4 — alignment requirement of int
alignof(double);   // 8

struct alignas(16) SimdVec {   // Force 16-byte alignment (for SSE/NEON)
    float data[4];
};

alignas(64) char cache_line[64];   // Aligned to cache line boundary

// std::aligned_storage (C++11, deprecated C++23)
std::aligned_storage_t<sizeof(T), alignof(T)> storage;
new (&storage) T(args...);   // Placement new
T* p = reinterpret_cast<T*>(&storage);
```

---

## 3. Undefined Behaviour (UB) Catalogue

UB means the C++ standard places **no requirements on program behaviour** — the compiler is free to assume UB never occurs, which leads to surprising optimisations.

### 3.1 Signed Integer Overflow

```cpp
// UNDEFINED: signed overflow (not wrapping!)
int x = INT_MAX;
int y = x + 1;    // UB — compiler may assume this never happens and optimise away checks
// Use unsigned int if you need wrapping arithmetic

// Safe check for overflow:
bool willOverflow(int a, int b) {
    return b > 0 && a > INT_MAX - b;   // No overflow in this check
}

// Or use __builtin_sadd_overflow (GCC/Clang):
int result;
if (__builtin_sadd_overflow(a, b, &result)) { /* overflow! */ }
```

### 3.2 Null Pointer Dereference

```cpp
int* p = nullptr;
*p = 5;   // UB — may crash, may be optimised away entirely, may do anything

// Compiler may optimise code assuming p is never null after its use:
if (p) {
    foo(p);   // Compiler may delete this null check because *p was used earlier
}
```

### 3.3 Use After Free / Dangling Pointer

```cpp
int* p = new int(42);
delete p;
*p = 10;       // UB: use after free — memory may have been reallocated

int& ref = *p; // Same: dangling reference
```

### 3.4 Buffer Overflow / Out-of-Bounds Access

```cpp
int arr[5];
arr[5] = 0;    // UB: one past end (also a security vulnerability)
arr[-1] = 0;   // UB

char buf[4];
strcpy(buf, "hello");  // UB: writes 6 bytes into 4-byte buffer
```

### 3.5 Strict Aliasing Violation

```cpp
// Accessing an object through a pointer of a different type is UB
float f = 3.14f;
int* p = reinterpret_cast<int*>(&f);   // UB!  (violates strict aliasing)
*p;   // Reading f as int — compiler may not have flushed f to memory

// CORRECT: use memcpy or std::bit_cast (C++20) for type punning
uint32_t bits;
memcpy(&bits, &f, sizeof(f));          // OK: well-defined
uint32_t b2 = std::bit_cast<uint32_t>(f);  // C++20: safer and inline
```

### 3.6 Shifting by Negative / Too-Large Amount

```cpp
int x = 1;
x << -1;   // UB: negative shift
x << 32;   // UB: shift >= bit width of type (32-bit int)
x << 31;   // UB: shifts into sign bit for signed int

// Use unsigned types for bit manipulation:
unsigned u = 1u;
u << 31;   // OK: well-defined for unsigned
```

### 3.7 Unsequenced Operations

```cpp
int i = 0;
i = ++i + i++;   // UB: multiple modifications to i without sequencing
// (C++17 clarified some cases but this is still ambiguous)
```

### 3.8 Other Common UB

```cpp
// Accessing object outside its lifetime
{
    int& r = *new int(5);   // r valid
    delete &r;              // Lifetime ended
    r = 10;                 // UB: r dangling
}

// Division by zero
int x = 5 / 0;   // UB for integers; float gives ±infinity or NaN (defined by IEEE 754)

// Misaligned pointer
char buf[8];
int* p = (int*)(buf + 1);  // Misaligned; *p is UB on strict-alignment architectures

// Calling a function through incompatible pointer
void(*fp)(int) = (void(*)(int))my_fn;  // Only safe if types match exactly

// Modifying a string literal
char* s = "hello";
s[0] = 'H';   // UB: string literal is read-only
```

---

## 4. AddressSanitizer (ASan)

Detects: **heap/stack/global buffer overflow, use-after-free, use-after-return, memory leaks**.

```bash
# Compile with ASan
g++ -fsanitize=address -fno-omit-frame-pointer -g -o program main.cpp
clang++ -fsanitize=address -fno-omit-frame-pointer -g -o program main.cpp

# Run normally — ASan instruments every memory access
./program

# Example output on buffer overflow:
# ==12345==ERROR: AddressSanitizer: heap-buffer-overflow on address 0x...
# READ of size 4 at 0x... thread T0
#     #0 0x...  in main /path/main.cpp:10
# ...
# SUMMARY: heap-buffer-overflow
```

### 4.1 Common ASan Errors

| Error | Cause |
|-------|-------|
| `heap-buffer-overflow` | Write/read past end of heap allocation |
| `stack-buffer-overflow` | Write/read past stack array |
| `heap-use-after-free` | Access after `delete` |
| `use-after-return` | Return pointer/reference to local variable |
| `direct-leak` | Memory allocated but never freed |

---

## 5. ThreadSanitizer (TSan)

Detects **data races** between threads.

```bash
g++ -fsanitize=thread -g -o program main.cpp
./program

# Example output on data race:
# WARNING: ThreadSanitizer: data race (pid=12345)
#   Write of size 4 at 0x... by thread T2:
#     #0 counter_increment /path/main.cpp:15
#   Read of size 4 at 0x... by thread T1:
#     #0 counter_read /path/main.cpp:22
```

**Note**: Cannot combine TSan and ASan in same build.

---

## 6. UndefinedBehaviourSanitizer (UBSan)

Detects **undefined behaviour at runtime**.

```bash
g++ -fsanitize=undefined -g -o program main.cpp
clang++ -fsanitize=undefined -fsanitize=integer -g -o program main.cpp

# Specific checks available:
-fsanitize=signed-integer-overflow
-fsanitize=null
-fsanitize=bounds
-fsanitize=alignment
-fsanitize=shift
-fsanitize=vptr        # virtual function table errors

# Combined (recommended):
-fsanitize=address,undefined
```

---

## 7. Valgrind

Tool suite for memory debugging, profiling. Slower than sanitisers but more portable.

```bash
# Memory error detection (memcheck — default)
valgrind --leak-check=full --show-leak-kinds=all ./program

# Common error types Valgrind reports:
# Invalid write/read of size N   → buffer overflow / use-after-free
# Use of uninitialised value      → reading uninitialised memory
# LEAK SUMMARY: definitely lost  → memory leak
```

### 7.1 Valgrind vs ASan

| Feature | ASan | Valgrind |
|---------|------|---------|
| Slowdown | ~2x | ~20x |
| Stack overflow detection | Yes | Limited |
| Heap overflow detection | Yes | Yes |
| Compile-time changes needed | Yes | No |
| Platform support | Wide | Linux/macOS |

---

## 8. GDB Reference

### 8.1 Build for Debug

```bash
g++ -g -O0 -o program main.cpp   # -g: debug symbols; -O0: no optimisation
```

### 8.2 GDB Command Reference

```gdb
# Start
gdb ./program            # Open program in gdb
gdb ./program core       # Post-mortem debug with core dump
gdb --args ./prog a b c  # Pass arguments

# Run
run                      # Run the program
run arg1 arg2            # Run with arguments
kill                     # Kill running program

# Breakpoints
break main               # Break at function main
break file.cpp:42        # Break at line 42 in file.cpp
break *0x4005a0          # Break at address
info breakpoints         # List all breakpoints
delete 2                 # Delete breakpoint #2
disable 2                # Disable without deleting
condition 2 x > 10       # Conditional breakpoint

# Execution control
step    (s)              # Step into function
next    (n)              # Step over function
finish                   # Run until current function returns
continue (c)             # Continue to next breakpoint
until 50                 # Continue until line 50

# Inspection
print x                  # Print variable x
print *ptr               # Dereference pointer
print arr[0]@5           # Print 5 elements of arr from index 0
display x                # Auto-print x after every step
info locals              # All local variables
info args                # Function arguments
backtrace (bt)           # Call stack
frame 2                  # Switch to stack frame 2
up / down               # Navigate frames

# Memory
x/10d addr               # Examine 10 decimal words at addr
x/10x 0x4005a0           # 10 hex words at address
x/s 0x402010             # Print C string at address
x/i $pc                  # Disassemble at instruction pointer

# Watchpoints
watch x                  # Break when x is written
rwatch x                 # Break when x is read
awatch x                 # Break when x is read OR written

# TUI mode
tui enable               # Split screen with source view
layout src               # Show source code pane
layout asm               # Show assembly pane

# Multi-thread
info threads             # List threads
thread 2                 # Switch to thread 2
thread apply all bt      # Print backtrace for all threads

# Core dump
ulimit -c unlimited      # Enable core dumps (in shell)
gdb ./program core       # Load core dump
```

---

## 9. CMake

### 9.1 Minimal CMakeLists.txt

```cmake
cmake_minimum_required(VERSION 3.20)
project(MyProject VERSION 1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)   # Disable GNU extensions (pure ISO C++)

add_executable(my_app
    src/main.cpp
    src/utils.cpp
)

target_include_directories(my_app PRIVATE include/)
```

### 9.2 Libraries

```cmake
# Static library
add_library(mylib STATIC src/lib.cpp)
target_include_directories(mylib PUBLIC include/)

# Shared library
add_library(mylib SHARED src/lib.cpp)

# Header-only (interface) library
add_library(mylib INTERFACE)
target_include_directories(mylib INTERFACE include/)

# Link libraries to executable
target_link_libraries(my_app PRIVATE mylib pthread)
# PRIVATE:  only this target uses it
# PUBLIC:   this target AND targets linking to it
# INTERFACE: only targets linking to it (not this target itself)
```

### 9.3 Build Options & Configuration

```cmake
# Define build options
option(ENABLE_TESTS "Build unit tests" ON)

# Compiler flags
target_compile_options(my_app PRIVATE
    -Wall -Wextra -Wpedantic    # Common warnings
    $<$<CONFIG:Debug>:-O0 -g>  # Debug flags only in Debug build
    $<$<CONFIG:Release>:-O3>   # Release optimisation
)

# Preprocessor definitions
target_compile_definitions(my_app PRIVATE
    MY_VERSION="1.0"
    $<$<CONFIG:Debug>:DEBUG_BUILD>
)

# Find and link system package
find_package(Threads REQUIRED)
target_link_libraries(my_app PRIVATE Threads::Threads)
```

### 9.4 Build Commands

```bash
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release    # Configure
cmake --build . --parallel 8           # Build with 8 parallel jobs
cmake --build . --target my_app        # Build specific target
ctest --test-dir .                     # Run tests
cmake --install . --prefix /usr/local  # Install
```

---

## 10. Linking & Symbols

### 10.1 Static vs Dynamic Libraries

```
Static library (.a / .lib):
  - Archive of object files (.o)
  - Linked into executable at compile time (code is part of binary)
  - No runtime dependency
  - Larger binary; each process has its own copy

Dynamic/Shared library (.so / .dylib / .dll):
  - Separate file; loaded at runtime (or at start with dlopen)
  - Multiple processes share the same library in memory
  - Smaller executable; but runtime dependency
  - Easier to update library without recompiling dependent programs
```

### 10.2 nm — Symbol Table Inspector

```bash
nm -C my_program           # List symbols (demangled C++ names)
nm -C --defined-only lib.a # Only defined symbols (not external references)

# Symbol types:
# T = text (code)
# D = initialised data
# B = BSS (uninitialised data)
# U = undefined (external reference, resolved at link time)
# W = weak symbol
```

### 10.3 objdump — Object File Inspection

```bash
objdump -d program          # Disassemble
objdump -D program          # Disassemble ALL sections
objdump -t program          # Symbol table
objdump -S program          # Interleaved source and assembly (-g build)
objdump -h program          # Section headers
```

### 10.4 ldd — Shared Library Dependencies

```bash
ldd ./program               # List dynamic library dependencies
ldd /usr/bin/ls             # What does ls depend on?

# Output example:
# libstdc++.so.6 => /usr/lib/x86_64-linux-gnu/libstdc++.so.6 (0x...)
# libc.so.6 => /lib/x86_64-linux-gnu/libc.so.6 (0x...)
```

### 10.5 Symbol Visibility

```cpp
// Control which symbols are exported from a shared library
__attribute__((visibility("default")))  void exported_fn();  // Visible in .so
__attribute__((visibility("hidden")))   void internal_fn();  // Not exported

// CMake: set default visibility
set(CMAKE_CXX_VISIBILITY_PRESET hidden)
set(CMAKE_VISIBILITY_INLINES_HIDDEN ON)

// Use -fvisibility=hidden to hide all symbols by default;
// explicitly mark public API as visible
```

---

## 11. Performance Profiling

### 11.1 perf (Linux)

```bash
# Record CPU samples for entire program run
perf record ./program
perf report              # Interactive report

# Record with call graph
perf record -g ./program
perf report --call-graph

# Count hardware events
perf stat ./program      # IPC, cache misses, branch mispredictions, etc.

# Record specific event
perf record -e cache-misses ./program
```

### 11.2 gprof

```bash
# Compile with profiling instrumentation
g++ -pg -O2 -o program main.cpp
./program                  # Generates gmon.out
gprof program gmon.out > profile.txt  # Human-readable report
```

### 11.3 Flame Graphs

```bash
# On Linux: use perf + Brendan Gregg's FlameGraph scripts
git clone https://github.com/brendangregg/FlameGraph.git
perf record -g ./program
perf script | ./FlameGraph/stackcollapse-perf.pl | ./FlameGraph/flamegraph.pl > perf.svg

# Visualise in browser: wider bars = more CPU time in that function
```

### 11.4 Timing in Code

```cpp
#include <chrono>

auto t1 = std::chrono::high_resolution_clock::now();
doWork();
auto t2 = std::chrono::high_resolution_clock::now();

auto ms = std::chrono::duration_cast<std::chrono::milliseconds>(t2 - t1).count();
std::cout << "Elapsed: " << ms << " ms\n";

// For micro-benchmarks: prevent optimisation of timed code
// Use Google Benchmark or nanobench libraries
```

---

## 12. Compiler Optimisation Flags

```bash
-O0   # No optimisation (debug default)
-O1   # Basic optimisations
-O2   # Standard release optimisation (recommended)
-O3   # Aggressive (may increase code size; sometimes slower than O2)
-Os   # Optimise for code size
-Oz   # Maximum size reduction (Clang)
-Og   # Optimise for debugging experience (better than O0 for debug builds)
-Ofast # O3 + violations of IEEE math standards — careful!

# Architecture-specific
-march=native            # Optimise for host CPU architecture (non-portable)
-march=x86-64-v3         # SSE4.2+AVX2 (widely supported x86)
-mtune=native            # Tune scheduling for host CPU (binary remains portable)

# Link-Time Optimisation (LTO)
-flto                    # Enable LTO (inlining across translation units)

# Profile-Guided Optimisation (PGO)
-fprofile-generate       # Step 1: instrument
./program                # Step 2: run to collect profile data
-fprofile-use            # Step 3: recompile with profile data

# Sanitisers (disable for production!)
-fsanitize=address,undefined
```

---

## 13. GCC/Clang Extensions

### 13.1 __builtin Functions

```cpp
// Bit counting (compiles to single instruction on modern CPUs)
__builtin_popcount(x)     // Number of set bits in unsigned int
__builtin_popcountll(x)   // unsigned long long version
__builtin_clz(x)          // Count leading zeros (undefined for x=0)
__builtin_ctz(x)          // Count trailing zeros
__builtin_parity(x)       // Parity of bit count (even=0, odd=1)

// Branch prediction hints
__builtin_expect(condition, expected)
// Example — mark the cold branch:
if (__builtin_expect(ptr == nullptr, 0)) {   // 0 = unlikely to be true
    handle_null();
}
// Modern alternative: [[likely]] / [[unlikely]] (C++20)
if (ptr == nullptr) [[unlikely]] { handle_null(); }

// Overflow detection
__builtin_sadd_overflow(a, b, &result)  // Signed add overflow → bool
__builtin_smul_overflow(a, b, &result)

// Assume (Clang; GCC uses __builtin_unreachable indirectly)
__builtin_unreachable();   // Tell compiler this point is never reached
// Can dramatically improve optimisation if used correctly — but is UB if reached!
// C++23 equivalent: std::unreachable()
```

### 13.2 __attribute__ Annotations

```cpp
__attribute__((noreturn))          // Function never returns (like exit, throw)
__attribute__((noinline))          // Never inline this function
__attribute__((always_inline))     // Always inline
__attribute__((cold))              // Rarely called — placed in cold section
__attribute__((hot))               // Frequently called — optimise aggressively
__attribute__((pure))              // No side effects; result depends only on args
__attribute__((const))             // No side effects; result depends only on args + no memory reads
__attribute__((unused))            // Suppress unused variable/function warning
__attribute__((deprecated))        // Emit warning when used
__attribute__((warn_unused_result))// Warn if return value discarded
__attribute__((packed))            // No padding (see Section 2)
__attribute__((aligned(N)))        // Align to N bytes
__attribute__((section(".mydata"))) // Place in named ELF section
__attribute__((constructor))       // Run before main()
__attribute__((destructor))        // Run after main()

// C++11 equivalent attributes (portable):
[[noreturn]]
[[deprecated("use new_fn instead")]]
[[nodiscard]]        // Same as warn_unused_result
[[maybe_unused]]     // Same as unused
[[likely]] [[unlikely]]   // C++20
```

---

## 14. Cross-Compilation

### 14.1 Cross-Compilation Concepts

```bash
# Host:   machine running the compiler
# Target: machine that will run the compiled code
# Toolchain: compiler + linker + headers + libraries for the target

# Example: compiling for ARM64 Linux on an x86_64 machine
apt install gcc-aarch64-linux-gnu
aarch64-linux-gnu-gcc -o my_program main.c
# Run on ARM target:
scp my_program arm_machine:/tmp/ && ssh arm_machine ./tmp/my_program
```

### 14.2 CMake Toolchain File

```cmake
# toolchain-arm64.cmake
set(CMAKE_SYSTEM_NAME Linux)
set(CMAKE_SYSTEM_PROCESSOR aarch64)

set(CMAKE_C_COMPILER   aarch64-linux-gnu-gcc)
set(CMAKE_CXX_COMPILER aarch64-linux-gnu-g++)
set(CMAKE_SYSROOT      /path/to/arm64/sysroot)

set(CMAKE_FIND_ROOT_PATH_MODE_PROGRAM NEVER)
set(CMAKE_FIND_ROOT_PATH_MODE_LIBRARY ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_INCLUDE ONLY)
```

```bash
cmake .. -DCMAKE_TOOLCHAIN_FILE=toolchain-arm64.cmake
cmake --build .
```

---

## 15. SIMD Intrinsics Overview

SIMD (Single Instruction, Multiple Data) processes multiple values in one CPU instruction.

### 15.1 SIMD Register Widths

| Instruction Set | Register Width | Floats / Ints per register |
|----------------|---------------|--------------------------|
| SSE2 (x86) | 128 bits | 4 floats or 2 doubles |
| AVX (x86) | 256 bits | 8 floats or 4 doubles |
| AVX-512 (x86) | 512 bits | 16 floats or 8 doubles |
| NEON (ARM) | 128 bits | 4 floats or 2 doubles |

### 15.2 Intel SSE2 Example

```cpp
#include <immintrin.h>   // SSE2/AVX intrinsics

// Add 4 pairs of floats simultaneously
void addFloat4(const float* a, const float* b, float* out) {
    __m128 va = _mm_loadu_ps(a);    // Load 4 unaligned floats
    __m128 vb = _mm_loadu_ps(b);
    __m128 vc = _mm_add_ps(va, vb); // Add 4 floats in parallel
    _mm_storeu_ps(out, vc);          // Store 4 floats
}

// Without SIMD:
// 4 floating-point additions
// With SIMD:
// 1 instruction doing all 4 additions
```

### 15.3 Auto-Vectorisation

Before writing intrinsics, try letting the compiler auto-vectorise:

```cpp
void addArrays(float* a, const float* b, size_t n) {
    for (size_t i = 0; i < n; i++) {
        a[i] += b[i];
    }
}
// With -O2 -march=native, GCC/Clang will often vectorise this automatically
// Check: gcc -O2 -march=native -fopt-info-vec -fopt-info-vec-missed main.cpp

// Annotations to help auto-vectoriser:
#pragma GCC ivdep       // Tell GCC: no loop-carried dependencies
for (int i = 0; i < n; i++) a[i] += b[i];
```

---

## Quick Reference: Compiler Toolchain Commands

```bash
# Compile only (produce .o, no linking)
g++ -c main.cpp -o main.o

# Link object files
g++ main.o utils.o -o program

# Preprocessing only (show macro-expanded output)
g++ -E main.cpp -o main.preprocessed

# Compilation to assembly
g++ -S -O2 main.cpp -o main.s

# Show predefined macros
g++ -dM -E - < /dev/null | sort

# Generate compile_commands.json (for clangd / IDE)
cmake .. -DCMAKE_EXPORT_COMPILE_COMMANDS=ON

# Check C++ name mangling
c++filt _ZN3FooC1Ev   # Demangle: Foo::Foo()

# Inspect ELF sections
readelf -S program       # Section headers
readelf -d program       # Dynamic section (for .so dependencies)
```

---

## Debugging Checklist

When a program crashes or behaves incorrectly:

1. **Build with debug symbols**: `-g -O0`
2. **Run under ASan**: `-fsanitize=address` → catches memory errors immediately
3. **Run under UBSan**: `-fsanitize=undefined` → catches UB
4. **Run under TSan** (if multi-threaded): `-fsanitize=thread` → data races
5. **Check with Valgrind**: `valgrind --leak-check=full ./program`
6. **Use GDB** for backtraces: `bt`, `info locals`, `watch`
7. **Look for UB** in code: signed overflow, wrong pointer casts, out-of-bounds
8. **Check alignment**: struct padding, cache alignment for hot data

---

*This document completes the C/C++ Learning Series. See [00_Master_Index.md](00_Master_Index.md) for the full series overview.*
