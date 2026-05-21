# 02 — C++ Core
## Classes, OOP, RAII, Inheritance, Polymorphism, Operator Overloading

---

## Table of Contents

1. [C vs C++ Key Differences](#1-c-vs-c-key-differences)
2. [Classes & Objects](#2-classes--objects)
3. [Constructors & Destructors](#3-constructors--destructors)
4. [RAII — Resource Acquisition Is Initialisation](#4-raii)
5. [The Rule of Zero / Three / Five](#5-rule-of-zero--three--five)
6. [Inheritance](#6-inheritance)
7. [Polymorphism & Virtual Functions](#7-polymorphism--virtual-functions)
8. [Abstract Classes & Interfaces](#8-abstract-classes--interfaces)
9. [Operator Overloading](#9-operator-overloading)
10. [References](#10-references)
11. [Namespaces](#11-namespaces)
12. [Exception Handling](#12-exception-handling)
13. [const Correctness](#13-const-correctness)
14. [static Members & Friend](#14-static-members--friend)
15. [Object Memory Layout](#15-object-memory-layout)

---

## 1. C vs C++ Key Differences

| Feature | C | C++ |
|---------|---|-----|
| Type system | Weak (void* conversion) | Strong (no implicit void* → T* conversion) |
| structs | Only data | Data + member functions |
| Polymorphism | Function pointers (manual) | `virtual` (automatic dispatch) |
| Memory safety | Manual `malloc`/`free` | Smart pointers, RAII |
| Generic code | Macros, void* | Templates |
| Error handling | Return codes | Exceptions (optional) + return codes |
| String handling | `char*` + `<string.h>` | `std::string` |
| Name mangling | No | Yes (enables overloading) |

---

## 2. Classes & Objects

### 2.1 Class vs Struct

```cpp
// In C++, struct and class are identical except for default access:
struct Point {      // Members default to public
    float x, y;
};

class Circle {      // Members default to private
    float radius_;
public:
    float getRadius() const { return radius_; }
};
```

### 2.2 Access Specifiers

```cpp
class MyClass {
public:
    // Accessible by anyone
    int value;
    void display();

protected:
    // Accessible by this class and derived classes
    void internalHelper();

private:
    // Accessible only by this class (and friends)
    int secret_;
};
```

### 2.3 Member Functions

```cpp
class Rectangle {
    float width_, height_;
public:
    Rectangle(float w, float h) : width_(w), height_(h) {}

    float area() const {      // const: this function doesn't modify the object
        return width_ * height_;
    }

    void scale(float factor) {  // Non-const: modifies the object
        width_  *= factor;
        height_ *= factor;
    }
};

Rectangle r(3.0f, 4.0f);
float a = r.area();    // 12.0
r.scale(2.0f);         // width=6, height=8
```

### 2.4 `this` Pointer

```cpp
class Builder {
    int value_ = 0;
public:
    Builder& setValue(int v) {
        value_ = v;
        return *this;    // Return self-reference for method chaining
    }
    Builder& setDouble() {
        value_ *= 2;
        return *this;
    }
};

Builder b;
b.setValue(5).setDouble();   // Chaining: value_ = 10
```

---

## 3. Constructors & Destructors

### 3.1 Constructor Types

```cpp
class Vector2D {
    float x_, y_;
public:
    // Default constructor
    Vector2D() : x_(0.0f), y_(0.0f) {}

    // Parameterised constructor
    Vector2D(float x, float y) : x_(x), y_(y) {}

    // Copy constructor — creates object from another of same type
    Vector2D(const Vector2D& other) : x_(other.x_), y_(other.y_) {}

    // Move constructor — "steals" resources from an rvalue (C++11)
    Vector2D(Vector2D&& other) noexcept : x_(other.x_), y_(other.y_) {
        other.x_ = other.y_ = 0.0f;  // Leave source in valid state
    }

    // Destructor — called when object goes out of scope or is deleted
    ~Vector2D() {
        // For simple types: nothing to do
        // For resource-owning types: release resources HERE
    }
};
```

### 3.2 Member Initialiser List

```cpp
class Config {
    const int    id_;     // const — MUST be initialised in initialiser list
    std::string  name_;
    int          count_;
public:
    // Initialiser list: faster than assignment in constructor body
    // Members initialised IN DECLARATION ORDER (not list order!)
    Config(int id, std::string name)
        : id_(id),            // const member — only way to set it
          name_(std::move(name)),  // Move instead of copy
          count_(0)
    {}
    // Body runs AFTER all members are constructed
};
```

### 3.3 Delegating Constructors (C++11)

```cpp
class Widget {
    int x_, y_, width_, height_;
public:
    Widget(int x, int y, int w, int h)
        : x_(x), y_(y), width_(w), height_(h) {}

    // Delegate to the full constructor
    Widget(int w, int h) : Widget(0, 0, w, h) {}
    Widget()             : Widget(100, 50)    {}
};
```

### 3.4 explicit Constructors

```cpp
class Radius {
    float val_;
public:
    explicit Radius(float v) : val_(v) {}  // Prevents implicit conversion
};

Radius r = 5.0f;   // ERROR: explicit prevents this
Radius r(5.0f);    // OK: direct initialisation
Radius r{5.0f};    // OK: direct-list initialisation

void drawCircle(Radius r);
drawCircle(5.0f);  // ERROR: explicit prevents implicit float→Radius conversion
```

### 3.5 Destructor

```cpp
class FileWrapper {
    FILE *file_;
public:
    FileWrapper(const char *path, const char *mode) {
        file_ = fopen(path, mode);
        if (!file_) throw std::runtime_error("Cannot open file");
    }

    ~FileWrapper() {
        if (file_) {
            fclose(file_);
            file_ = nullptr;
        }
    }
    // Destructor called automatically when FileWrapper goes out of scope
    // — even if an exception was thrown!
};
```

---

## 4. RAII

**Resource Acquisition Is Initialisation** — the most important C++ idiom.

### 4.1 The Concept

| Phase | Action |
|-------|--------|
| **Constructor** | Acquire the resource (open file, allocate memory, lock mutex) |
| **Lifetime** | Resource is valid — use it |
| **Destructor** | Release the resource (close file, free memory, unlock mutex) |

The destructor runs **regardless of how the scope is exited** — normal return, exception, or early return. This makes resource leaks nearly impossible with RAII.

### 4.2 RAII Mutex Lock

```cpp
class MutexLock {
    std::mutex& m_;
public:
    explicit MutexLock(std::mutex& m) : m_(m) { m_.lock(); }
    ~MutexLock() { m_.unlock(); }

    // Non-copyable, non-movable (resource semantics)
    MutexLock(const MutexLock&) = delete;
    MutexLock& operator=(const MutexLock&) = delete;
};

std::mutex mtx;
void safeFunction() {
    MutexLock lock(mtx);   // lock() called in constructor
    doWork();
    // lock destructor called here — unlock() guaranteed
    // (Even if doWork() throws)
}
// std::lock_guard<std::mutex> is the standard version of this pattern
```

### 4.3 RAII Dynamic Buffer

```cpp
class Buffer {
    uint8_t *data_;
    size_t   size_;
public:
    explicit Buffer(size_t n) : data_(new uint8_t[n]), size_(n) {}
    ~Buffer() { delete[] data_; }

    uint8_t* data() { return data_; }
    size_t   size() const { return size_; }
};
// std::vector<uint8_t> is the standard version
```

---

## 5. Rule of Zero / Three / Five

### 5.1 Rule of Zero

If your class manages no resources directly (uses RAII types like `std::string`, `std::vector`, smart pointers), declare NO special member functions — the compiler-generated ones are correct.

```cpp
class Sensor {
    std::string name_;
    std::vector<float> readings_;
    int id_;
public:
    Sensor(std::string name, int id) : name_(std::move(name)), id_(id) {}
    // Compiler generates correct: copy constructor, copy assignment,
    //   move constructor, move assignment, destructor
    // Nothing to write!
};
```

### 5.2 Rule of Three (C++03)

If you define any of: **destructor, copy constructor, copy assignment** — define all three.

```cpp
class RawBuffer {
    int *data_;
    size_t size_;
public:
    explicit RawBuffer(size_t n) : data_(new int[n]), size_(n) {}

    // Must define: destructor
    ~RawBuffer() { delete[] data_; }

    // Must define: copy constructor (deep copy)
    RawBuffer(const RawBuffer& other)
        : data_(new int[other.size_]), size_(other.size_) {
        std::copy(other.data_, other.data_ + size_, data_);
    }

    // Must define: copy assignment (deep copy + self-assignment guard)
    RawBuffer& operator=(const RawBuffer& other) {
        if (this != &other) {  // Guard against self-assignment
            delete[] data_;
            data_ = new int[other.size_];
            size_ = other.size_;
            std::copy(other.data_, other.data_ + size_, data_);
        }
        return *this;
    }
};
```

### 5.3 Rule of Five (C++11)

Extend Rule of Three with **move constructor** and **move assignment**:

```cpp
class RawBuffer {
    // ... (as above) ...

    // Move constructor — transfer ownership
    RawBuffer(RawBuffer&& other) noexcept
        : data_(other.data_), size_(other.size_) {
        other.data_ = nullptr;   // Source left in valid-but-empty state
        other.size_ = 0;
    }

    // Move assignment
    RawBuffer& operator=(RawBuffer&& other) noexcept {
        if (this != &other) {
            delete[] data_;         // Free existing
            data_ = other.data_;   // Steal
            size_ = other.size_;
            other.data_ = nullptr;
            other.size_ = 0;
        }
        return *this;
    }
};
```

### 5.4 = delete and = default

```cpp
class Singleton {
public:
    Singleton(const Singleton&) = delete;             // Prevent copying
    Singleton& operator=(const Singleton&) = delete;  // Prevent copy assignment
    Singleton(Singleton&&) = delete;                  // Prevent moving
    Singleton& operator=(Singleton&&) = delete;

    static Singleton& instance() {
        static Singleton s;
        return s;
    }
private:
    Singleton() = default;   // Compiler generates default constructor body
};
```

---

## 6. Inheritance

### 6.1 Basic Inheritance

```cpp
class Animal {
protected:
    std::string name_;
public:
    Animal(std::string name) : name_(std::move(name)) {}
    virtual ~Animal() = default;   // Virtual destructor — ALWAYS for base classes!

    virtual void speak() const {
        std::cout << name_ << " makes a sound\n";
    }
    const std::string& name() const { return name_; }
};

class Dog : public Animal {
    int tricks_;
public:
    Dog(std::string name) : Animal(std::move(name)), tricks_(0) {}

    void speak() const override {   // override — compiler checks it's actually virtual
        std::cout << name_ << " says: Woof!\n";
    }

    void learnTrick() { ++tricks_; }
};
```

### 6.2 Inheritance Types

```cpp
class Base { public: int x; protected: int y; private: int z; };

class PubDerived   : public    Base { };  // x→public, y→protected, z→inaccessible
class ProtDerived  : protected Base { };  // x→protected, y→protected, z→inaccessible
class PrivDerived  : private   Base { };  // x→private, y→private, z→inaccessible
```

Most commonly: `public` inheritance (IS-A relationship).

### 6.3 Constructor/Destructor Order

```cpp
// Construction: base → derived (top-down)
// Destruction:  derived → base (bottom-up)

class A { public: A() { puts("A()"); } ~A() { puts("~A()"); } };
class B : public A { public: B() { puts("B()"); } ~B() { puts("~B()"); } };
class C : public B { public: C() { puts("C()"); } ~C() { puts("~C()"); } };

C c;
// Output: A(), B(), C(), then ~C(), ~B(), ~A()
```

### 6.4 Multiple Inheritance & Virtual Base

```cpp
class Flyable { public: virtual void fly() = 0; };
class Swimmable { public: virtual void swim() = 0; };

class Duck : public Flyable, public Swimmable {
public:
    void fly()  override { puts("Duck flies"); }
    void swim() override { puts("Duck swims"); }
};

// Diamond problem:
class A { public: int x; };
class B : public A {};
class C : public A {};
class D : public B, public C {};  // D has TWO copies of A::x!
// D d; d.x = 5;  // ERROR: ambiguous

// Solution: virtual base class
class B2 : virtual public A {};
class C2 : virtual public A {};
class D2 : public B2, public C2 {};  // D2 has ONE copy of A::x
```

---

## 7. Polymorphism & Virtual Functions

### 7.1 How Virtual Dispatch Works (vtable)

```
Object memory layout with virtual functions:

class Base {
    virtual void foo();
    virtual void bar();
    int data_;
};

class Derived : public Base {
    void foo() override;  // Overrides Base::foo
    // bar() not overridden
};

Memory layout of Derived object:
┌─────────────────────────┐
│  vptr  (8 bytes)        │──► vtable for Derived
│  data_ (4 bytes)        │
└─────────────────────────┘

vtable for Derived:
┌──────────────────────────┐
│  Derived::foo() address  │  ← overridden
│  Base::bar()   address   │  ← not overridden, points to base
└──────────────────────────┘
```

### 7.2 Virtual Dispatch Example

```cpp
Animal *animals[] = { new Dog("Rex"), new Cat("Whiskers"), new Dog("Buddy") };

for (auto *a : animals) {
    a->speak();   // Virtual dispatch — calls the ACTUAL type's speak()
}
// Rex says: Woof!
// Whiskers says: Meow!
// Buddy says: Woof!
```

### 7.3 virtual Destructor — Why Critical

```cpp
class Base { public: ~Base() { puts("~Base"); } };
class Derived : public Base { int *data_; public: ~Derived() { delete[] data_; } };

Base *b = new Derived();
delete b;   // ONLY calls ~Base if destructor is NOT virtual — MEMORY LEAK!

// Fix:
class Base { public: virtual ~Base() { puts("~Base"); } };
// Now: ~Derived() is called first, then ~Base() — correct
```

**Rule**: Any class with virtual functions must have a `virtual` destructor.

### 7.4 override and final (C++11)

```cpp
class Base {
    virtual void foo(int x);
    virtual void bar();
};

class Derived : public Base {
    void foo(int x) override;  // Compiler verifies this overrides Base::foo(int)
    void bar() final;           // No further derived class can override bar()
    // void foo(float x) override;  // COMPILE ERROR: no such virtual in Base
};

class Sealed final : public Base { };  // No class can inherit from Sealed
```

---

## 8. Abstract Classes & Interfaces

```cpp
// Pure virtual function = 0 → class becomes abstract (cannot be instantiated)
class Shape {
public:
    virtual ~Shape() = default;

    virtual float area()      const = 0;   // Pure virtual — MUST be overridden
    virtual float perimeter() const = 0;
    virtual void  draw()      const = 0;

    // Non-pure virtual — has default, can be overridden
    virtual std::string describe() const {
        return "Shape with area=" + std::to_string(area());
    }
};

class Circle : public Shape {
    float radius_;
public:
    explicit Circle(float r) : radius_(r) {}
    float area()      const override { return 3.14159f * radius_ * radius_; }
    float perimeter() const override { return 2.0f * 3.14159f * radius_; }
    void  draw()      const override { puts("Drawing circle"); }
};

// Shape s;           // ERROR: cannot instantiate abstract class
Circle c(5.0f);       // OK: all pure virtuals implemented
Shape *s = &c;        // OK: pointer to base
s->area();            // Calls Circle::area() via vtable
```

### 8.1 Pure Interface Pattern

```cpp
// Interface: only pure virtuals, no data members, virtual destructor
class ILogger {
public:
    virtual ~ILogger() = default;
    virtual void log(const std::string& msg) = 0;
    virtual void flush() = 0;
};

class ConsoleLogger : public ILogger {
public:
    void log(const std::string& msg) override { std::cout << msg << '\n'; }
    void flush() override { std::cout.flush(); }
};

class FileLogger : public ILogger {
    std::ofstream file_;
public:
    explicit FileLogger(const std::string& path) : file_(path) {}
    void log(const std::string& msg) override { file_ << msg << '\n'; }
    void flush() override { file_.flush(); }
};

// Code depends on interface, not implementation:
void doWork(ILogger& logger) {
    logger.log("Starting work");
    // ...
    logger.log("Done");
}
```

---

## 9. Operator Overloading

### 9.1 Rules

- Cannot create new operators
- Cannot change precedence or associativity
- Cannot overload: `::` `.` `.*` `?:` `sizeof`
- At least one operand must be a user-defined type

### 9.2 Arithmetic Operators

```cpp
class Vec3 {
public:
    float x, y, z;

    Vec3(float x=0, float y=0, float z=0) : x(x), y(y), z(z) {}

    // Compound assignment (member function)
    Vec3& operator+=(const Vec3& rhs) {
        x += rhs.x; y += rhs.y; z += rhs.z;
        return *this;
    }

    // Binary + defined in terms of += (non-member, canonical pattern)
    friend Vec3 operator+(Vec3 lhs, const Vec3& rhs) {
        return lhs += rhs;   // lhs is a copy, so we can modify it
    }

    // Unary minus
    Vec3 operator-() const { return {-x, -y, -z}; }

    // Dot product (not an arithmetic operator — use named function or *, but be careful)
    float dot(const Vec3& rhs) const {
        return x*rhs.x + y*rhs.y + z*rhs.z;
    }
};
```

### 9.3 Comparison Operators

```cpp
// C++20 spaceship operator — generates all 6 comparisons
#include <compare>
struct Version {
    int major, minor, patch;
    auto operator<=>(const Version&) const = default;  // compiler generates all comparisons
};
Version v1{1,2,3}, v2{1,3,0};
if (v1 < v2) { ... }   // Works!

// C++17 and earlier: define manually
bool operator==(const Vec3& a, const Vec3& b) {
    return a.x == b.x && a.y == b.y && a.z == b.z;
}
bool operator!=(const Vec3& a, const Vec3& b) { return !(a == b); }
```

### 9.4 Stream Operators

```cpp
std::ostream& operator<<(std::ostream& os, const Vec3& v) {
    return os << '(' << v.x << ", " << v.y << ", " << v.z << ')';
}

std::istream& operator>>(std::istream& is, Vec3& v) {
    return is >> v.x >> v.y >> v.z;
}

Vec3 v{1, 2, 3};
std::cout << v;     // (1, 2, 3)
```

### 9.5 Subscript, Call, Dereference Operators

```cpp
// operator[] — array-like access
class Matrix {
    float data_[16];
public:
    float& operator[](size_t i)       { return data_[i]; }
    float  operator[](size_t i) const { return data_[i]; }
};

// operator() — function object (functor)
class Adder {
    int base_;
public:
    explicit Adder(int base) : base_(base) {}
    int operator()(int x) const { return base_ + x; }
};
Adder add5(5);
int r = add5(3);   // Calls operator()(3) → 8

// operator* and operator-> — smart pointer pattern
template <typename T>
class Ptr {
    T *raw_;
public:
    T& operator*()  const { return *raw_; }
    T* operator->() const { return raw_; }
};
```

### 9.6 Conversion Operators

```cpp
class Celsius {
    float temp_;
public:
    explicit Celsius(float t) : temp_(t) {}

    explicit operator float() const { return temp_; }  // explicit: no implicit conversion

    operator std::string() const {
        return std::to_string(temp_) + "°C";
    }
};

Celsius c(100.0f);
float f = static_cast<float>(c);   // Explicit conversion
std::string s = c;                 // Implicit (non-explicit operator)
```

---

## 10. References

### 10.1 Lvalue Reference

```cpp
int x = 5;
int& ref = x;   // ref is an alias for x
ref = 10;       // x is now 10
&ref == &x;     // true — same address

// References MUST be initialised and CANNOT be rebound
int& r;         // ERROR: must initialise
int& r = x;
r = y;          // Does NOT rebind r to y — assigns y's value to x!

// Use case: function out-parameter
void increment(int& n) { ++n; }
increment(x);   // x modified in-place
```

### 10.2 const Reference — Extends Lifetime

```cpp
// const reference can bind to rvalues (temporaries)
const int& r = 5;      // Creates a temporary int(5), binds r to it
// Temporary's lifetime extended to r's lifetime

// Use for read-only function parameters (avoids copy, accepts any value)
float computeNorm(const std::vector<float>& v);  // Accepts lvalue and const lvalue
```

### 10.3 Rvalue Reference (C++11)

```cpp
// Binds ONLY to rvalues (temporaries, std::move() results)
int&& rr = 5;          // OK: 5 is rvalue
int x = 5;
int&& rr2 = x;         // ERROR: x is lvalue
int&& rr3 = std::move(x);  // OK: std::move casts to rvalue

// Primary use: move constructors, move assignment operators
class String {
    char *data_;
public:
    String(String&& other) noexcept : data_(other.data_) {
        other.data_ = nullptr;  // Transfer ownership
    }
};
```

### 10.4 Reference Collapsing Rules

```
T&  &  → T&
T&  && → T&
T&& &  → T&
T&& && → T&&
```

Used in perfect forwarding with universal references (see `03_Modern_CPP.md §6`).

---

## 11. Namespaces

```cpp
// Prevent name collisions
namespace adas {
namespace perception {

class ObjectDetector { ... };
float computeTTC(float range, float closing_vel);

}  // namespace perception
}  // namespace adas

// Usage
adas::perception::ObjectDetector detector;
float ttc = adas::perception::computeTTC(40.0f, 10.0f);

// using declaration (imports one name)
using adas::perception::ObjectDetector;
ObjectDetector d;   // No prefix needed

// using directive (imports all names — use sparingly, never in headers)
using namespace adas::perception;

// Namespace alias
namespace ap = adas::perception;
ap::ObjectDetector d2;

// Anonymous namespace — internal linkage (replaces static at file scope in C++)
namespace {
    int helper_value = 42;   // Only visible in this translation unit
    void helperFn() { }
}
```

---

## 12. Exception Handling

### 12.1 throw / try / catch

```cpp
// throw: any copyable type (prefer deriving from std::exception)
class SensorError : public std::runtime_error {
public:
    explicit SensorError(const std::string& msg)
        : std::runtime_error("SensorError: " + msg) {}
};

// throw in constructor to signal failure
class CameraDriver {
public:
    CameraDriver(int id) {
        if (id < 0) throw SensorError("Invalid camera ID: " + std::to_string(id));
    }
};

// catch
try {
    CameraDriver cam(-1);
    cam.capture();
}
catch (const SensorError& e) {   // Catch by const reference — no slice, no copy
    std::cerr << e.what() << '\n';
}
catch (const std::exception& e) { // Catch base class
    std::cerr << "Error: " << e.what() << '\n';
}
catch (...) {                     // Catch anything (last resort)
    std::cerr << "Unknown exception\n";
}
```

### 12.2 noexcept

```cpp
// noexcept — function promises it won't throw
// If it does throw: std::terminate() is called immediately
void processData() noexcept { ... }

// noexcept(expr) — conditional
template <typename T>
void swap(T& a, T& b) noexcept(std::is_nothrow_move_constructible_v<T>) { ... }

// Important: destructors and move operations should be noexcept
// If move constructor can throw, std::vector cannot use it during reallocation
// → fallback to slower copy
```

### 12.3 Standard Exception Hierarchy

```
std::exception
    std::runtime_error
        std::range_error
        std::overflow_error
        std::underflow_error
        std::system_error
    std::logic_error
        std::invalid_argument
        std::domain_error
        std::length_error
        std::out_of_range
    std::bad_alloc        ← thrown by new
    std::bad_cast         ← thrown by dynamic_cast
    std::bad_typeid
    std::bad_exception
```

### 12.4 Exception Safety Guarantees

| Guarantee | Meaning |
|-----------|---------|
| **No-throw** (`noexcept`) | Function never throws |
| **Strong** | Operation either succeeds completely or leaves state unchanged |
| **Basic** | If exception thrown, object is in a valid (but unspecified) state; no leaks |
| **None** | No guarantee — object may be in invalid state |

```cpp
// Strong guarantee example (commit-or-rollback pattern)
void appendToVector(std::vector<int>& v, int val) {
    std::vector<int> tmp = v;   // Make a copy
    tmp.push_back(val);         // Modify the copy (may throw std::bad_alloc)
    v = std::move(tmp);         // Commit: noexcept move — cannot fail
}
// If push_back throws: v is untouched (strong guarantee)
```

---

## 13. const Correctness

```cpp
class Buffer {
    std::vector<uint8_t> data_;
public:
    // Non-const version: returns modifiable reference
    uint8_t& operator[](size_t i) {
        return data_[i];
    }

    // const version: called on const objects, returns const reference
    const uint8_t& operator[](size_t i) const {
        return data_[i];
    }

    // const member function: compiler verifies no modification of members
    size_t size() const { return data_.size(); }

    // mutable: modifiable even in const member function
    mutable int access_count_ = 0;
    size_t sizeTracked() const {
        ++access_count_;       // OK: mutable
        return data_.size();
    }
};

const Buffer b = createBuffer();
b[0];           // Calls const operator[]
b.size();       // OK: const member function
// b[0] = 5;   // ERROR: cannot modify through const reference
```

---

## 14. static Members & Friend

### 14.1 static Members

```cpp
class Counter {
    static int count_;          // Shared by ALL instances; must be defined outside
public:
    Counter()  { ++count_; }
    ~Counter() { --count_; }

    static int getCount() { return count_; }  // No 'this' pointer
};

int Counter::count_ = 0;   // Definition outside class (in .cpp file)

Counter c1, c2, c3;
Counter::getCount();   // 3
```

### 14.2 friend

```cpp
class Vec3 {
    float x_, y_, z_;
public:
    // Grant operator<< access to private members
    friend std::ostream& operator<<(std::ostream& os, const Vec3& v);

    // Grant another class access to private members
    friend class Vec3Builder;
};

std::ostream& operator<<(std::ostream& os, const Vec3& v) {
    return os << v.x_ << " " << v.y_ << " " << v.z_;  // Can access private!
}
```

---

## 15. Object Memory Layout

### 15.1 Plain Class (No Virtuals)

```cpp
class Point { float x, y; };
// Layout: [x:4 bytes][y:4 bytes] = 8 bytes total
// No overhead, same as C struct
```

### 15.2 Class with Virtual Functions

```cpp
class Base { int x; virtual void foo(); };
// Layout: [vptr:8 bytes][x:4 bytes][4 padding] = 16 bytes
//          vptr points to vtable in rodata segment

class Derived : public Base { int y; virtual void foo() override; virtual void bar(); };
// Layout: [vptr:8 bytes][x:4 bytes][y:4 bytes] = 16 bytes
//          vptr now points to Derived's vtable
```

### 15.3 sizeof Rules

```cpp
sizeof(int)          // 4
sizeof(void*)        // 8 (64-bit)
sizeof(Base)         // Includes vptr: 16 (not 4!)
sizeof(Derived)      // 16 (same as Base since y fits in same padding slot)

// Empty base optimisation (EBO):
class Empty {};
class HasMember : public Empty { int x; };
sizeof(HasMember) == sizeof(int)  // == 4 (compiler may apply EBO)
```

---

*Continue to*: [03_Modern_CPP.md](03_Modern_CPP.md) — C++11 through C++23: move semantics, smart pointers, lambdas, concepts, ranges, coroutines.
