# 04 — Templates & STL
## Templates, Metaprogramming, SFINAE, All Containers, Algorithms, Iterators

---

## Table of Contents

1. [Function Templates](#1-function-templates)
2. [Class Templates](#2-class-templates)
3. [Template Specialisation](#3-template-specialisation)
4. [Variadic Templates](#4-variadic-templates)
5. [Template Metaprogramming (TMP)](#5-template-metaprogramming)
6. [SFINAE & type_traits](#6-sfinae--type_traits)
7. [STL Architecture](#7-stl-architecture)
8. [Sequence Containers](#8-sequence-containers)
9. [Associative Containers](#9-associative-containers)
10. [Unordered Containers](#10-unordered-containers)
11. [Container Adaptors](#11-container-adaptors)
12. [Iterators](#12-iterators)
13. [STL Algorithms](#13-stl-algorithms)
14. [std::string & Related](#14-stdstring--related)
15. [Utilities: pair, tuple, optional, variant, any](#15-utilities)

---

## 1. Function Templates

### 1.1 Basic Function Template

```cpp
// Compiler generates a specific function for each T used
template <typename T>
T max_of(T a, T b) {
    return a > b ? a : b;
}

max_of(3, 5);           // T=int deduced
max_of(3.0, 5.0);       // T=double deduced
max_of<float>(3, 5.0f); // T=float: explicit
// max_of(3, 5.0);      // DEDUCTION FAILURE: ambiguous int vs double
```

### 1.2 Non-Type Template Parameters

```cpp
// Template parameter that is a value, not a type
template <typename T, size_t N>
T sum(const T (&arr)[N]) {   // Reference to array of N elements
    T result = T{};
    for (size_t i = 0; i < N; i++) result += arr[i];
    return result;
}

int arr[] = {1, 2, 3, 4, 5};
sum(arr);   // T=int, N=5 deduced — returns 15
```

### 1.3 Template Template Parameters

```cpp
template <typename T, template <typename> class Container>
class Stack {
    Container<T> data_;
public:
    void push(const T& v) { data_.push_back(v); }
    T    pop()  { T v = data_.back(); data_.pop_back(); return v; }
};

Stack<int, std::vector> int_stack;
Stack<int, std::deque>  deq_stack;
```

---

## 2. Class Templates

### 2.1 Class Template Basics

```cpp
template <typename T>
class Optional {
    bool has_value_;
    alignas(T) unsigned char storage_[sizeof(T)];
public:
    Optional() : has_value_(false) {}

    Optional(const T& val) : has_value_(true) {
        new (storage_) T(val);   // Placement new
    }

    ~Optional() {
        if (has_value_) reinterpret_cast<T*>(storage_)->~T();
    }

    bool has_value() const { return has_value_; }

    T& value() {
        if (!has_value_) throw std::bad_optional_access{};
        return *reinterpret_cast<T*>(storage_);
    }
};

Optional<int> o1;
Optional<int> o2(42);
o2.value();   // 42
```

### 2.2 Member Function Templates

```cpp
template <typename T>
class Converter {
public:
    T value;

    // Member function template — different type than class type
    template <typename U>
    Converter(const Converter<U>& other)
        : value(static_cast<T>(other.value)) {}  // Cross-type conversion
};

Converter<double> d{ .value = 3.14 };
Converter<int> i(d);   // value = 3
```

### 2.3 Default Template Arguments

```cpp
template <typename T, typename Allocator = std::allocator<T>>
class MyVector { ... };

MyVector<int>                     v1;  // Uses default allocator
MyVector<int, PoolAllocator<int>> v2;  // Custom allocator
```

---

## 3. Template Specialisation

### 3.1 Full Specialisation

```cpp
// Primary template
template <typename T>
struct Serialiser {
    static std::string to_string(const T& v) {
        return std::to_string(v);
    }
};

// Full specialisation for std::string (T is known completely)
template <>
struct Serialiser<std::string> {
    static std::string to_string(const std::string& v) {
        return '"' + v + '"';   // Wrap in quotes
    }
};

// Full specialisation for bool
template <>
struct Serialiser<bool> {
    static std::string to_string(bool v) {
        return v ? "true" : "false";
    }
};
```

### 3.2 Partial Specialisation

```cpp
// Primary template
template <typename T>
struct IsPointer { static constexpr bool value = false; };

// Partial specialisation: matches any T*
template <typename T>
struct IsPointer<T*> { static constexpr bool value = true; };

// Partial specialisation: matches any const T*
template <typename T>
struct IsPointer<const T*> { static constexpr bool value = true; };

IsPointer<int>::value;       // false
IsPointer<int*>::value;      // true
IsPointer<const int*>::value;// true

// Real world: specialize for std::vector<bool> (done in standard library)
template <typename Allocator>
class vector<bool, Allocator> { ... };  // Packed bit storage
```

---

## 4. Variadic Templates

### 4.1 Parameter Packs

```cpp
// Accepts any number of arguments of any types
template <typename... Args>
void printAll(Args&&... args) {
    (std::cout << ... << args) << '\n';   // Fold expression (C++17)
}

printAll(1, " + ", 2, " = ", 3);   // 1 + 2 = 3
```

### 4.2 Recursive Variadic (C++11 style)

```cpp
// Base case
void print() {}

// Recursive case: peel off first argument
template <typename First, typename... Rest>
void print(First&& first, Rest&&... rest) {
    std::cout << first << ' ';
    print(std::forward<Rest>(rest)...);  // Recurse with remaining
}
```

### 4.3 std::tuple Internals (concept)

```cpp
// tuple<int, double, std::string> is like:
struct Tuple3 {
    int    elem0;
    double elem1;
    std::string elem2;
};

// Actual implementation uses recursive inheritance
template <typename... Types>
struct tuple;

template <typename Head, typename... Tail>
struct tuple<Head, Tail...> : tuple<Tail...> {
    Head value;
};

template <>
struct tuple<> {};   // Base case

// std::get<0>(t) accesses value at index 0
std::tuple<int, double, std::string> t(42, 3.14, "hello");
std::get<0>(t);   // 42
std::get<2>(t);   // "hello"
```

### 4.4 Index Sequences (for tuple iteration)

```cpp
template <typename Tuple, size_t... I>
void printTupleImpl(const Tuple& t, std::index_sequence<I...>) {
    ((std::cout << std::get<I>(t) << ' '), ...);
}

template <typename... Args>
void printTuple(const std::tuple<Args...>& t) {
    printTupleImpl(t, std::make_index_sequence<sizeof...(Args)>{});
}
```

---

## 5. Template Metaprogramming

TMP uses the template system as a compile-time computation engine.

### 5.1 Compile-Time Values

```cpp
// Compile-time factorial (classic TMP)
template <unsigned N>
struct Factorial {
    static constexpr unsigned value = N * Factorial<N-1>::value;
};

template <>
struct Factorial<0> {
    static constexpr unsigned value = 1;
};

static_assert(Factorial<5>::value == 120);

// Modern: use constexpr function (cleaner)
constexpr unsigned factorial(unsigned n) {
    return n == 0 ? 1 : n * factorial(n-1);
}
```

### 5.2 Type Lists

```cpp
// A list of types at compile time
template <typename... Ts>
struct TypeList {};

using MyTypes = TypeList<int, double, std::string, float>;

// Get the Nth type
template <size_t N, typename List>
struct TypeAt;

template <size_t N, typename Head, typename... Tail>
struct TypeAt<N, TypeList<Head, Tail...>> {
    using type = typename TypeAt<N-1, TypeList<Tail...>>::type;
};

template <typename Head, typename... Tail>
struct TypeAt<0, TypeList<Head, Tail...>> {
    using type = Head;
};

// TypeAt<2, MyTypes>::type → std::string
```

---

## 6. SFINAE & type_traits

### 6.1 SFINAE (Substitution Failure Is Not An Error)

When template substitution fails, the compiler doesn't error — it just removes that candidate from overload resolution.

```cpp
// Enable a function only for integer types (C++11 style)
template <typename T>
typename std::enable_if<std::is_integral<T>::value, T>::type
only_for_ints(T x) {
    return x * 2;
}

only_for_ints(5);      // Works: int is integral
// only_for_ints(5.0); // SFINAE removes this overload → "no matching function"
```

### 6.2 C++17 SFINAE with if constexpr (Modern)

```cpp
// Much cleaner than enable_if for same purpose:
template <typename T>
auto process(T x) {
    if constexpr (std::is_integral_v<T>) {
        return x * 2;
    } else if constexpr (std::is_floating_point_v<T>) {
        return x * 2.0;
    } else {
        return x;
    }
}
```

### 6.3 std::type_traits Catalogue

```cpp
#include <type_traits>

// Type categories
std::is_integral_v<T>           // int, char, bool, etc.
std::is_floating_point_v<T>     // float, double, long double
std::is_arithmetic_v<T>         // integral or floating_point
std::is_pointer_v<T>
std::is_reference_v<T>
std::is_const_v<T>
std::is_void_v<T>
std::is_enum_v<T>
std::is_class_v<T>
std::is_function_v<T>
std::is_trivial_v<T>
std::is_trivially_copyable_v<T>
std::is_standard_layout_v<T>

// Type relationships
std::is_same_v<T, U>
std::is_base_of_v<Base, Derived>
std::is_convertible_v<From, To>
std::is_constructible_v<T, Args...>
std::is_destructible_v<T>

// Type modifications
std::remove_const_t<const int>      // int
std::remove_reference_t<int&>       // int
std::add_pointer_t<int>             // int*
std::decay_t<int[5]>                // int* (array → pointer)
std::common_type_t<int, double>     // double
std::underlying_type_t<MyEnum>      // int (or whatever enum's base is)

// noexcept properties
std::is_nothrow_constructible_v<T>
std::is_nothrow_move_constructible_v<T>
std::is_nothrow_destructible_v<T>
```

### 6.4 Custom Traits

```cpp
// Check if type has a serialize() method
template <typename T, typename = void>
struct has_serialize : std::false_type {};

template <typename T>
struct has_serialize<T, std::void_t<decltype(std::declval<T>().serialize())>>
    : std::true_type {};

template <typename T>
void save(const T& obj) {
    if constexpr (has_serialize<T>::value) {
        obj.serialize();
    } else {
        // fallback
    }
}
```

---

## 7. STL Architecture

```
STL has three pillars:
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Containers  │◄──►│  Iterators   │◄──►│  Algorithms  │
│  (store data)│    │  (bridge)    │    │  (operate)   │
└──────────────┘    └──────────────┘    └──────────────┘
     ▲                                       ▲
     └─────────── Allocators ────────────────┘
```

Algorithms work with any container through iterators — completely generic.

---

## 8. Sequence Containers

### 8.1 std::vector

```cpp
#include <vector>

std::vector<int> v;
v.reserve(100);          // Pre-allocate capacity; NO elements added
v.resize(50);            // Set size to 50 (fills with 0)

v.push_back(42);         // Add to end — O(amortised 1)
v.emplace_back(42);      // Construct in-place (faster for complex types)
v.insert(v.begin()+2, 99);  // Insert at index 2 — O(n)
v.erase(v.begin()+2);    // Erase at index 2 — O(n)
v.pop_back();            // Remove last — O(1)
v.clear();               // Remove all (capacity unchanged)

v[0];                    // Unchecked access — UB if out of bounds
v.at(0);                 // Checked access — throws std::out_of_range
v.front(); v.back();     // First / last element
v.data();                // Pointer to underlying array
v.size();                // Number of elements
v.capacity();            // Allocated capacity
v.empty();               // size() == 0

// Internals:
// - Contiguous memory (cache-friendly)
// - Doubles capacity when full → amortised O(1) push_back
// - push_back may invalidate ALL iterators/pointers if reallocation
// - insert/erase invalidate iterators at/after the position
```

### 8.2 std::array (C++11)

```cpp
#include <array>

std::array<int, 5> arr = {1, 2, 3, 4, 5};   // Fixed size, stack-allocated
arr.size();       // 5 — compile-time constant
arr.fill(0);      // Set all elements to 0
arr[0];           // Unchecked
arr.at(0);        // Checked

// Unlike C array:
// - Has begin/end/size
// - Can be passed to algorithms
// - Can be returned from functions
// - Never decays to pointer
```

### 8.3 std::deque

```cpp
#include <deque>

std::deque<int> d;
d.push_front(1);    // Efficient O(1) front insertion (unlike vector)
d.push_back(2);
d.pop_front();
d.pop_back();
d[0];               // Random access — O(1) but not contiguous memory

// Internals: array of fixed-size chunks; pointer map to chunks
// Memory NOT contiguous → worse cache performance than vector
// Use when: frequent insertion/deletion at BOTH ends
```

### 8.4 std::list

```cpp
#include <list>

std::list<int> lst = {1, 2, 3};
lst.push_front(0); lst.push_back(4);
lst.pop_front();   lst.pop_back();

auto it = lst.begin();
std::advance(it, 2);       // Move iterator forward 2 — O(2)
lst.insert(it, 99);        // O(1) if you have iterator — no shifting!
lst.erase(it);             // O(1)

lst.sort();                // Member sort (can't use std::sort — no random access)
lst.merge(other_lst);      // Merge sorted lists O(n)
lst.unique();              // Remove consecutive duplicates

// Internals: doubly-linked list
// No random access — O(n) to reach element i
// Iterators NEVER invalidated (except for erased elements)
// High memory overhead: each node has prev/next pointers
// Use when: frequent insertion/deletion in MIDDLE with pre-held iterator
```

### 8.5 std::forward_list (C++11)

```cpp
// Singly-linked list — lower overhead than std::list
std::forward_list<int> fl = {1, 2, 3};
fl.push_front(0);
fl.insert_after(fl.begin(), 99);  // Insert AFTER given position
fl.erase_after(fl.begin());       // Erase AFTER given position

// No size() method, no push_back
// Use when: lowest overhead singly-linked list needed
```

---

## 9. Associative Containers

All store elements in **sorted order** (red-black tree internally).

### 9.1 std::map

```cpp
#include <map>

std::map<std::string, int> scores;

scores["Alice"] = 95;              // Insert or update
scores.insert({"Bob", 87});        // Insert (does NOT overwrite if key exists)
scores.emplace("Charlie", 92);     // Construct in-place

scores.find("Alice");              // Returns iterator; end() if not found
scores.count("Alice");             // 0 or 1 (map has unique keys)
scores.contains("Alice");          // C++20: bool
scores.at("Alice");                // 95; throws if not found
scores["Alice"];                   // Creates default (0) if not present!

scores.erase("Bob");               // Erase by key — O(log n)
scores.erase(scores.begin());      // Erase by iterator — O(1) amortised

for (auto& [key, val] : scores) { ... }  // Iterates in sorted key order

// Internals: red-black tree; O(log n) for find/insert/erase
// Keys always sorted; no duplicates
```

### 9.2 std::multimap

```cpp
std::multimap<int, std::string> mm;
mm.insert({5, "five"});
mm.insert({5, "cinco"});   // Duplicate key allowed!
mm.count(5);               // 2
mm.equal_range(5);         // Returns pair<it,it> for all elements with key 5
```

### 9.3 std::set

```cpp
std::set<int> s = {3, 1, 4, 1, 5, 9};  // {1, 3, 4, 5, 9} — duplicates removed, sorted
s.insert(6);
s.erase(3);
s.count(4);    // 0 or 1
s.find(4);     // iterator

// std::multiset allows duplicates
```

---

## 10. Unordered Containers

Hash-based; average O(1) operations but worst-case O(n) on hash collision.

### 10.1 std::unordered_map

```cpp
#include <unordered_map>

std::unordered_map<std::string, int> umap;
umap["key"] = 42;
umap.find("key");    // Average O(1); O(n) worst case
umap.count("key");
umap.erase("key");

// Internals: array of buckets; each bucket is a linked list
// load_factor = size / bucket_count
// Rehash when load_factor > max_load_factor (default 1.0)
umap.reserve(100);              // Pre-allocate for ~100 elements
umap.max_load_factor(0.7f);     // Rehash sooner

// Custom hash and equality
struct MyHash {
    size_t operator()(const MyKey& k) const {
        return std::hash<int>{}(k.id) ^ (std::hash<std::string>{}(k.name) << 1);
    }
};
std::unordered_map<MyKey, Value, MyHash> custom_map;
```

### 10.2 Ordered vs Unordered — When to Use

| Container | Access | Insert/Erase | Sorted | Use When |
|-----------|--------|-------------|--------|---------|
| `std::map` | O(log n) | O(log n) | Yes | Need sorted order, range queries |
| `std::unordered_map` | O(1) avg | O(1) avg | No | Fast lookup, no ordering needed |

---

## 11. Container Adaptors

Built on top of other containers, expose restricted interface.

### 11.1 std::stack (LIFO)

```cpp
#include <stack>

std::stack<int> s;           // Default: uses deque
std::stack<int, std::vector<int>> vs;  // Use vector as underlying
s.push(1); s.push(2);
s.top();    // 2 (peek, no removal)
s.pop();    // Remove top (no return value!)
s.size();   s.empty();
```

### 11.2 std::queue (FIFO)

```cpp
#include <queue>

std::queue<int> q;   // Default: uses deque
q.push(1); q.push(2);
q.front();  // 1 (peek front)
q.back();   // 2 (peek back)
q.pop();    // Remove front
```

### 11.3 std::priority_queue

```cpp
#include <queue>

std::priority_queue<int> pq;          // Max-heap by default
pq.push(3); pq.push(1); pq.push(4);
pq.top();   // 4 (max element)
pq.pop();   // Remove max

// Min-heap:
std::priority_queue<int, std::vector<int>, std::greater<int>> min_pq;
```

---

## 12. Iterators

### 12.1 Iterator Categories

| Category | Operations | Examples |
|----------|-----------|---------|
| **Input** | Read once, advance | `std::istream_iterator` |
| **Output** | Write once, advance | `std::ostream_iterator` |
| **Forward** | Read/write, multi-pass, advance | `std::forward_list::iterator` |
| **Bidirectional** | Forward + `--` | `std::list::iterator`, `std::map::iterator` |
| **Random Access** | Bidirectional + `+n`, `-n`, `[]` | `std::vector::iterator`, `T*` |
| **Contiguous** (C++17) | Random access + data is contiguous | `std::vector::iterator` |

### 12.2 Iterator Usage

```cpp
std::vector<int> v = {1, 2, 3, 4, 5};

// Manual iteration
for (auto it = v.begin(); it != v.end(); ++it) {
    std::cout << *it << ' ';
}

// Reverse
for (auto it = v.rbegin(); it != v.rend(); ++it) { ... }

// Const iterators
for (auto it = v.cbegin(); it != v.cend(); ++it) { ... }

// std::advance and std::distance
auto it = v.begin();
std::advance(it, 3);         // it now points to v[3]
std::distance(v.begin(), it); // 3
auto it2 = std::next(it, 2); // Copy of it advanced by 2
auto it3 = std::prev(it, 1); // Copy of it retreated by 1
```

### 12.3 Insert Iterators

```cpp
std::vector<int> dst;

// Back inserter — calls push_back
std::back_insert_iterator<std::vector<int>> bi(dst);
*bi = 42;   // dst.push_back(42)
++bi;

// Or use helper:
std::copy(src.begin(), src.end(), std::back_inserter(dst));

// Front inserter — calls push_front (for deque, list)
std::front_inserter(deq);

// General insert — calls insert at given position
std::inserter(s, s.begin());   // For std::set
```

---

## 13. STL Algorithms

All in `<algorithm>` (and `<numeric>`). Work on **iterator ranges** `[first, last)`.

### 13.1 Non-Modifying Algorithms

```cpp
std::find(first, last, val)         // Find value; returns iterator (or last)
std::find_if(first, last, pred)     // Find first element satisfying pred
std::count(first, last, val)        // Count occurrences
std::count_if(first, last, pred)
std::all_of(first, last, pred)      // All elements satisfy pred
std::any_of(first, last, pred)      // At least one satisfies pred
std::none_of(first, last, pred)
std::for_each(first, last, fn)      // Apply fn to each element
std::equal(f1, l1, f2)             // Two ranges are equal
std::mismatch(f1, l1, f2)         // First mismatching pair
std::search(f1, l1, f2, l2)       // Find subsequence
```

### 13.2 Modifying Algorithms

```cpp
std::copy(first, last, dest)
std::copy_if(first, last, dest, pred)
std::move(first, last, dest)        // Move elements
std::transform(first, last, dest, unary_op)
std::transform(f1, l1, f2, dest, binary_op)  // Two-range version
std::replace(first, last, old_val, new_val)
std::replace_if(first, last, pred, new_val)
std::fill(first, last, val)
std::generate(first, last, gen)     // Fill with generated values
std::remove(first, last, val)       // "Remove" (moves non-matching to front, returns new end)
std::remove_if(first, last, pred)
std::unique(first, last)            // Remove consecutive duplicates
std::reverse(first, last)
std::rotate(first, new_first, last)
std::shuffle(first, last, rng)      // Random shuffle

// IMPORTANT: remove/remove_if do NOT erase — use the erase-remove idiom:
v.erase(std::remove(v.begin(), v.end(), val), v.end());
// C++20: std::erase(v, val); — cleaner
```

### 13.3 Sorting Algorithms

```cpp
std::sort(first, last)              // Introsort — O(n log n) average and worst
std::sort(first, last, comp)        // With custom comparator
std::stable_sort(first, last)       // Stable sort — preserves relative order of equals
std::partial_sort(first, middle, last)  // Sort [first, middle), rest unordered
std::nth_element(first, nth, last)  // nth element in sorted position; O(n) average
std::is_sorted(first, last)
std::binary_search(first, last, val)   // Requires sorted range — O(log n)
std::lower_bound(first, last, val)     // First element >= val
std::upper_bound(first, last, val)     // First element > val
std::equal_range(first, last, val)     // [lower_bound, upper_bound)
```

### 13.4 Numeric Algorithms (`<numeric>`)

```cpp
std::accumulate(first, last, init)          // Sum (or any binary op)
std::accumulate(first, last, init, op)
std::inner_product(f1, l1, f2, init)        // Dot product
std::partial_sum(first, last, dest)         // Prefix sums
std::adjacent_difference(first, last, dest) // Differences
std::iota(first, last, val)                 // Fill with val, val+1, val+2, ...

// C++17 parallel numeric
std::reduce(first, last, init)              // Like accumulate but parallelisable
std::transform_reduce(f1, l1, f2, init)    // transform + reduce in one pass
std::inclusive_scan(first, last, dest)
std::exclusive_scan(first, last, dest, init)
```

### 13.5 Set Algorithms

```cpp
// All require sorted ranges
std::set_union(f1, l1, f2, l2, dest)
std::set_intersection(f1, l1, f2, l2, dest)
std::set_difference(f1, l1, f2, l2, dest)
std::set_symmetric_difference(f1, l1, f2, l2, dest)
std::includes(f1, l1, f2, l2)         // Is range2 a subset of range1?
std::merge(f1, l1, f2, l2, dest)      // Merge two sorted ranges
```

---

## 14. std::string & Related

### 14.1 std::string Operations

```cpp
#include <string>

std::string s = "Hello, World!";
s.size();               // 13
s.length();             // 13 (same as size)
s.empty();              // false
s.capacity();           // >= 13 (often 15 due to SSO)

s[0];                   // 'H' (unchecked)
s.at(0);                // 'H' (checked)
s.front();              // 'H'
s.back();               // '!'

s.substr(7, 5);         // "World" (start, length)
s.find("World");        // 7 (position); std::string::npos if not found
s.rfind('l');           // Last 'l' position
s.find_first_of("aeiou"); // First vowel position
s.find_last_not_of(" \t"); // Trim helper

s += " Bye";            // Append
s.append(" Bye");       // Same
s.insert(7, "Beautiful ");  // Insert at position
s.erase(7, 10);         // Erase 10 chars at pos 7
s.replace(0, 5, "Hi");  // Replace "Hello" with "Hi"

s.c_str();              // Null-terminated const char*
s.data();               // Non-null-terminated pointer (C++11: same as c_str())

// Conversion
std::stoi("42");        // string → int
std::stof("3.14");      // string → float
std::to_string(42);     // int → string
```

### 14.2 Small String Optimisation (SSO)

Most `std::string` implementations store short strings (≤ 15-23 chars typically) directly inside the string object itself (no heap allocation). This makes small strings essentially free in terms of allocation.

```cpp
std::string short_s = "hello";   // Stored in SSO buffer — NO heap allocation
std::string long_s  = "This string is longer than 15 characters"; // Heap allocated
```

### 14.3 std::string_view

```cpp
// Non-owning reference to a string segment — O(1) substr, no allocation
void process(std::string_view sv);   // Accepts const char*, std::string, substring

std::string s = "Hello, World";
std::string_view sv(s.data() + 7, 5);  // "World" — points into s
sv.remove_prefix(2);  // "rld" — adjusts pointer, no copy
```

---

## 15. Utilities

### 15.1 std::pair

```cpp
std::pair<int, std::string> p = {42, "answer"};
p.first;   // 42
p.second;  // "answer"

auto p2 = std::make_pair(1, 2.5);   // Deduced: pair<int, double>
auto [a, b] = p;   // C++17 structured bindings
```

### 15.2 std::tuple

```cpp
#include <tuple>

auto t = std::make_tuple(1, 2.5, std::string("hi"));
std::get<0>(t);   // 1
std::get<1>(t);   // 2.5
std::get<std::string>(t);  // "hi" — by type (C++14)

std::tuple_size<decltype(t)>::value;  // 3

// Unpack
auto [x, y, z] = t;   // C++17

// std::tie — unpack into existing variables
int a; double b; std::string c;
std::tie(a, b, c) = t;

// std::tie for lexicographic comparison
struct Record { int id; std::string name; };
bool operator<(const Record& a, const Record& b) {
    return std::tie(a.id, a.name) < std::tie(b.id, b.name);
}
```

### 15.3 std::optional (C++17)

```cpp
#include <optional>

std::optional<int> safe_sqrt(double x) {
    if (x < 0) return std::nullopt;
    return static_cast<int>(std::sqrt(x));
}

auto r = safe_sqrt(16.0);
r.has_value();      // true
*r;                 // 4
r.value();          // 4
r.value_or(0);      // 4 (or 0 if empty)

// Monadic (C++23)
auto doubled = safe_sqrt(16.0).transform([](int x) { return x * 2; });  // optional<int>{8}
```

### 15.4 std::variant (C++17)

```cpp
#include <variant>

using Token = std::variant<int, double, std::string>;

Token t = 42;
std::holds_alternative<int>(t);    // true
std::get<int>(t);                  // 42
t.index();                         // 0

// Type-safe visitor pattern
struct Printer {
    void operator()(int i)               const { std::cout << "int: " << i; }
    void operator()(double d)            const { std::cout << "double: " << d; }
    void operator()(const std::string& s) const { std::cout << "string: " << s; }
};

std::visit(Printer{}, t);   // Calls the right overload
```

### 15.5 std::function

```cpp
#include <functional>

std::function<int(int, int)> fn;     // Type-erased callable
fn = [](int a, int b) { return a + b; };
fn(3, 4);   // 7

fn = std::plus<int>{};   // Standard functor
fn(3, 4);   // 7

// std::function has overhead (virtual dispatch internally)
// For single-call-site callbacks, prefer template + lambda
// For stored, heterogeneous callbacks: std::function is appropriate
```

---

*Continue to*: [05_Concurrency_Memory.md](05_Concurrency_Memory.md) — threading, atomics, lock-free patterns, and the C++ memory model.
