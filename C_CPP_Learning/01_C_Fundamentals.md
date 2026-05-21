# 01 — C Fundamentals
## Complete In-Depth Reference

---

## Table of Contents

1. [Program Structure & Compilation Model](#1-program-structure--compilation-model)
2. [Data Types & Type System](#2-data-types--type-system)
3. [Operators](#3-operators)
4. [Control Flow](#4-control-flow)
5. [Functions](#5-functions)
6. [Arrays & Strings](#6-arrays--strings)
7. [Pointers](#7-pointers)
8. [Structs, Unions & Enums](#8-structs-unions--enums)
9. [Dynamic Memory Management](#9-dynamic-memory-management)
10. [File I/O](#10-file-io)
11. [Preprocessor](#11-preprocessor)
12. [Bit Manipulation](#12-bit-manipulation)
13. [Storage Classes & Linkage](#13-storage-classes--linkage)
14. [C Standard Library Essentials](#14-c-standard-library-essentials)
15. [Common Pitfalls & Undefined Behaviour](#15-common-pitfalls--undefined-behaviour)

---

## 1. Program Structure & Compilation Model

### 1.1 From Source to Binary

```
source.c
   │
   ▼  Preprocessor  (cpp)    → expand macros, includes, conditionals
source.i
   │
   ▼  Compiler      (cc1)    → .i → assembly .s
source.s
   │
   ▼  Assembler     (as)     → .s → object file .o   (ELF sections)
source.o
   │
   ▼  Linker        (ld)     → .o + libs → executable or .so
a.out / program
```

### 1.2 ELF Sections in a .o File

| Section | Content |
|---------|---------|
| `.text` | Machine code (read + execute) |
| `.rodata` | String literals, `const` global data (read only) |
| `.data` | Initialised global/static variables (read + write) |
| `.bss` | Uninitialised globals (zero-initialised by OS at load; not stored in file) |
| `.symtab` | Symbol table (names → addresses) |
| `.rel.text` | Relocation entries (linker patches) |

### 1.3 Minimal C Program

```c
// Every C program requires exactly one main() with these signatures:
int main(void)                          { return 0; }
int main(int argc, char *argv[])        { return 0; }
int main(int argc, char *argv[], char *envp[])  { return 0; }  // POSIX extension
```

---

## 2. Data Types & Type System

### 2.1 Fundamental Types

| Type | C Standard | Typical Size (64-bit) | Range |
|------|-----------|----------------------|-------|
| `char` | signed or unsigned (impl-defined) | 1 byte | ±127 or 0–255 |
| `signed char` | always signed | 1 byte | -128 to +127 |
| `unsigned char` | always unsigned | 1 byte | 0 to 255 |
| `short` | at least 16 bits | 2 bytes | -32768 to +32767 |
| `int` | at least 16 bits | 4 bytes | -2³¹ to 2³¹-1 |
| `long` | at least 32 bits | 8 bytes (Linux), 4 bytes (Windows) | platform |
| `long long` | at least 64 bits | 8 bytes | -2⁶³ to 2⁶³-1 |
| `float` | IEEE 754 single | 4 bytes | ~1.2×10⁻³⁸ to ~3.4×10³⁸ |
| `double` | IEEE 754 double | 8 bytes | ~2.2×10⁻³⁰⁸ to ~1.8×10³⁰⁸ |
| `long double` | extended precision | 16 bytes (x86) | larger |
| `_Bool` | C99 | 1 byte | 0 or 1 |

### 2.2 Fixed-Width Integer Types (`<stdint.h>`)

```c
#include <stdint.h>

int8_t   x8;    // exactly  8 bits, signed
uint8_t  u8;    // exactly  8 bits, unsigned
int16_t  x16;
uint16_t u16;
int32_t  x32;
uint32_t u32;
int64_t  x64;
uint64_t u64;

// Fastest type of at least N bits
int_fast8_t   f8;
uint_fast32_t f32;

// Smallest type of at least N bits
int_least16_t l16;

// Pointer-sized integer
intptr_t  ptr_val;
uintptr_t uptr_val;

// Largest integer type
intmax_t  big;
uintmax_t ubig;
```

**Why use fixed-width?** Portability — `int` is 16 bits on some embedded platforms. Always use `uint8_t` for byte manipulation, `uint32_t` for register values.

### 2.3 Type Conversion Rules

**Implicit Arithmetic Conversions** (applied before any binary operation):

```
1. Integer promotion: types smaller than int → promoted to int (or unsigned int)
2. If operands differ: lower rank converted to higher rank
3. Rank order: int < long < long long < float < double < long double
4. If signed and unsigned have same rank: signed → unsigned

Example:
  unsigned int u = 10;
  int i = -1;
  if (i < u)  // DANGER: i promoted to unsigned → wraps to UINT_MAX
              // Condition is FALSE — counterintuitive!
```

### 2.4 Type Qualifiers

| Qualifier | Meaning |
|-----------|---------|
| `const` | Value must not change after initialisation |
| `volatile` | Value may change externally (hardware register, signal handler) — no caching by compiler |
| `restrict` (C99) | Pointer is the only reference to the object — enables aliasing optimisations |
| `_Atomic` (C11) | Atomic access — no data races |

```c
// const correctness:
const int x = 5;          // x is const
int * const p = &x;       // p is const (pointer itself can't change)
const int *q = &x;        // *q is const (what p points to can't change)
const int * const r = &x; // both const

// volatile for hardware registers:
volatile uint32_t *UART_STATUS = (volatile uint32_t *)0x40011000;
while (!(*UART_STATUS & 0x01)) {}  // compiler must re-read each iteration
```

---

## 3. Operators

### 3.1 Operator Precedence Table (highest to lowest)

| Precedence | Operator | Associativity |
|-----------|---------|--------------|
| 1 | `()` `[]` `->` `.` `++` `--` (postfix) | Left |
| 2 | `++` `--` (prefix) `+` `-` (unary) `!` `~` `*` `&` `sizeof` `(type)` | Right |
| 3 | `*` `/` `%` | Left |
| 4 | `+` `-` | Left |
| 5 | `<<` `>>` | Left |
| 6 | `<` `<=` `>` `>=` | Left |
| 7 | `==` `!=` | Left |
| 8 | `&` | Left |
| 9 | `^` | Left |
| 10 | `\|` | Left |
| 11 | `&&` | Left |
| 12 | `\|\|` | Left |
| 13 | `?:` | Right |
| 14 | `=` `+=` `-=` `*=` `/=` `%=` `&=` `^=` `\|=` `<<=` `>>=` | Right |
| 15 | `,` | Left |

### 3.2 Bitwise Operators

```c
uint8_t a = 0b10110100;   // 0xB4
uint8_t b = 0b11001011;   // 0xCB

a & b   // AND: 0b10000000 (0x80) — bit is 1 only if both bits are 1
a | b   // OR:  0b11111111 (0xFF) — bit is 1 if either bit is 1
a ^ b   // XOR: 0b01111111 (0x7F) — bit is 1 if bits differ
~a      // NOT: 0b01001011 (0x4B) — flip all bits
a << 2  // Left shift:  0b11010000 (0xD0) — shift left, fill 0
a >> 2  // Right shift: 0b00101101 (0x2D) — for unsigned, fill 0 (logical shift)

// Common idioms:
#define BIT(n)          (1U << (n))
#define SET_BIT(reg, n)   ((reg) |= BIT(n))
#define CLEAR_BIT(reg, n) ((reg) &= ~BIT(n))
#define TOGGLE_BIT(reg,n) ((reg) ^= BIT(n))
#define TEST_BIT(reg, n)  (((reg) >> (n)) & 1U)
```

### 3.3 sizeof and alignof

```c
sizeof(int)         // 4 (bytes)
sizeof(int *)       // 8 (bytes) on 64-bit
sizeof("hello")     // 6 (5 chars + null terminator)
sizeof(int [10])    // 40

int arr[10];
sizeof(arr) / sizeof(arr[0])  // 10 — ONLY works when arr is an array, not a pointer

// _Alignof (C11)
_Alignof(int)       // 4 — minimum alignment requirement
_Alignof(double)    // 8
```

---

## 4. Control Flow

### 4.1 if / else if / else

```c
// Always use braces — avoids dangling-else ambiguity
if (x > 0) {
    printf("positive\n");
} else if (x < 0) {
    printf("negative\n");
} else {
    printf("zero\n");
}
```

### 4.2 switch

```c
switch (day) {
    case 0: printf("Mon"); break;
    case 1: printf("Tue"); break;
    case 5:
    case 6: printf("Weekend"); break;   // Fallthrough intentional
    default: printf("?");
}
// switch operates on integer types only (not strings, not floats)
// Missing break causes fallthrough to next case — common bug
```

### 4.3 Loops

```c
// for — use when iteration count is known
for (int i = 0; i < n; ++i) { ... }

// while — use when condition tested before body
while (condition) { ... }

// do-while — body always executes at least once
do { ... } while (condition);

// break — exit innermost loop/switch
// continue — skip to next iteration
// goto — rarely used; acceptable in C for single-exit cleanup patterns:
void process(void) {
    FILE *f = fopen("data", "r");
    if (!f) goto cleanup;
    // ... work ...
cleanup:
    if (f) fclose(f);
}
```

---

## 5. Functions

### 5.1 Declaration, Definition, Call

```c
// Declaration (prototype) — tells compiler the signature
int add(int a, int b);

// Definition — provides the body
int add(int a, int b) {
    return a + b;
}

// Call
int result = add(3, 4);
```

### 5.2 Parameter Passing

**C is pass-by-value** — function always receives a copy.

```c
void bad_swap(int a, int b) {
    int tmp = a; a = b; b = tmp;  // Only swaps LOCAL copies
}

void good_swap(int *a, int *b) {
    int tmp = *a; *a = *b; *b = tmp;  // Swaps via pointers
}

int x = 3, y = 7;
good_swap(&x, &y);  // Pass addresses
```

### 5.3 Variadic Functions

```c
#include <stdarg.h>

int sum(int count, ...) {
    va_list args;
    va_start(args, count);
    int total = 0;
    for (int i = 0; i < count; i++) {
        total += va_arg(args, int);
    }
    va_end(args);
    return total;
}

sum(3, 10, 20, 30);  // Returns 60
```

### 5.4 Function Pointers

```c
// Declare a pointer to a function taking (int, int) returning int
int (*fp)(int, int);

fp = add;           // Assign
int r = fp(3, 4);   // Call through pointer

// Typedef for readability
typedef int (*BinaryOp)(int, int);
BinaryOp ops[] = { add, sub, mul };
ops[0](5, 3);

// Common use: callbacks
void sort(int *arr, int n, int (*cmp)(int, int)) {
    // ... use cmp(arr[i], arr[j]) for comparison
}

// Returning function pointer
BinaryOp getOp(char op) {
    if (op == '+') return add;
    return sub;
}
```

### 5.5 Inline Functions

```c
// Hint to compiler to substitute function body at call site (no call overhead)
static inline int max(int a, int b) {
    return a > b ? a : b;
}
// Prefer over macros — type-safe, debuggable
```

### 5.6 Recursive Functions

```c
// Direct recursion
int factorial(int n) {
    if (n <= 1) return 1;
    return n * factorial(n - 1);
}

// Tail recursion (compiler may optimise to loop)
int factorial_tail(int n, int acc) {
    if (n <= 1) return acc;
    return factorial_tail(n - 1, n * acc);
}
```

---

## 6. Arrays & Strings

### 6.1 Arrays

```c
// Stack-allocated, fixed size known at compile time
int arr[5] = {1, 2, 3, 4, 5};
int zeros[100] = {0};         // All elements zero
int partial[5] = {1, 2};     // {1, 2, 0, 0, 0}

// VLA — Variable Length Array (C99, optional in C11)
void process(int n) {
    int buf[n];   // Size determined at runtime, on stack
    // WARNING: no bounds checking, can stack-overflow for large n
}

// Multidimensional
int matrix[3][4];             // 3 rows, 4 columns (row-major order)
matrix[1][2] = 99;

// Array ≠ Pointer
// An array name decays to pointer to first element in most expressions:
int *p = arr;   // arr → &arr[0] (decay)
// Exceptions: sizeof(arr), &arr, _Alignof(arr)
```

### 6.2 C Strings

```c
// C strings are null-terminated char arrays
char s1[] = "hello";          // {'h','e','l','l','o','\0'} — 6 bytes, on stack, mutable
const char *s2 = "hello";     // Pointer to string literal (read-only segment) — do NOT modify

// Key: '\0' is the sentinel — determines string length

#include <string.h>
strlen(s1)           // 5 — does NOT count the '\0'
strcpy(dst, src)     // Copy src into dst — ENSURE dst is large enough!
strncpy(dst, src, n) // Copy at most n bytes — safer, but may not null-terminate
strcat(dst, src)     // Append src to dst
strcmp(a, b)         // Compare: < 0, 0, or > 0
strncmp(a, b, n)     // Compare at most n bytes
strchr(s, c)         // Find first occurrence of char c
strstr(hay, needle)  // Find first occurrence of substring
sprintf(buf, fmt, ...)  // printf into buffer — check overflow!
snprintf(buf, n, fmt, ...)  // SAFE version — always use this

// Safe pattern
char buf[64];
snprintf(buf, sizeof(buf), "Value: %d", value);
```

### 6.3 Array Passed to Function

```c
// Array decays to pointer — function receives ONLY the pointer, not the size!
void print_arr(int *arr, size_t n) {  // Must pass n separately
    for (size_t i = 0; i < n; i++) {
        printf("%d ", arr[i]);
    }
}

// Passing 2D array:
void process_matrix(int rows, int cols, int mat[rows][cols]) {  // C99 VLA syntax
    mat[1][2] = 42;
}
// Or with explicit pointer arithmetic:
void process_matrix2(int *mat, int rows, int cols) {
    *(mat + 1 * cols + 2) = 42;  // mat[1][2]
}
```

---

## 7. Pointers

### 7.1 Pointer Fundamentals

```c
int x = 42;
int *p = &x;     // p holds the ADDRESS of x
printf("%d\n", *p);   // Dereference: read the value at address p
*p = 100;        // Write through pointer → x is now 100

int **pp = &p;   // Pointer to pointer
**pp = 200;      // x is now 200
```

### 7.2 Pointer Arithmetic

```c
int arr[] = {10, 20, 30, 40, 50};
int *p = arr;    // p points to arr[0]

p + 1;           // Points to arr[1] (advances by sizeof(int) = 4 bytes)
*(p + 2);        // Same as arr[2] = 30
p++;             // p now points to arr[1]

// Pointer difference:
int *end = arr + 5;
ptrdiff_t dist = end - arr;  // 5

// Valid: arithmetic within same array (including one-past-end for comparison)
// INVALID: arithmetic across different objects → undefined behaviour
```

### 7.3 Pointer to Function, const Pointer, void Pointer

```c
// void* — generic pointer, can hold any address
void *vp = malloc(100);      // malloc returns void*
int *ip = (int *)vp;         // Must cast before dereferencing

// NULL pointer — points to nothing
int *null_p = NULL;          // Initialise to NULL, not 0 (though equivalent)
if (null_p != NULL) { ... }  // Always check before dereferencing

// const combinations (read right-to-left):
const int *p1 = &x;    // pointer to const int — can't change *p1
int * const p2 = &x;   // const pointer to int — can't change p2
const int * const p3 = &x;  // both const
```

### 7.4 Pointer Common Mistakes

```c
// 1. Dangling pointer — pointing to freed/out-of-scope memory
int *dangling(void) {
    int local = 5;
    return &local;   // UNDEFINED BEHAVIOUR — local destroyed on return
}

// 2. Wild pointer — uninitialised
int *wild;
*wild = 5;   // UNDEFINED BEHAVIOUR

// 3. Double free
int *p = malloc(4);
free(p);
free(p);   // UNDEFINED BEHAVIOUR — set p = NULL after free

// 4. One-past-end dereference
int arr[5];
int *p = arr + 5;  // Valid: one-past-end pointer for comparison
*p = 0;            // INVALID: dereference is UB

// Safe free pattern:
#define SAFE_FREE(p) do { free(p); (p) = NULL; } while(0)
```

### 7.5 restrict Keyword (C99)

```c
// Without restrict: compiler must assume p and q could alias
void add_arrays(int *p, const int *q, int n) {
    for (int i = 0; i < n; i++)
        p[i] += q[i];   // Compiler reloads *q each iteration
}

// With restrict: programmer guarantees no aliasing → vectorisation enabled
void add_arrays_fast(int * restrict p, const int * restrict q, int n) {
    for (int i = 0; i < n; i++)
        p[i] += q[i];   // Compiler can use SIMD
}
```

---

## 8. Structs, Unions & Enums

### 8.1 Structs

```c
// Define a type
struct Point {
    float x;
    float y;
};

// Typedef (common pattern)
typedef struct {
    float x;
    float y;
} Point;

// Initialisation
Point p1 = { 1.0f, 2.0f };            // Positional
Point p2 = { .x = 1.0f, .y = 2.0f }; // Designated (C99) — preferred
Point p3 = {0};                        // All zero

// Access
p1.x = 3.0f;
Point *pp = &p1;
pp->x = 3.0f;    // Arrow: dereference + member access
(*pp).x = 3.0f;  // Equivalent

// Struct padding & alignment
struct Padded {
    char  a;    // offset 0, size 1
    // 3 bytes padding
    int   b;    // offset 4, size 4
    char  c;    // offset 8, size 1
    // 3 bytes padding (to satisfy int alignment of next potential member)
};              // Total: 12 bytes (not 6!)

sizeof(struct Padded) == 12  // Not 6!

// Minimise padding: declare largest members first
struct Better {
    int  b;     // offset 0
    char a;     // offset 4
    char c;     // offset 5
    // 2 bytes padding
};              // Total: 8 bytes

// Force packing (non-portable, GCC/Clang):
struct __attribute__((packed)) Packed { char a; int b; };
// sizeof(Packed) == 5 — but unaligned access may be slow or trap
```

### 8.2 Struct as Value vs Pointer

```c
// Struct assignment = full shallow copy
Point a = {1.0f, 2.0f};
Point b = a;     // b is an independent copy
b.x = 99.0f;    // Does NOT affect a

// Pass by value to function = copy (use pointer for large structs)
void process(Point p) { ... }    // Copies — ok for small structs
void process2(const Point *p) { ... }  // No copy — efficient
```

### 8.3 Unions

```c
// All members share the SAME memory location
union Value {
    int    i;
    float  f;
    char   bytes[4];
};

union Value v;
v.i = 0x3F800000;      // Write as int
printf("%f\n", v.f);   // Read as float — 1.0f (IEEE 754 encoding)
// Only the last-written member is guaranteed valid (type punning rule)
// Exception: accessing bytes[] is always valid in C (not C++)

// Tagged union (discriminated union) — safe type punning pattern
typedef struct {
    enum { TYPE_INT, TYPE_FLOAT, TYPE_STR } tag;
    union {
        int   i;
        float f;
        char *s;
    } val;
} Variant;
```

### 8.4 Enums

```c
enum Color { RED, GREEN, BLUE };            // RED=0, GREEN=1, BLUE=2
enum Status { OK = 0, ERR_IO = -1, ERR_MEM = -2 };

// Underlying type is implementation-defined int
// Enums are NOT type-safe in C (can assign any int)

// Pattern: use enum for named constants instead of #define (has type, debuggable)
typedef enum {
    SENSOR_CAMERA = 0,
    SENSOR_RADAR  = 1,
    SENSOR_LIDAR  = 2,
} SensorType;
```

### 8.5 Flexible Array Members (C99)

```c
// Last member of struct can be an incomplete array
typedef struct {
    int length;
    double data[];   // Flexible array member — no size
} FloatBuffer;

// Allocate:
FloatBuffer *buf = malloc(sizeof(FloatBuffer) + n * sizeof(double));
buf->length = n;
buf->data[0] = 3.14;
```

### 8.6 Bit Fields

```c
// Pack multiple small values into a single integer
struct Flags {
    unsigned int is_valid   : 1;   // 1 bit
    unsigned int is_error   : 1;   // 1 bit
    unsigned int priority   : 3;   // 3 bits (0–7)
    unsigned int type       : 4;   // 4 bits (0–15)
    unsigned int reserved   : 23;  // Fill remaining bits
};

struct Flags f = {0};
f.is_valid = 1;
f.priority = 5;

// WARNING: Layout (order, padding, sign) is implementation-defined
// For portable bit packing: use shift + mask explicitly
```

---

## 9. Dynamic Memory Management

### 9.1 Heap Allocation Functions

```c
#include <stdlib.h>

// malloc — allocate uninitialized memory
void *malloc(size_t size);
int *arr = malloc(10 * sizeof(int));
if (!arr) { /* handle allocation failure */ }

// calloc — allocate AND zero-initialize
void *calloc(size_t nmemb, size_t size);
int *arr = calloc(10, sizeof(int));   // arr[0..9] = 0

// realloc — resize allocation
void *realloc(void *ptr, size_t size);
arr = realloc(arr, 20 * sizeof(int));  // Grow to 20 elements

// free — release memory
void free(void *ptr);
free(arr);
arr = NULL;  // IMPORTANT: prevent use-after-free

// aligned_alloc (C11)
void *aligned_alloc(size_t alignment, size_t size);
int *aligned = aligned_alloc(64, 64 * sizeof(int));  // 64-byte aligned
```

### 9.2 Allocation Failure Handling

```c
// malloc returns NULL on failure — ALWAYS check
char *buf = malloc(1024 * 1024 * 1024);  // 1 GB — may fail!
if (buf == NULL) {
    perror("malloc");
    return -1;  // or handle gracefully
}
```

### 9.3 Memory Leak Detection Patterns

```c
// valgrind — run-time leak detector:
// valgrind --leak-check=full ./program

// Address sanitizer — compile-time instrumentation:
// gcc -fsanitize=address -g program.c && ./a.out

// Static analysis:
// clang --analyze program.c
// cppcheck --enable=all program.c
```

### 9.4 Arena / Pool Allocator (Common Embedded Pattern)

```c
// Pre-allocate a large block; sub-allocate from it — no fragmentation
typedef struct {
    uint8_t *base;
    size_t   used;
    size_t   capacity;
} Arena;

void *arena_alloc(Arena *a, size_t size) {
    size = (size + 7) & ~7ULL;  // Align to 8 bytes
    if (a->used + size > a->capacity) return NULL;
    void *ptr = a->base + a->used;
    a->used += size;
    return ptr;
}

void arena_reset(Arena *a) { a->used = 0; }  // Free all at once — O(1)
```

---

## 10. File I/O

### 10.1 File Streams

```c
#include <stdio.h>

// Open
FILE *f = fopen("data.bin", "rb");  // r=read, w=write, a=append; b=binary
if (!f) { perror("fopen"); return -1; }

// Read/Write text
fprintf(f, "Value: %d\n", 42);
fscanf(f, "%d", &val);

// Read/Write binary
size_t n = fread(buf, sizeof(uint32_t), 10, f);   // Read 10 uint32_t's
size_t w = fwrite(buf, sizeof(uint32_t), 10, f);  // Write 10 uint32_t's

// Seek / Tell
fseek(f, 0, SEEK_SET);   // Beginning
fseek(f, 0, SEEK_END);   // End
long pos = ftell(f);     // Current position (bytes)

// Check errors
if (ferror(f)) { perror("file error"); }
if (feof(f))   { /* end of file */    }
clearerr(f);

// Always close
fclose(f);
```

### 10.2 POSIX Low-Level I/O

```c
#include <fcntl.h>
#include <unistd.h>

int fd = open("data.bin", O_RDWR | O_CREAT | O_TRUNC, 0644);
if (fd < 0) { perror("open"); exit(1); }

ssize_t n = read(fd, buf, sizeof(buf));
ssize_t w = write(fd, buf, n);

off_t pos = lseek(fd, 0, SEEK_SET);

close(fd);
```

### 10.3 Standard Streams

| Stream | FD | Buffering | Purpose |
|--------|-----|-----------|---------|
| `stdin` | 0 | Line | Standard input |
| `stdout` | 1 | Line (tty) / Block (pipe) | Standard output |
| `stderr` | 2 | None | Error output (immediately flushed) |

```c
// Force flush (important before fork, exec, or crash)
fflush(stdout);
fflush(NULL);  // Flush all open streams
```

---

## 11. Preprocessor

### 11.1 Macros

```c
// Object-like macro
#define MAX_BUFFER 256
#define PI 3.14159265358979f

// Function-like macro — parenthesise EVERYTHING
#define SQUARE(x)    ((x) * (x))
#define MAX(a, b)    ((a) > (b) ? (a) : (b))

// Pitfall: macro expansion, not a function call
int y = SQUARE(x++);  // Expands to ((x++) * (x++)) — DOUBLE INCREMENT = UB!
// Prefer inline functions for this reason

// Stringification (#)
#define STRINGIFY(x) #x
STRINGIFY(hello)  // → "hello"

// Token pasting (##)
#define CONCAT(a, b) a##b
CONCAT(my, var)  // → myvar

// Variadic macro (C99)
#define LOG(fmt, ...) fprintf(stderr, "[LOG] " fmt "\n", __VA_ARGS__)
LOG("Value: %d", 42);   // → fprintf(stderr, "[LOG] Value: %d\n", 42);
```

### 11.2 Predefined Macros

```c
__FILE__        // Current file name (string literal)
__LINE__        // Current line number (integer)
__func__        // Current function name (C99, string literal)
__DATE__        // Compilation date: "May 18 2026"
__TIME__        // Compilation time: "14:32:05"
__STDC__        // 1 if strictly conforming C
__STDC_VERSION__ // 201710L for C17, 201112L for C11, 199901L for C99

// Usage:
#define ASSERT(cond) \
    do { \
        if (!(cond)) { \
            fprintf(stderr, "Assertion failed: %s at %s:%d\n", \
                    #cond, __FILE__, __LINE__); \
            abort(); \
        } \
    } while(0)
```

### 11.3 Conditional Compilation

```c
#if defined(DEBUG) || defined(_DEBUG)
#  define DLOG(msg) printf("[DEBUG] %s\n", msg)
#else
#  define DLOG(msg) /* nothing — zero overhead */
#endif

// Include guard (ALWAYS use in header files)
#ifndef MY_HEADER_H
#define MY_HEADER_H

// ... header content ...

#endif /* MY_HEADER_H */

// #pragma once (non-standard but widely supported)
#pragma once

// Compiler detection
#if defined(__GNUC__)
    // GCC-specific code
#elif defined(__clang__)
    // Clang-specific code
#elif defined(_MSC_VER)
    // MSVC-specific code
#endif
```

### 11.4 X-Macros Pattern

```c
// Define data once, use in multiple contexts
#define SENSOR_LIST(X) \
    X(CAMERA, 0) \
    X(RADAR,  1) \
    X(LIDAR,  2)

// Generate enum
typedef enum {
#define X(name, val) SENSOR_##name = val,
    SENSOR_LIST(X)
#undef X
} SensorType;

// Generate string table
const char *sensor_names[] = {
#define X(name, val) [val] = #name,
    SENSOR_LIST(X)
#undef X
};
```

---

## 12. Bit Manipulation

### 12.1 Essential Techniques

```c
// Set bit n
x |= (1U << n);

// Clear bit n
x &= ~(1U << n);

// Toggle bit n
x ^= (1U << n);

// Test bit n (returns 0 or non-zero)
x & (1U << n)

// Extract bits [hi:lo] (inclusive)
uint32_t extract(uint32_t val, int hi, int lo) {
    uint32_t mask = ((1U << (hi - lo + 1)) - 1) << lo;
    return (val & mask) >> lo;
}

// Set bits [hi:lo] to field
uint32_t insert(uint32_t val, uint32_t field, int hi, int lo) {
    uint32_t mask = ((1U << (hi - lo + 1)) - 1) << lo;
    return (val & ~mask) | ((field << lo) & mask);
}

// Swap two values without temporary
a ^= b; b ^= a; a ^= b;  // Works but obscures intent — use tmp!

// Test if power of 2
int is_pow2(unsigned n) { return n && !(n & (n - 1)); }

// Round up to next power of 2
uint32_t next_pow2(uint32_t n) {
    n--;
    n |= n >> 1;  n |= n >> 2;  n |= n >> 4;
    n |= n >> 8;  n |= n >> 16;
    return n + 1;
}

// Count set bits (popcount)
int popcount(uint32_t n) {
    n = n - ((n >> 1) & 0x55555555u);
    n = (n & 0x33333333u) + ((n >> 2) & 0x33333333u);
    return (int)(((n + (n >> 4) & 0x0F0F0F0Fu) * 0x01010101u) >> 24);
}
// Or use: __builtin_popcount(n)  (GCC/Clang intrinsic)

// Reverse bits (byte)
uint8_t reverse_bits(uint8_t b) {
    b = (b & 0xF0) >> 4 | (b & 0x0F) << 4;
    b = (b & 0xCC) >> 2 | (b & 0x33) << 2;
    b = (b & 0xAA) >> 1 | (b & 0x55) << 1;
    return b;
}
```

### 12.2 Endianness

```c
// Little-endian (x86): least significant byte at lowest address
// Big-endian (network): most significant byte at lowest address

uint32_t val = 0x12345678;
uint8_t *bytes = (uint8_t *)&val;
// Little-endian: bytes[0]=0x78, bytes[1]=0x56, bytes[2]=0x34, bytes[3]=0x12
// Big-endian:    bytes[0]=0x12, bytes[1]=0x34, bytes[2]=0x56, bytes[3]=0x78

// Byte-swap (C23 has byteswap; use compiler builtins otherwise)
uint16_t bswap16(uint16_t x) { return (x << 8) | (x >> 8); }
uint32_t bswap32(uint32_t x) { return __builtin_bswap32(x); }  // GCC/Clang

// Network byte order (always big-endian)
#include <arpa/inet.h>
uint32_t host = 0x12345678;
uint32_t net  = htonl(host);   // host-to-network-long
uint32_t back = ntohl(net);    // network-to-host-long
```

---

## 13. Storage Classes & Linkage

```c
// auto — default for local variables (stack, block scope)
int local = 5;          // auto by default

// register — hint to keep in CPU register (compiler may ignore)
register int counter = 0;  // Rarely useful today

// static — two different meanings:
// 1. Inside function: persists across calls (not on stack)
void count_calls(void) {
    static int count = 0;  // Initialised only once
    printf("Call #%d\n", ++count);
}
// 2. At file scope: internal linkage (not visible in other .c files)
static int file_private = 0;  // Cannot be accessed from other TUs

// extern — declare that definition is in another translation unit
extern int global_counter;    // Declaration only, no definition

// Linkage:
// External linkage: visible across all TUs (default for global functions/variables)
// Internal linkage: visible only in current TU (static at file scope)
// No linkage: local variables
```

---

## 14. C Standard Library Essentials

### 14.1 `<string.h>` — Memory & String Operations

```c
memcpy(dst, src, n)    // Copy n bytes (undefined if regions overlap)
memmove(dst, src, n)   // Copy n bytes (handles overlapping regions)
memset(ptr, val, n)    // Fill n bytes with val (val is int, stored as unsigned char)
memcmp(a, b, n)        // Compare n bytes; returns < 0, 0, or > 0
memchr(ptr, val, n)    // Find first occurrence of byte val
```

### 14.2 `<stdlib.h>` — General Utilities

```c
abs(x)               // Integer absolute value
labs(x), llabs(x)    // long, long long versions
atoi(s), atol(s)     // String → int (no error check — prefer strtol)
strtol(s, &end, base)  // String → long (with error check)
strtod(s, &end)        // String → double

qsort(arr, n, sizeof(T), cmp_fn)  // In-place quicksort
bsearch(key, arr, n, sizeof(T), cmp_fn)  // Binary search (array must be sorted)

exit(status)    // Normal program exit (flushes buffers, calls atexit())
abort()         // Abnormal termination (raises SIGABRT, core dump)
atexit(fn)      // Register function called on exit()
getenv("PATH")  // Get environment variable
system("ls")    // Run shell command (SECURITY: never with user input)
```

### 14.3 `<math.h>`

```c
#include <math.h>
// Link with -lm

sqrt(x)      // Square root
pow(x, y)    // x^y
fabs(x)      // Absolute value (float)
floor(x)     // Round toward -∞
ceil(x)      // Round toward +∞
round(x)     // Round to nearest (half away from zero)
sin/cos/tan  // Trig
atan2(y, x)  // Arctangent of y/x, correct quadrant
fmin/fmax    // Float min/max (NaN-handling)
isnan(x)     // Test for NaN
isinf(x)     // Test for infinity
INFINITY     // Float infinity constant
NAN          // Not-a-number constant
M_PI         // π (non-standard but widely available)
```

### 14.4 `<time.h>`

```c
#include <time.h>

time_t t = time(NULL);      // Seconds since epoch (1970-01-01)
struct tm *lt = localtime(&t);
char buf[64];
strftime(buf, sizeof(buf), "%Y-%m-%d %H:%M:%S", lt);

// High-resolution timing
struct timespec ts;
clock_gettime(CLOCK_MONOTONIC, &ts);  // POSIX
// ts.tv_sec + ts.tv_nsec * 1e-9 = seconds
```

---

## 15. Common Pitfalls & Undefined Behaviour

### 15.1 Signed Integer Overflow

```c
int x = INT_MAX;
int y = x + 1;   // UNDEFINED BEHAVIOUR (not wrapping!)
// Use: if (x > INT_MAX - 1) → overflow
// Or use unsigned arithmetic (which wraps defined)
```

### 15.2 Accessing Freed Memory

```c
int *p = malloc(4);
free(p);
*p = 5;         // USE AFTER FREE — UB, may corrupt allocator heap
```

### 15.3 Unsequenced Modifications

```c
int i = 0;
i = i++;        // UNDEFINED BEHAVIOUR (C99/C11)
int j = i + i++;  // UB — side effect not sequenced

// Safe: separate into two statements
int old = i;
i++;
```

### 15.4 Null Pointer Dereference

```c
int *p = NULL;
*p = 5;         // Segfault on most systems, but technically UB
```

### 15.5 Buffer Overflow

```c
char buf[8];
strcpy(buf, "this string is too long");  // Writes past end → stack corruption
// Use strncpy or snprintf with size checks
```

### 15.6 Signed / Unsigned Comparison

```c
int n = -1;
unsigned int size = 10;
if (n < size)  // FALSE! n becomes huge unsigned value
```

### 15.7 Strict Aliasing

```c
float f = 1.0f;
// Wrong (violates strict aliasing — UB in C99+):
int *ip = (int *)&f;
int raw = *ip;

// Correct — use memcpy (always safe, optimised away by compiler):
int raw;
memcpy(&raw, &f, sizeof(raw));

// Or use union (valid in C, NOT in C++):
union { float f; int i; } u;
u.f = 1.0f;
int raw = u.i;
```

---

*Continue to*: [02_CPP_Core.md](02_CPP_Core.md) — C++ classes, OOP, RAII, inheritance, polymorphism.
