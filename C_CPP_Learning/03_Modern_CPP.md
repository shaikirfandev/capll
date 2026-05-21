# 03 — Modern C++ (C++11 through C++23)
## Every Feature, With Rationale and Examples

---

## Table of Contents

1. [C++11 — The Revolution](#1-c11--the-revolution)
2. [auto and Type Deduction](#2-auto-and-type-deduction)
3. [Move Semantics & Rvalue References](#3-move-semantics--rvalue-references)
4. [Smart Pointers](#4-smart-pointers)
5. [Lambda Expressions](#5-lambda-expressions)
6. [Perfect Forwarding & Universal References](#6-perfect-forwarding--universal-references)
7. [constexpr and Compile-Time Computation](#7-constexpr-and-compile-time-computation)
8. [Range-Based for Loop](#8-range-based-for-loop)
9. [Initialiser Lists & Uniform Initialisation](#9-initialiser-lists--uniform-initialisation)
10. [C++14 Additions](#10-c14-additions)
11. [C++17 Additions](#11-c17-additions)
12. [C++20 — Concepts](#12-c20--concepts)
13. [C++20 — Ranges](#13-c20--ranges)
14. [C++20 — Coroutines](#14-c20--coroutines)
15. [C++20 — Modules](#15-c20--modules)
16. [C++23 Additions](#16-c23-additions)

---

## 1. C++11 — The Revolution

C++11 fundamentally changed how C++ is written. The key additions:

| Feature | Impact |
|---------|--------|
| Move semantics | Eliminates unnecessary copies; `std::vector` reallocation became fast |
| Smart pointers | `unique_ptr`, `shared_ptr` — safe memory management |
| Lambda expressions | In-place function objects for algorithms |
| `auto` | Less verbose type declarations |
| Range-based for | Clean iteration over any range |
| `constexpr` | True compile-time computation |
| Variadic templates | Type-safe printf, `std::tuple`, `std::variant` |
| `nullptr` | Type-safe null pointer constant |
| `override` / `final` | Compiler-verified virtual overrides |
| Threading library | `std::thread`, `std::mutex`, `std::atomic` |
| Initialiser lists | Consistent `{}` initialisation |

---

## 2. auto and Type Deduction

### 2.1 auto Variable Declarations

```cpp
auto i     = 42;           // int
auto d     = 3.14;         // double
auto s     = std::string("hello");  // std::string
auto p     = new int(5);   // int*
auto& r    = i;            // int& (reference — explicit &)
const auto& cr = s;        // const std::string&

// auto drops const and reference from initialiser:
int x = 5;
const int cx = x;
auto  a1 = cx;    // int (not const int) — copy drops const
auto& a2 = cx;    // const int& (reference preserves const)

// Iterators — major win for readability
std::map<std::string, std::vector<int>> m;
for (auto it = m.begin(); it != m.end(); ++it) {  // vs. std::map<...>::iterator
    auto& key = it->first;
    auto& val = it->second;
}
```

### 2.2 decltype

```cpp
int x = 5;
decltype(x) y = 10;          // y is int
decltype(x + 3.0) z;         // z is double

// decltype(auto): deduce type including references and const
int  a = 5;
int& r = a;
decltype(auto) d1 = r;       // int& (preserves reference — unlike auto)
auto           d2 = r;       // int  (auto drops reference)

// Return type deduction
auto getRef(int& x) -> decltype(x) { return x; }  // Returns int&
```

### 2.3 auto in Function Signatures (C++14)

```cpp
// Return type deduction
auto add(int a, int b) { return a + b; }         // Returns int
auto divide(double a, double b) { return a / b;} // Returns double

// Trailing return type (C++11, useful for complex types)
auto getItem(int idx) -> std::optional<Item>;
```

---

## 3. Move Semantics & Rvalue References

### 3.1 The Problem Move Solves

```cpp
std::string makeGreeting() {
    std::string s = "Hello, World!";
    return s;   // Without move: copies the entire string on return
}              // With NRVO/move: string is moved or constructed in-place

std::string g = makeGreeting();   // Potentially zero copies in C++11+
```

### 3.2 std::move — Cast to Rvalue

```cpp
std::string s1 = "hello";
std::string s2 = std::move(s1);   // s2 "steals" s1's buffer
// s1 is now in valid-but-unspecified state (probably empty string)
// s2 has the "hello" string — NO character was copied!

// IMPORTANT: std::move does NOT move anything — it just casts to rvalue reference
// The MOVE CONSTRUCTOR or MOVE ASSIGNMENT of the target type does the actual moving
```

### 3.3 Move Constructor & Move Assignment

```cpp
class Buffer {
    int   *data_;
    size_t size_;
public:
    // Move constructor
    Buffer(Buffer&& src) noexcept
        : data_(src.data_), size_(src.size_) {
        src.data_ = nullptr;   // ← src must be left in valid state!
        src.size_ = 0;
    }

    // Move assignment
    Buffer& operator=(Buffer&& src) noexcept {
        if (this != &src) {
            delete[] data_;         // Free my current resource
            data_ = src.data_;     // Steal src's resource
            size_ = src.size_;
            src.data_ = nullptr;   // Leave src valid
            src.size_ = 0;
        }
        return *this;
    }
};
```

### 3.4 When Move Happens Automatically

```cpp
// 1. Return local variable (NRVO may elide entirely)
Buffer createBuffer() {
    Buffer b(1024);
    return b;   // Moved (or elided) automatically
}

// 2. push_back/emplace_back with temporary
std::vector<Buffer> v;
v.push_back(Buffer(512));   // Temporary → moved into vector

// 3. std::move to force move on lvalue
Buffer src(1024);
v.push_back(std::move(src));  // src→moved; don't use src after this!
```

### 3.5 Return Value Optimisation (RVO / NRVO)

```cpp
// RVO (compiler creates object directly in caller's space — no copy, no move)
std::string getString() {
    return std::string("hello");  // RVO: constructed directly in caller
}

// NRVO (Named RVO — not guaranteed but typically applied)
std::string getNamedString() {
    std::string s = "hello";
    return s;   // NRVO: s may be constructed in caller's space
}

// Anti-pattern: returning std::move() prevents NRVO!
std::string bad() {
    std::string s = "hello";
    return std::move(s);  // PREVENTS NRVO — forces a move instead of elision
}
```

---

## 4. Smart Pointers

### 4.1 unique_ptr — Exclusive Ownership

```cpp
#include <memory>

// Create
auto p1 = std::make_unique<int>(42);         // Preferred
auto p2 = std::make_unique<std::string>("hi");
auto p3 = std::make_unique<int[]>(100);      // Array variant

// Access
*p1;          // 42
p2->size();   // 2

// Ownership transfer
auto p4 = std::move(p1);   // p1 is now nullptr; p4 owns the int
// p1.get() == nullptr

// Custom deleter
auto file_del = [](FILE* f) { if (f) fclose(f); };
std::unique_ptr<FILE, decltype(file_del)> fp(fopen("data.txt", "r"), file_del);

// In factory functions
std::unique_ptr<Shape> createShape(int type) {
    switch(type) {
        case 0: return std::make_unique<Circle>(5.0f);
        case 1: return std::make_unique<Rectangle>(3.0f, 4.0f);
        default: return nullptr;
    }
}
```

### 4.2 shared_ptr — Shared Ownership

```cpp
// Reference-counted — destroyed when last owner released
auto sp1 = std::make_shared<int>(42);   // Preferred (single allocation)
auto sp2 = sp1;   // sp1 and sp2 both own the int; ref count = 2
{
    auto sp3 = sp2;  // ref count = 3
}   // sp3 destroyed; ref count = 2

sp1.use_count();  // 2

// Circular reference problem → use weak_ptr
struct Node {
    std::shared_ptr<Node> next;
    std::weak_ptr<Node>   prev;  // weak_ptr breaks cycle
};
```

### 4.3 weak_ptr — Non-Owning Observer

```cpp
std::weak_ptr<int> wp;
{
    auto sp = std::make_shared<int>(99);
    wp = sp;           // wp observes but does not own
    auto locked = wp.lock();  // Returns shared_ptr if still alive
    if (locked) { *locked; }  // 99
}   // sp destroyed → int deleted

auto locked = wp.lock();  // Returns nullptr — object gone
wp.expired();             // true
```

### 4.4 Ownership Guidelines

| Scenario | Smart Pointer |
|----------|--------------|
| Single, clear owner | `unique_ptr` |
| Shared lifetime unknown at compile time | `shared_ptr` |
| Observe without ownership (cache, observer pattern) | `weak_ptr` |
| Raw pointer (non-owning) | `T*` or `T&` |

---

## 5. Lambda Expressions

### 5.1 Lambda Syntax

```
[captures](parameters) specifiers -> return_type { body }
   │           │           │               │          │
   │           │           │               │          └─ Code
   │           │           │               └─── Optional return type
   │           │           └───────────────────── Optional: mutable, noexcept, constexpr
   │           └───────────────────────────────── Optional parameters
   └───────────────────────────────────────────── Capture list
```

### 5.2 Capture Modes

```cpp
int x = 10, y = 20;

// Capture by value (copy)
auto f1 = [x]() { return x; };    // x is a copy; x cannot be modified (const by default)

// Capture by reference
auto f2 = [&x]() { x++; };       // x is a reference; modifies outer x

// Capture all by value
auto f3 = [=]() { return x + y; };

// Capture all by reference
auto f4 = [&]() { x++; y++; };

// Mixed
auto f5 = [=, &x]() { return y + x; };   // y by value, x by reference

// mutable — allows modifying value captures
auto f6 = [x]() mutable { return ++x; };  // ++x modifies the local copy

// C++14: init capture (move into lambda)
auto ptr = std::make_unique<int>(5);
auto f7 = [p = std::move(ptr)]() { return *p; };  // ptr moved into lambda
```

### 5.3 Lambdas as Function Objects

```cpp
// Lambda's type is anonymous — use auto or std::function
auto sum = [](int a, int b) { return a + b; };
sum(3, 4);   // 7

// std::function — type-erased wrapper (has overhead)
std::function<int(int,int)> fn = sum;
fn(3, 4);   // 7

// Lambdas with STL algorithms
std::vector<int> v = {5, 1, 3, 2, 4};
std::sort(v.begin(), v.end(), [](int a, int b) { return a > b; });  // Descending

std::vector<int> evens;
std::copy_if(v.begin(), v.end(), std::back_inserter(evens),
             [](int n) { return n % 2 == 0; });
```

### 5.4 Generic Lambdas (C++14)

```cpp
// auto parameter → template function call operator
auto print = [](auto x) { std::cout << x << '\n'; };
print(42);         // Works for int
print(3.14);       // Works for double
print("hello");    // Works for const char*

// C++20: explicit template parameter
auto typed = []<typename T>(T a, T b) { return a + b; };
typed(1, 2);         // int
typed(1.0, 2.0);     // double
// typed(1, 2.0);    // ERROR: different types for T
```

---

## 6. Perfect Forwarding & Universal References

### 6.1 The Problem

```cpp
// We want to forward arguments EXACTLY as received (preserving lvalue/rvalue, const)
template <typename T>
void wrapper(T arg) {
    target(arg);   // WRONG: arg is always lvalue here — loses rvalue info
}
```

### 6.2 Universal References (Forwarding References)

```cpp
// T&& in a TEMPLATE CONTEXT is a "universal reference" (Scott Meyers term)
// It can bind to both lvalues AND rvalues
template <typename T>
void wrapper(T&& arg) {         // T&& here = forwarding reference
    target(std::forward<T>(arg));  // Perfect forward — preserves value category
}

int x = 5;
wrapper(x);    // T=int&,   arg=int&  (lvalue)
wrapper(5);    // T=int,    arg=int&& (rvalue)
wrapper(std::move(x));   // T=int, arg=int&&
```

### 6.3 std::forward

```cpp
// std::forward<T>(arg):
//   If T is lvalue ref (T=int&): returns lvalue reference (no move)
//   If T is rvalue ref (T=int):  returns rvalue reference (enables move)

template <typename T>
void logAndForward(T&& arg) {
    log(arg);                     // Use arg (lvalue)
    target(std::forward<T>(arg)); // Forward preserving original value category
}
// Rule: use std::forward exactly once — the last time arg is used
```

### 6.4 Variadic Forwarding (emplace)

```cpp
template <typename... Args>
void construct(Args&&... args) {
    T obj(std::forward<Args>(args)...);
}
// The pattern for std::vector::emplace_back, std::make_unique, etc.
```

---

## 7. constexpr and Compile-Time Computation

### 7.1 constexpr Functions (C++11)

```cpp
// C++11: body must be a single return statement
constexpr int factorial(int n) {
    return n <= 1 ? 1 : n * factorial(n - 1);
}

// C++14+: arbitrary statements allowed
constexpr int factorial14(int n) {
    int result = 1;
    for (int i = 2; i <= n; ++i) result *= i;
    return result;
}

constexpr int f5 = factorial14(5);   // Computed at compile time → 120
static_assert(f5 == 120, "factorial wrong");  // Compile-time assertion

// Can also be called at runtime if argument is not constexpr
int n;
std::cin >> n;
int fn = factorial14(n);   // Runtime computation
```

### 7.2 constexpr Variables & User-Defined Types

```cpp
struct Vec2 {
    float x, y;
    constexpr Vec2(float x, float y) : x(x), y(y) {}
    constexpr float norm2() const { return x*x + y*y; }
};

constexpr Vec2 v{3.0f, 4.0f};
constexpr float n2 = v.norm2();   // 25.0f — computed at compile time

// constexpr arrays (C++17)
constexpr int primes[] = {2, 3, 5, 7, 11, 13};
constexpr int num_primes = sizeof(primes)/sizeof(primes[0]);
```

### 7.3 if constexpr (C++17)

```cpp
// Compile-time branch — the false branch is NOT compiled
template <typename T>
void process(T value) {
    if constexpr (std::is_integral_v<T>) {
        // Only compiled when T is an integer type
        std::cout << "Integer: " << value << '\n';
    } else if constexpr (std::is_floating_point_v<T>) {
        // Only compiled when T is floating-point
        std::cout << std::fixed << value << '\n';
    } else {
        // Everything else
        std::cout << value << '\n';
    }
}
```

### 7.4 consteval (C++20)

```cpp
// consteval: function MUST be evaluated at compile time
// (constexpr: can be evaluated at compile or runtime)
consteval int sqrtCompileTime(int n) {
    // Called at runtime? → compile error
    int root = 0;
    while ((root+1)*(root+1) <= n) ++root;
    return root;
}

constexpr int r = sqrtCompileTime(16);   // OK: compile time
int n = 16;
// sqrtCompileTime(n);  // ERROR: n not constexpr
```

### 7.5 constinit (C++20)

```cpp
// Guarantees variable is initialised with a constant expression at start-up
// (Does NOT make it const — value can change at runtime)
constinit int counter = 0;   // Zero-initialised before any code runs
counter++;                   // OK: not const
```

---

## 8. Range-Based for Loop

```cpp
std::vector<int> v = {1, 2, 3, 4, 5};

// Copy each element
for (int x : v) { std::cout << x; }

// Reference (modify in-place, no copy)
for (int& x : v) { x *= 2; }

// Const reference (read-only, no copy)
for (const int& x : v) { std::cout << x; }

// auto (deduced type — usually const ref for complex types)
for (const auto& [key, val] : some_map) { ... }  // Structured bindings (C++17)

// Works on any type with begin()/end():
// - C arrays
// - std::array, std::vector, std::list, std::map, std::set, std::string
// - Custom types with begin()/end() member or free functions
// - Ranges (C++20)
```

---

## 9. Initialiser Lists & Uniform Initialisation

### 9.1 Brace Initialisation (Uniform)

```cpp
int x{5};               // Direct-list-init
int y = {5};            // Copy-list-init
std::vector<int> v{1,2,3,4,5};

// Narrowing conversion prevented (unlike = and ())
double d = 3.14;
int i{d};               // ERROR: narrowing conversion
int i2(d);              // OK (but loses precision — bad!)
int i3 = d;             // OK (but loses precision — bad!)

// Empty braces → zero/default initialisation
int a{};                // 0
std::string s{};        // ""
std::vector<int> empty{};
```

### 9.2 std::initializer_list

```cpp
class NumberList {
    std::vector<int> nums_;
public:
    NumberList(std::initializer_list<int> init) : nums_(init) {}
};

NumberList list{1, 2, 3, 4, 5};   // Calls initializer_list constructor

// PITFALL: {} prefers initializer_list constructor when available
std::vector<int> v1(5, 0);   // 5 elements, each 0: {0,0,0,0,0}
std::vector<int> v2{5, 0};   // 2 elements: {5, 0} (initializer_list!)
```

---

## 10. C++14 Additions

### 10.1 Generic Lambdas

```cpp
auto mul = [](auto a, auto b) { return a * b; };
mul(3, 4);      // int × int
mul(3.0, 4.0);  // double × double
```

### 10.2 std::make_unique

```cpp
auto p = std::make_unique<MyClass>(arg1, arg2);  // Added in C++14
```

### 10.3 Return Type Deduction

```cpp
auto square(int x) { return x * x; }  // Deduced as int
```

### 10.4 Variable Templates

```cpp
template <typename T>
constexpr T pi = T(3.14159265358979);

double d = pi<double>;
float  f = pi<float>;
```

### 10.5 Relaxed constexpr

C++14 allows loops, local variables, multiple statements in constexpr functions (C++11 required single-return).

---

## 11. C++17 Additions

### 11.1 Structured Bindings

```cpp
std::pair<int, std::string> p = {42, "answer"};
auto [num, text] = p;         // num=42, text="answer"

std::map<std::string, int> m;
for (const auto& [key, value] : m) { ... }

// Works with structs too
struct Point { int x, y; };
auto [x, y] = Point{3, 4};
```

### 11.2 if / switch with Initialiser

```cpp
if (auto it = m.find(key); it != m.end()) {
    // it is scoped to this if/else block
    use(it->second);
} else {
    // it is still in scope here
}

switch (auto status = getStatus(); status) {
    case OK:    break;
    case ERROR: handle(); break;
}
```

### 11.3 std::optional

```cpp
#include <optional>

std::optional<int> divide(int a, int b) {
    if (b == 0) return std::nullopt;
    return a / b;
}

auto result = divide(10, 2);
if (result) { std::cout << *result; }  // Dereference only if has value
result.value_or(0);                    // Return 0 if empty
result.has_value();                    // bool
```

### 11.4 std::variant

```cpp
#include <variant>

std::variant<int, double, std::string> v;
v = 42;                // Holds int
v = 3.14;             // Now holds double
v = "hello";          // Now holds string

std::get<std::string>(v);         // "hello"
std::get<int>(v);                 // throws std::bad_variant_access

// Type-safe visitation
std::visit([](auto& val) { std::cout << val; }, v);

// Index-based check
v.index();   // 2 (string is at index 2)
std::holds_alternative<std::string>(v);  // true
```

### 11.5 std::any

```cpp
#include <any>

std::any a = 42;
a = std::string("hello");
a = 3.14;

std::any_cast<double>(a);         // 3.14
// std::any_cast<int>(a)          // throws std::bad_any_cast
a.type() == typeid(double);       // true
```

### 11.6 std::string_view (C++17)

```cpp
#include <string_view>

// Non-owning view of a string — no heap allocation
void print(std::string_view sv) {   // Accepts const char*, std::string, substring
    std::cout << sv;
}

std::string s = "hello, world";
std::string_view sv = s;
sv.substr(0, 5);    // "hello" — O(1), no allocation
sv.remove_prefix(7);  // "world" — just moves pointer + adjusts length

// WARNING: string_view does NOT own the data
// Lifetime of view must not exceed lifetime of underlying string!
```

### 11.7 Fold Expressions (C++17)

```cpp
// Sum of any number of arguments
template <typename... Args>
auto sum(Args... args) {
    return (args + ...);    // Unary right fold: a + (b + (c + d))
}
sum(1, 2, 3, 4);  // 10

// All-true check
template <typename... Args>
bool allTrue(Args... args) {
    return (... && args);   // Unary left fold: ((a && b) && c) && d
}
allTrue(true, true, false);  // false

// Print all args
template <typename... Args>
void printAll(Args&&... args) {
    (std::cout << ... << args);   // Binary left fold with <<
}
```

### 11.8 Parallel STL Algorithms (C++17)

```cpp
#include <execution>

std::vector<int> v = {5,3,1,4,2};

// Parallel sort
std::sort(std::execution::par, v.begin(), v.end());

// Parallel transform
std::transform(std::execution::par_unseq,
    v.begin(), v.end(), v.begin(), [](int x) { return x * x; });

// Execution policies:
// std::execution::seq         — sequential
// std::execution::par         — parallel (threads)
// std::execution::par_unseq   — parallel + vectorised (SIMD)
// std::execution::unseq       — vectorised, single thread (C++20)
```

### 11.9 Class Template Argument Deduction (CTAD, C++17)

```cpp
// Before C++17: must specify template arguments
std::pair<int, std::string> p(42, "hello");

// C++17 CTAD: compiler deduces arguments
std::pair p(42, "hello");          // pair<int, const char*>
std::vector v{1, 2, 3};           // vector<int>
std::optional opt = 42;            // optional<int>
std::lock_guard lock(mtx);        // lock_guard<std::mutex>
```

### 11.10 Inline Variables

```cpp
// In a header, previously caused multiple-definition errors
struct Config {
    inline static int max_objects = 64;   // Defined here, no .cpp needed
};

// Free inline variable in header
inline constexpr double kEpsilon = 1e-9;
```

---

## 12. C++20 — Concepts

Concepts are **named constraints on template parameters**. They replace SFINAE and `enable_if` with readable, compile-error-friendly code.

### 12.1 Defining Concepts

```cpp
#include <concepts>

// Concept using requires expression
template <typename T>
concept Numeric = std::is_arithmetic_v<T>;

template <typename T>
concept Printable = requires(T t) {
    std::cout << t;   // Expression must be valid
};

template <typename T>
concept Container = requires(T c) {
    c.begin();
    c.end();
    typename T::value_type;
    { c.size() } -> std::convertible_to<std::size_t>;
};
```

### 12.2 Using Concepts

```cpp
// Method 1: requires clause
template <typename T>
    requires Numeric<T>
T square(T x) { return x * x; }

// Method 2: concept directly as constraint
template <Numeric T>
T cube(T x) { return x * x * x; }

// Method 3: abbreviated function template (C++20)
auto add(Numeric auto a, Numeric auto b) { return a + b; }

// Constrained auto
Numeric auto x = 5;   // Compiler checks: int satisfies Numeric
```

### 12.3 Standard Library Concepts

```cpp
// <concepts>
std::integral<T>           // T is an integer type
std::floating_point<T>     // T is floating-point
std::arithmetic<T>         // integral or floating_point
std::signed_integral<T>
std::unsigned_integral<T>
std::same_as<T, U>         // T and U are the same type
std::derived_from<T, Base> // T derives from Base
std::convertible_to<From, To>
std::invocable<F, Args...> // F is callable with Args
std::regular<T>            // Default-constructible, copyable, equality comparable

// <iterator>
std::input_iterator<I>
std::forward_iterator<I>
std::bidirectional_iterator<I>
std::random_access_iterator<I>

// <ranges>
std::ranges::range<R>
std::ranges::contiguous_range<R>
```

---

## 13. C++20 — Ranges

The Ranges library provides **composable, lazy pipelines** over sequences.

### 13.1 Range Adaptors

```cpp
#include <ranges>
#include <algorithm>

std::vector<int> v = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10};

// Pipeline with | operator
auto result = v
    | std::views::filter([](int x) { return x % 2 == 0; })  // evens
    | std::views::transform([](int x) { return x * x; });    // squared

for (int n : result) { std::cout << n << ' '; }  // 4 16 36 64 100

// LAZY: no elements computed until iterated — no temporary vector!
```

### 13.2 Common Range Views

```cpp
std::views::filter(pred)        // Keep elements satisfying pred
std::views::transform(fn)       // Apply fn to each element
std::views::take(n)             // First n elements
std::views::drop(n)             // Skip n elements
std::views::reverse             // Reverse iteration
std::views::iota(0, 10)         // [0,1,2,...,9] — generate integers
std::views::enumerate           // (C++23) pairs (index, element)
std::views::zip(r1, r2)         // (C++23) combine two ranges
std::views::split(delim)        // Split range by delimiter
std::views::join                // Flatten range of ranges

// Example: generate first 5 square numbers starting from 3
auto squares = std::views::iota(3)          // 3,4,5,6,...  (infinite!)
             | std::views::transform([](int x) { return x*x; })
             | std::views::take(5);
// Result: 9, 16, 25, 36, 49
```

### 13.3 Range Algorithms

```cpp
// All std::algorithm functions have ranges:: versions (take ranges, not iterators)
std::ranges::sort(v);
std::ranges::sort(v, std::greater{});

auto it = std::ranges::find(v, 42);
std::ranges::copy(v, std::ostream_iterator<int>(std::cout, " "));
bool sorted = std::ranges::is_sorted(v);

// Projections — transform elements before comparison
struct Employee { std::string name; int salary; };
std::vector<Employee> staff = { ... };
std::ranges::sort(staff, {}, &Employee::salary);  // Sort by salary field
```

---

## 14. C++20 — Coroutines

Coroutines are functions that can **suspend and resume** their execution.

### 14.1 Coroutine Keywords

```cpp
co_yield value;   // Suspend and yield a value to caller
co_await expr;    // Suspend until expr completes (async)
co_return value;  // Return and finalize the coroutine
```

### 14.2 Generator Example

```cpp
#include <coroutine>
#include <generator>  // C++23 std::generator; in C++20 you build your own

// A generator function is a coroutine that yields values lazily
std::generator<int> fibonacci() {
    int a = 0, b = 1;
    while (true) {
        co_yield a;
        auto next = a + b;
        a = b;
        b = next;
    }
}

for (int fib : fibonacci() | std::views::take(10)) {
    std::cout << fib << ' ';  // 0 1 1 2 3 5 8 13 21 34
}
// Zero heap allocation for the numbers — lazy, on-demand generation
```

### 14.3 Async Coroutine (Conceptual)

```cpp
// With a coroutine task library (Asio, libcoro, etc.)
Task<std::string> fetchData(const std::string& url) {
    auto response = co_await httpGet(url);   // Suspend: control returns to event loop
    auto body     = co_await response.body();
    co_return body;
}

Task<void> main_task() {
    auto data = co_await fetchData("https://example.com/api");
    std::cout << data;
}
```

---

## 15. C++20 — Modules

Modules replace the header file + `#include` model with a proper module system.

### 15.1 Module Interface File

```cpp
// math.cppm (or .ixx — convention varies by compiler)
export module math;

export int add(int a, int b) { return a + b; }
export float pi = 3.14159265f;

// Non-exported: only visible within module
int internal_helper() { return 42; }
```

### 15.2 Importing a Module

```cpp
import math;   // Replaces #include <math.h>

int main() {
    int r = add(3, 4);   // 7
    float p = pi;        // 3.14159
}
```

### 15.3 Importing Standard Library (C++23)

```cpp
import std;   // Import the entire standard library as a module
// Faster compile times — no header text processing
```

---

## 16. C++23 Additions

### 16.1 std::expected

```cpp
#include <expected>

// Type-safe error-or-value return (alternative to exceptions)
std::expected<int, std::string> divide(int a, int b) {
    if (b == 0) return std::unexpected("Division by zero");
    return a / b;
}

auto result = divide(10, 2);
if (result) {
    std::cout << *result;       // 5
} else {
    std::cout << result.error();  // "Division by zero"
}

// Monadic operations
auto doubled = divide(10, 2)
    .transform([](int x) { return x * 2; })   // If success: double it
    .transform_error([](auto e) { return "Error: " + e; });  // If error: prefix
```

### 16.2 std::flat_map / std::flat_set

```cpp
#include <flat_map>

// Cache-friendly ordered map: stores keys and values in separate sorted vectors
// Better cache performance than std::map (which uses tree nodes)
std::flat_map<std::string, int> fmap;
fmap["alpha"] = 1;
fmap["beta"]  = 2;
// Internally: keys=["alpha","beta"] values=[1,2] — contiguous memory
```

### 16.3 std::print / std::println

```cpp
#include <print>

std::println("Hello, {}!", "world");      // Like Python's print + format
std::print(std::cout, "x = {}\n", x);    // Print to specific stream
```

### 16.4 Deducing this (Explicit Object Parameter)

```cpp
struct Widget {
    // C++23: deduce the type of 'this' — enables CRTP without CRTP
    template <typename Self>
    auto& value(this Self& self) { return self.value_; }

    // Also enables recursive lambdas
    auto fib = [](this auto self, int n) -> int {
        return n <= 1 ? n : self(n-1) + self(n-2);
    };
};
```

---

## C++ Version Feature Summary

| Feature | C++11 | C++14 | C++17 | C++20 | C++23 |
|---------|-------|-------|-------|-------|-------|
| Move semantics | ✓ | | | | |
| `auto` | ✓ | | | | |
| Lambda | ✓ | Generic | | Template params | |
| Smart pointers | ✓ | `make_unique` | | | |
| `constexpr` | Basic | Loops | `if constexpr` | `consteval`/`constinit` | |
| Structured bindings | | | ✓ | | |
| `std::optional` | | | ✓ | | |
| `std::variant` | | | ✓ | | |
| `std::string_view` | | | ✓ | | |
| Parallel STL | | | ✓ | | |
| Concepts | | | | ✓ | |
| Ranges | | | | ✓ | Extended |
| Coroutines | | | | ✓ | `std::generator` |
| Modules | | | | ✓ | `import std` |
| `std::expected` | | | | | ✓ |
| `std::print` | | | | | ✓ |

---

*Continue to*: [04_Templates_STL.md](04_Templates_STL.md) — Templates, template metaprogramming, SFINAE, and the complete STL.
